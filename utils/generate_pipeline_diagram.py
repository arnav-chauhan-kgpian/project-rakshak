import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
import matplotlib.patheffects as path_effects

def create_premium_pipeline_diagram(output_path="rakshak_pipeline_architecture_premium.png"):
    """
    Generates a PREMIUM, high-resolution state diagram of the Rakshak Intel Pipeline.
    Style: Modern Dark / Tech Aesthetic.
    """
    # Setup Figure with Dark Background
    fig, ax = plt.subplots(figsize=(24, 14), facecolor='#0E1117')
    ax.set_facecolor('#0E1117')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # --- Config ---
    colors = {
        'layer1_bg': '#1E2329', 'layer1_border': '#4A90E2', 'layer1_title': '#4A90E2',
        'layer2_bg': '#1E2329', 'layer2_border': '#9B59B6', 'layer2_title': '#9B59B6',
        'layer3_bg': '#1E2329', 'layer3_border': '#E74C3C', 'layer3_title': '#E74C3C',
        'node_bg': '#262730', 'node_text': '#FFFFFF',
        'arrow': '#808495'
    }
    
    font_family = 'sans-serif'

    # --- Helpers ---
    def draw_glowing_box(x, y, w, h, label, border_color, fill_color='#262730', text_color='white', sublabel=None):
        # Shadow/Glow effect (simple offset)
        shadow = patches.FancyBboxPatch(
            (x+0.3, y-0.3), w, h,
            boxstyle="round,pad=0.8",
            linewidth=0,
            facecolor='black',
            alpha=0.3,
            zorder=2
        )
        ax.add_patch(shadow)

        # Main Box
        rect = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.8",
            linewidth=2,
            edgecolor=border_color,
            facecolor=fill_color,
            zorder=3
        )
        ax.add_patch(rect)
        
        # Text
        cx, cy = x + w/2, y + h/2
        
        main_text = ax.text(cx, cy + (0.8 if sublabel else 0), label, 
                           ha='center', va='center', 
                           fontsize=11, fontweight='bold', color=text_color, zorder=4, fontfamily=font_family)
        
        if sublabel:
            ax.text(cx, cy - 1.2, sublabel, 
                   ha='center', va='center', 
                   fontsize=9, color='#A0A0A0', zorder=4, fontstyle='italic', fontfamily=font_family)
            
        return (cx, cy)

    def draw_tech_arrow(start, end, text=None, curved=True, color='#808495'):
        style = "Simple, tail_width=1.0, head_width=6, head_length=8"
        conn_style = "arc3,rad=-0.15" if curved else "arc3,rad=0"
        
        arrow = patches.FancyArrowPatch(
            start, end, 
            connectionstyle=conn_style,
            arrowstyle=style, color=color, lw=1.0, zorder=2,
            alpha=0.8
        )
        ax.add_patch(arrow)
        
        if text:
            # Calculate mid point for text with curve offset
            mx, my = (start[0]+end[0])/2, (start[1]+end[1])/2
            # Offset slightly for clarity
            offset_y = 1.0 if start[1] == end[1] else 0.0
            
            t = ax.text(mx, my + offset_y, text, 
                   ha='center', va='center', 
                   fontsize=8, color=color, zorder=4, 
                   bbox=dict(facecolor='#0E1117', edgecolor='none', pad=2, alpha=0.7))

    # ==================== LAYOUT ====================

    # --- Layer 1: Perception (Top Left) ---
    # Zone
    ax.add_patch(patches.FancyBboxPatch((4, 55), 28, 40, boxstyle="round,pad=1", ec=colors['layer1_border'], fc=colors['layer1_bg'], alpha=0.95))
    ax.text(18, 92, "LAYER 1: PERCEPTION", ha='center', fontsize=14, fontweight='bold', color=colors['layer1_title'], fontfamily=font_family)

    # Nodes
    p_input = draw_glowing_box(8, 80, 20, 5, "SATELLITE INPUT", "#4A90E2", sublabel="Sentinel-2 / Maxar")
    p_embed = draw_glowing_box(8, 70, 20, 4, "EMBEDDING AGENT", "#4A90E2", sublabel="DINOv2 (Vision)")
    p_sparse = draw_glowing_box(8, 62, 20, 3, "SPARSE AGENT", "#4A90E2", sublabel="BM25 Keywords")
    
    # Arrows
    draw_tech_arrow((p_input[0], p_input[1]-3.5), (p_embed[0], p_embed[1]+3), color=colors['layer1_border'], curved=False)
    draw_tech_arrow((p_input[0], p_input[1]-3.5), (p_sparse[0], p_sparse[1]+2.5), color=colors['layer1_border'], curved=True)


    # --- Layer 2: Retrieval (Directly Below L1) ---
    # Zone
    ax.add_patch(patches.FancyBboxPatch((4, 5), 28, 45, boxstyle="round,pad=1", ec=colors['layer2_border'], fc=colors['layer2_bg'], alpha=0.95))
    ax.text(18, 47, "LAYER 2: RETRIEVAL", ha='center', fontsize=14, fontweight='bold', color=colors['layer2_title'], fontfamily=font_family)
    
    # Nodes
    r_db = draw_glowing_box(8, 35, 20, 6, "QDRANT VECTOR DB", "#9B59B6", fill_color="#36174D", sublabel="Disaster Memory Collection")
    r_search = draw_glowing_box(8, 25, 20, 4, "SEARCH EXECUTION", "#9B59B6", sublabel="Hybrid Fusion (RRF)")
    r_geo = draw_glowing_box(8, 15, 20, 4, "GEO-SIMILARITY", "#9B59B6", sublabel="Spatial Search")
    
    # Arrows
    draw_tech_arrow((p_embed[0], p_embed[1]-3), (r_db[0], r_db[1]+4), text="Dense Vectors", color='#A0A0A0')
    draw_tech_arrow((p_sparse[0], p_sparse[1]-2.5), (r_db[0], r_db[1]+4), text="Sparse Vectors", color='#A0A0A0', curved=True)
    
    draw_tech_arrow((r_db[0], r_db[1]-4), (r_search[0], r_search[1]+3), curved=False)
    draw_tech_arrow((r_search[0], r_search[1]-3), (r_geo[0], r_geo[1]+3), curved=False)


    # --- Layer 3: Reasoning (Right Side) ---
    # Zone
    ax.add_patch(patches.FancyBboxPatch((38, 5), 58, 90, boxstyle="round,pad=1", ec=colors['layer3_border'], fc=colors['layer3_bg'], alpha=0.95))
    ax.text(67, 92, "LAYER 3: REASONING & OUTPUT", ha='center', fontsize=14, fontweight='bold', color=colors['layer3_title'], fontfamily=font_family)
    
    # Main Workflow Nodes
    logic_synth = draw_glowing_box(44, 75, 20, 6, "EVIDENCE SYNTHESIS", "#E74C3C", sublabel="Pattern Recognition")
    logic_hist = draw_glowing_box(44, 60, 20, 5, "HISTORY SUMMARIZER", "#E74C3C", sublabel="Context Narrative")
    
    llm_core = draw_glowing_box(72, 68, 20, 8, "LLM REASONING", "#E74C3C", fill_color="#5D1815", sublabel="Gemini 2.5 Flash")
    
    audit = draw_glowing_box(72, 52, 20, 5, "REPORT AUDITOR", "#F1C40F", sublabel="Fact Checking", text_color="#F1C40F") # Gold for auditor
    
    # Output Flow
    post = draw_glowing_box(58, 35, 20, 5, "POST-PROCESSOR", "#2ECC71", sublabel="Confidence & Triage")
    viz = draw_glowing_box(58, 22, 20, 5, "VISUALIZATION", "#2ECC71", sublabel="Charts & Graphs")
    final = draw_glowing_box(58, 10, 20, 6, "FINAL REPORT UI", "#FFFFFF", fill_color="#2ECC71", text_color="#000000", sublabel="Streamlit Dashboard")

    # --- Connections (The Web) ---
    
    # Connect Retrieval to Reasoning
    draw_tech_arrow((r_geo[0]+11, r_geo[1]), (logic_synth[0]-11, logic_synth[1]), text="Filtered Incidents", color='#FFFFFF')
    draw_tech_arrow((r_search[0]+11, r_search[1]), (logic_synth[0]-11, logic_synth[1]), curved=True)
    
    # Synthesis -> History
    draw_tech_arrow((logic_synth[0], logic_synth[1]-4), (logic_hist[0], logic_hist[1]+3.5), curved=False)
    
    # Into LLM
    draw_tech_arrow((logic_synth[0]+11, logic_synth[1]), (llm_core[0]-11, llm_core[1]+2), text="Structured Evidence")
    draw_tech_arrow((logic_hist[0]+11, logic_hist[1]), (llm_core[0]-11, llm_core[1]-2), text="Historical Context")
    
    # LLM Loop
    draw_tech_arrow((llm_core[0], llm_core[1]-5), (audit[0], audit[1]+3.5), text="Draft Report", curved=False)
    draw_tech_arrow((audit[0], audit[1]+3.5), (llm_core[0]+10, llm_core[1]), text="Feedback Loop", curved=True, color="#F1C40F") # Feedback
    
    # Downstream
    draw_tech_arrow((audit[0]-11, audit[1]), (post[0]+11, post[1]), text="Verified Report", curved=True)
    draw_tech_arrow((post[0], post[1]-3.5), (viz[0], viz[1]+3.5), curved=False)
    draw_tech_arrow((viz[0], viz[1]-3.5), (final[0], final[1]+4), curved=False)
    

    # --- Titles & Branding ---
    plt.text(50, 97, "PROJECT RAKSHAK SYSTEM ARCHITECTURE", ha='center', fontsize=22, fontweight='bold', color='white', fontfamily=font_family)
    plt.text(50, 2, "15-Agent Multi-Modal Neural Pipeline", ha='center', fontsize=12, color='#808495', fontfamily=font_family)
    
    # Legend/Key
    # (Optional, but adds to the look)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='#0E1117')
    print(f"Premium Diagram saved to {output_path}")

if __name__ == "__main__":
    create_premium_pipeline_diagram()
