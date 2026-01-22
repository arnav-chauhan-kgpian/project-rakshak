"""
PostProcessorAgent: Unified Output Packager (Agents 11-13 Merged)
Handles all non-AI post-processing: confidence calibration, explanation packaging, and triage priority.
"""

import math
from layers.reasoning.explanation import ExplanationAgent


class PostProcessorAgent:
    """
    Unified agent for all output post-processing.
    Merges: ConfidenceControllerAgent (11), ExplanationAgent (12), PriorityAgent (13).
    """
    
    def __init__(self):
        self.base_calibration = 0.7
        self.severity_levels = ["low", "medium", "high", "critical"]
        self.priority_thresholds = {
            "low": (0.0, 0.5),
            "medium": (0.5, 0.7),
            "high": (0.7, 0.85),
            "critical": (0.85, 1.0)
        }
        # Initialize the real Visualization Agent
        self.explainer = ExplanationAgent()
    

    
    # ===== Confidence Calculation (Former Agent 11) =====
    def _calculate_confidence(self, vector_score, evidence_quality_score, quality_metrics=None):
        """Calculates calibrated confidence score."""
        try:
            weights = {
                "vector_similarity": 0.5,
                "evidence_quality": 0.3,
                "additional_factors": 0.2
            }
            
            additional_score = 0.5
            if quality_metrics:
                result_count = quality_metrics.get("result_count", 1)
                count_factor = min(1.0, math.log(result_count + 1) / math.log(11))
                consistency = quality_metrics.get("consistency_ratio", 0.5)
                variance = quality_metrics.get("score_variance", 0)
                variance_penalty = min(0.3, variance * 0.5)
                additional_score = (count_factor * 0.4 + consistency * 0.4 + (1 - variance_penalty) * 0.2)
            
            combined_score = (
                vector_score * weights["vector_similarity"] +
                evidence_quality_score * weights["evidence_quality"] +
                additional_score * weights["additional_factors"]
            )
            
            calibrated = (
                self.base_calibration +
                (combined_score - 0.5) * (1 - 2 * abs(self.base_calibration - 0.5))
            )
            
            return max(0.0, min(1.0, calibrated))
        except Exception as e:
            print(f"Confidence Error: {e}")
            return 0.5
    
    # ===== Explanation Package (Former Agent 12) =====
    def _generate_explanation(self, report, patterns, confidence_score, incident_id=None):
        """Generates visual explanation package with REAL charts via ExplanationAgent."""
        try:
            # Delegate to the real ExplanationAgent which generates PNG files
            return self.explainer.generate_explanation(
                report=report,
                patterns=patterns,
                confidence_score=confidence_score,
                incident_id=incident_id
            )
        except Exception as e:
            print(f"Explanation Error: {e}")
            return {}
    
    # ===== Triage Priority (Former Agent 13) =====
    def _recommend_priority(self, damage_mode, confidence_factor, override=None, casualty_data=None):
        """Recommends triage priority and resource allocation."""
        try:
            damage_to_priority = {"low": 1, "medium": 2, "high": 3, "critical": 4, "unknown": 2}
            base_priority = damage_to_priority.get(damage_mode.lower(), 2)
            
            # Apply Override from Chatbot (Panic Boost)
            if override and override.get("panic_score"):
                panic_map = {"Low": 0, "Medium": 1, "High": 2, "Extreme": 3}
                panic_boost = panic_map.get(override.get("panic_score"), 0)
                base_priority = min(4, base_priority + panic_boost)
                
            adjusted_priority = min(4, max(1, base_priority * confidence_factor))
            
            priority_level = "medium"
            for level, (min_val, max_val) in self.priority_thresholds.items():
                if min_val <= adjusted_priority / 4 < max_val:
                    priority_level = level
                    break
            
            # --- Dynamic Resource Calculation ---
            # Base resources from tier
            base_resources = {
                "low": {"personnel": 10, "vehicles": 2},
                "medium": {"personnel": 20, "vehicles": 4},
                "high": {"personnel": 40, "vehicles": 10},
                "critical": {"personnel": 80, "vehicles": 20}
            }
            res = base_resources.get(priority_level, base_resources["medium"]).copy()
            
            # Add resources based on actual casualty data
            if casualty_data:
                # Personnel: 2 per wounded, 4 per fatality (recovery), 5 per medical team request
                extra_personnel = (
                    casualty_data.get("wounded", 0) * 2 + 
                    casualty_data.get("fatalities", 0) * 4 +
                    casualty_data.get("medical_teams", 0) * 5
                )
                
                # Vehicles: 1 ambulance per 2 wounded, 1 hearse per 5 fatalities
                extra_vehicles = (
                    math.ceil(casualty_data.get("wounded", 0) / 2) +
                    math.ceil(casualty_data.get("fatalities", 0) / 5)
                )
                
                res["personnel"] += extra_personnel
                res["vehicles"] += extra_vehicles
                
            # Budget is proportional to personnel (approx $1000 per person deployment)
            res["funds_percent"] = min(100, int(res["personnel"] / 2)) # Cap at 100%
            
            response_times = {"low": 72, "medium": 24, "high": 6, "critical": 1}
            final_response_time = response_times.get(priority_level, 24)
            
            # Faster response if severe casualties
            if casualty_data and (casualty_data.get("fatalities", 0) > 0 or casualty_data.get("severe_injuries", 0) > 0):
                final_response_time = max(1, final_response_time // 2)

            return {
                "priority_level": priority_level,
                "priority_score": adjusted_priority / 4,
                "damage_severity": damage_mode,
                "confidence_adjusted": confidence_factor,
                "resource_allocation": res,
                "response_time_hours": final_response_time,
                "triage_notes": f"Priority: {priority_level.upper()} | Damage: {damage_mode}"
            }
        except Exception as e:
            print(f"Priority Error: {e}")
            return {}

    def process(self, report, patterns, quality_metrics, triage_override=None, casualty_data=None, incident_id=None):
        """
        Single entry point for all post-processing.
        
        Args:
            report: Final verified report from Agent 14
            patterns: Pattern analysis from EvidenceSynthesisAgent
            quality_metrics: Quality metrics from validation
            triage_override: Optional dict from Chatbot Triage (Panic Score)
            casualty_data: Optional dict with 'fatalities', 'wounded', 'medical_teams'
            incident_id: Unique incident identifier for file naming
            
        Returns:
            Dict with confidence, explanation, and triage results.
        """
        # Step 1: Calculate confidence
        vector_score = quality_metrics.get("avg_score", 0.5)
        evidence_quality = quality_metrics.get("quality_score", 0.5)
        confidence = self._calculate_confidence(vector_score, evidence_quality, quality_metrics)
        
        # Step 2: Generate explanation package
        explanation = self._generate_explanation(report, patterns, confidence, incident_id=incident_id)
        
        # Step 3: Calculate triage priority
        damage_mode = patterns.get("mode", "medium")
        triage = self._recommend_priority(damage_mode, 1.5, triage_override, casualty_data)
        
        return {
            "confidence_score": confidence,
            "explanation_package": explanation,
            "triage_priority_map": triage
        }
