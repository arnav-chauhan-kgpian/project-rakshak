import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

from utils.async_utils import retry_with_backoff

# Load environment variables (API keys)
load_dotenv()

class LLMReasoningAgent:
    """
    Agent 10: Citation LLM Reasoning (Gemini Powered via google.genai SDK)
    Generates journalistic damage assessment reports by comparing new incidents 
    with historical precedents found in the vector database.
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("⚠ Warning: GEMINI_API_KEY not found in .env. LLM agent will use mock fallback.")
            self.client = None
        else:
            try:
                self.client = genai.Client(api_key=self.api_key)
                self.model = "gemini-2.5-flash"
                print(f"✓ Gemini LLM Agent initialized ({self.model})")
            except Exception as e:
                print(f"⚠ Gemini initialization failed: {e}")
                self.client = None
    
    @retry_with_backoff(retries=3, initial_delay=2.0)
    def generate_report(self, incident_id, incident_metadata, history_summary, audio_context=None):
        """
        Generates a formal damage assessment report using Gemini.
        Stage 2 LLM - receives pre-summarized history from Agent 10a.
        """
        visual_summary = history_summary.get("visual_summary", "No visual context available.")
        geo_summary = history_summary.get("geo_summary", "No geographic context available.")

        lat = incident_metadata.get("latitude")
        lon = incident_metadata.get("longitude")
        subject_data = f"""
        - Disaster Type: {incident_metadata.get("disaster_type", "Unknown")}
        - GPS Coordinates: Lat {lat}, Lon {lon}
        - ASSESSED DAMAGE LEVEL: {incident_metadata.get("inferred_damage", "unknown").upper()}
        - Damage Distribution: {incident_metadata.get("damage_distribution", {})}
        """
        
        audio_section = ""
        if audio_context and audio_context.get("transcript"):
            audio_section = f"""
            AUDIO INTELLIGENCE:
            - Transcript: "{audio_context.get('transcript')}"
            - Panic Level: {audio_context.get('panic_score', 'Unknown')}
            """

        prompt = f"""
        ROLE:
        You are an Emergency Response Coordinator. Write a formal EMERGENCY ALERT.

        CURRENT SITUATION DATA:
        {subject_data}
        {audio_section}

        HISTORICAL CONTEXT (Narrative):
        {visual_summary}
        {geo_summary}

        TASK:
        Write a concise EMERGENCY ALERT REPORT.
        
        CRITICAL: Use the GPS coordinates (Lat {lat}, Lon {lon}) to determine the actual location (city, region, country).
        Do NOT rely on any ID strings. Use your geographic knowledge to identify the location.
        
        REQUIRED SECTIONS & STRICT FORMATTING:
        1. **Location & Urgency**: (DETAILED) Use the coordinates to identify the city/region.
        2. **Situation Overview**: (COMPREHENSIVE) thorough summary of disaster type and assessed damage distribution.
        3. **Historical Context**: (DETAILED) Elaborate on how past similar events match this one.
        4. **Audio Insights**: (DETAILED) If audio exists, extract every relevant detail.
        5. **Impact Reality**: (VERY SHORT) Max 1 line per point.
        6. **Responder Actions**: (CONCISE) Bullet points. Immediate, high-impact steps.

        RULES:
        - Sections 1-4 must be INSIGHTFUL and DETAILED.
        - Sections 5-6 must be BRIEF and ACTIONABLE.
        - **DO NOT INVENT NUMBERS**. Use "multiple", "significant", "localized" instead of fake counts.
        """

        if self.client:
            try:
                print(f"    ⟳ Querying Gemini ({self.model})...")
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
                return response.text
            except Exception as e:
                print(f"    ⚠ Gemini error: {e}")
                return self._fallback_report(incident_id, incident_metadata)
        else:
            return self._fallback_report(incident_id, incident_metadata)

    def _fallback_report(self, incident_id, incident_metadata):
        """Fallback template for offline mode"""
        return f"""# EMERGENCY ALERT: {incident_metadata.get('disaster_type', 'Unknown')}
**INCIDENT ID:** {incident_id}
**ASSESSED DAMAGE:** {incident_metadata.get('inferred_damage', 'unknown').upper()}
**LOCATION:** Lat {incident_metadata.get('latitude')}, Lon {incident_metadata.get('longitude')}

Gemini API unavailable. Please proceed with standard emergency protocols.
"""