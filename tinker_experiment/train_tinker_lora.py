"""Run real supervised LoRA fine-tuning through the Thinking Machines Tinker SDK."""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TinkerTrainer")

SYSTEM_PROMPT = """You are MarginLeak Normalizer, an accounts-payable AI that normalizes messy supplier invoice line descriptions into standardized structured JSON.
You extract the true product identity, pack quantity, pack unit, size, and attributes.
Never invent information. If an attribute is ambiguous or missing, do not guess; record it in uncertain_fields.
Output ONLY a valid JSON object matching the requested schema."""


def load_jsonl(filepath: str) -> List[Dict[str, Any]]:
    with open(filepath, "r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def format_prompt(example: Dict[str, Any]) -> str:
    inp = example["input"]
    return (
        f"{SYSTEM_PROMPT}\n\n"
        "Normalize the following supplier line-item description into structured canonical JSON:\n\n"
        f"Supplier Description: {json.dumps(inp['supplier_description'])}\n"
        f"Supplier SKU: {json.dumps(inp.get('supplier_sku'))}\n\n"
        "Output strictly in JSON format:\n"
    )


def make_datum(tinker_module: Any, tokenizer: Any, example: Dict[str, Any]) -> Any:
    prompt_tokens = tokenizer.encode(format_prompt(example))
    target_tokens = tokenizer.encode(json.dumps(example["target"], separators=(",", ":")))
    tokens = prompt_tokens + target_tokens
    weights = [0.0] * len(prompt_tokens) + [1.0] * len(target_tokens)
    return tinker_module.types.Datum(
        model_input=tinker_module.types.ModelInput.from_ints(tokens),
        loss_fn_inputs={
            "target_tokens": tinker_module.types.ModelInput.from_ints(tokens),
            "weights": tinker_module.types.TensorData(
                data=weights, dtype="float32", shape=[len(weights)]
            ),
        },
    )


def run_training() -> None:
    parser = argparse.ArgumentParser(description="Tinker LoRA fine-tuning for MarginLeak")
    parser.add_argument("--smoke-test", action="store_true", help="Train on two examples for SDK verification")
    parser.add_argument("--model", default="Qwen/Qwen3-8B")
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--lora-rank", type=int, default=16)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--checkpoint-name", default="marginleak-qwen3-8b-lora")
    args = parser.parse_args()

    api_key = os.getenv("TINKER_API_KEY")
    if not api_key:
        raise RuntimeError("TINKER_API_KEY is required. No simulated training path is provided.")
    if args.epochs < 1 or args.lora_rank < 1:
        raise ValueError("epochs and lora-rank must be positive")

    data_dir = os.path.join(os.path.dirname(__file__), "data")
    train_data = load_jsonl(os.path.join(data_dir, "train.jsonl"))
    if args.smoke_test:
        train_data = train_data[:2]
    if not train_data:
        raise RuntimeError("Training dataset is empty")

    import tinker

    service_client = tinker.ServiceClient(api_key=api_key)
    training_client = service_client.create_lora_training_client(
        base_model=args.model,
        rank=args.lora_rank,
        user_metadata={"project": "MarginLeak", "dataset": "train.jsonl"},
    )
    tokenizer = training_client.get_tokenizer()
    data = [make_datum(tinker, tokenizer, example) for example in train_data]
    losses: List[float] = []

    for epoch in range(args.epochs):
        for offset in range(0, len(data), 8):
            batch = data[offset : offset + 8]
            forward_backward = training_client.forward_backward(batch, "cross_entropy")
            optim_step = training_client.optim_step(
                adam_params=tinker.types.AdamParams(learning_rate=args.lr)
            )
            result = forward_backward.result()
            optim_step.result()
            loss = result.metrics.get("loss:sum")
            if loss is not None:
                losses.append(float(loss))
            logger.info(
                "epoch=%d/%d batch=%d/%d loss=%s",
                epoch + 1, args.epochs, min(offset + 8, len(data)), len(data), loss,
            )

    checkpoint = training_client.save_weights_for_sampler(
        name=args.checkpoint_name,
        user_metadata={"base_model": args.model, "lora_rank": str(args.lora_rank)},
    ).result()
    checkpoint_data = checkpoint.model_dump() if hasattr(checkpoint, "model_dump") else vars(checkpoint)
    metadata = {
        "status": "trained",
        "base_model": args.model,
        "checkpoint_name": args.checkpoint_name,
        "checkpoint": checkpoint_data,
        "epochs": args.epochs,
        "examples_trained": len(data),
        "lora_rank": args.lora_rank,
        "learning_rate": args.lr,
        "observed_loss": losses,
    }
    output_path = os.path.join(os.path.dirname(__file__), "checkpoint_metadata.json")
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, default=str)
    logger.info("Saved checkpoint metadata to %s", output_path)


if __name__ == "__main__":
    try:
        run_training()
    except Exception as exc:
        logger.error("Tinker training failed: %s", exc)
        sys.exit(1)
