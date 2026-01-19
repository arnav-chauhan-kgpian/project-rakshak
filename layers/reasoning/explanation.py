import json

class ExplanationAgent:
    """Agent 12: Visual Explanation Package - Generates interpretable explanations with visuals"""
    
    def __init__(self):
        self.explanation_components = [
            "severity_heatmap",
            "timeline",
            "impact_zones",
            "confidence_visualization"
        ]
    
    def generate_explanation(self, report, patterns, confidence_score):
        """
        Generates comprehensive visual explanation package.
        
        Args:
            report: Text report from LLMReasoningAgent
            patterns: Pattern analysis from EvidenceSynthesisAgent
            confidence_score: Confidence score from ConfidenceControllerAgent
            
        Returns:
            Dictionary with explanation components
        """
        try:
            explanation_package = {
                "report_summary": report[:500] + "..." if len(report) > 500 else report,
                "components": {},
                "metadata": {
                    "confidence_score": confidence_score,
                    "pattern_mode": patterns.get("mode", "unknown"),
                    "result_count": patterns.get("result_count", 0)
                }
            }
            
            # Generate component explanations
            explanation_package["components"]["severity_heatmap"] = {
                "type": "spatial_heatmap",
                "center": patterns.get("geographic_center"),
                "data": patterns.get("severity_distribution"),
                "url": "severity_heatmap.png"
            }
            
            explanation_package["components"]["timeline"] = {
                "type": "temporal_chart",
                "trend": patterns.get("temporal_trend"),
                "url": "timeline.png"
            }
            
            explanation_package["components"]["confidence_visualization"] = {
                "type": "confidence_gauge",
                "score": confidence_score,
                "threshold": 0.60,
                "url": "confidence_gauge.png"
            }
            
            return explanation_package
        except Exception as e:
            print(f"Explanation Agent Error: {e}")
            return {}