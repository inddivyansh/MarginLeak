from typing import Dict, Any, List, Optional, Tuple
from rapidfuzz import fuzz
from backend.app.engine.normalizer import TextNormalizer
from backend.app.ai.tinker_client import tinker_client

class LineMatcher:
    @staticmethod
    def match_invoice_lines(
        invoice_lines: List[Dict[str, Any]],
        po_lines: List[Dict[str, Any]],
        approved_aliases: Optional[Dict[str, str]] = None,
        use_model_normalization: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Executes hierarchical matching pipeline:
        1. Exact SKU
        2. Approved supplier alias
        3. Deterministic fuzzy similarity
        4. Model-assisted canonical normalization
        Returns match decisions with method, confidence, and ambiguous candidates.
        """
        results = []
        aliases = approved_aliases or {}

        # Precompute normalized PO descriptions and SKUs
        normalized_pos = []
        for po in po_lines:
            po_norm = TextNormalizer.normalize_description(po["description"])
            normalized_pos.append({
                "po_line": po,
                "clean_desc": po_norm["canonical_description"],
                "clean_sku": TextNormalizer.normalize_sku(po.get("sku")),
                "pack_qty": po_norm["pack_quantity"],
                "pack_unit": po_norm["pack_unit"],
                "unit": TextNormalizer.normalize_unit(po.get("unit"))
            })

        for inv in invoice_lines:
            inv_sku = TextNormalizer.normalize_sku(inv.get("sku"))
            inv_norm = TextNormalizer.normalize_description(inv["description"])
            inv_clean_desc = inv_norm["canonical_description"]
            inv_unit = TextNormalizer.normalize_unit(inv.get("unit"))
            inv_pack_qty = inv_norm["pack_quantity"]

            matched_po = None
            method = "none"
            confidence = 0.0
            is_ambiguous = False
            ambiguity_reason = None
            candidate_scores = []

            # Step 1: Exact SKU match
            if inv_sku:
                for p in normalized_pos:
                    if p["clean_sku"] and p["clean_sku"] == inv_sku:
                        matched_po = p["po_line"]
                        method = "exact_sku"
                        confidence = 1.0
                        break

            # Step 2: Approved Supplier Alias match
            if not matched_po and inv_clean_desc in aliases:
                target_po_sku = aliases[inv_clean_desc]
                for p in normalized_pos:
                    if p["clean_sku"] == target_po_sku or p["clean_desc"] == target_po_sku:
                        matched_po = p["po_line"]
                        method = "supplier_alias"
                        confidence = 0.98
                        break

            # Step 3: Text & Fuzzy Scoring
            if not matched_po:
                for p in normalized_pos:
                    # Token sort & token set ratio
                    sort_ratio = fuzz.token_sort_ratio(inv_clean_desc, p["clean_desc"])
                    set_ratio = fuzz.token_set_ratio(inv_clean_desc, p["clean_desc"])
                    base_similarity = max(sort_ratio, set_ratio)

                    # Check unit compatibility
                    unit_penalty = 0
                    if inv_unit != p["unit"] and inv_unit != "each" and p["unit"] != "each":
                        unit_penalty = 20

                    # Check pack quantity mismatch penalty (e.g. box of 100 vs box of 200)
                    pack_penalty = 0
                    if inv_pack_qty and p["pack_qty"] and inv_pack_qty != p["pack_qty"]:
                        pack_penalty = 35

                    final_score = max(0, base_similarity - unit_penalty - pack_penalty)
                    candidate_scores.append((final_score, p))

                candidate_scores.sort(key=lambda x: x[0], reverse=True)

                if candidate_scores:
                    top_score, top_candidate = candidate_scores[0]
                    second_score = candidate_scores[1][0] if len(candidate_scores) > 1 else 0

                    # Step 4: Model normalization enhancement if score is borderline (60 - 85)
                    if 60 <= top_score < 85 and use_model_normalization:
                        model_norm = tinker_client.normalize_line(inv["description"], inv.get("sku"))
                        model_desc = model_norm.get("canonical_description", "")
                        model_ratio = fuzz.token_set_ratio(model_desc.lower(), top_candidate["clean_desc"])
                        if model_ratio > top_score:
                            top_score = model_ratio
                            method = "model_normalization"
                        else:
                            method = "fuzzy_token"
                    else:
                        method = "fuzzy_token"

                    # Ambiguity threshold checks
                    if top_score >= 82:
                        if second_score > 75 and (top_score - second_score) < 10:
                            # Too close to call between two PO lines
                            is_ambiguous = True
                            ambiguity_reason = f"Multiple close matches ({round(top_score)}% vs {round(second_score)}%)"
                            matched_po = top_candidate["po_line"]
                            confidence = round(top_score / 100.0, 2)
                        else:
                            matched_po = top_candidate["po_line"]
                            confidence = round(top_score / 100.0, 2)
                    elif top_score >= 60:
                        # Moderate similarity -> Flag as ambiguous for human review
                        is_ambiguous = True
                        ambiguity_reason = f"Borderline match score ({round(top_score)}%). Review recommended."
                        matched_po = top_candidate["po_line"]
                        confidence = round(top_score / 100.0, 2)
                    else:
                        # Low similarity
                        matched_po = None
                        confidence = round(top_score / 100.0, 2)
                        method = "unmatched"

            results.append({
                "invoice_line": inv,
                "matched_po_line": matched_po,
                "method": method,
                "confidence": confidence,
                "is_ambiguous": is_ambiguous,
                "ambiguity_reason": ambiguity_reason,
                "candidates_considered": len(candidate_scores)
            })

        return results
