#!/usr/bin/env python3
"""
Diagram Recreator - Creates clean diagrams for all NCERT subjects.
Supports: Chemistry, Physics, Biology, Maths (Class 11 & 12)
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, FancyArrowPatch
import numpy as np

from ncert_subjects import detect_subject

# Import subject-specific recreators
from recreate_physics import PHYSICS_DIAGRAMS, identify_physics_diagram
from recreate_biology import BIOLOGY_DIAGRAMS, identify_biology_diagram
from recreate_maths import MATHS_DIAGRAMS, identify_maths_diagram


# ================== CHEMISTRY DIAGRAMS ==================

def create_beaker_diagram(output_path: Path, params: dict = None):
    """Create a beaker/container diagram showing gas dissolution."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 6))

    for idx, ax in enumerate(axes):
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 12)
        ax.set_aspect('equal')
        ax.axis('off')

        # Beaker outline
        beaker = FancyBboxPatch((1, 0.5), 8, 9, boxstyle="round,pad=0.1",
                                 facecolor='none', edgecolor='black', linewidth=2)
        ax.add_patch(beaker)

        # Liquid layers
        bottom = Rectangle((1.2, 0.7), 7.6, 3, facecolor='#D3D3D3', edgecolor='none')
        ax.add_patch(bottom)
        middle = Rectangle((1.2, 3.7), 7.6, 3, facecolor='#87CEEB', edgecolor='none')
        ax.add_patch(middle)

        # Hatched top area
        for i in range(20):
            x1 = 1.2 + i * 0.4
            ax.plot([x1, x1 + 0.3], [6.7, 7.2], 'k-', linewidth=0.5)

        # Gas particles
        np.random.seed(42 + idx)
        n_particles = 30 if idx == 0 else 50
        x_liquid = np.random.uniform(1.5, 8.5, n_particles)
        y_liquid = np.random.uniform(1, 6.5, n_particles)
        ax.scatter(x_liquid, y_liquid, c='black', s=15)

        x_gas = np.random.uniform(1.5, 8.5, 15)
        y_gas = np.random.uniform(7.5, 9, 15)
        ax.scatter(x_gas, y_gas, c='black', s=15)

        # Weight on top
        if idx == 0:
            weight = Rectangle((3.5, 9.5), 3, 1, facecolor='white', edgecolor='black')
            ax.add_patch(weight)
            ax.text(5, 10, r'$W_1$', ha='center', va='center', fontsize=12)
        else:
            for j, x in enumerate([2, 4.5, 7]):
                weight = Rectangle((x, 9.5), 2, 0.8, facecolor='white', edgecolor='black')
                ax.add_patch(weight)
                ax.text(x + 1, 9.9, f'$W_{j+1}$', ha='center', va='center', fontsize=10)
            ax.annotate('Piston', xy=(9, 7.5), xytext=(11, 7.5),
                       fontsize=10, ha='left',
                       arrowprops=dict(arrowstyle='->', color='black'))

        ax.text(5, -0.5, f'({chr(97+idx)})', ha='center', fontsize=12)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def create_graph(output_path: Path, graph_type: str, params: dict = None):
    """Create various types of graphs."""
    fig, ax = plt.subplots(figsize=(8, 6))

    if graph_type == "linear":
        x = np.linspace(0, 0.025, 100)
        y = x * 40000
        ax.plot(x, y, 'g-', linewidth=2)
        ax.scatter([0.002, 0.004, 0.006, 0.008, 0.010, 0.012, 0.014, 0.016, 0.018, 0.020],
                  [80, 160, 240, 320, 400, 480, 560, 640, 720, 800],
                  c='blue', s=50, zorder=5)
        ax.set_xlabel('Mole fraction of HCl in its\nsolution in cyclohexane', fontsize=11)
        ax.set_ylabel('Partial pressure of HCl /torr', fontsize=11)
        ax.set_xlim(0, 0.025)
        ax.set_ylim(0, 1000)
        ax.set_facecolor('#FFFFD0')

    elif graph_type == "vapour_pressure":
        x = np.linspace(0, 1, 100)
        p1_0, p2_0 = 200, 400
        p1 = p1_0 * (1 - x)
        p2 = p2_0 * x
        p_total = p1 + p2
        ax.plot(x, p1, 'g--', linewidth=2, label='$p_1$')
        ax.plot(x, p2, 'g--', linewidth=2, label='$p_2$')
        ax.plot(x, p_total, 'g-', linewidth=2, label='$p_{total}$')
        ax.set_xlabel('Mole fraction $x_2$', fontsize=11)
        ax.set_ylabel('Vapour pressure →', fontsize=11)
        ax.set_facecolor('#FFFFD0')
        ax.text(0.9, p1_0 * 0.1, 'I', fontsize=12)
        ax.text(0.9, p2_0 * 0.9, 'II', fontsize=12)
        ax.text(0.9, p_total[-10], 'III', fontsize=12)
        ax.text(-0.05, p1_0, '$p_1^0$', fontsize=11, ha='right')
        ax.text(1.05, p2_0, '$p_2^0$', fontsize=11, ha='left')

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def create_boiling_point_diagram(output_path: Path):
    """Create boiling point elevation diagram."""
    fig, ax = plt.subplots(figsize=(8, 6))
    T = np.linspace(300, 400, 100)
    p_pure = np.exp((T - 350) / 20)
    p_solution = np.exp((T - 355) / 20)

    ax.plot(T, p_pure, 'b-', linewidth=2, label='Pure solvent')
    ax.plot(T, p_solution, 'r-', linewidth=2, label='Solution')
    ax.axhline(y=1.013, color='black', linestyle='--', linewidth=1)
    ax.text(302, 1.1, '1.013 bar', fontsize=10)

    T_b0, T_b = 373.15, 375
    ax.axvline(x=T_b0, color='gray', linestyle=':', ymax=0.5)
    ax.axvline(x=T_b, color='gray', linestyle=':', ymax=0.55)
    ax.annotate('', xy=(T_b, 0.3), xytext=(T_b0, 0.3),
               arrowprops=dict(arrowstyle='<->', color='black'))
    ax.text((T_b0 + T_b)/2, 0.35, r'$\Delta T_b$', ha='center', fontsize=11)

    ax.set_xlabel('Temperature / K', fontsize=11)
    ax.set_ylabel('Vapour pressure / bar', fontsize=11)
    ax.set_xlim(300, 400)
    ax.set_ylim(0, 3)
    ax.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def create_osmosis_diagram(output_path: Path):
    """Create osmosis/semipermeable membrane diagram."""
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12)
    ax.set_aspect('equal')
    ax.axis('off')

    container = FancyBboxPatch((1, 1), 8, 8, boxstyle="round,pad=0.05",
                                facecolor='none', edgecolor='black', linewidth=2)
    ax.add_patch(container)
    ax.plot([5, 5], [1.5, 8.5], 'k-', linewidth=3)

    left = Rectangle((1.2, 1.2), 3.6, 7.6, facecolor='#ADD8E6', edgecolor='none')
    ax.add_patch(left)
    right = Rectangle((5.2, 1.2), 3.6, 7.6, facecolor='#4682B4', edgecolor='none')
    ax.add_patch(right)

    np.random.seed(42)
    x_solute = np.random.uniform(5.5, 8.5, 20)
    y_solute = np.random.uniform(1.5, 8.5, 20)
    ax.scatter(x_solute, y_solute, c='red', s=30)

    for y in [3, 5, 7]:
        ax.annotate('', xy=(5.3, y), xytext=(4.7, y),
                   arrowprops=dict(arrowstyle='->', color='green', lw=2))

    ax.text(3, 10, 'Pure Solvent', ha='center', fontsize=11)
    ax.text(7, 10, 'Solution', ha='center', fontsize=11)
    ax.text(5, 0.3, 'Semipermeable\nMembrane', ha='center', fontsize=10)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def create_reverse_osmosis_diagram(output_path: Path):
    """Create reverse osmosis diagram."""
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12)
    ax.set_aspect('equal')
    ax.axis('off')

    container = FancyBboxPatch((1, 1), 8, 8, boxstyle="round,pad=0.05",
                                facecolor='none', edgecolor='black', linewidth=2)
    ax.add_patch(container)
    ax.plot([5, 5], [1.5, 8.5], 'k-', linewidth=3)

    left = Rectangle((1.2, 1.2), 3.6, 7.6, facecolor='#4682B4', edgecolor='none')
    ax.add_patch(left)
    right = Rectangle((5.2, 1.2), 3.6, 7.6, facecolor='#ADD8E6', edgecolor='none')
    ax.add_patch(right)

    np.random.seed(42)
    x_solute = np.random.uniform(1.5, 4.5, 20)
    y_solute = np.random.uniform(1.5, 8.5, 20)
    ax.scatter(x_solute, y_solute, c='red', s=30)

    ax.annotate('', xy=(2.5, 9.5), xytext=(2.5, 11),
               arrowprops=dict(arrowstyle='->', color='black', lw=3))
    ax.text(2.5, 11.3, 'Pressure > π', ha='center', fontsize=11)

    for y in [3, 5, 7]:
        ax.annotate('', xy=(4.7, y), xytext=(5.3, y),
                   arrowprops=dict(arrowstyle='->', color='blue', lw=2))

    ax.text(3, 0.3, 'Sea Water', ha='center', fontsize=11)
    ax.text(7, 0.3, 'Pure Water', ha='center', fontsize=11)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def create_deviation_graphs(output_path: Path):
    """Create positive and negative deviation from Raoult's law graphs."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    x = np.linspace(0, 1, 100)
    p1_0, p2_0 = 100, 200
    p_ideal = p1_0 * (1 - x) + p2_0 * x

    for idx, ax in enumerate(axes):
        ax.plot(x, p_ideal, 'k--', linewidth=1.5, label='Ideal (Raoult\'s law)')
        if idx == 0:
            deviation = 30 * np.sin(np.pi * x)
            p_real = p_ideal + deviation
            ax.set_title('(a) Positive deviation', fontsize=12)
            color = 'red'
        else:
            deviation = -25 * np.sin(np.pi * x)
            p_real = p_ideal + deviation
            ax.set_title('(b) Negative deviation', fontsize=12)
            color = 'blue'

        ax.plot(x, p_real, color=color, linewidth=2, label='Real solution')
        ax.fill_between(x, p_ideal, p_real, alpha=0.3, color=color)
        ax.set_xlabel('Mole fraction', fontsize=11)
        ax.set_ylabel('Vapour pressure', fontsize=11)
        ax.legend()
        ax.set_xlim(0, 1)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


# Chemistry diagram mapping
CHEMISTRY_DIAGRAMS = {
    "beaker": create_beaker_diagram,
    "linear_graph": lambda p: create_graph(p, "linear"),
    "vapour_pressure_graph": lambda p: create_graph(p, "vapour_pressure"),
    "boiling_point": create_boiling_point_diagram,
    "osmosis": create_osmosis_diagram,
    "reverse_osmosis": create_reverse_osmosis_diagram,
    "deviation": create_deviation_graphs,
}


def identify_chemistry_diagram(caption: str, figure_num: str) -> str:
    """Identify chemistry diagram type from caption."""
    caption_lower = caption.lower()

    if "pressure" in caption_lower and "solubility" in caption_lower:
        return "beaker"
    elif "henry" in caption_lower or "hcl" in caption_lower:
        return "linear_graph"
    elif "vapour pressure" in caption_lower and "mole fraction" in caption_lower:
        return "vapour_pressure_graph"
    elif "boiling point" in caption_lower or "elevation" in caption_lower:
        return "boiling_point"
    elif "osmosis" in caption_lower and "reverse" not in caption_lower:
        return "osmosis"
    elif "reverse osmosis" in caption_lower:
        return "reverse_osmosis"
    elif "deviation" in caption_lower or "positive" in caption_lower or "negative" in caption_lower:
        return "deviation"

    # Default mapping for Solutions chapter
    fig_mapping = {
        "1.1": "beaker", "1.2": "linear_graph", "1.3": "vapour_pressure_graph",
        "1.4": "osmosis", "1.5": "vapour_pressure_graph", "1.6": "deviation",
        "1.7": "boiling_point", "1.8": "boiling_point", "1.9": "osmosis",
        "1.10": "osmosis", "1.11": "reverse_osmosis",
    }
    return fig_mapping.get(figure_num, None)


# ================== UNIFIED DIAGRAM FUNCTIONS ==================

def get_diagram_creators(subject: str) -> dict:
    """Get diagram creators for a subject."""
    creators = {
        "chemistry": CHEMISTRY_DIAGRAMS,
        "physics": PHYSICS_DIAGRAMS,
        "biology": BIOLOGY_DIAGRAMS,
        "maths": MATHS_DIAGRAMS,
    }
    return creators.get(subject, {})


def identify_diagram(caption: str, figure_num: str, subject: str) -> str:
    """Identify diagram type for any subject."""
    identifiers = {
        "chemistry": identify_chemistry_diagram,
        "physics": identify_physics_diagram,
        "biology": identify_biology_diagram,
        "maths": identify_maths_diagram,
    }
    identifier = identifiers.get(subject)
    if identifier:
        return identifier(caption, figure_num)
    return None


def recreate_diagrams(book_code: str):
    """Recreate all diagrams for a book (any subject)."""
    base_dir = Path("extracted") / book_code
    figures_json = base_dir / "figures.json"
    output_dir = base_dir / "diagrams"
    output_dir.mkdir(exist_ok=True)

    if not figures_json.exists():
        print(f"No figures.json found for {book_code}")
        return []

    # Detect subject from book code
    subject_info = detect_subject(book_code)
    subject = subject_info["subject"]
    print(f"Detected subject: {subject.upper()} (Class {subject_info['class']})")

    # Get appropriate diagram creators
    diagram_creators = get_diagram_creators(subject)

    if not diagram_creators:
        print(f"No diagram creators available for subject: {subject}")
        return []

    figures = json.loads(figures_json.read_text())

    # Deduplicate
    seen = set()
    unique_figures = []
    for fig in figures:
        if fig["figure"] not in seen:
            seen.add(fig["figure"])
            unique_figures.append(fig)

    created = []
    for fig in unique_figures:
        fig_num = fig["figure"]
        caption = fig.get("caption", "")

        diagram_type = identify_diagram(caption, fig_num, subject)

        if diagram_type and diagram_type in diagram_creators:
            output_path = output_dir / f"fig{fig_num.replace('.', '_')}_clean.png"

            try:
                diagram_creators[diagram_type](output_path)
                print(f"  Created: {output_path.name} ({diagram_type})")
                created.append({
                    "figure": fig_num,
                    "type": diagram_type,
                    "original": fig.get("image"),
                    "recreated": output_path.name,
                    "caption": caption[:100]
                })
            except Exception as e:
                print(f"  Error creating {fig_num}: {e}")
        else:
            print(f"  Skipped: Fig {fig_num} (unknown type: {diagram_type})")

    # Save manifest
    manifest = output_dir / "manifest.json"
    manifest.write_text(json.dumps(created, indent=2, ensure_ascii=False))

    print(f"\nRecreated {len(created)} diagrams in {output_dir}/")
    return created


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python recreate_diagram.py <book_code>")
        print("Examples:")
        print("  python recreate_diagram.py lech101  (Chemistry Class 11)")
        print("  python recreate_diagram.py leph201  (Physics Class 12)")
        print("  python recreate_diagram.py lebo102  (Biology Class 11)")
        print("  python recreate_diagram.py lemh203  (Maths Class 12)")
        sys.exit(1)

    book_code = sys.argv[1]
    recreate_diagrams(book_code)
