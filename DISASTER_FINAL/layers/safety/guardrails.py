import re
from typing import Dict, Any, List, Optional, Union

class PIIScrubber:
    """
    Agent 14a: PII Redaction (Safety Layer)
    Removes sensitive personally identifiable information from text and metadata
    before it enters the memory store.
    """
    def __init__(self):
        # Pre-compiled high-performance regex patterns
        self.patterns = {
            # Email: Standard implementation
            "email": re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
            # Phone: US/Intl formats
            "phone": re.compile(r'\b(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b'),
            # SSN: US Social Security
            "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            # Credit Card: Basic grouping check
            "cc": re.compile(r'\b(?:\d{4}[- ]?){3}\d{4}\b'),
            # IPv4 Address (internal network leaks)
            "ipv4": re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
        }
        self.replacement = "[REDACTED]"

    def scrub_text(self, text: str) -> str:
        """Sanitize a single string."""
        if not text or not isinstance(text, str): 
            return text
            
        cleaned = text
        for name, pattern in self.patterns.items():
            cleaned = pattern.sub(f"[{name.upper()}_REDACTED]", cleaned)
        return cleaned

    def scrub_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize a dictionary."""
        if not metadata:
            return {}
            
        clean = {}
        for k, v in metadata.items():
            # Skip scrubbing keys, only values
            if isinstance(v, str):
                clean[k] = self.scrub_text(v)
            elif isinstance(v, dict):
                clean[k] = self.scrub_metadata(v)
            elif isinstance(v, list):
                clean[k] = [self.scrub_text(i) if isinstance(i, str) else i for i in v]
            else:
                clean[k] = v
        return clean


class BiasMonitor:
    """
    Agent 14b: Bias Monitor (Safety Layer)
    Analyzes decision outputs for potential fairness issues or logical inconsistencies
    that may suggest bias (e.g., under-responding to high damage).
    """
    def check_fairness(self, recommendation: Dict[str, Any], incident_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Audit a recommendation for fairness.
        
        Logic:
        1. Consistency: Priority must be proportional to Damage Severity.
        2. Neglect Check: If Damage is Critical but Priority is Low/Medium -> FLAG.
        """
        try:
            damage = str(recommendation.get("damage_severity", "unknown")).lower()
            priority = str(recommendation.get("priority_level", "medium")).lower()
            
            # Numeric scale for comparison
            score_map = {"no-damage": 0, "minor-damage": 1, "low": 1, "medium": 2, "major-damage": 3, "high": 3, "destroyed": 4, "critical": 4, "unknown": 2}
            
            d_score = score_map.get(damage, 2)
            p_score = score_map.get(priority, 2)
            
            diff = p_score - d_score
            
            # ALGORITHM 1: Neglect Detection (Critical Failure Mode)
            # If priority is 2 levels below damage (e.g., Critical Damage (4) vs Medium Priority (2))
            if diff <= -2:
                return {
                    "is_fair": False,
                    "status": "FAIL",
                    "reason": f"Bias Detected: Under-allocation. Incident has {damage.upper()} damage but assigned {priority.upper()} priority.",
                    "requires_approval": True
                }
            
            # ALGORITHM 2: Over-Response (Resource Waste, but safe)
            if diff >= 2:
                return {
                    "is_fair": True,
                    "status": "WARN",
                    "reason": "Aggressive response strategy (Priority > Damage). Acceptable but resource intensive.",
                    "requires_approval": False
                }
                
            return {
                "is_fair": True,
                "status": "PASS",
                "reason": "Priority allocation is proportional to damage assessment.",
                "requires_approval": False
            }
            
        except Exception as e:
            print(f"Bias Monitor Error: {e}")
            return {"is_fair": True, "status": "ERROR", "reason": "Could not verify fairness"}
