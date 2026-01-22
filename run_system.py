
import os
import sys
import json
from pathlib import Path
from chatbot_client import main as run_chat_client
from main import run_rakshak_assessment, CentralCoordinator, initialize_qdrant
from layers.reasoning.post_processor import PostProcessorAgent

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def generate_unified_triage(active_logs=None):
    """Aggregates chat logs. If active_logs provided, uses only those. Else falls back to all (or empty)."""
    log_dir = Path("chat_logs")
    
    if active_logs is not None:
        # Filter active_logs that actually exist
        logs = [Path(l) for l in active_logs if l and Path(l).exists()]
    else:
        # Fallback to Glob if None passed (legacy behavior)
        logs = list(log_dir.glob("*.json")) if log_dir.exists() else []

    if not logs:
        print("\n[No distress signals received this session]")
        print("Generating fallback triage report...")
        
        # Fallback: Use PostProcessor with default values
        processor = PostProcessorAgent()
        result = processor.process(
            report="No distress communications logged.",
            patterns={"mode": "low"},
            quality_metrics={"quality_score": 0.5, "result_count": 0}
        )
        triage = result["triage_priority_map"]
        conf = result["confidence_score"]
        
        print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║                    UNIFIED TRIAGE REPORT (DEFAULT)                   ║
╠══════════════════════════════════════════════════════════════════════╣
║  Distress Signals Received:  0                                       ║
║  Priority Level:             {triage.get('priority_level', 'LOW').upper():<40} ║
║  Personnel Required:         {triage.get('resource_allocation', {}).get('personnel', 10):<40} ║
║  Vehicles Required:          {triage.get('resource_allocation', {}).get('vehicles', 2):<40} ║
║  Response Time:              {triage.get('response_time_hours', 72)} hours{' '*33} ║
╚══════════════════════════════════════════════════════════════════════╝
        """)
        return
    
    print(f"\n[Aggregating {len(logs)} distress signals from current session...]")
    
    highest_panic = "Low"
    panic_map = {"Low": 0, "Medium": 1, "High": 2, "Extreme": 3}
    all_locations = []
    
    # Casualties & Response Counters
    fatalities_count = 0
    wounded_count = 0
    medical_teams_dispatched = 0
    severe_injuries = 0
    
    critical_summaries = []
    
    for log in logs:
        try:
            with open(log, 'r') as f:
                data = json.load(f)
                report = json.loads(data.get("triage_report", "{}"))
                p_score = report.get("panic_score", "Low")
                
                # Update Panic Level
                if panic_map.get(p_score, 0) > panic_map.get(highest_panic, 0):
                    highest_panic = p_score
                
                # Highlight Critical Summaries
                if p_score in ["High", "Extreme"]:
                    critical_summaries.append(f"[{p_score}] {report.get('summary', 'No summary')}")
                
                # Location - Get actual GPS coordinates
                risk_init = data.get("risk_assessment_init", {})
                # Try user_location string first (format: "lat, lon")
                user_loc = risk_init.get("user_location", "")
                if user_loc and "," in user_loc:
                    loc = user_loc.strip()
                else:
                    # Fallback to separate lat/lon fields
                    lat = risk_init.get("lat", "?")
                    lon = risk_init.get("lon", "?")
                    loc = f"{lat}, {lon}"
                all_locations.append(loc)
                
                # Analyze key_details for casualties (Simulated extraction)
                key_details = report.get("key_details", [])
                details_str = " ".join(key_details).lower()
                summary_str = report.get("summary", "").lower()
                
                # Naive Keyword Detection for Demo (In PROD use LLM extraction)
                if "dead" in details_str or "fatality" in details_str:
                    fatalities_count += 1
                if "injured" in details_str or "bleeding" in details_str or "broken" in details_str:
                    wounded_count += 1
                if "severe" in details_str or "critical" in details_str:
                    severe_injuries += 1
                    
                # Count Medical Teams (1 per distress signal requesting medical)
                rec_action = report.get("recommended_response", "").lower()
                if "medical" in rec_action or "ambulance" in rec_action or "rescue" in rec_action:
                    medical_teams_dispatched += 1
                    
        except:
            continue
    
    # Generate unified triage with panic override
    processor = PostProcessorAgent()
    
    casualty_data = {
        "fatalities": fatalities_count,
        "wounded": wounded_count,
        "medical_teams": medical_teams_dispatched,
        "severe_injuries": severe_injuries
    }
    
    result = processor.process(
        report=f"Aggregated {len(logs)} distress signals.",
        patterns={"mode": "high" if highest_panic in ["High", "Extreme"] else "medium"},
        quality_metrics={"quality_score": 0.7, "result_count": len(logs)},
        triage_override={"panic_score": highest_panic},
        casualty_data=casualty_data
    )
    triage = result["triage_priority_map"]
    conf = result["confidence_score"]
    
    # Unique locations
    unique_locs = list(set(all_locations))[:3]
    loc_str = " | ".join(unique_locs) if unique_locs else "N/A"
    
    # Format Critical Intel
    intel_str = ""
    if critical_summaries:
        intel_str = "\n".join([f"║  • {s[:60]}..." for s in critical_summaries[:3]])
    else:
        intel_str = "║  (No critical qualitative data available)"

    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║                    🚨 UNIFIED TRIAGE REPORT 🚨                        ║
╠══════════════════════════════════════════════════════════════════════╣
║  METRIC                        │  VALUE                              ║
├────────────────────────────────┼─────────────────────────────────────┤
║  Distress Signals Received     │  {len(logs):<37} ║
║  Highest Panic Level           │  {highest_panic.upper():<37} ║
║  Affected Locations            │  {loc_str[:35]:<37} ║
├────────────────────────────────┼─────────────────────────────────────┤
║  CASUALTY ASSESSMENT           │                                     ║
├────────────────────────────────┼─────────────────────────────────────┤
║  Confirmed Fatalities          │  {fatalities_count:<37} ║
║  Wounded / Injured             │  {wounded_count:<37} ║
║  Severe/Critical Cases         │  {severe_injuries:<37} ║
├────────────────────────────────┼─────────────────────────────────────┤
║  RESPONSE LOGISTICS            │                                     ║
├────────────────────────────────┼─────────────────────────────────────┤
║  Medical Teams Dispatched      │  {medical_teams_dispatched:<37} ║
║  Final Priority Level          │  {triage.get('priority_level', 'N/A').upper():<37} ║
║  Est. Response Time            │  {triage.get('response_time_hours', 'N/A')} hours{' '*31} ║
├────────────────────────────────┼─────────────────────────────────────┤
║  RESOURCE ALLOCATION (Derived from Casualty Metrics)                  ║
├────────────────────────────────┼─────────────────────────────────────┤
║  Personnel Required            │  {triage.get('resource_allocation', {}).get('personnel', 0):<37} ║
║  Vehicles Required             │  {triage.get('resource_allocation', {}).get('vehicles', 0):<37} ║
║  Budget Allocation (%)         │  {triage.get('resource_allocation', {}).get('funds_percent', 0):<37} ║
╠══════════════════════════════════════════════════════════════════════╣
║  CRITICAL SITUATION HIGHLIGHTS (From Chat Logs)                      ║
╠══════════════════════════════════════════════════════════════════════╣
{intel_str}
╚══════════════════════════════════════════════════════════════════════╝
    """)

def main_menu():
    """Main System Router"""
    # Pre-load Coordinator to save time
    print("Loading Core Systems...")
    initialize_qdrant()
    coordinator = CentralCoordinator()
    
    # Session Log Tracker
    session_logs = []
    
    while True:
        clear_screen()
        print(f"""
    ╔════════════════════════════════════════════════════════════╗
    ║      PROJECT RAKSHAK: DISASTER RESPONSE CONTROL CENTER     ║
    ╚════════════════════════════════════════════════════════════╝
    
    SESSION STATS: {len(session_logs)} Distress Signals Active
    
    SELECT OPERATION MODE:
    
    [1] 🚨 DISTRESS SIGNAL MODE (Victim Chat)
        - Simulate distressed user
        - Emergency dispatch on exit
        - Logs saved for unified triage
        
    [2] 🌍 RAKSHAK INTEL (Damage Assessment)
        - Full 13-Agent Pipeline
        - Satellite Imagery Analysis
        - Generate Detailed Report

    [3] 🖥️ LAUNCH DASHBOARD (Streamlit UI)
        - Interactive Web Interface
        - Visual Analytics
        - Combined Modes
        
    [t] 🔌 TERMINATE & SHOW UNIFIED TRIAGE
        - Aggregate all distress signals
        - Generate final resource allocation
    """)
        
        choice = input("COMMAND > ").lower().strip()
        
        if choice == '1':
            print("\nInitializing Distress Protocol...")
            try:
                # Capture log from chatbot
                log = run_chat_client()
                if log:
                    session_logs.append(log)
            except KeyboardInterrupt:
                pass
            input("\nPress ENTER to return to menu...")
            
        elif choice == '2':
            print("\nInitializing Overwatch Protocols...")
            try:
                run_rakshak_assessment(coordinator, session_logs=session_logs)
            except Exception as e:
                print(f"System Error: {e}")
            input("\nPress ENTER to return to menu...")
            
        elif choice == '3':
            print("\nLaunching Streamlit Dashboard...")
            try:
                import subprocess
                subprocess.run(["streamlit", "run", "app.py"])
            except KeyboardInterrupt:
                pass
            input("\nPress ENTER to return to menu...")
            
        elif choice == 't':
            print("\n" + "="*70)
            print("      SYSTEM SHUTDOWN - GENERATING UNIFIED TRIAGE")
            print("="*70)
            generate_unified_triage(active_logs=session_logs)
            print("\nProject Rakshak systems offline. Goodbye.")
            sys.exit(0)
            
        else:
            print("Invalid Command.")
            
if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nForce Shutdown.")

