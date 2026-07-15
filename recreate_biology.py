#!/usr/bin/env python3
"""
Biology Diagram Recreator - Creates clean biology diagrams.
Covers: Cell structures, Organ systems, Plant anatomy, DNA/RNA, Lifecycles, etc.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle, Ellipse, Rectangle, Polygon, FancyArrowPatch
import numpy as np
from pathlib import Path


def create_animal_cell(output_path: Path):
    """Create diagram of animal cell."""
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_xlim(-6, 6)
    ax.set_ylim(-6, 6)
    ax.set_aspect('equal')
    ax.axis('off')

    # Cell membrane (outer)
    cell = Ellipse((0, 0), 10, 8, facecolor='#ffe4c4', edgecolor='brown', linewidth=2)
    ax.add_patch(cell)

    # Nucleus
    nucleus = Ellipse((0, 0), 3, 2.5, facecolor='#add8e6', edgecolor='darkblue', linewidth=2)
    ax.add_patch(nucleus)
    ax.text(0, 0, 'Nucleus', fontsize=10, ha='center', va='center')

    # Nucleolus
    nucleolus = Circle((0.5, 0.3), 0.4, facecolor='#4169e1', edgecolor='darkblue')
    ax.add_patch(nucleolus)
    ax.text(0.5, 0.3, 'N', fontsize=8, ha='center', va='center', color='white')

    # Mitochondria
    for pos in [(-3, 2), (-2.5, -2), (3, 1.5)]:
        mito = Ellipse(pos, 1.2, 0.6, angle=30, facecolor='#ff6347', edgecolor='darkred', linewidth=1.5)
        ax.add_patch(mito)
        # Inner folds
        ax.plot([pos[0] - 0.3, pos[0] - 0.3], [pos[1] - 0.15, pos[1] + 0.15], 'darkred', linewidth=1)
        ax.plot([pos[0], pos[0]], [pos[1] - 0.2, pos[1] + 0.2], 'darkred', linewidth=1)
        ax.plot([pos[0] + 0.3, pos[0] + 0.3], [pos[1] - 0.15, pos[1] + 0.15], 'darkred', linewidth=1)
    ax.text(-3, 2.7, 'Mitochondrion', fontsize=9, ha='center')

    # Rough ER (with ribosomes)
    for y in [1.8, 2.2, 2.6]:
        ax.plot([1.5, 3.5], [y, y], 'purple', linewidth=2)
        for x in np.arange(1.6, 3.5, 0.3):
            ax.plot(x, y, 'ko', markersize=3)
    ax.text(2.5, 3.1, 'Rough ER', fontsize=9, ha='center')

    # Smooth ER
    for y in [-1.8, -2.2, -2.6]:
        ax.plot([1.5, 3.5], [y, y], 'purple', linewidth=2)
    ax.text(2.5, -3.1, 'Smooth ER', fontsize=9, ha='center')

    # Golgi apparatus
    for i, r in enumerate([1.5, 1.3, 1.1, 0.9]):
        arc = patches.Arc((-3, -0.5), r * 2, 0.6, angle=0, theta1=30, theta2=150,
                         color='goldenrod', linewidth=2)
        ax.add_patch(arc)
    ax.text(-3, -1.5, 'Golgi Body', fontsize=9, ha='center')

    # Lysosomes
    for pos in [(-1.5, 3), (2, -0.5)]:
        lyso = Circle(pos, 0.3, facecolor='#32cd32', edgecolor='darkgreen')
        ax.add_patch(lyso)
    ax.text(-1.5, 3.5, 'Lysosome', fontsize=9, ha='center')

    # Ribosomes
    for pos in [(0, 3), (1, 2.8), (-0.5, 2.5)]:
        ax.plot(pos[0], pos[1], 'ko', markersize=5)
    ax.text(0, 3.5, 'Ribosomes', fontsize=9, ha='center')

    # Centrosome
    ax.plot([3.5], [-1.5], 'k+', markersize=15, markeredgewidth=2)
    ax.text(3.5, -2, 'Centrosome', fontsize=9, ha='center')

    # Cell membrane label
    ax.annotate('Cell Membrane', xy=(4.5, 2), xytext=(5.5, 3),
               arrowprops=dict(arrowstyle='->', color='black'),
               fontsize=10)

    ax.set_title('Animal Cell', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def create_plant_cell(output_path: Path):
    """Create diagram of plant cell."""
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_xlim(-6, 6)
    ax.set_ylim(-6, 6)
    ax.set_aspect('equal')
    ax.axis('off')

    # Cell wall (outer rectangle)
    wall = Rectangle((-5, -4), 10, 8, facecolor='none', edgecolor='saddlebrown',
                    linewidth=4, linestyle='-')
    ax.add_patch(wall)
    ax.text(5.5, 3, 'Cell Wall', fontsize=9, ha='left')

    # Cell membrane
    membrane = Rectangle((-4.8, -3.8), 9.6, 7.6, facecolor='#ffe4c4', edgecolor='brown', linewidth=2)
    ax.add_patch(membrane)

    # Central vacuole (large)
    vacuole = Ellipse((0, 0), 6, 4, facecolor='#e6e6fa', edgecolor='purple', linewidth=2)
    ax.add_patch(vacuole)
    ax.text(0, 0, 'Central Vacuole', fontsize=10, ha='center', va='center')

    # Nucleus (pushed to edge)
    nucleus = Ellipse((-3, 2.5), 2, 1.5, facecolor='#add8e6', edgecolor='darkblue', linewidth=2)
    ax.add_patch(nucleus)
    ax.text(-3, 2.5, 'Nucleus', fontsize=9, ha='center', va='center')

    # Chloroplasts
    for pos in [(3, 2.5), (3.5, 1.5), (2.5, -2.5)]:
        chloro = Ellipse(pos, 1.2, 0.6, facecolor='#228b22', edgecolor='darkgreen', linewidth=1.5)
        ax.add_patch(chloro)
        # Grana
        for dx in [-0.3, 0, 0.3]:
            ax.plot([pos[0] + dx], [pos[1]], 'lime', marker='_', markersize=8)
    ax.text(3.5, 3.1, 'Chloroplast', fontsize=9, ha='center')

    # Mitochondria
    for pos in [(-3.5, -2.5), (3.5, -1.5)]:
        mito = Ellipse(pos, 0.8, 0.4, facecolor='#ff6347', edgecolor='darkred')
        ax.add_patch(mito)
    ax.text(-3.5, -3, 'Mitochondrion', fontsize=9, ha='center')

    ax.set_title('Plant Cell', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def create_dna_structure(output_path: Path):
    """Create DNA double helix diagram."""
    fig, ax = plt.subplots(figsize=(8, 12))
    ax.set_xlim(-4, 4)
    ax.set_ylim(0, 12)
    ax.axis('off')

    # Double helix
    t = np.linspace(0, 4 * np.pi, 200)
    x1 = np.sin(t)
    x2 = np.sin(t + np.pi)
    y = t / (4 * np.pi) * 10 + 1

    # Sugar-phosphate backbone
    ax.plot(x1, y, 'b-', linewidth=3, label='Sugar-phosphate backbone')
    ax.plot(x2, y, 'b-', linewidth=3)

    # Base pairs (rungs)
    base_colors = {'A-T': '#ff6b6b', 'T-A': '#ff6b6b', 'G-C': '#4ecdc4', 'C-G': '#4ecdc4'}
    bases = ['A-T', 'G-C', 'T-A', 'C-G', 'A-T', 'G-C', 'G-C', 'T-A']

    for i, (t_val, base) in enumerate(zip(np.linspace(0.5, 3.5 * np.pi, 8), bases * 2)):
        y_pos = t_val / (4 * np.pi) * 10 + 1
        x_left = np.sin(t_val)
        x_right = np.sin(t_val + np.pi)

        if abs(x_left - x_right) > 0.3:  # Only draw if visible
            ax.plot([x_left, x_right], [y_pos, y_pos],
                   color=base_colors.get(base[:3], 'gray'), linewidth=2)
            ax.text(0, y_pos, base[:3], fontsize=8, ha='center', va='center',
                   bbox=dict(boxstyle='round', facecolor='white', edgecolor='none', alpha=0.7))

    # Labels
    ax.text(-2.5, 11, 'Sugar-Phosphate\nBackbone', fontsize=10, ha='center', color='blue')
    ax.text(2.5, 6, 'Base Pairs:\nA-T (Adenine-Thymine)\nG-C (Guanine-Cytosine)', fontsize=9, ha='left')

    ax.set_title('DNA Double Helix Structure', fontsize=14, fontweight='bold')

    # Legend
    legend_elements = [
        patches.Patch(facecolor='#ff6b6b', label='A-T pair'),
        patches.Patch(facecolor='#4ecdc4', label='G-C pair'),
    ]
    ax.legend(handles=legend_elements, loc='lower right')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def create_heart_diagram(output_path: Path):
    """Create simplified heart diagram showing chambers and blood flow."""
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_xlim(-6, 6)
    ax.set_ylim(-6, 6)
    ax.set_aspect('equal')
    ax.axis('off')

    # Heart outline (simplified)
    heart_x = [-3, -3.5, -3, -1, 0, 1, 3, 3.5, 3, 0]
    heart_y = [3, 0, -3, -5, -5.5, -5, -3, 0, 3, 4]
    ax.fill(heart_x, heart_y, facecolor='#ffb6c1', edgecolor='red', linewidth=3)

    # Septum (middle wall)
    ax.plot([0, 0], [3, -4], 'red', linewidth=3)

    # Chambers
    # Right Atrium
    ax.add_patch(Rectangle((-2.5, 0.5), 2, 2, facecolor='#4169e1', edgecolor='blue', linewidth=2))
    ax.text(-1.5, 1.5, 'Right\nAtrium', fontsize=9, ha='center', va='center', color='white')

    # Left Atrium
    ax.add_patch(Rectangle((0.5, 0.5), 2, 2, facecolor='#dc143c', edgecolor='darkred', linewidth=2))
    ax.text(1.5, 1.5, 'Left\nAtrium', fontsize=9, ha='center', va='center', color='white')

    # Right Ventricle
    ax.add_patch(Rectangle((-2.5, -3), 2, 3, facecolor='#6495ed', edgecolor='blue', linewidth=2))
    ax.text(-1.5, -1.5, 'Right\nVentricle', fontsize=9, ha='center', va='center', color='white')

    # Left Ventricle
    ax.add_patch(Rectangle((0.5, -3), 2, 3, facecolor='#ff4500', edgecolor='darkred', linewidth=2))
    ax.text(1.5, -1.5, 'Left\nVentricle', fontsize=9, ha='center', va='center', color='white')

    # Blood vessels
    # Pulmonary artery (to lungs)
    ax.annotate('', xy=(-3, 4), xytext=(-1.5, 2.5),
               arrowprops=dict(arrowstyle='->', color='blue', lw=2))
    ax.text(-3.5, 4.5, 'To Lungs\n(Pulmonary\nArtery)', fontsize=8, ha='center')

    # Pulmonary vein (from lungs)
    ax.annotate('', xy=(1.5, 2.5), xytext=(3, 4),
               arrowprops=dict(arrowstyle='->', color='red', lw=2))
    ax.text(3.5, 4.5, 'From Lungs\n(Pulmonary\nVein)', fontsize=8, ha='center')

    # Aorta (to body)
    ax.annotate('', xy=(3, 0), xytext=(1.5, -1.5),
               arrowprops=dict(arrowstyle='->', color='red', lw=2))
    ax.text(4, 0, 'To Body\n(Aorta)', fontsize=8, ha='center')

    # Vena cava (from body)
    ax.annotate('', xy=(-1.5, 1.5), xytext=(-4, 0),
               arrowprops=dict(arrowstyle='->', color='blue', lw=2))
    ax.text(-4.5, 0, 'From Body\n(Vena Cava)', fontsize=8, ha='center')

    ax.set_title('Human Heart Structure', fontsize=14, fontweight='bold')

    # Legend
    legend_elements = [
        patches.Patch(facecolor='blue', label='Deoxygenated blood'),
        patches.Patch(facecolor='red', label='Oxygenated blood'),
    ]
    ax.legend(handles=legend_elements, loc='lower right')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def create_photosynthesis_diagram(output_path: Path):
    """Create photosynthesis process diagram."""
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # Leaf shape
    leaf = Ellipse((6, 4), 8, 5, facecolor='#90ee90', edgecolor='darkgreen', linewidth=3)
    ax.add_patch(leaf)

    # Chloroplast
    chloro = Ellipse((6, 4), 3, 2, facecolor='#228b22', edgecolor='darkgreen', linewidth=2)
    ax.add_patch(chloro)
    ax.text(6, 4, 'Chloroplast', fontsize=10, ha='center', va='center', color='white')

    # Inputs
    # Sunlight
    ax.annotate('Sunlight', xy=(6, 6.5), xytext=(6, 7.5),
               fontsize=11, ha='center', color='orange', fontweight='bold')
    for angle in [-30, 0, 30]:
        ax.annotate('', xy=(6 + np.sin(np.radians(angle)), 6.5),
                   xytext=(6 + np.sin(np.radians(angle)) * 2, 7.5),
                   arrowprops=dict(arrowstyle='->', color='orange', lw=2))

    # CO2
    ax.annotate('$CO_2$', xy=(1.5, 4), xytext=(0, 4),
               fontsize=12, ha='center',
               arrowprops=dict(arrowstyle='->', color='gray', lw=2))

    # H2O
    ax.annotate('$H_2O$', xy=(6, 1), xytext=(6, 0),
               fontsize=12, ha='center',
               arrowprops=dict(arrowstyle='->', color='blue', lw=2))

    # Outputs
    # Glucose
    ax.annotate('$C_6H_{12}O_6$\n(Glucose)', xy=(10.5, 4), xytext=(11.5, 4),
               fontsize=11, ha='left',
               arrowprops=dict(arrowstyle='<-', color='brown', lw=2))

    # O2
    ax.annotate('$O_2$', xy=(9, 6), xytext=(10.5, 7),
               fontsize=12, ha='center',
               arrowprops=dict(arrowstyle='<-', color='green', lw=2))

    # Equation
    ax.text(6, -0.5, '$6CO_2 + 6H_2O + Light → C_6H_{12}O_6 + 6O_2$',
            fontsize=12, ha='center', style='italic')

    ax.set_title('Photosynthesis', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def create_mitosis_stages(output_path: Path):
    """Create diagram showing mitosis stages."""
    fig, axes = plt.subplots(1, 5, figsize=(15, 4))
    stages = ['Interphase', 'Prophase', 'Metaphase', 'Anaphase', 'Telophase']

    for ax, stage in zip(axes, stages):
        ax.set_xlim(-2, 2)
        ax.set_ylim(-2, 2)
        ax.set_aspect('equal')
        ax.axis('off')

        # Cell
        cell = Circle((0, 0), 1.5, facecolor='#ffe4c4', edgecolor='brown', linewidth=2)
        ax.add_patch(cell)

        if stage == 'Interphase':
            # Nucleus with diffuse chromatin
            nucleus = Circle((0, 0), 0.6, facecolor='#add8e6', edgecolor='darkblue', linewidth=2)
            ax.add_patch(nucleus)
            ax.text(0, 0, 'Chromatin', fontsize=7, ha='center', va='center')

        elif stage == 'Prophase':
            # Chromosomes condensing
            for pos in [(-0.2, 0.2), (0.2, -0.2), (0.1, 0.3), (-0.1, -0.3)]:
                ax.plot([pos[0] - 0.1, pos[0] + 0.1], [pos[1], pos[1]], 'darkblue', linewidth=3)

        elif stage == 'Metaphase':
            # Chromosomes at metaphase plate
            for y in [-0.15, 0, 0.15]:
                ax.plot([-0.2, 0.2], [y, y], 'darkblue', linewidth=4)
            # Spindle fibers
            ax.plot([-1, 0], [0, 0], 'gray', linewidth=0.5, linestyle='--')
            ax.plot([1, 0], [0, 0], 'gray', linewidth=0.5, linestyle='--')

        elif stage == 'Anaphase':
            # Chromosomes moving apart
            for y in [-0.15, 0, 0.15]:
                ax.plot([-0.6, -0.4], [y, y], 'darkblue', linewidth=3)
                ax.plot([0.4, 0.6], [y, y], 'darkblue', linewidth=3)
            # Arrows showing movement
            ax.annotate('', xy=(-0.8, 0), xytext=(-0.3, 0),
                       arrowprops=dict(arrowstyle='->', color='gray'))
            ax.annotate('', xy=(0.8, 0), xytext=(0.3, 0),
                       arrowprops=dict(arrowstyle='->', color='gray'))

        elif stage == 'Telophase':
            # Two nuclei forming, cell pinching
            nucleus1 = Circle((-0.5, 0), 0.4, facecolor='#add8e6', edgecolor='darkblue', linewidth=2)
            nucleus2 = Circle((0.5, 0), 0.4, facecolor='#add8e6', edgecolor='darkblue', linewidth=2)
            ax.add_patch(nucleus1)
            ax.add_patch(nucleus2)
            # Cleavage furrow
            ax.plot([0, 0], [-1.5, -0.5], 'brown', linewidth=2)
            ax.plot([0, 0], [0.5, 1.5], 'brown', linewidth=2)

        ax.set_title(stage, fontsize=11, fontweight='bold')

    plt.suptitle('Stages of Mitosis', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def create_pedigree_chart(output_path: Path):
    """Create a pedigree chart for genetics."""
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # Legend
    ax.add_patch(Rectangle((0.5, 7), 0.4, 0.4, facecolor='white', edgecolor='black'))
    ax.text(1.1, 7.2, '= Male (unaffected)', fontsize=9, va='center')

    ax.add_patch(Circle((0.7, 6.4), 0.2, facecolor='white', edgecolor='black'))
    ax.text(1.1, 6.4, '= Female (unaffected)', fontsize=9, va='center')

    ax.add_patch(Rectangle((3.5, 7), 0.4, 0.4, facecolor='black', edgecolor='black'))
    ax.text(4.1, 7.2, '= Male (affected)', fontsize=9, va='center')

    ax.add_patch(Circle((3.7, 6.4), 0.2, facecolor='black', edgecolor='black'))
    ax.text(4.1, 6.4, '= Female (affected)', fontsize=9, va='center')

    # Generation I
    ax.text(0.5, 5, 'I', fontsize=12, fontweight='bold')
    ax.add_patch(Rectangle((2.8, 4.8), 0.4, 0.4, facecolor='white', edgecolor='black', linewidth=2))
    ax.add_patch(Circle((4.2, 5), 0.2, facecolor='black', edgecolor='black', linewidth=2))
    ax.plot([3.2, 4], [5, 5], 'k-', linewidth=2)

    # Generation II
    ax.text(0.5, 3, 'II', fontsize=12, fontweight='bold')
    # Vertical line down
    ax.plot([3.6, 3.6], [4.8, 4], 'k-', linewidth=2)
    # Horizontal line for children
    ax.plot([2, 5.5], [4, 4], 'k-', linewidth=2)
    # Children
    positions_II = [(2, 3), (3.5, 3), (5, 3)]
    fills = ['white', 'black', 'white']
    shapes = ['circle', 'rect', 'circle']

    for (x, y), fill, shape in zip(positions_II, fills, shapes):
        ax.plot([x, x], [4, y + 0.3], 'k-', linewidth=2)
        if shape == 'rect':
            ax.add_patch(Rectangle((x - 0.2, y - 0.2), 0.4, 0.4, facecolor=fill, edgecolor='black', linewidth=2))
        else:
            ax.add_patch(Circle((x, y), 0.2, facecolor=fill, edgecolor='black', linewidth=2))

    # Generation III (children of affected male in Gen II)
    ax.text(0.5, 1, 'III', fontsize=12, fontweight='bold')
    # Marriage line for Gen II male
    ax.add_patch(Circle((4.5, 3), 0.2, facecolor='white', edgecolor='black', linewidth=2))
    ax.plot([3.7, 4.3], [3, 3], 'k-', linewidth=2)
    # Children
    ax.plot([4, 4], [2.8, 2], 'k-', linewidth=2)
    ax.plot([3, 5], [2, 2], 'k-', linewidth=2)
    for x, fill in [(3, 'white'), (4, 'black'), (5, 'white')]:
        ax.plot([x, x], [2, 1.3], 'k-', linewidth=2)
        ax.add_patch(Circle((x, 1), 0.2, facecolor=fill, edgecolor='black', linewidth=2))

    ax.set_title('Pedigree Chart (Autosomal Dominant)', fontsize=12, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


# Biology diagram type mapping
BIOLOGY_DIAGRAMS = {
    "animal_cell": create_animal_cell,
    "plant_cell": create_plant_cell,
    "dna": create_dna_structure,
    "heart": create_heart_diagram,
    "photosynthesis": create_photosynthesis_diagram,
    "mitosis": create_mitosis_stages,
    "pedigree": create_pedigree_chart,
}


def identify_biology_diagram(caption: str, figure_num: str) -> str:
    """Identify biology diagram type from caption."""
    caption_lower = caption.lower()

    if any(w in caption_lower for w in ["animal cell", "cell structure", "cell organelle"]):
        return "animal_cell"
    elif any(w in caption_lower for w in ["plant cell", "cell wall", "chloroplast"]):
        return "plant_cell"
    elif any(w in caption_lower for w in ["dna", "double helix", "nucleotide"]):
        return "dna"
    elif any(w in caption_lower for w in ["heart", "cardiac", "ventricle", "atrium"]):
        return "heart"
    elif any(w in caption_lower for w in ["photosynthesis", "chlorophyll", "light reaction"]):
        return "photosynthesis"
    elif any(w in caption_lower for w in ["mitosis", "cell division", "metaphase", "anaphase"]):
        return "mitosis"
    elif any(w in caption_lower for w in ["pedigree", "inheritance", "genetic"]):
        return "pedigree"

    return None
