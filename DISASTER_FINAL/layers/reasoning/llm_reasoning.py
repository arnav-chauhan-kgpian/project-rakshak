"""
Agent 10: LLM Reasoning - Generates damage reports using Google Gemini API.

Supports both Gemini API (production) and template-based fallback.
"""

import os
from datetime import datetime


class LLMReasoningAgent:
    """Agent 10: Citation LLM Reasoning - Generates damage reports with Gemini AI"""
    
    def __init__(self):
        self.model = None
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self._initialized = False
        
        # Fallback template for when Gemini is unavailable
        self.report_template = """
DAMAGE ASSESSMENT REPORT
========================
Incident ID: {incident_id}
Assessment Time: {timestamp}
Disaster Type: {disaster_type}

SEVERITY ASSESSMENT:
- Primary Damage Level: {primary_damage}
- Affected Area: ~{affected_area_km2} km²
- Geographic Center: Lat {lat:.4f}, Lon {lon:.4f}

ANALYSIS:
{analysis}

EVIDENCE SOURCES:
{citations}

CONFIDENCE SCORE: {confidence:.2%}
"""
    
    def _lazy_init(self):
        """Lazy initialization of Gemini model."""
        if self._initialized:
            return
            
        if not self.api_key:
            print("  ⚠ GEMINI_API_KEY not set - using template fallback")
            self._initialized = False
            return
            
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            print("  ✓ Gemini LLM initialized (gemini-2.5-flash)")
            self._initialized = True
            
        except ImportError:
            print("  ⚠ google-generativeai not installed - using template fallback")
            print("    Install with: pip install google-generativeai")
            self._initialized = False
        except Exception as e:
            print(f"  ⚠ Gemini initialization error: {e}")
            self._initialized = False
    
    def generate_report(self, incident_id, search_results, current_metadata=None):
        """
        Generates damage assessment report with citations using Gemini.
        
        Args:
            incident_id: Unique incident identifier
            search_results: List of evidence from search results
            current_metadata: Metadata dict of the current incident (includes transcript)
            
        Returns:
            Formatted report string (AI-generated or template)
        """
        try:
            if not search_results and not current_metadata:
                return "No evidence available for report generation."
            
            # Lazy load Gemini
            self._lazy_init()
            
            # Extract evidence data
            evidence_data = self._extract_evidence(search_results, current_metadata)
            
            # Try Gemini first, fallback to template
            if self._initialized and self.model is not None:
                return self._generate_with_gemini(incident_id, evidence_data, search_results)
            else:
                return self._generate_template_report(incident_id, evidence_data, search_results)
                
        except Exception as e:
            print(f"  LLM Reasoning Error: {e}")
            return f"Error generating report: {str(e)}"
    
    def _extract_evidence(self, search_results, current_metadata=None):
        """Extract structured evidence from search results and current metadata."""
        # Default to first search result if no current metadata
        primary = current_metadata if current_metadata else (search_results[0]["payload"] if search_results else {})
        
        # Audio Intelligence
        audio_transcript = primary.get("audio_transcript") or primary.get("transcript")
        audio_panic = primary.get("audio_panic_score") or primary.get("panic_score", 0.0)
        
        # Aggregate damage counts from search results (historical context)
        total_damage = {"destroyed": 0, "major-damage": 0, "minor-damage": 0, "no-damage": 0}
        disaster_types = set()
        locations = []
        
        if search_results:
            for result in search_results:
                p = result["payload"]
                counts = p.get("damage_counts", {})
                for k, v in counts.items():
                    if k in total_damage:
                        total_damage[k] += v
                disaster_types.add(p.get("disaster_type", "unknown"))
                if p.get("latitude") and p.get("longitude"):
                    locations.append((p["latitude"], p["longitude"]))
        
        # Use current metadata values for the specific incident details
        damage_counts = primary.get("damage_counts", {})
        if not damage_counts:
             damage_counts = total_damage # Fallback to aggregate if missing
             
        return {
            "disaster_type": primary.get("disaster_type", "unknown"),
            "primary_damage": primary.get("damage_severity", "medium"),
            "timestamp": primary.get("timestamp", datetime.now().isoformat()),
            "latitude": primary.get("latitude", 0) if isinstance(primary.get("latitude"), (int, float)) else 0,
            "longitude": primary.get("longitude", 0) if isinstance(primary.get("longitude"), (int, float)) else 0,
            "total_buildings": sum(damage_counts.values()) if damage_counts else sum(total_damage.values()),
            "damage_counts": damage_counts if current_metadata else total_damage,
            "confidence": primary.get("confidence_score", 0.75),
            "num_incidents": len(search_results) if search_results else 0,
            "disaster_types": list(disaster_types),
            "audio_transcript": audio_transcript,
            "audio_panic_score": audio_panic
        }
    
    def _generate_with_gemini(self, incident_id, evidence, search_results):
        """Generate report using Gemini AI."""
        prompt = f"""You are a disaster response analyst. Generate a professional damage assessment report based on the following satellite imagery analysis data.

INCIDENT: {incident_id}
DISASTER TYPE: {evidence['disaster_type'].upper()}
LOCATION: Lat {evidence['latitude']:.4f}, Lon {evidence['longitude']:.4f}
TIMESTAMP: {evidence['timestamp']}

BUILDING DAMAGE ANALYSIS:
- Total Buildings Analyzed: {evidence['total_buildings']}
- Destroyed: {evidence['damage_counts']['destroyed']}
- Major Damage: {evidence['damage_counts']['major-damage']}
- Minor Damage: {evidence['damage_counts']['minor-damage']}
- No Damage: {evidence['damage_counts']['no-damage']}
"""

        # Inject Audio Data if available
        if evidence.get('audio_transcript'):
            prompt += f"""
EMERGENCY AUDIO LOG:
- Transcript: "{evidence['audio_transcript']}"
- Detected Panic Score: {evidence['audio_panic_score']:.2f} / 1.0
"""

        prompt += f"""
EVIDENCE:
- {evidence['num_incidents']} similar historical incidents found
- Primary match confidence: {evidence['confidence']:.2%}
- Related disaster types: {', '.join(evidence['disaster_types'])}

SIMILAR INCIDENTS FOR CITATION:
"""
        for i, result in enumerate(search_results[:5], 1):
            p = result["payload"]
            prompt += f"[{i}] {p.get('incident_id', 'Unknown')} - Score: {result['score']:.2f}, Type: {p.get('disaster_type')}\n"
        
        prompt += """

Generate a structured damage assessment report with:
1. Executive Summary (2-3 sentences)
2. Severity Assessment with damage breakdown
3. **Emergency Call Analysis** (If audio data is present, analyze the caller's urgency, describe the situation, and extract key details like trapped people, fire, or hazards).
4. Geographic Impact Analysis
5. Recommended Response Priority (CRITICAL/HIGH/MEDIUM/LOW)
6. Evidence Citations referencing the incidents above

Keep the report concise but informative. Use markdown formatting."""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"  Gemini API error: {e} - falling back to template")
            return self._generate_template_report(incident_id, evidence, search_results)
    
    def _generate_template_report(self, incident_id, evidence, search_results):
        """Fallback template-based report when Gemini unavailable."""
        # Generate citations
        citations = ""
        for i, result in enumerate(search_results[:5], 1):
            p = result["payload"]
            citations += f"[{i}] Incident {p.get('incident_id')} - "
            citations += f"Timestamp: {p.get('timestamp')}, "
            citations += f"Match Score: {result['score']:.2f}\n"
        
        # Generate analysis
        damage = evidence['damage_counts']
        analysis = f"""
Based on analysis of {evidence['num_incidents']} similar historical incidents:
- {damage['destroyed']} buildings destroyed ({damage['destroyed']/max(1,evidence['total_buildings'])*100:.1f}%)
- {damage['major-damage']} buildings with major damage
- {damage['minor-damage']} buildings with minor damage
- {damage['no-damage']} buildings undamaged

The {evidence['disaster_type'].title()} event shows patterns consistent with 
{evidence['primary_damage']} severity classification. Vector similarity analysis 
indicates strong correlation with historical events (confidence: {evidence['confidence']:.2%}).
"""
        
        return self.report_template.format(
            incident_id=incident_id,
            timestamp=evidence['timestamp'],
            disaster_type=evidence['disaster_type'].title(),
            primary_damage=evidence['primary_damage'].title(),
            affected_area_km2=evidence['num_incidents'] * 15,
            lat=evidence['latitude'],
            lon=evidence['longitude'],
            analysis=analysis,
            citations=citations,
            confidence=evidence['confidence']
        )