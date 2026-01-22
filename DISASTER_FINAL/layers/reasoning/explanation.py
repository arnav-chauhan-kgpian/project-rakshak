"""
Agent 12: Visual Explanation Package - Generates real visualizations with matplotlib.

Creates:
- Damage distribution bar chart
- Confidence gauge
- Severity pie chart
"""

import os
from pathlib import Path
from datetime import datetime


class ExplanationAgent:
    """Agent 12: Visual Explanation Package - Generates interpretable explanations with visuals"""
    
    def __init__(self, output_dir="reports/visualizations"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.explanation_components = [
            "damage_distribution",
            "confidence_gauge",
            "severity_breakdown"
        ]
        self._matplotlib_available = None
    
    def _check_matplotlib(self):
        """Check if matplotlib is available."""
        if self._matplotlib_available is None:
            try:
                import matplotlib
                matplotlib.use('Agg')  # Non-interactive backend
                import matplotlib.pyplot as plt
                self._matplotlib_available = True
            except ImportError:
                print("  ⚠ matplotlib not installed - visualizations disabled")
                print("    Install with: pip install matplotlib")
                self._matplotlib_available = False
        return self._matplotlib_available
    
    def generate_explanation(self, report, patterns, confidence_score, incident_id=None):
        """
        Generates comprehensive visual explanation package with real charts.
        
        Args:
            report: Text report from LLMReasoningAgent
            patterns: Pattern analysis from EvidenceSynthesisAgent
            confidence_score: Confidence score from ConfidenceControllerAgent
            incident_id: Optional incident identifier for filenames
            
        Returns:
            Dictionary with explanation components and generated image paths
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prefix = f"{incident_id}_{timestamp}" if incident_id else timestamp
            
            explanation_package = {
                "report_summary": report[:500] + "..." if len(report) > 500 else report,
                "components": {},
                "metadata": {
                    "confidence_score": confidence_score,
                    "pattern_mode": patterns.get("mode", "unknown"),
                    "result_count": patterns.get("result_count", 0),
                    "generated_at": datetime.now().isoformat()
                }
            }
            
            # Generate visualizations if matplotlib available
            if self._check_matplotlib():
                # 1. Damage Distribution Chart
                damage_path = self._generate_damage_chart(
                    patterns.get("damage_counts", {}),
                    prefix
                )
                explanation_package["components"]["damage_distribution"] = {
                    "type": "bar_chart",
                    "title": "Building Damage Distribution",
                    "data": patterns.get("damage_counts", {}),
                    "path": str(damage_path) if damage_path else None
                }
                
                # 2. Confidence Gauge
                gauge_path = self._generate_confidence_gauge(
                    confidence_score,
                    prefix
                )
                explanation_package["components"]["confidence_gauge"] = {
                    "type": "gauge_chart",
                    "title": "Assessment Confidence",
                    "score": confidence_score,
                    "threshold": 0.60,
                    "path": str(gauge_path) if gauge_path else None
                }
                
                # 3. Severity Breakdown Pie Chart
                severity_path = self._generate_severity_pie(
                    patterns.get("severity_distribution", {}),
                    prefix
                )
                explanation_package["components"]["severity_breakdown"] = {
                    "type": "pie_chart",
                    "title": "Severity Level Distribution",
                    "data": patterns.get("severity_distribution", {}),
                    "path": str(severity_path) if severity_path else None
                }
                
                print(f"  ✓ Generated 3 visualization charts in {self.output_dir}")
            else:
                # Fallback: placeholder URLs
                explanation_package["components"]["damage_distribution"] = {
                    "type": "bar_chart",
                    "data": patterns.get("damage_counts", {}),
                    "path": None,
                    "note": "matplotlib not available"
                }
                explanation_package["components"]["confidence_gauge"] = {
                    "type": "gauge_chart",
                    "score": confidence_score,
                    "path": None,
                    "note": "matplotlib not available"
                }
                explanation_package["components"]["severity_breakdown"] = {
                    "type": "pie_chart",
                    "data": patterns.get("severity_distribution", {}),
                    "path": None,
                    "note": "matplotlib not available"
                }
            
            # Add geographic center
            explanation_package["components"]["geographic_info"] = {
                "type": "location_data",
                "center": patterns.get("geographic_center"),
                "disaster_types": patterns.get("disaster_types", [])
            }
            
            return explanation_package
            
        except Exception as e:
            print(f"  Explanation Agent Error: {e}")
            return {"error": str(e)}
    
    def _generate_damage_chart(self, damage_counts, prefix):
        """Generate bar chart of building damage distribution."""
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            
            if not damage_counts or sum(damage_counts.values()) == 0:
                return None
            
            # Prepare data
            categories = ['No Damage', 'Minor', 'Major', 'Destroyed']
            keys = ['no-damage', 'minor-damage', 'major-damage', 'destroyed']
            values = [damage_counts.get(k, 0) for k in keys]
            colors = ['#4CAF50', '#FFC107', '#FF9800', '#F44336']
            
            # Create figure
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(categories, values, color=colors, edgecolor='white', linewidth=2)
            
            # Add value labels on bars
            for bar, val in zip(bars, values):
                if val > 0:
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                           str(val), ha='center', va='bottom', fontsize=12, fontweight='bold')
            
            # Styling
            ax.set_ylabel('Number of Buildings', fontsize=12)
            ax.set_title('Building Damage Distribution', fontsize=14, fontweight='bold')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.set_ylim(0, max(values) * 1.15 if max(values) > 0 else 10)
            
            # Save
            filepath = self.output_dir / f"{prefix}_damage_distribution.png"
            plt.tight_layout()
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()
            
            return filepath
            
        except Exception as e:
            print(f"    Damage chart error: {e}")
            return None
    
    def _generate_confidence_gauge(self, confidence, prefix):
        """Generate a half-circle gauge chart for confidence score."""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as patches
            import numpy as np
            import matplotlib
            matplotlib.use('Agg')
            
            fig, ax = plt.subplots(figsize=(8, 5))
            
            # Draw gauge background
            theta1, theta2 = 0, 180
            radius = 1.0
            
            # Background arc (gray)
            arc_bg = patches.Wedge(center=(0.5, 0), r=radius, theta1=theta1, theta2=theta2,
                                   facecolor='#E0E0E0', edgecolor='white', linewidth=3)
            ax.add_patch(arc_bg)
            
            # Colored sections
            sections = [(0, 40, '#F44336'), (40, 60, '#FF9800'), 
                       (60, 80, '#FFC107'), (80, 100, '#4CAF50')]
            
            for start_pct, end_pct, color in sections:
                start_angle = start_pct * 1.8  # 180 degrees / 100%
                end_angle = end_pct * 1.8
                arc = patches.Wedge(center=(0.5, 0), r=radius * 0.85, 
                                   theta1=start_angle, theta2=end_angle,
                                   facecolor=color, edgecolor='white', linewidth=1)
                ax.add_patch(arc)
            
            # Needle
            needle_angle = confidence * 180  # Convert 0-1 to 0-180 degrees
            needle_rad = np.radians(needle_angle)
            needle_length = 0.7
            needle_x = 0.5 + needle_length * np.cos(needle_rad)
            needle_y = needle_length * np.sin(needle_rad)
            ax.annotate('', xy=(needle_x, needle_y), xytext=(0.5, 0),
                       arrowprops=dict(arrowstyle='->', color='#333', lw=3))
            
            # Center circle
            center = plt.Circle((0.5, 0), 0.08, color='#333', zorder=5)
            ax.add_patch(center)
            
            # Score text
            score_text = f"{confidence:.1%}"
            ax.text(0.5, -0.3, score_text, ha='center', va='top', 
                   fontsize=28, fontweight='bold', color='#333')
            ax.text(0.5, -0.5, 'Confidence Score', ha='center', va='top', 
                   fontsize=12, color='#666')
            
            # Labels
            ax.text(0.0, -0.05, 'Low', ha='center', fontsize=10, color='#666')
            ax.text(1.0, -0.05, 'High', ha='center', fontsize=10, color='#666')
            
            ax.set_xlim(-0.2, 1.2)
            ax.set_ylim(-0.6, 1.1)
            ax.set_aspect('equal')
            ax.axis('off')
            ax.set_title('Assessment Confidence', fontsize=14, fontweight='bold', y=0.95)
            
            # Save
            filepath = self.output_dir / f"{prefix}_confidence_gauge.png"
            plt.tight_layout()
            plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            
            return filepath
            
        except Exception as e:
            print(f"    Confidence gauge error: {e}")
            return None
    
    def _generate_severity_pie(self, severity_dist, prefix):
        """Generate pie chart of severity distribution."""
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            
            if not severity_dist or sum(severity_dist.values()) == 0:
                return None
            
            # Filter out zero values
            labels = []
            sizes = []
            colors_map = {
                'low': '#4CAF50', 'medium': '#FFC107', 
                'high': '#FF9800', 'critical': '#F44336',
                'unknown': '#9E9E9E'
            }
            colors = []
            
            for k, v in severity_dist.items():
                if v > 0:
                    labels.append(k.title())
                    sizes.append(v)
                    colors.append(colors_map.get(k.lower(), '#9E9E9E'))
            
            if not sizes:
                return None
            
            # Create pie chart
            fig, ax = plt.subplots(figsize=(8, 8))
            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                startangle=90, explode=[0.02]*len(sizes),
                textprops={'fontsize': 11},
                wedgeprops={'edgecolor': 'white', 'linewidth': 2}
            )
            
            # Style autopct
            for autotext in autotexts:
                autotext.set_fontweight('bold')
                autotext.set_fontsize(12)
            
            ax.set_title('Severity Level Distribution', fontsize=14, fontweight='bold')
            
            # Save
            filepath = self.output_dir / f"{prefix}_severity_breakdown.png"
            plt.tight_layout()
            plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            
            return filepath
            
        except Exception as e:
            print(f"    Severity pie error: {e}")
            return None