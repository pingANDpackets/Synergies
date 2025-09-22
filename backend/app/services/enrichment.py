# backend/app/services/enrichment.py
import re
from typing import Dict, Any
from backend.app.core.config import settings

class EnrichmentPipeline:
    def __init__(self):
        # placeholder: integrate Form Recognizer / Text Analytics in prod
        pass

    def ocr_extract(self, file_path: str) -> str:
        """
        Stub: in prod call Azure Form Recognizer or Computer Vision.
        Here we simply read text files or return placeholder text for other file types.
        """
        text = ""
        try:
            if file_path.lower().endswith((".txt", ".md")):
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
            else:
                # placeholder for PDFs/images
                text = f"[EXTRACTED TEXT PLACEHOLDER FOR {file_path}]"
        except Exception:
            text = f"[ERROR_READING_FILE:{file_path}]"
        return text

    def detect_entities(self, text: str) -> Dict[str, Any]:
        """
        Very lightweight heuristics for procurement entities.
        In prod use Azure Text Analytics NER.
        """
        supplier = None
        amount = None
        # naive supplier search: look for uppercase words near 'Supplier' token
        m = re.search(r"(Supplier|vendor)[:\\s]*([A-Z0-9 &,-]{3,100})", text, re.IGNORECASE)
        if m:
            supplier = m.group(2).strip()
        # naive currency extraction
        m2 = re.search(r"\\$?([0-9,]+(?:\\.[0-9]{1,2})?)", text.replace(",", ""))
        if m2:
            try:
                amount = float(m2.group(1))
            except:
                amount = None
        return {"supplier": supplier, "amount": amount}

    def normalize_currency(self, raw_amount) -> float:
        try:
            return float(raw_amount) if raw_amount is not None else 0.0
        except:
            return 0.0

    def map_category(self, text: str) -> Dict[str, str]:
        """
        Simple rule-based category mapping. Replace with classifier for better coverage.
        """
        low = text.lower()
        if "pump" in low:
            return {"Validated_L0": "RawMaterials", "Validated_L1": "Pumps", "Validated_L2": "Centrifugal", "Validated_L3": "UnknownModel"}
        if "valve" in low:
            return {"Validated_L0": "RawMaterials", "Validated_L1": "Valves", "Validated_L2": "Control", "Validated_L3": "UnknownModel"}
        return {"Validated_L0": "Misc", "Validated_L1": "Other", "Validated_L2": "Other", "Validated_L3": "Other"}

    def enrich_document(self, file_path: str) -> Dict[str, Any]:
        text = self.ocr_extract(file_path)
        entities = self.detect_entities(text)
        amount = self.normalize_currency(entities.get("amount"))
        category = self.map_category(text)
        return {
            "content": text,
            "entities": entities,
            "amount": amount,
            "category": category
        }