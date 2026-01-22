"""
Distress Signal Client (Fast-Path)
Simulates a client-side app connecting to the Disaster Convolve backend.
"""

import os
import random
import time
from layers.reasoning.victim_chat import VictimChatAgent
from layers.reasoning.post_processor import PostProcessorAgent
from layers.safety.guardrails import PIIScrubber
from utils.qdrant_init import initialize_qdrant
from utils.voice_input import get_voice_input, WHISPER_AVAILABLE
from qdrant_client import models
import json

# Initialize PII scrubber
pii_scrubber = PIIScrubber()

def get_live_location():
    """Simulates getting GPS from device hardware (User Input for Demo)"""
    print("\n📡 INITIALIZING GPS SENSOR SIMULATION...")
    try:
        lat_in = input("Enter Latitude (e.g., 34.0522): ").strip()
        lon_in = input("Enter Longitude (e.g., -118.2437): ").strip()
        
        lat = float(lat_in) if lat_in else 34.0522
        lon = float(lon_in) if lon_in else -118.2437
        
        desc = "User Coordinates"
        print(f"📍 LOCKED: {lat}, {lon}")
        return {"lat": lat, "lon": lon, "desc": desc}
    except ValueError:
        print("⚠ Invalid coordinates. Using default (Los Angeles).")
        return {"lat": 34.0522, "lon": -118.2437, "desc": "Default LA"}

def check_safety(client, lat, lon):
    """Fast-Path safety check using Qdrant Geo-Index"""
    print("🔄 Checking Safety Database (Qdrant Geo-Index)...")
    
    try:
        # Search for incidents within 50km
        results, _ = client.scroll(
            collection_name="disaster_memory",
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="location",
                        geo_radius=models.GeoRadius(
                            center=models.GeoPoint(lat=lat, lon=lon),
                            radius=50000  # 50 km
                        )
                    )
                ]
            ),
            limit=5,
            with_payload=True
        )
        
        # Generate Satellite View URL (Simulated)
        # 200d = 200 meters distance (Close Zoom for building inspection)
        google_earth_url = f"https://earth.google.com/web/@{lat},{lon},100a,200d,35y,0h,0t,0r"
        
        if not results:
            return {
                "risk_level": "LOW",
                "incident_count": 0,
                "threats": ["No historical incidents detected nearby"],
                "user_location": f"{lat}, {lon}",
                "satellite_view": google_earth_url
            }
            
        # Analyze threats found
        types = [p.payload.get("disaster_type", "unknown") for p in results]
        
        # Generate Satellite View URL (Simulated)
        google_earth_url = f"https://earth.google.com/web/@{lat},{lon},100a,1000d,35y,0h,0t,0r"
        
        return {
            "risk_level": "HIGH",
            "incident_count": len(results),
            "threats": list(set(types)),
            "nearest_safe_zone_km": 55,
            "user_location": f"{lat}, {lon}",
            "satellite_view": google_earth_url
        }
        
    except Exception as e:
        print(f"⚠ Safety Check Error: {e}")
        return {"risk_level": "UNKNOWN", "user_location": f"{lat}, {lon}"}

def main():
    print("=========================================")
    print("      DISTRESS SIGNAL APP v1.0")
    print("=========================================")
    
    # 1. Connect to Backend (Use initialize to ensure indexes exist)
    client = initialize_qdrant()
    
    # 2. Get Location
    loc = get_live_location()
    
    # 3. Fast Safety Check
    risk_data = check_safety(client, loc['lat'], loc['lon'])
    
    print(f"\n⚠ RISK ASSESSMENT: {risk_data['risk_level']}")
    if risk_data.get('satellite_view'):
         print(f"   Satellite Feed: {risk_data['satellite_view']}")
         
    if risk_data['risk_level'] == 'HIGH':
        print(f"   Detected Threats: {', '.join(risk_data['threats'])}")
    
    # 4. Start Chat
    print("\nConnecting to Rakshak AI Responder...\n")
    agent = VictimChatAgent()
    greeting = agent.start_chat(risk_data)
    
    print(f"Rakshak: {greeting}")
    
    # Voice Input Instructions
    if WHISPER_AVAILABLE:
        print("\n💡 TIP: Type 'v' to use VOICE input (5 sec recording)")
    
    while True:
        try:
            user_input = input("\nYou: ")
            
            # Check for exit
            if user_input.lower() == 'q':
                break
            
            # Check for voice input
            if user_input.lower() == 'v':
                if WHISPER_AVAILABLE:
                    # Use panic analysis for voice input
                    result = get_voice_input(duration=5.0, analyze_panic=True)
                    if isinstance(result, tuple):
                        transcript, panic_level, audio_path = result
                    else:
                        transcript, panic_level, audio_path = result, None, None
                    
                    if transcript:
                        user_msg = transcript
                        # Add panic context to message if detected
                        if panic_level and panic_level in ["high", "extreme"]:
                            print(f"  ⚠️ HIGH DISTRESS DETECTED - Prioritizing response")
                    else:
                        print("⚠️ Voice input failed. Please type your message.")
                        continue
                else:
                    print("⚠️ Voice input not available. Please type your message.")
                    continue
            else:
                user_msg = user_input
            
            # PII Scrubbing - Remove sensitive data before sending to LLM
            clean_msg = pii_scrubber.scrub_text(user_msg)
            if clean_msg != user_msg:
                print("⚠️  [PRIVACY] Sensitive data detected and removed for your protection.")
            
            response = agent.send_message(clean_msg)
            print(f"Rakshak: {response}")
            
        except KeyboardInterrupt:
            break
            
            
    # 5. End Session - Simple Emergency Dispatch
    print("\n" + "="*50)
    print("      🚨 EMERGENCY DISPATCH INITIATED 🚨")
    print("="*50)
    
    # Analyze session for log purposes (stored for unified triage later)
    triage_report = agent.analyze_session()
    clean_report = triage_report.replace("```json", "").replace("```", "")
    
    # Parse for display (Robust JSON extraction)
    import re
    try:
        # specific regex to find json structure
        json_match = re.search(r'\{.*\}', clean_report, re.DOTALL)
        if json_match:
            triage_data = json.loads(json_match.group(0))
        else:
            triage_data = json.loads(clean_report)
    except:
        # Fallback if JSON fails
        print("⚠ Triage Report Parsing Failed. Raw output saved to log.")
        triage_data = {}
    
    # Save Log (for unified triage on system exit)
    log_file = agent.save_session_log(clean_report, risk_data)
    
    # Extract injury info from key_details
    # Extract injury info from key_details (Display all detected injuries/symptoms)
    key_details = triage_data.get('key_details', [])
    injury_info = ", ".join(key_details) if key_details else "Not specified"
    needs_info = triage_data.get('recommended_response', 'Rescue Team')
    
    # Simple Emergency Report with injury details
    print(f"""
    ╔══════════════════════════════════════════════════╗
    ║  🚨 EMERGENCY DISPATCH INITIATED 🚨              ║
    ╠══════════════════════════════════════════════════╣
    ║  📍 GPS: {risk_data.get('user_location', 'Unknown'):<38} ║
    ║  🩹 Injury: {str(injury_info)[:35]:<35} ║
    ║  🚑 Needs: {str(needs_info)[:36]:<36} ║
    ║  ✅ Status: TEAMS DISPATCHED                     ║
    ╚══════════════════════════════════════════════════╝
    """)
    
    print(f"[Session logged: {log_file}]")
    print("Stay calm. Help is on the way.")
    
    return log_file

if __name__ == "__main__":
    main()
