import os
import sys
from unittest.mock import MagicMock
from layers.reasoning.synthesis import EvidenceSynthesisAgent
from layers.reasoning.llm_reasoning import LLMReasoningAgent

# Mock Data
MOCK_SEARCH_RESULTS = [
    {
        "id": "uuid-1",
        "score": 0.92,
        "payload": {
            "incident_id": "Hurricane_Ian_004",
            "disaster_type": "hurricane",
            "damage_severity": "destroyed",
            "latitude": 26.6406,
            "longitude": -81.8723,
            "total_buildings": 45,
            "timestamp": "2022-09-28T14:30:00Z"
        }
    },
    {
        "id": "uuid-2",
        "score": 0.88,
        "payload": {
            "incident_id": "Hurricane_Michael_012",
            "disaster_type": "hurricane",
            "damage_severity": "major-damage",
            "latitude": 30.1588,
            "longitude": -85.6602,
            "total_buildings": 30,
            "timestamp": "2018-10-10T12:00:00Z"
        }
    }
]

def test_reasoning_layer():
    print("="*60)
    print("TESTING REASONING LAYER (Agents 9 & 10)")
    print("="*60)

    # 1. Test Agent 9: Evidence Synthesis (with Mock Recommendation)
    print("\n[TEST] Agent 9: Evidence Synthesis (Recommendation Loop)")
    
    # Mock Qdrant Client for Recommendation
    mock_client = MagicMock()
    # Mock recommendation return value (ScoredPoint-like objects)
    mock_point = MagicMock()
    mock_point.id = "uuid-rec-1"
    mock_point.score = 0.85
    mock_point.payload = {
        "incident_id": "Hurricane_Idalia_001", 
        "disaster_type": "hurricane",
        "damage_severity": "major-damage"
    }
    mock_client.recommend.return_value = [mock_point]
    
    synthesizer = EvidenceSynthesisAgent(mock_client)
    patterns = synthesizer.analyze_patterns(MOCK_SEARCH_RESULTS)
    
    print(f"  ✓ Evidence expanded to: {patterns['result_count']} incidents")
    print(f"  ✓ Mode Severity: {patterns['mode']}")
    print(f"  ✓ Confidence Level: {patterns['confidence_level']:.2f}")

    # 2. Test Agent 10: LLM Reasoning (Gemini)
    print("\n[TEST] Agent 10: Gemini News Reporter")
    
    # Check if API key is present
    from dotenv import load_dotenv
    load_dotenv()
    if not os.getenv("GEMINI_API_KEY"):
        print("  ⚠ GEMINI_API_KEY not found. Test will use fallback/mock.")
        print("  (To test real Gemini generation, add key to .env)")
    
    llm_agent = LLMReasoningAgent()
    
    incident_id = "TEST_INCIDENT_2024"
    report = llm_agent.generate_report(incident_id, MOCK_SEARCH_RESULTS)
    
    print("\n--- GENERATED REPORT START ---")
    print(report)
    print("--- GENERATED REPORT END ---\n")

if __name__ == "__main__":
    test_reasoning_layer()
