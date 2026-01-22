"""
Agent 10a: Historical Context Summarizer
Takes raw lists of similar incidents and produces a narrative summary.
This reduces hallucination in the final report by pre-processing historical data.
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class HistorySummarizerAgent:
    """
    Agent 10a: Summarizes historical context from visual and geo similar incidents.
    Extracts location names from incident_ids and explains key events.
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            self.model = None
        else:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-2.5-flash')
            except Exception as e:
                print(f"    ⚠ Summarizer LLM init failed: {e}")
                self.model = None
    
    def summarize_history(self, visual_results, geo_results, current_disaster_type):
        """
        Summarizes historical incidents into a coherent narrative.
        
        Args:
            visual_results: Visually similar incidents from Agent 9a
            geo_results: Geographically nearby incidents from Agent 9b
            current_disaster_type: Type of current incident for context
            
        Returns:
            Dict with 'visual_summary' and 'geo_summary' narratives
        """
        visual_summary = self._summarize_visual(visual_results, current_disaster_type)
        geo_summary = self._summarize_geo(geo_results)
        
        return {
            "visual_summary": visual_summary,
            "geo_summary": geo_summary
        }
    
    def _summarize_visual(self, results, disaster_type):
        """Summarize visually similar incidents."""
        if not results:
            return "No visually similar events were found in the database."
        
        # Build data for LLM
        incidents_data = ""
        for res in results[:5]:
            payload = res.get("payload", {})
            incidents_data += f"""
            - ID: {payload.get("incident_id")}
            - Type: {payload.get("disaster_type")}
            - Damage: {payload.get("damage_severity")}
            """
        
        prompt = f"""
        You are analyzing disaster incidents with SIMILAR VISUAL DAMAGE PATTERNS.
        
        These incidents had similar satellite imagery patterns to the current {disaster_type}:
        {incidents_data}
        
        TASK: Write a 2-3 sentence summary explaining:
        1. Extract the LOCATION from each incident_id (e.g., "mexico-earthquake" → Mexico)
        2. What damage patterns were observed
        3. What this suggests about the current incident
        
        RULES:
        - Do NOT list incidents, explain them narratively
        - Extract location from the incident ID name
        - Keep it brief and factual
        - Example: "Similar damage patterns were observed in Mexico's 2017 earthquake events, 
          which predominantly showed low to medium structural damage..."
        """
        
        if self.model:
            try:
                response = self.model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                return self._fallback_visual(results)
        return self._fallback_visual(results)
    
    def _summarize_geo(self, results):
        """Summarize geographically nearby incidents."""
        if not results:
            return "No historical disaster events were found at this geographic location."
        
        # Build data for LLM
        incidents_data = ""
        for res in results[:5]:
            payload = res.get("payload", {})
            incidents_data += f"""
            - ID: {payload.get("incident_id")}
            - Type: {payload.get("disaster_type")}
            - Damage: {payload.get("damage_severity")}
            - Coordinates: {payload.get("latitude"):.4f}, {payload.get("longitude"):.4f}
            """
        
        prompt = f"""
        You are analyzing HISTORICAL DISASTERS that occurred at THIS SAME LOCATION.
        
        These past incidents happened within 100km of the current event:
        {incidents_data}
        
        TASK: Write a 2-3 sentence summary explaining:
        1. Extract the LOCATION/REGION from each incident_id (e.g., "socal-fire" -> Southern California, "mexico-earthquake" -> Mexico).
        2. What types of disasters have affected this area historically?
        3. The typical severity levels observed and what responders should be prepared for.
        
        RULES:
        - NEVER list IDs (e.g., socal-fire_00898). Use semantic names instead (e.g., "Southern California wildfire").
        - Explain the history narratively.
        - Focus on what this means for the CURRENT response team.
        """
        
        if self.model:
            try:
                response = self.model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                return self._fallback_geo(results)
        return self._fallback_geo(results)
    
    def _fallback_visual(self, results):
        """Fallback summary without LLM."""
        if not results:
            return "No visually similar events found."
        return "Multiple historical incidents with similar structural damage signatures were identified, suggesting consistent impact patterns with previous events."
    
    def _fallback_geo(self, results):
        """Fallback summary without LLM."""
        if not results:
            return "No historical events at this location."
        return "The region has a history of disaster events, indicating localized vulnerabilities that may impact the current emergency response."
