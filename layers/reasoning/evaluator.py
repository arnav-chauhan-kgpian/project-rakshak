"""
Agent 14: Disaster Report Auditor (The Hallucination Killer)
Uses the new google.genai SDK for Gemini 2.5 Flash.
"""

import os
from google import genai
from utils.async_utils import retry_with_backoff

from dotenv import load_dotenv

load_dotenv()


class ReportAuditorAgent:
    """
    Agent 14: Audits and fact-checks the final emergency report.
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            self.client = None
        else:
            try:
                self.client = genai.Client(api_key=self.api_key)
                self.model = "gemini-2.5-flash"
            except Exception as e:
                print(f"    ⚠ Auditor LLM init failed: {e}")
                self.client = None
    
    @retry_with_backoff(retries=3, initial_delay=2.0)
    def audit_report(self, draft_report, ground_truth_metadata):
        """
        Audits the draft report against ground truth metadata.
        """
        if not self.client:
            return draft_report
            
        gt_lat = ground_truth_metadata.get("latitude")
        gt_lon = ground_truth_metadata.get("longitude")
        gt_type = ground_truth_metadata.get("disaster_type")
        gt_damage = ground_truth_metadata.get("inferred_damage")
        
        prompt = f"""
        ROLE:
        You are an Emergency Management Analyst & Auditor. Your job is to FACT-CHECK a draft disaster report AND ENHANCE its insights.
        
        GROUND TRUTH DATA (The ONLY 100% accurate data):
        - Incident Location: Lat {gt_lat}, Lon {gt_lon}
        - Disaster Type: {gt_type}
        - Assessed Damage Level: {gt_damage}
        
        DRAFT REPORT TO AUDIT:
        ---
        {draft_report}
        ---
        
        CRITICAL AUDIT RULES:
        1. **NO HALLUCINATED NUMBERS**: If the report mentions specific counts NOT in Ground Truth, DELETE them.
        2. **VERIFY LOCATION**: Ensure the location matches the coordinates.
        3. **FORMATTING**: Keep the Markdown structure exactly as it is.
        
        ENHANCEMENT TASKS (Apply to Sections 1-4 ONLY):
        1. **Location Insight**: Add context about the area's vulnerability.
        2. **Historical Context**: Add 1-2 sentences about similar past events.
        3. **Audio Insights**: Ensure audio details aren't missed.
        
        OUTPUT:
        The verified and enhanced Markdown report text only. 
        """
        
        try:
            print("    ⟳ Auditor (Agent 14) is fact-checking the report...")
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            verified_report = response.text.strip()
            return verified_report
        except Exception as e:
            print(f"    ⚠ Auditor failed: {e}. Returning draft as-is.")
            return draft_report
