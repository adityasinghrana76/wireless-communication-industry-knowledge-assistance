import re

TECHNOLOGIES = {"4G", "5G", "6G", "LTE", "NB-IoT", "Wi-Fi", "LoRaWAN", "Satellite"}
COMPONENTS = {"antenna", "rf module", "router", "gateway", "modem", "base station", "transceiver", "sensor"}
EXPERTISE = {"RF Engineering", "Signal Processing", "Embedded Systems", "Network Security", "IoT"}


class ExtractionService:
    def extract_entities(self, text: str) -> dict:
        company_candidates = sorted(set(re.findall(r"\b[A-Z][A-Za-z0-9&.\- ]{2,40}(?:Inc|Ltd|LLC|Corp|Systems)\b", text)))
        lower = text.lower()
        return {
            "companies": company_candidates[:20],
            "technologies": sorted(t for t in TECHNOLOGIES if t.lower() in lower),
            "components": sorted(c for c in COMPONENTS if c in lower),
            "expertise": sorted(e for e in EXPERTISE if e.lower() in lower),
            "locations": sorted(set(re.findall(r"\b(?:USA|India|China|Europe|Japan|Korea|Germany)\b", text))),
        }

    def classify_company(self, text: str) -> str:
        lower = text.lower()
        if "operator" in lower or "network provider" in lower:
            return "Network Provider"
        if "antenna" in lower or "rf module" in lower or "semiconductor" in lower:
            return "Component Manufacturer"
        if "university" in lower or "research" in lower:
            return "Research Organization"
        if "base station" in lower or "radio access network" in lower:
            return "Telecom Vendor"
        return "Technology Company"
