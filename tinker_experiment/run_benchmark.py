"""Evaluate deterministic and available Tinker model artifacts on held-out data."""

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rapidfuzz import fuzz
from backend.app.ai.fallback_engine import FallbackNormalizer


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def empty_model_result(name: str, reason: str) -> Dict[str, Any]:
    return {"name": name, "status": "not_run", "reason": reason, "metrics": None}


def measured_metrics(name: str, predictions: List[Optional[Dict[str, Any]]], test_data: List[Dict[str, Any]], latencies: List[float]) -> Dict[str, Any]:
    valid_predictions = [prediction for prediction in predictions if prediction is not None]
    field_names = ["pack_quantity", "pack_unit", "size", "canonical_description"]
    correct = 0
    total = len(test_data) * len(field_names)
    false_merges = 0
    for item, prediction in zip(test_data, predictions):
        target = item["target"]
        if prediction is None:
            continue
        correct += sum(
            prediction.get(field) == target.get(field)
            if field != "canonical_description"
            else fuzz.token_set_ratio(
                str(prediction.get(field, "")).lower(), str(target.get(field, "")).lower()
            ) > 80
            for field in field_names
        )
        if target.get("pack_quantity") == 200 and prediction.get("pack_quantity") != 200:
            false_merges += 1
    latencies = sorted(latencies)
    metrics = {
        "name": name,
        "status": "measured",
        "exact_structured_field_acc": round(correct / total * 100, 2) if total else 0.0,
        "json_validity_rate": round(len(valid_predictions) / len(test_data) * 100, 2) if test_data else 0.0,
        "false_merge_rate": round(false_merges / len(test_data) * 100, 2) if test_data else 0.0,
        "p50_latency_ms": round(latencies[len(latencies) // 2], 2) if latencies else None,
        "p95_latency_ms": round(latencies[min(len(latencies) - 1, int(len(latencies) * 0.95))], 2) if latencies else None,
        "sample_count": len(test_data),
    }
    return metrics


def evaluate_fallback(test_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    predictions = []
    latencies = []
    for item in test_data:
        start = time.perf_counter()
        predictions.append(FallbackNormalizer.normalize(item["input"]["supplier_description"], item["input"].get("supplier_sku")))
        latencies.append((time.perf_counter() - start) * 1000)
    result = measured_metrics("Baseline A (Deterministic Normalization)", predictions, test_data, latencies)
    result["cost_per_1k_lines"] = 0.0
    return result


def parse_prediction(text: str) -> Optional[Dict[str, Any]]:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        value = json.loads(text[start : end + 1])
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        return None


def format_prompt(example: Dict[str, Any]) -> str:
    inp = example["input"]
    return (
        "You are MarginLeak Normalizer. Output only JSON with canonical_description, pack_quantity, "
        "pack_unit, size, attributes, and uncertain_fields.\n"
        f"Supplier Description: {json.dumps(inp['supplier_description'])}\n"
        f"Supplier SKU: {json.dumps(inp.get('supplier_sku'))}\n"
    )


def evaluate_sampling_client(client: Any, tokenizer: Any, name: str, test_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    import tinker

    predictions: List[Optional[Dict[str, Any]]] = []
    latencies: List[float] = []
    params = tinker.types.SamplingParams(max_tokens=256, temperature=0.0)
    for item in test_data:
        start = time.perf_counter()
        response = client.sample(
            tinker.types.ModelInput.from_ints(tokenizer.encode(format_prompt(item))),
            1,
            params,
        ).result()
        sequence = response.sequences[0]
        text = tokenizer.decode(sequence.tokens)
        predictions.append(parse_prediction(text))
        latencies.append((time.perf_counter() - start) * 1000)
    return measured_metrics(name, predictions, test_data, latencies)


def build_client(service_client: Any, model_path: Optional[str], base_model: Optional[str]) -> Any:
    if model_path:
        return service_client.create_sampling_client(model_path=model_path)
    if base_model:
        return service_client.create_sampling_client(base_model=base_model)
    return None


def run_heldout_benchmark() -> None:
    parser = argparse.ArgumentParser(description="Measured MarginLeak held-out benchmark")
    parser.add_argument("--base-model", help="Tinker base model for zero-shot evaluation")
    parser.add_argument("--tinker-model-path", help="Persistent Tinker sampler path from training")
    parser.add_argument("--api-key", default=os.getenv("TINKER_API_KEY"))
    args = parser.parse_args()

    test_data = load_jsonl(os.path.join(os.path.dirname(__file__), "data", "test_heldout.jsonl"))
    base_a = evaluate_fallback(test_data)
    base_b = empty_model_result("Baseline B (Base Model)", "Pass --base-model and TINKER_API_KEY to run inference")
    cand_c = empty_model_result("Candidate C (Tinker LoRA)", "Pass --tinker-model-path and TINKER_API_KEY to run inference")

    if args.api_key and (args.base_model or args.tinker_model_path):
        import tinker

        service_client = tinker.ServiceClient(api_key=args.api_key)
        if args.base_model:
            base_client = build_client(service_client, None, args.base_model)
            base_b["metrics"] = evaluate_sampling_client(base_client, base_client.get_tokenizer(), base_b["name"], test_data)
            base_b["status"] = "measured"
        if args.tinker_model_path:
            candidate_client = build_client(service_client, args.tinker_model_path, None)
            cand_c["metrics"] = evaluate_sampling_client(candidate_client, candidate_client.get_tokenizer(), cand_c["name"], test_data)
            cand_c["status"] = "measured"

    improvements = None
    if base_b.get("metrics") and cand_c.get("metrics"):
        improvements = {
            "field_accuracy_gain_pts": round(cand_c["metrics"]["exact_structured_field_acc"] - base_b["metrics"]["exact_structured_field_acc"], 2),
            "false_merge_reduction_pct": round(((base_b["metrics"]["false_merge_rate"] - cand_c["metrics"]["false_merge_rate"]) / base_b["metrics"]["false_merge_rate"] * 100), 2) if base_b["metrics"]["false_merge_rate"] else None,
            "json_reliability_gain_pts": round(cand_c["metrics"]["json_validity_rate"] - base_b["metrics"]["json_validity_rate"], 2),
        }
    results = {
        "model_name": "Qwen/Qwen3-8B (measured Tinker evaluation)",
        "dataset_version": "v1.2-heldout",
        "held_out_samples_evaluated": len(test_data),
        "metrics": {
            "baseline_a_deterministic": base_a,
            "baseline_b_base_model": base_b,
            "candidate_c_tinker_lora": cand_c,
        },
        "improvements": improvements,
        "claims": "Metrics are measured only when the corresponding model artifact is supplied; no fallback values are fabricated.",
    }
    out_file = os.path.join(os.path.dirname(__file__), "benchmark_results.json")
    with open(out_file, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    run_heldout_benchmark()
