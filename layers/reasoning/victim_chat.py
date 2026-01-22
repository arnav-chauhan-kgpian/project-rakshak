"""
VictimChatAgent: Live Distress Signal Responder
Uses the new google.genai SDK for Gemini 2.5 Flash.
"""

import os
import json
import datetime
from google import genai

class VictimChatAgent:
    """Agent for interactive distress signal response"""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("⚠ Gemini API Key missing for Chatbot. Responses will be simulated.")
            self.client = None
        else:
            self.client = genai.Client(api_key=api_key)
            self.model = "gemini-2.5-flash"
            
        self.chat_history = []
        self.chat_session = None
        self.system_prompt = """
        ROLE: You are an AI Emergency Responder named 'Rakshak'.
        MISSION: Assist a civilian in potential distress by sending medical teams to their location.
        
        GUIDELINES:
        1. LOCATION PRIVACY: NEVER mention raw latitude/longitude coordinates. Say "I have your location" or name the generated city/area if known.
        2. AUTHORITY: You ARE the dispatch authority. Do NOT ask user to call 911. Tell them "Teams are on the way".
        3. BREVITY: Messages must be short (1-2 sentences). Do not talk much.
        4. TONE: Empathetic, calm, polite, but firm.
        5. ADVICE: Give brief, actionable safety tips (e.g., "Stay put", "Cover your mouth", "Find high ground").
        
        GOAL: Keep them calm, confirmed help is coming. You ARE the helper here. Give immediate safety advice.
        """

    def start_chat(self, risk_assessment):
        """Initializes the chat session with safety context"""
        context_str = f"""
        - User Location: {risk_assessment.get('user_location')}
        - Risk Level: {risk_assessment.get('risk_level', 'UNKNOWN')}
        - Nearby Incidents: {risk_assessment.get('incident_count', 0)}
        - Nearest Safe Zone Distance: {risk_assessment.get('nearest_safe_zone_km', 'Unknown')} km
        - Specific Threats: {risk_assessment.get('threats', ['None identified'])}
        """
        
        if self.client:
            # Create a chat session with the new SDK
            self.chat_session = self.client.chats.create(
                model=self.model,
                config={
                    "system_instruction": self.system_prompt + f"\n\nCONTEXT DATA:\n{context_str}"
                }
            )
        
        return "CONNECTION ESTABLISHED. Rakshak AI Online. Please state your emergency or situation."

    def send_message(self, user_input):
        """Processes user input and returns AI response"""
        if not self.client:
            return "⚠ AI Offline. Please evacuate to high ground immediately."
            
        try:
            self.chat_history.append(f"User: {user_input}")
            
            if self.chat_session:
                response = self.chat_session.send_message(user_input)
                reply = response.text
            else:
                # Fallback: single-turn if chat session failed
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=user_input
                )
                reply = response.text
                
            self.chat_history.append(f"Rakshak: {reply}")
            return reply
        except Exception as e:
            return f"⚠ Connection Error: {str(e)}. Protocol: SEEK SAFETY."

    def analyze_session(self):
        """Analyzes the conversation history to generate a triage report"""
        if not self.chat_history:
            return "No conversation data."
            
        history_text = "\n".join(self.chat_history)
        
        analysis_prompt = f"""
        ACT AS: Triage Officer analyzing a DISTRESS CALL.
        TASK: Extract ALL medical emergencies, injuries, and location information.
        
        TRANSCRIPT:
        {history_text}
        
        CRITICAL INSTRUCTIONS:
        1. SCAN for ANY physical symptom or injury - be EXTREMELY thorough.
        2. INJURY KEYWORDS (if ANY of these appear, it's an injury):
           - Body parts: "chest", "leg", "arm", "head", "back", "neck", "ankle", "knee", "eye", "lung", "heart"
           - Symptoms: "pain", "hurt", "hurts", "ache", "burning", "bleeding", "blood", "broken", "fracture", "sprain"
           - Breathing: "breath", "breathing", "cant breathe", "suffocating", "choking", "asthma", "inhaled"
           - Burns: "burn", "burned", "fire", "hot", "scalded", "smoke inhalation"
           - Trauma: "crushed", "trapped", "stuck", "pinned", "collapsed", "fall", "fell"
           - Emergencies: "dying", "dead", "unconscious", "faint", "dizzy", "drowning", "stroke", "heart attack"
           - Wounds: "cut", "wound", "gash", "laceration", "puncture", "stab"
           - Other: "fever", "vomit", "nausea", "blind", "deaf", "numb", "paralyzed"
        3. LOCATION: Extract any location mentioned (city, area, landmark, address, "near X", etc.)
        4. If the user mentions ANYTHING related to physical distress, LIST IT in key_details.
        5. Default panic_score to "High" if any injury keyword is detected.
        
        OUTPUT FORMAT (Strict JSON - no extra text):
        {{
            "summary": "1 sentence: 'User reports [specific injuries/situation]'",
            "panic_score": "Low|Medium|High|Extreme",
            "credibility_score": 8,
            "recommended_response": "Immediate Rescue|Medical Evac|Police|Fire Department|Advisory",
            "affected_location": "Location mentioned by user or 'Not specified'",
            "key_details": ["Injury 1", "Injury 2", "Symptom", "Environment hazard"]
        }}
        """
        
        try:
            if not self.client:
                return "Triage Analysis Failed - No API key."
            response = self.client.models.generate_content(
                model=self.model,
                contents=analysis_prompt
            )
            return response.text
        except:
            return "Triage Analysis Failed."

    def save_session_log(self, triage_report, risk_assessment):
        """Saves the full session data to a JSON log file"""
        log_dir = "chat_logs"
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{log_dir}/session_{timestamp}.json"
        
        log_data = {
            "timestamp": timestamp,
            "risk_assessment_init": risk_assessment,
            "chat_history": self.chat_history,
            "triage_report": triage_report
        }
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2)
            return filename
        except Exception as e:
            return f"Error saving log: {e}"
