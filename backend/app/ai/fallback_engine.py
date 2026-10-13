import re
from typing import Dict, Any, List, Optional
from backend.app.engine.normalizer import TextNormalizer

COLOR_ATTRS = ["blue", "black", "white", "red", "green", "silver", "gray", "grey", "gold", "yellow"]
MATERIAL_ATTRS = ["nitrile", "latex", "vinyl", "aluminum", "stainless steel", "cotton", "plastic", "copper"]
SIZE_ATTRS = ["small", "medium", "large", "x-large", "xl", "sml", "med", "lrg", "2xl"]

class FallbackNormalizer:
    @staticmethod
    def normalize(description: str, sku: Optional[str] = None) -> Dict[str, Any]:
        """
        Rule-based deterministic normalization fallback engine.
        Produces the exact schema as the fine-tuned Tinker model.
        """
        norm_result = TextNormalizer.normalize_description(description)
        raw_lower = description.lower()

        # Extract size
        detected_size = None
        for s in SIZE_ATTRS:
            if re.search(rf"\b{s}\b", raw_lower):
                detected_size = "large" if s in ["large", "lrg"] else ("medium" if s in ["medium", "med"] else ("small" if s in ["small", "sml"] else s))
                break

        # Extract attributes
        attributes = []
        for c in COLOR_ATTRS:
            if re.search(rf"\b{c}\b", raw_lower):
                attributes.append(c)
        for m in MATERIAL_ATTRS:
            if re.search(rf"\b{m}\b", raw_lower):
                attributes.append(m)

        # Detect uncertainty
        uncertain_fields = []
        if "?" in description or "equiv" in raw_lower or "substitute" in raw_lower or "generic" in raw_lower:
            uncertain_fields.append("substitution_risk")
        if not norm_result["pack_quantity"] and any(w in raw_lower for w in ["case", "pack", "box"]):
            uncertain_fields.append("pack_quantity_unspecified")

        return {
            "canonical_description": norm_result["canonical_description"],
            "pack_quantity": norm_result["pack_quantity"],
            "pack_unit": norm_result["pack_unit"],
            "size": detected_size,
            "attributes": sorted(list(set(attributes))),
            "uncertain_fields": uncertain_fields
        }
