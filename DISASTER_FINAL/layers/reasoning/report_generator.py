"""
Agent 14: Report Generator - Creates structured markdown reports for disaster assessments.
"""

from datetime import datetime
from pathlib import Path


class ReportGeneratorAgent:
    """Generates well-formatted markdown reports from disaster assessment results."""
    
    def __init__(self, output_dir="reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_report(self, assessment_result, save_to_file=True):
        """
        Generate a structured markdown report from assessment results.
        
        Args:
            assessment_result: Dictionary containing full assessment data
            save_to_file: Whether to save the report to a file
            
        Returns:
            Tuple of (report_content, file_path or None)
        """
        try:
            incident_id = assessment_result.get("incident_id", "Unknown")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Build report sections
            report = self._build_header(incident_id, timestamp, assessment_result)
            report += self._build_executive_summary(assessment_result)
            report += self._build_confidence_analysis(assessment_result)
            report += self._build_damage_assessment(assessment_result)
            report += self._build_evidence_table(assessment_result)
            report += self._build_recommendations(assessment_result)
            report += self._build_footer(timestamp)
            
            # Save to file if requested
            file_path = None
            if save_to_file:
                file_path = self.output_dir / f"report_{incident_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                file_path.write_text(report, encoding="utf-8")
            
            return report, file_path
            
        except Exception as e:
            error_report = f"# Error Generating Report\n\nError: {str(e)}\n"
            return error_report, None
    
    def _build_header(self, incident_id, timestamp, result):
        """Build report header section."""
        disaster_type = result.get("disaster_type", "Unknown").title()
        location = result.get("location", {})
        lat = location.get("latitude", 0)
        lon = location.get("longitude", 0)
        
        return f"""# 🚨 Disaster Assessment Report

## Incident: {incident_id}

| Field | Value |
|-------|-------|
| **Report Generated** | {timestamp} |
| **Disaster Type** | {disaster_type} |
| **Location** | {lat:.4f}°, {lon:.4f}° |
| **Status** | {result.get("status", "Unknown")} |

---

"""
    
    def _build_executive_summary(self, result):
        """Build executive summary section."""
        conf_score = result.get("confidence_score", 0)
        triage = result.get("triage_priority_map", {})
        priority = triage.get("priority_level", "unknown").upper()
        response_time = triage.get("response_time_hours", "N/A")
        
        # Confidence indicator
        if conf_score >= 0.8:
            conf_indicator = "🟢 HIGH"
        elif conf_score >= 0.6:
            conf_indicator = "🟡 MEDIUM"
        else:
            conf_indicator = "🔴 LOW"
        
        # Priority indicator
        priority_indicators = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢"
        }
        priority_icon = priority_indicators.get(priority, "⚪")
        
        return f"""## 📋 Executive Summary

| Metric | Value |
|--------|-------|
| **Overall Confidence** | {conf_indicator} ({conf_score:.1%}) |
| **Priority Level** | {priority_icon} {priority} |
| **Recommended Response Time** | {response_time} hours |

"""
    
    def _build_confidence_analysis(self, result):
        """Build confidence analysis section with breakdown."""
        quality_metrics = result.get("quality_metrics", {})
        breakdown = quality_metrics.get("score_breakdown", {})
        
        result_count = quality_metrics.get("result_count", 0)
        avg_score = quality_metrics.get("avg_score", 0)
        consistency = quality_metrics.get("consistency_ratio", 0)
        variance = quality_metrics.get("score_variance", 0)
        
        section = f"""## 📊 Confidence Analysis

### Score Breakdown

| Component | Value | Impact |
|-----------|-------|--------|
| **Base Quality Score** | {breakdown.get('base', 0):.3f} | Primary |
| **Consistency Bonus** | +{breakdown.get('consistency_bonus', 0):.3f} | Positive |
| **Result Count Bonus** | +{breakdown.get('count_bonus', 0):.3f} | Positive |
| **Variance Penalty** | {breakdown.get('variance_penalty', 0):.3f} | Negative |
| **Final Quality Score** | {quality_metrics.get('quality_score', 0):.3f} | — |

### Evidence Statistics

- **Total Results Analyzed**: {result_count}
- **Average Match Score**: {avg_score:.4f}
- **Type Consistency**: {consistency:.1%}
- **Score Variance**: {variance:.6f}
- **Geographic Diversity**: {quality_metrics.get('geo_diversity', 0):.2f}

"""
        return section
    
    def _build_damage_assessment(self, result):
        """Build damage assessment section from patterns."""
        patterns = result.get("patterns", {})
        damage_counts = patterns.get("damage_counts", {})
        total_buildings = patterns.get("total_buildings", 0)
        
        # Calculate percentages
        damage_rows = ""
        for damage_type in ["destroyed", "major-damage", "minor-damage", "no-damage"]:
            count = damage_counts.get(damage_type, 0)
            pct = (count / total_buildings * 100) if total_buildings > 0 else 0
            damage_rows += f"| {damage_type.replace('-', ' ').title()} | {count} | {pct:.1f}% |\n"
        
        # Geographic center
        geo_center = patterns.get("geographic_center", {})
        
        return f"""## 🏚️ Damage Assessment

### Building Damage Distribution

| Damage Level | Count | Percentage |
|--------------|-------|------------|
{damage_rows}| **Total** | **{total_buildings}** | **100%** |

### Pattern Analysis

- **Primary Damage Mode**: {patterns.get("mode", "Unknown").title()}
- **Temporal Trend**: {patterns.get("temporal_trend", "Unknown").title()}
- **Geographic Center**: {geo_center.get("latitude", 0):.4f}°, {geo_center.get("longitude", 0):.4f}°
- **Disaster Types Found**: {", ".join(patterns.get("disaster_types", ["Unknown"]))}

"""
    
    def _build_evidence_table(self, result):
        """Build evidence citations table."""
        # Extract from the damage assessment report (citations section)
        report_text = result.get("damage_assessment_report", "")
        
        # Parse the explanation package for evidence
        explanation = result.get("explanation_package", {})
        components = explanation.get("components", {})
        
        return f"""## 📚 Evidence Sources

The following historical incidents were retrieved and analyzed:

| # | Source | Relevance |
|---|--------|-----------|
| 1 | Vector similarity search | Primary evidence |
| 2 | Sparse text matching | Supporting context |
| 3 | Cross-disaster transfer | Domain adaptation |

### Raw Report Data

```
{report_text[:5000]}{"..." if len(report_text) > 5000 else ""}
```

"""
    
    def _build_recommendations(self, result):
        """Build recommendations section."""
        triage = result.get("triage_priority_map", {})
        priority = triage.get("priority_level", "medium")
        conf_score = result.get("confidence_score", 0)
        
        # Dynamic recommendations based on priority
        if priority == "critical":
            rec_list = """
- 🚨 **Immediate evacuation** of affected zones required
- Deploy emergency response teams within 2 hours
- Establish field hospitals and shelter points
- Request additional resources from neighboring regions
"""
        elif priority == "high":
            rec_list = """
- ⚠️ **Rapid assessment teams** should be deployed within 6 hours
- Prepare evacuation routes and shelters
- Coordinate with local emergency services
- Begin damage documentation
"""
        else:
            rec_list = """
- 📋 **Standard assessment** procedures recommended
- Monitor situation for escalation
- Document damage for insurance and recovery planning
- Coordinate community support resources
"""
        
        # Add confidence-based caveats
        if conf_score < 0.6:
            rec_list += "\n> ⚠️ **Note**: Confidence score is below 60%. Consider additional verification before major resource allocation.\n"
        
        return f"""## 💡 Recommendations

Based on the analysis, the following actions are recommended:

{rec_list}

"""
    
    def _build_footer(self, timestamp):
        """Build report footer."""
        return f"""---

*Report generated by Multi-Agent Disaster Response System (MAS)*  
*Timestamp: {timestamp}*  
*Confidence scores are based on vector similarity and historical pattern matching.*
"""
