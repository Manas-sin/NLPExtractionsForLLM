#!/usr/bin/env python3
"""
Physics Diagram Recreator - Creates clean physics diagrams.
Covers: Circuits, Ray diagrams, Force vectors, Waves, Field lines, etc.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, FancyArrowPatch, Arc
import numpy as np
from pathlib import Path


def create_circuit_simple(output_path: Path, params: dict = None):
    """Create a simple circuit with battery and resistor."""
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.set_aspect('equal')
    ax.axis('off')

    # Battery
    ax.plot([2, 2], [5, 5.3], 'k-', linewidth=2)
    ax.plot([1.7, 2.3], [5.3, 5.3], 'k-', linewidth=3)
    ax.plot([1.85, 2.15], [5.5, 5.5], 'k-', linewidth=1)
    ax.text(2, 4.5, '+', fontsize=12, ha='center')
    ax.text(2, 5.8, '−', fontsize=12, ha='center')

    # Wires
    ax.plot([2, 2, 8, 8], [5.5, 7, 7, 5.5], 'k-', linewidth=2)
    ax.plot([2, 2, 8, 8], [5, 3, 3, 5], 'k-', linewidth=2)

    # Resistor (zigzag)
    x_res = np.linspace(7, 9, 9)
    y_res = [5.5, 6, 5, 6, 5, 6, 5, 6, 5.5]
    ax.plot(x_res, y_res, 'k-', linewidth=2)
    ax.text(8, 6.5, 'R', fontsize=14, ha='center')

    # Current arrow
    ax.annotate('', xy=(5, 7.2), xytext=(3, 7.2),
               arrowprops=dict(arrowstyle='->', color='blue', lw=2))
    ax.text(4, 7.5, 'I', fontsize=12, ha='center', color='blue')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def create_ray_diagram_lens(output_path: Path, lens_type: str = "convex"):
    """Create ray diagram for convex/concave lens."""
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_xlim(-8, 8)
    ax.set_ylim(-4, 4)
    ax.set_aspect('equal')
    ax.axis('off')

    # Principal axis
    ax.axhline(y=0, color='black', linewidth=1)

    # Lens
    if lens_type == "convex":
        lens = Arc((0, 0), 1, 6, angle=0, theta1=90, theta2=270, color='blue', linewidth=2)
        ax.add_patch(lens)
        lens2 = Arc((0, 0), 1, 6, angle=0, theta1=-90, theta2=90, color='blue', linewidth=2)
        ax.add_patch(lens2)
        f = 3  # Focal length
    else:
        # Concave lens representation
        ax.plot([0, 0], [-3, 3], 'b-', linewidth=2)
        f = -3

    # Focus points
    ax.plot([f, f], [-0.1, 0.1], 'k-', linewidth=2)
    ax.plot([-f, -f], [-0.1, 0.1], 'k-', linewidth=2)
    ax.text(f, -0.5, 'F', fontsize=10, ha='center')
    ax.text(-f, -0.5, 'F', fontsize=10, ha='center')

    # Object (arrow)
    obj_x = -5
    obj_h = 2
    ax.annotate('', xy=(obj_x, obj_h), xytext=(obj_x, 0),
               arrowprops=dict(arrowstyle='->', color='red', lw=2))
    ax.text(obj_x, obj_h + 0.3, 'Object', fontsize=10, ha='center')

    # Rays
    # Ray 1: Parallel to axis, through focus
    ax.plot([obj_x, 0], [obj_h, obj_h], 'g-', linewidth=1.5)
    ax.plot([0, 6], [obj_h, 0], 'g-', linewidth=1.5)

    # Ray 2: Through center
    ax.plot([obj_x, 6], [obj_h, -obj_h * 6 / 5], 'g-', linewidth=1.5)

    # Ray 3: Through focus, parallel after lens
    ax.plot([obj_x, 0], [obj_h, obj_h - (obj_h * (obj_x + f) / obj_x)], 'g-', linewidth=1.5)

    # Labels
    ax.text(0, 3.5, 'Convex Lens' if lens_type == "convex" else 'Concave Lens',
            fontsize=12, ha='center')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def create_force_diagram(output_path: Path, diagram_type: str = "inclined"):
    """Create force/free body diagram."""
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(-2, 8)
    ax.set_ylim(-2, 8)
    ax.set_aspect('equal')
    ax.axis('off')

    if diagram_type == "inclined":
        # Inclined plane
        ax.fill([0, 6, 6], [0, 0, 4], color='lightgray', edgecolor='black')

        # Block
        block_x, block_y = 3, 2
        block = Rectangle((block_x - 0.5, block_y - 0.3), 1, 0.6,
                          angle=33.7, facecolor='lightblue', edgecolor='black')
        ax.add_patch(block)

        # Weight (mg)
        ax.annotate('', xy=(block_x, block_y - 1.5), xytext=(block_x, block_y),
                   arrowprops=dict(arrowstyle='->', color='red', lw=2))
        ax.text(block_x + 0.3, block_y - 1, 'mg', fontsize=12, color='red')

        # Normal force (N)
        ax.annotate('', xy=(block_x - 0.8, block_y + 1.2), xytext=(block_x, block_y),
                   arrowprops=dict(arrowstyle='->', color='blue', lw=2))
        ax.text(block_x - 1.2, block_y + 0.8, 'N', fontsize=12, color='blue')

        # Friction (f)
        ax.annotate('', xy=(block_x - 1, block_y - 0.5), xytext=(block_x, block_y),
                   arrowprops=dict(arrowstyle='->', color='green', lw=2))
        ax.text(block_x - 1.2, block_y - 0.8, 'f', fontsize=12, color='green')

        # Angle
        angle_arc = Arc((6, 0), 2, 2, angle=0, theta1=90, theta2=123.7,
                        color='black', linewidth=1)
        ax.add_patch(angle_arc)
        ax.text(5, 0.8, 'θ', fontsize=12)

    else:  # Simple block
        # Block
        block = Rectangle((2, 2), 2, 1.5, facecolor='lightblue', edgecolor='black')
        ax.add_patch(block)

        center = (3, 2.75)

        # Weight
        ax.annotate('', xy=(3, 0.5), xytext=center,
                   arrowprops=dict(arrowstyle='->', color='red', lw=2))
        ax.text(3.3, 1.5, 'W = mg', fontsize=11, color='red')

        # Normal
        ax.annotate('', xy=(3, 5), xytext=center,
                   arrowprops=dict(arrowstyle='->', color='blue', lw=2))
        ax.text(3.3, 4.2, 'N', fontsize=11, color='blue')

        # Applied force
        ax.annotate('', xy=(5.5, 2.75), xytext=center,
                   arrowprops=dict(arrowstyle='->', color='green', lw=2))
        ax.text(4.8, 3.1, 'F', fontsize=11, color='green')

        # Ground
        ax.plot([0, 6], [2, 2], 'k-', linewidth=2)
        for i in range(12):
            ax.plot([i * 0.5, i * 0.5 + 0.3], [2, 1.7], 'k-', linewidth=1)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def create_wave_diagram(output_path: Path, wave_type: str = "transverse"):
    """Create wave diagram showing wavelength, amplitude."""
    fig, ax = plt.subplots(figsize=(12, 5))

    x = np.linspace(0, 4 * np.pi, 500)

    if wave_type == "transverse":
        y = np.sin(x)
        ax.plot(x, y, 'b-', linewidth=2)
        ax.axhline(y=0, color='gray', linewidth=0.5, linestyle='--')

        # Wavelength
        ax.annotate('', xy=(2 * np.pi, -1.3), xytext=(0, -1.3),
                   arrowprops=dict(arrowstyle='<->', color='red', lw=1.5))
        ax.text(np.pi, -1.5, 'λ (wavelength)', fontsize=11, ha='center', color='red')

        # Amplitude
        ax.annotate('', xy=(np.pi / 2, 1), xytext=(np.pi / 2, 0),
                   arrowprops=dict(arrowstyle='<->', color='green', lw=1.5))
        ax.text(np.pi / 2 + 0.3, 0.5, 'A', fontsize=11, color='green')

        ax.set_ylabel('Displacement', fontsize=11)
        ax.set_title('Transverse Wave', fontsize=12)

    else:  # Longitudinal
        # Compression and rarefaction representation
        for i in range(20):
            spacing = 0.3 + 0.2 * np.sin(i * 0.5)
            ax.axvline(x=i * 0.5, ymin=0.3, ymax=0.7, color='blue',
                      linewidth=2, alpha=0.7)

        ax.text(2.5, 0.8, 'Compression', fontsize=10, ha='center')
        ax.text(7.5, 0.8, 'Rarefaction', fontsize=10, ha='center')
        ax.set_title('Longitudinal Wave', fontsize=12)
        ax.set_ylim(0, 1)

    ax.set_xlabel('Distance', fontsize=11)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def create_electric_field(output_path: Path, field_type: str = "point_charge"):
    """Create electric field line diagrams."""
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(-5, 5)
    ax.set_ylim(-5, 5)
    ax.set_aspect('equal')
    ax.axis('off')

    if field_type == "point_charge":
        # Positive charge at center
        circle = Circle((0, 0), 0.3, facecolor='red', edgecolor='black')
        ax.add_patch(circle)
        ax.text(0, 0, '+', fontsize=16, ha='center', va='center', color='white')

        # Field lines radiating outward
        for angle in np.linspace(0, 2 * np.pi, 12, endpoint=False):
            x_end = 4 * np.cos(angle)
            y_end = 4 * np.sin(angle)
            ax.annotate('', xy=(x_end, y_end), xytext=(0.4 * np.cos(angle), 0.4 * np.sin(angle)),
                       arrowprops=dict(arrowstyle='->', color='blue', lw=1.5))

        ax.set_title('Electric Field: Positive Point Charge', fontsize=12)

    elif field_type == "dipole":
        # Positive charge
        circle_pos = Circle((-2, 0), 0.3, facecolor='red', edgecolor='black')
        ax.add_patch(circle_pos)
        ax.text(-2, 0, '+', fontsize=14, ha='center', va='center', color='white')

        # Negative charge
        circle_neg = Circle((2, 0), 0.3, facecolor='blue', edgecolor='black')
        ax.add_patch(circle_neg)
        ax.text(2, 0, '−', fontsize=14, ha='center', va='center', color='white')

        # Field lines (curved)
        for y_offset in [-2, -1, 0, 1, 2]:
            t = np.linspace(-1.7, 1.7, 50)
            y = y_offset * np.cosh(t) / np.cosh(1.7) * 0.5
            x = t * 1.2
            ax.plot(x, y + y_offset * 0.3, 'b-', linewidth=1)

        ax.set_title('Electric Field: Dipole', fontsize=12)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def create_projectile_motion(output_path: Path):
    """Create projectile motion diagram."""
    fig, ax = plt.subplots(figsize=(10, 6))

    # Trajectory
    g = 10
    v0 = 20
    theta = np.radians(45)

    t = np.linspace(0, 2 * v0 * np.sin(theta) / g, 100)
    x = v0 * np.cos(theta) * t
    y = v0 * np.sin(theta) * t - 0.5 * g * t ** 2

    ax.plot(x, y, 'b-', linewidth=2, label='Trajectory')
    ax.fill_between(x, 0, y, alpha=0.1)

    # Initial velocity vector
    ax.annotate('', xy=(v0 * np.cos(theta) * 0.15, v0 * np.sin(theta) * 0.15),
               xytext=(0, 0),
               arrowprops=dict(arrowstyle='->', color='red', lw=2))
    ax.text(2, 3, '$v_0$', fontsize=12, color='red')

    # Components
    ax.annotate('', xy=(v0 * np.cos(theta) * 0.15, 0), xytext=(0, 0),
               arrowprops=dict(arrowstyle='->', color='green', lw=1.5))
    ax.text(1.5, -0.8, '$v_0 \\cos θ$', fontsize=10, color='green')

    # Angle
    angle_arc = Arc((0, 0), 3, 3, angle=0, theta1=0, theta2=45, color='black')
    ax.add_patch(angle_arc)
    ax.text(2, 0.5, 'θ', fontsize=12)

    # Labels
    ax.axhline(y=0, color='brown', linewidth=2)
    max_height = (v0 * np.sin(theta)) ** 2 / (2 * g)
    range_val = v0 ** 2 * np.sin(2 * theta) / g
    ax.axhline(y=max_height, color='gray', linestyle='--', linewidth=1)
    ax.text(range_val / 2, max_height + 0.5, f'H = {max_height:.1f} m', fontsize=10, ha='center')
    ax.text(range_val / 2, -1.5, f'R = {range_val:.1f} m', fontsize=10, ha='center')

    ax.set_xlabel('Horizontal Distance (m)', fontsize=11)
    ax.set_ylabel('Vertical Distance (m)', fontsize=11)
    ax.set_title('Projectile Motion', fontsize=12)
    ax.set_ylim(-2, max_height + 2)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


# Physics diagram type mapping
PHYSICS_DIAGRAMS = {
    "circuit": create_circuit_simple,
    "ray_convex": lambda p: create_ray_diagram_lens(p, "convex"),
    "ray_concave": lambda p: create_ray_diagram_lens(p, "concave"),
    "force_inclined": lambda p: create_force_diagram(p, "inclined"),
    "force_block": lambda p: create_force_diagram(p, "block"),
    "wave_transverse": lambda p: create_wave_diagram(p, "transverse"),
    "wave_longitudinal": lambda p: create_wave_diagram(p, "longitudinal"),
    "electric_field_point": lambda p: create_electric_field(p, "point_charge"),
    "electric_field_dipole": lambda p: create_electric_field(p, "dipole"),
    "projectile": create_projectile_motion,
}


def identify_physics_diagram(caption: str, figure_num: str) -> str:
    """Identify physics diagram type from caption."""
    caption_lower = caption.lower()

    if any(w in caption_lower for w in ["circuit", "resistor", "battery", "current"]):
        return "circuit"
    elif any(w in caption_lower for w in ["convex lens", "converging"]):
        return "ray_convex"
    elif any(w in caption_lower for w in ["concave lens", "diverging"]):
        return "ray_concave"
    elif any(w in caption_lower for w in ["inclined", "slope", "friction"]):
        return "force_inclined"
    elif any(w in caption_lower for w in ["force", "free body", "block"]):
        return "force_block"
    elif any(w in caption_lower for w in ["transverse wave", "wavelength", "amplitude"]):
        return "wave_transverse"
    elif any(w in caption_lower for w in ["longitudinal", "compression", "sound"]):
        return "wave_longitudinal"
    elif any(w in caption_lower for w in ["electric field", "point charge"]):
        return "electric_field_point"
    elif any(w in caption_lower for w in ["dipole", "two charges"]):
        return "electric_field_dipole"
    elif any(w in caption_lower for w in ["projectile", "trajectory", "parabola"]):
        return "projectile"

    return None
