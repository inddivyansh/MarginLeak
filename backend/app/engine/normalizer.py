import re
from typing import Dict, Any, Tuple, Optional

UNIT_CANONICAL_MAP = {
    "ea": "each",
    "each": "each",
    "pc": "each",
    "pcs": "each",
    "piece": "each",
    "pieces": "each",
    "unit": "each",
    "units": "each",
    "item": "each",
    "bx": "box",
    "box": "box",
    "boxes": "box",
    "pk": "pack",
    "pack": "pack",
    "packs": "pack",
    "pkg": "pack",
    "cs": "case",
    "case": "case",
    "cases": "case",
    "ctn": "carton",
    "carton": "carton",
    "dz": "dozen",
    "doz": "dozen",
    "dozen": "dozen",
    "kg": "kg",
    "kgs": "kg",
    "kilo": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "lb": "lb",
    "lbs": "lb",
    "pound": "lb",
    "pounds": "lb",
    "m": "meter",
    "meter": "meter",
    "meters": "meter",
    "ft": "foot",
    "foot": "foot",
    "feet": "foot",
    "l": "liter",
    "ltr": "liter",
    "liter": "liter",
    "liters": "liter",
    "set": "set",
    "roll": "roll",
    "rolls": "roll"
}

PACK_PATTERN = re.compile(
    r"(?:(?:box|pack|case|bag|pkg|set)\s+of\s+(\d+))|(?:(\d+)\s*(?:/|\s*per\s*|\-)(?:box|pk|case|bx|pack|ea|pcs))|(?:(\d+)\s*(?:pack|pk|ct|count))",
    re.IGNORECASE
)

class TextNormalizer:
    @staticmethod
    def normalize_unit(unit_str: Optional[str]) -> str:
        if not unit_str:
            return "each"
        cleaned = unit_str.strip().lower()
        cleaned = re.sub(r"[^\w]", "", cleaned)
        return UNIT_CANONICAL_MAP.get(cleaned, cleaned)

    @staticmethod
    def extract_pack_info(text: str) -> Tuple[Optional[int], Optional[str]]:
        """Extracts pack size (e.g. 100/box -> 100, box)"""
        match = PACK_PATTERN.search(text)
        if match:
            qty = match.group(1) or match.group(2) or match.group(3)
            if qty:
                return int(qty), "box" if "box" in text.lower() or "bx" in text.lower() else "pack"
        return None, None

    @staticmethod
    def normalize_sku(sku: Optional[str]) -> Optional[str]:
        if not sku:
            return None
        # Remove whitespace, lowercase, preserve alphanumeric and hyphens
        cleaned = sku.strip().upper()
        cleaned = re.sub(r"[\s_]+", "-", cleaned)
        return cleaned

    @staticmethod
    def normalize_description(text: str) -> Dict[str, Any]:
        """
        Deterministic normalization of supplier descriptions:
        - standardizes case and whitespace
        - extracts pack quantity and unit
        - normalizes common abbreviations
        """
        if not text:
            return {
                "canonical_description": "",
                "clean_tokens": [],
                "pack_quantity": 1,
                "pack_unit": "each"
            }

        raw = text.strip()
        pack_qty, pack_unit = TextNormalizer.extract_pack_info(raw)

        # Standardize common supplier abbreviations
        substitutions = [
            (r"\btype[\s-]c\b", "usb-c"),
            (r"\btypc\b", "usb-c"),
            (r"\bbt\b", "bluetooth"),
            (r"\bwl\b", "wireless"),
            (r"\bblu\b", "blue"),
            (r"\bblk\b", "black"),
            (r"\bwht\b", "white"),
            (r"\blrg\b", "large"),
            (r"\bmed\b", "medium"),
            (r"\bsml\b", "small"),
            (r"\bport\b", "p"),
            (r"\b7[\s-]?port\b", "7-in-1"),
            (r"\b7p\b", "7-in-1"),
            (r"\bhd\b", "heavy duty"),
            (r"\bss\b", "stainless steel"),
            (r"\balum\b", "aluminum"),
            (r"\bqty\b", "quantity"),
            (r"\bstd\b", "standard"),
        ]

        normalized = raw.lower()
        for pattern, repl in substitutions:
            normalized = re.sub(pattern, repl, normalized, flags=re.IGNORECASE)

        # Clean punctuation except hyphens between alphanumeric words
        cleaned_text = re.sub(r"[^\w\s\-]", " ", normalized)
        cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()

        tokens = [t for t in cleaned_text.split() if len(t) > 1 or t.isdigit()]

        return {
            "canonical_description": cleaned_text,
            "clean_tokens": sorted(list(set(tokens))),
            "pack_quantity": pack_qty or 1,
            "pack_unit": pack_unit or "each"
        }
