#!/usr/bin/env python3
"""
Maths Diagram Recreator - Creates clean mathematics diagrams.
Covers: Coordinate geometry, Triangles, Circles, Conics, Vectors, 3D shapes, etc.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle, Ellipse, Rectangle, Polygon, FancyArrowPatch, Arc
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
from pathlib import Path


def create_coordinate_graph(output_path: Path, func_type: str = "parabola"):
    """Create coordinate graph with function."""
    fig, ax = plt.subplots(figsize=(10, 8))

    # Grid
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.axhline(y=0, color='k', linewidth=1.5)
    ax.axvline(x=0, color='k', linewidth=1.5)

    x = np.linspace(-5, 5, 500)

    if func_type == "parabola":
        y = x ** 2
        ax.plot(x, y, 'b-', linewidth=2, label='$y = x^2$')
        ax.set_ylim(-2, 25)
        ax.set_title('Parabola: $y = x^2$', fontsize=14)

        # Vertex
        ax.plot(0, 0, 'ro', markersize=8)
        ax.annotate('Vertex (0, 0)', xy=(0, 0), xytext=(1, 3),
                   arrowprops=dict(arrowstyle='->', color='red'))

    elif func_type == "sine":
        y = np.sin(x)
        ax.plot(x, y, 'b-', linewidth=2, label='$y = \\sin(x)$')
        ax.set_ylim(-1.5, 1.5)
        ax.set_title('Sine Function: $y = \\sin(x)$', fontsize=14)

        # Key points
        ax.plot([0, np.pi / 2, np.pi, 3 * np.pi / 2], [0, 1, 0, -1], 'ro', markersize=6)

    elif func_type == "exponential":
        y = np.exp(x / 2)
        ax.plot(x, y, 'b-', linewidth=2, label='$y = e^{x/2}$')
        ax.set_ylim(-2, 15)
        ax.set_title('Exponential: $y = e^{x/2}$', fontsize=14)

    elif func_type == "linear":
        y = 2 * x + 3
        ax.plot(x, y, 'b-', linewidth=2, label='$y = 2x + 3$')
        ax.set_ylim(-10, 15)
        ax.set_title('Linear: $y = 2x + 3$', fontsize=14)

        # Intercepts
        ax.plot(0, 3, 'ro', markersize=8)
        ax.plot(-1.5, 0, 'go', markersize=8)
        ax.annotate('y-intercept (0, 3)', xy=(0, 3), xytext=(1, 5),
                   arrowprops=dict(arrowstyle='->'))
        ax.annotate('x-intercept (-1.5, 0)', xy=(-1.5, 0), xytext=(-4, 2),
                   arrowprops=dict(arrowstyle='->'))

    ax.set_xlabel('x', fontsize=12)
    ax.set_ylabel('y', fontsize=12)
    ax.legend(fontsize=11)
    ax.set_xlim(-5, 5)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def create_triangle_diagram(output_path: Path, triangle_type: str = "general"):
    """Create triangle with labeled parts."""
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_aspect('equal')
    ax.axis('off')

    if triangle_type == "general":
        # General triangle with angle labels
        A = np.array([0, 0])
        B = np.array([6, 0])
        C = np.array([2, 4])

        triangle = Polygon([A, B, C], fill=False, edgecolor='blue', linewidth=2)
        ax.add_patch(triangle)

        # Vertices
        ax.plot(*A, 'ko', markersize=8)
        ax.plot(*B, 'ko', markersize=8)
        ax.plot(*C, 'ko', markersize=8)

        # Labels
        ax.text(A[0] - 0.3, A[1] - 0.3, 'A', fontsize=14, fontweight='bold')
        ax.text(B[0] + 0.2, B[1] - 0.3, 'B', fontsize=14, fontweight='bold')
        ax.text(C[0] - 0.1, C[1] + 0.3, 'C', fontsize=14, fontweight='bold')

        # Sides
        ax.text(3, -0.5, 'c', fontsize=12, ha='center', color='blue')
        ax.text(-0.2, 2, 'b', fontsize=12, ha='center', color='blue')
        ax.text(4.3, 2.2, 'a', fontsize=12, ha='center', color='blue')

        # Angle arcs
        angle_A = Arc(A, 1, 1, angle=0, theta1=0, theta2=63, color='red', linewidth=1.5)
        ax.add_patch(angle_A)
        ax.text(0.6, 0.3, 'α', fontsize=11, color='red')

        ax.set_xlim(-1, 7)
        ax.set_ylim(-1, 5)
        ax.set_title('Triangle ABC', fontsize=14, fontweight='bold')

    elif triangle_type == "right":
        A = np.array([0, 0])
        B = np.array([5, 0])
        C = np.array([0, 3])

        triangle = Polygon([A, B, C], fill=False, edgecolor='blue', linewidth=2)
        ax.add_patch(triangle)

        # Right angle marker
        right_angle = Rectangle((0, 0), 0.4, 0.4, fill=False, edgecolor='red', linewidth=1.5)
        ax.add_patch(right_angle)

        # Labels
        ax.text(-0.3, -0.3, 'A', fontsize=14, fontweight='bold')
        ax.text(5.2, -0.3, 'B', fontsize=14, fontweight='bold')
        ax.text(-0.3, 3.2, 'C', fontsize=14, fontweight='bold')

        # Sides with Pythagoras
        ax.text(2.5, -0.5, 'a (base)', fontsize=11, ha='center')
        ax.text(-0.6, 1.5, 'b\n(height)', fontsize=11, ha='center')
        ax.text(3, 1.8, 'c (hypotenuse)', fontsize=11, ha='center', rotation=-31)

        ax.text(2.5, 4, '$a^2 + b^2 = c^2$', fontsize=12, ha='center',
               bbox=dict(boxstyle='round', facecolor='lightyellow'))

        ax.set_xlim(-1, 6)
        ax.set_ylim(-1, 5)
        ax.set_title('Right-Angled Triangle', fontsize=14, fontweight='bold')

    elif triangle_type == "equilateral":
        h = np.sqrt(3) / 2 * 4
        A = np.array([0, 0])
        B = np.array([4, 0])
        C = np.array([2, h])

        triangle = Polygon([A, B, C], fill=False, edgecolor='blue', linewidth=2)
        ax.add_patch(triangle)

        # Equal marks on sides
        for start, end in [(A, B), (B, C), (C, A)]:
            mid = (start + end) / 2
            ax.plot(mid[0], mid[1], 'r|', markersize=10, markeredgewidth=2)

        # Labels
        ax.text(-0.3, -0.3, 'A', fontsize=14, fontweight='bold')
        ax.text(4.2, -0.3, 'B', fontsize=14, fontweight='bold')
        ax.text(1.9, h + 0.3, 'C', fontsize=14, fontweight='bold')

        ax.text(2, -0.5, 'a', fontsize=12, ha='center')
        ax.text(3.3, h / 2, 'a', fontsize=12, ha='center')
        ax.text(0.5, h / 2, 'a', fontsize=12, ha='center')

        ax.text(2, h + 1, 'All sides equal: AB = BC = CA', fontsize=11, ha='center')
        ax.text(2, h + 1.6, 'All angles = 60°', fontsize=11, ha='center')

        ax.set_xlim(-1, 5)
        ax.set_ylim(-1, h + 2.5)
        ax.set_title('Equilateral Triangle', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def create_circle_diagram(output_path: Path, show_type: str = "parts"):
    """Create circle with labeled parts."""
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_xlim(-6, 6)
    ax.set_ylim(-6, 6)
    ax.set_aspect('equal')
    ax.axis('off')

    # Circle
    circle = Circle((0, 0), 4, fill=False, edgecolor='blue', linewidth=2)
    ax.add_patch(circle)

    # Center
    ax.plot(0, 0, 'ko', markersize=6)
    ax.text(0.2, 0.2, 'O (center)', fontsize=10)

    if show_type == "parts":
        # Radius
        ax.plot([0, 4 * np.cos(np.pi / 4)], [0, 4 * np.sin(np.pi / 4)], 'r-', linewidth=2)
        ax.text(1.5, 2, 'r (radius)', fontsize=11, color='red', rotation=45)

        # Diameter
        ax.plot([-4, 4], [0, 0], 'g-', linewidth=2)
        ax.text(0, -0.5, 'd = 2r (diameter)', fontsize=11, color='green', ha='center')

        # Chord
        theta1, theta2 = np.pi / 3, 2 * np.pi / 3
        x1, y1 = 4 * np.cos(theta1), 4 * np.sin(theta1)
        x2, y2 = 4 * np.cos(theta2), 4 * np.sin(theta2)
        ax.plot([x1, x2], [y1, y2], 'm-', linewidth=2)
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.4, 'chord', fontsize=11, color='purple', ha='center')

        # Arc (highlighted)
        arc = Arc((0, 0), 8, 8, angle=0, theta1=60, theta2=120, color='orange', linewidth=3)
        ax.add_patch(arc)
        ax.text(-0.5, 4.5, 'arc', fontsize=11, color='orange')

        # Tangent
        ax.plot([4, 4], [-3, 3], 'c-', linewidth=2)
        ax.text(4.3, 1, 'tangent', fontsize=11, color='cyan', rotation=90)

        # Sector (shaded)
        sector = patches.Wedge((0, 0), 4, -60, -20, facecolor='lightyellow', edgecolor='orange', linewidth=2)
        ax.add_patch(sector)
        ax.text(3, -1.5, 'sector', fontsize=10, color='orange')

        ax.set_title('Parts of a Circle', fontsize=14, fontweight='bold')

    elif show_type == "angles":
        # Central angle
        ax.plot([0, 4], [0, 0], 'r-', linewidth=2)
        ax.plot([0, 4 * np.cos(np.pi / 3)], [0, 4 * np.sin(np.pi / 3)], 'r-', linewidth=2)
        central_arc = Arc((0, 0), 1.5, 1.5, angle=0, theta1=0, theta2=60, color='red', linewidth=2)
        ax.add_patch(central_arc)
        ax.text(1, 0.5, 'θ', fontsize=14, color='red')
        ax.text(3, -0.8, 'Central Angle', fontsize=10, color='red')

        # Inscribed angle
        P = np.array([4 * np.cos(4 * np.pi / 3), 4 * np.sin(4 * np.pi / 3)])
        A = np.array([4, 0])
        B = np.array([4 * np.cos(np.pi / 3), 4 * np.sin(np.pi / 3)])
        ax.plot([P[0], A[0]], [P[1], A[1]], 'g-', linewidth=2)
        ax.plot([P[0], B[0]], [P[1], B[1]], 'g-', linewidth=2)
        ax.text(-3, -3, 'θ/2', fontsize=12, color='green')
        ax.text(-3.5, -4, 'Inscribed Angle', fontsize=10, color='green')

        ax.text(0, 5, 'Inscribed angle = ½ × Central angle', fontsize=12, ha='center',
               bbox=dict(boxstyle='round', facecolor='lightyellow'))

        ax.set_title('Circle Angles', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def create_conic_section(output_path: Path, conic_type: str = "ellipse"):
    """Create conic section diagram."""
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_aspect('equal')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.axhline(y=0, color='k', linewidth=1)
    ax.axvline(x=0, color='k', linewidth=1)

    if conic_type == "ellipse":
        a, b = 4, 2.5  # Semi-major and semi-minor axes
        theta = np.linspace(0, 2 * np.pi, 100)
        x = a * np.cos(theta)
        y = b * np.sin(theta)
        ax.plot(x, y, 'b-', linewidth=2)

        # Foci
        c = np.sqrt(a ** 2 - b ** 2)
        ax.plot([-c, c], [0, 0], 'ro', markersize=8)
        ax.text(-c, -0.5, 'F₁', fontsize=11, ha='center', color='red')
        ax.text(c, -0.5, 'F₂', fontsize=11, ha='center', color='red')

        # Axes
        ax.plot([-a, a], [0, 0], 'g--', linewidth=1.5, label=f'Major axis = 2a = {2 * a}')
        ax.plot([0, 0], [-b, b], 'm--', linewidth=1.5, label=f'Minor axis = 2b = {2 * b}')

        ax.text(0, 3.5, f'$\\frac{{x^2}}{{{a ** 2}}} + \\frac{{y^2}}{{{b ** 2}}} = 1$', fontsize=14, ha='center')
        ax.set_title('Ellipse', fontsize=14, fontweight='bold')
        ax.set_xlim(-6, 6)
        ax.set_ylim(-4, 5)

    elif conic_type == "hyperbola":
        a, b = 2, 1.5
        x = np.linspace(-5, 5, 500)
        y_pos = b * np.sqrt(x ** 2 / a ** 2 - 1)
        y_neg = -y_pos

        # Only plot where valid
        mask = x ** 2 / a ** 2 >= 1
        ax.plot(x[mask], y_pos[mask], 'b-', linewidth=2)
        ax.plot(x[mask], y_neg[mask], 'b-', linewidth=2)

        # Asymptotes
        ax.plot([-5, 5], [-5 * b / a, 5 * b / a], 'r--', linewidth=1, label='Asymptotes')
        ax.plot([-5, 5], [5 * b / a, -5 * b / a], 'r--', linewidth=1)

        # Foci
        c = np.sqrt(a ** 2 + b ** 2)
        ax.plot([-c, c], [0, 0], 'go', markersize=8)
        ax.text(-c, -0.5, 'F₁', fontsize=11, ha='center', color='green')
        ax.text(c, -0.5, 'F₂', fontsize=11, ha='center', color='green')

        ax.text(0, 4, f'$\\frac{{x^2}}{{{a ** 2}}} - \\frac{{y^2}}{{{b ** 2}}} = 1$', fontsize=14, ha='center')
        ax.set_title('Hyperbola', fontsize=14, fontweight='bold')
        ax.set_xlim(-5, 5)
        ax.set_ylim(-4, 5)

    elif conic_type == "parabola":
        a = 1
        y = np.linspace(-4, 4, 100)
        x = y ** 2 / (4 * a)
        ax.plot(x, y, 'b-', linewidth=2)

        # Focus and directrix
        ax.plot(a, 0, 'ro', markersize=8)
        ax.text(a, 0.4, 'F (Focus)', fontsize=10, color='red', ha='center')

        ax.axvline(x=-a, color='green', linestyle='--', linewidth=1.5, label='Directrix')
        ax.text(-a - 0.3, 3, 'Directrix', fontsize=10, color='green', rotation=90)

        ax.text(3, 4, f'$y^2 = 4ax$', fontsize=14, ha='center')
        ax.set_title('Parabola', fontsize=14, fontweight='bold')
        ax.set_xlim(-3, 6)
        ax.set_ylim(-5, 5)

    ax.legend(loc='lower right')
    ax.set_xlabel('x', fontsize=12)
    ax.set_ylabel('y', fontsize=12)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def create_vector_diagram(output_path: Path, vector_type: str = "addition"):
    """Create vector diagram."""
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlim(-1, 8)
    ax.set_ylim(-1, 6)
    ax.set_aspect('equal')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.axhline(y=0, color='k', linewidth=0.5)
    ax.axvline(x=0, color='k', linewidth=0.5)

    if vector_type == "addition":
        # Vector A
        ax.annotate('', xy=(3, 2), xytext=(0, 0),
                   arrowprops=dict(arrowstyle='->', color='blue', lw=2))
        ax.text(1.5, 1.3, '$\\vec{A}$', fontsize=14, color='blue')

        # Vector B (starting from A's end)
        ax.annotate('', xy=(5, 5), xytext=(3, 2),
                   arrowprops=dict(arrowstyle='->', color='red', lw=2))
        ax.text(4.3, 3.3, '$\\vec{B}$', fontsize=14, color='red')

        # Resultant A + B
        ax.annotate('', xy=(5, 5), xytext=(0, 0),
                   arrowprops=dict(arrowstyle='->', color='green', lw=2))
        ax.text(2.2, 3, '$\\vec{A} + \\vec{B}$', fontsize=14, color='green')

        ax.set_title('Vector Addition (Triangle Law)', fontsize=14, fontweight='bold')

    elif vector_type == "components":
        # Original vector
        ax.annotate('', xy=(4, 3), xytext=(0, 0),
                   arrowprops=dict(arrowstyle='->', color='blue', lw=2))
        ax.text(2.3, 1.8, '$\\vec{A}$', fontsize=14, color='blue')

        # X-component
        ax.annotate('', xy=(4, 0), xytext=(0, 0),
                   arrowprops=dict(arrowstyle='->', color='red', lw=2))
        ax.text(2, -0.5, '$A_x = A\\cos\\theta$', fontsize=12, color='red')

        # Y-component
        ax.annotate('', xy=(4, 3), xytext=(4, 0),
                   arrowprops=dict(arrowstyle='->', color='green', lw=2))
        ax.text(4.3, 1.5, '$A_y = A\\sin\\theta$', fontsize=12, color='green')

        # Angle
        angle_arc = Arc((0, 0), 1.5, 1.5, angle=0, theta1=0, theta2=36.87, color='orange', linewidth=2)
        ax.add_patch(angle_arc)
        ax.text(1, 0.4, 'θ', fontsize=14, color='orange')

        # Dashed lines
        ax.plot([4, 4], [0, 3], 'k--', linewidth=1)

        ax.set_title('Vector Components', fontsize=14, fontweight='bold')

    elif vector_type == "cross_product":
        # Show right-hand rule
        ax.annotate('', xy=(3, 0), xytext=(0, 0),
                   arrowprops=dict(arrowstyle='->', color='blue', lw=3))
        ax.text(1.5, -0.5, '$\\vec{A}$', fontsize=14, color='blue')

        ax.annotate('', xy=(0, 3), xytext=(0, 0),
                   arrowprops=dict(arrowstyle='->', color='red', lw=3))
        ax.text(-0.5, 1.5, '$\\vec{B}$', fontsize=14, color='red')

        # Cross product (perpendicular, coming out of page - represented by circle)
        ax.plot(0, 0, 'go', markersize=15)
        ax.plot(0, 0, 'g.', markersize=8)
        ax.text(0.5, 0.5, '$\\vec{A} × \\vec{B}$', fontsize=14, color='green')

        ax.text(4, 4, 'Right-Hand Rule:\nCurl fingers from $\\vec{A}$ to $\\vec{B}$\nThumb points in direction of $\\vec{A} × \\vec{B}$',
               fontsize=10, ha='left', bbox=dict(boxstyle='round', facecolor='lightyellow'))

        ax.set_title('Cross Product (Right-Hand Rule)', fontsize=14, fontweight='bold')

    ax.set_xlabel('x', fontsize=12)
    ax.set_ylabel('y', fontsize=12)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def create_venn_diagram(output_path: Path, sets: int = 2):
    """Create Venn diagram."""
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlim(-4, 4)
    ax.set_ylim(-3, 3)
    ax.set_aspect('equal')
    ax.axis('off')

    if sets == 2:
        # Two overlapping circles
        circle_A = Circle((-1, 0), 2, facecolor='lightblue', edgecolor='blue', linewidth=2, alpha=0.5)
        circle_B = Circle((1, 0), 2, facecolor='lightgreen', edgecolor='green', linewidth=2, alpha=0.5)
        ax.add_patch(circle_A)
        ax.add_patch(circle_B)

        # Labels
        ax.text(-2, 0, 'A', fontsize=16, fontweight='bold', ha='center')
        ax.text(2, 0, 'B', fontsize=16, fontweight='bold', ha='center')
        ax.text(0, 0, 'A ∩ B', fontsize=12, ha='center')

        # Outside labels
        ax.text(-2.5, 2.2, 'A only', fontsize=10, ha='center')
        ax.text(2.5, 2.2, 'B only', fontsize=10, ha='center')

        ax.set_title('Venn Diagram: Two Sets', fontsize=14, fontweight='bold')

    elif sets == 3:
        # Three overlapping circles
        positions = [(-1, 0.5), (1, 0.5), (0, -1)]
        colors = [('lightblue', 'blue'), ('lightgreen', 'green'), ('lightyellow', 'orange')]
        labels = ['A', 'B', 'C']

        for pos, (fc, ec), label in zip(positions, colors, labels):
            circle = Circle(pos, 1.5, facecolor=fc, edgecolor=ec, linewidth=2, alpha=0.4)
            ax.add_patch(circle)
            ax.text(pos[0] + (pos[0] * 0.5), pos[1] + (pos[1] * 0.5), label,
                   fontsize=14, fontweight='bold', ha='center')

        # Center label
        ax.text(0, 0, 'A∩B∩C', fontsize=10, ha='center')

        ax.set_title('Venn Diagram: Three Sets', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def create_3d_shape(output_path: Path, shape_type: str = "cube"):
    """Create 3D shape diagram."""
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    if shape_type == "cube":
        vertices = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
                            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]])

        faces = [[vertices[j] for j in [0, 1, 2, 3]],
                [vertices[j] for j in [4, 5, 6, 7]],
                [vertices[j] for j in [0, 1, 5, 4]],
                [vertices[j] for j in [2, 3, 7, 6]],
                [vertices[j] for j in [0, 3, 7, 4]],
                [vertices[j] for j in [1, 2, 6, 5]]]

        ax.add_collection3d(Poly3DCollection(faces, facecolors='cyan', linewidths=1,
                                             edgecolors='blue', alpha=0.5))
        ax.set_title('Cube', fontsize=14, fontweight='bold')

    elif shape_type == "cylinder":
        z = np.linspace(0, 2, 50)
        theta = np.linspace(0, 2 * np.pi, 50)
        theta_grid, z_grid = np.meshgrid(theta, z)
        x_grid = np.cos(theta_grid)
        y_grid = np.sin(theta_grid)

        ax.plot_surface(x_grid, y_grid, z_grid, alpha=0.5, color='cyan', edgecolor='blue')
        ax.set_title('Cylinder', fontsize=14, fontweight='bold')

    elif shape_type == "cone":
        z = np.linspace(0, 2, 50)
        theta = np.linspace(0, 2 * np.pi, 50)
        theta_grid, z_grid = np.meshgrid(theta, z)
        r = (2 - z_grid)  # Radius decreases with height
        x_grid = r * np.cos(theta_grid)
        y_grid = r * np.sin(theta_grid)

        ax.plot_surface(x_grid, y_grid, z_grid, alpha=0.5, color='cyan', edgecolor='blue')
        ax.set_title('Cone', fontsize=14, fontweight='bold')

    elif shape_type == "sphere":
        u = np.linspace(0, 2 * np.pi, 50)
        v = np.linspace(0, np.pi, 50)
        x = np.outer(np.cos(u), np.sin(v))
        y = np.outer(np.sin(u), np.sin(v))
        z = np.outer(np.ones(np.size(u)), np.cos(v))

        ax.plot_surface(x, y, z, alpha=0.5, color='cyan', edgecolor='blue', linewidth=0.2)
        ax.set_title('Sphere', fontsize=14, fontweight='bold')

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


# Maths diagram type mapping
MATHS_DIAGRAMS = {
    "parabola": lambda p: create_coordinate_graph(p, "parabola"),
    "sine": lambda p: create_coordinate_graph(p, "sine"),
    "exponential": lambda p: create_coordinate_graph(p, "exponential"),
    "linear": lambda p: create_coordinate_graph(p, "linear"),
    "triangle": lambda p: create_triangle_diagram(p, "general"),
    "right_triangle": lambda p: create_triangle_diagram(p, "right"),
    "equilateral": lambda p: create_triangle_diagram(p, "equilateral"),
    "circle_parts": lambda p: create_circle_diagram(p, "parts"),
    "circle_angles": lambda p: create_circle_diagram(p, "angles"),
    "ellipse": lambda p: create_conic_section(p, "ellipse"),
    "hyperbola": lambda p: create_conic_section(p, "hyperbola"),
    "conic_parabola": lambda p: create_conic_section(p, "parabola"),
    "vector_addition": lambda p: create_vector_diagram(p, "addition"),
    "vector_components": lambda p: create_vector_diagram(p, "components"),
    "cross_product": lambda p: create_vector_diagram(p, "cross_product"),
    "venn_2": lambda p: create_venn_diagram(p, 2),
    "venn_3": lambda p: create_venn_diagram(p, 3),
    "cube": lambda p: create_3d_shape(p, "cube"),
    "cylinder": lambda p: create_3d_shape(p, "cylinder"),
    "cone": lambda p: create_3d_shape(p, "cone"),
    "sphere": lambda p: create_3d_shape(p, "sphere"),
}


def identify_maths_diagram(caption: str, figure_num: str) -> str:
    """Identify maths diagram type from caption."""
    caption_lower = caption.lower()

    # Graphs
    if any(w in caption_lower for w in ["parabola", "quadratic", "y = x²", "x^2"]):
        return "parabola"
    elif any(w in caption_lower for w in ["sine", "sin x", "trigonometric"]):
        return "sine"
    elif any(w in caption_lower for w in ["exponential", "e^x"]):
        return "exponential"
    elif any(w in caption_lower for w in ["linear", "straight line", "y = mx"]):
        return "linear"

    # Triangles
    elif any(w in caption_lower for w in ["right angle", "right-angled", "pythagoras"]):
        return "right_triangle"
    elif any(w in caption_lower for w in ["equilateral"]):
        return "equilateral"
    elif any(w in caption_lower for w in ["triangle"]):
        return "triangle"

    # Circles
    elif any(w in caption_lower for w in ["chord", "tangent", "radius", "diameter", "arc", "sector"]):
        return "circle_parts"
    elif any(w in caption_lower for w in ["inscribed angle", "central angle"]):
        return "circle_angles"

    # Conics
    elif any(w in caption_lower for w in ["ellipse", "foci"]):
        return "ellipse"
    elif any(w in caption_lower for w in ["hyperbola", "asymptote"]):
        return "hyperbola"
    elif any(w in caption_lower for w in ["parabola", "focus", "directrix"]):
        return "conic_parabola"

    # Vectors
    elif any(w in caption_lower for w in ["vector addition", "triangle law", "parallelogram"]):
        return "vector_addition"
    elif any(w in caption_lower for w in ["component", "resolve"]):
        return "vector_components"
    elif any(w in caption_lower for w in ["cross product", "right hand"]):
        return "cross_product"

    # Sets
    elif any(w in caption_lower for w in ["venn", "intersection", "union"]):
        if "three" in caption_lower:
            return "venn_3"
        return "venn_2"

    # 3D shapes
    elif any(w in caption_lower for w in ["cube", "cuboid"]):
        return "cube"
    elif any(w in caption_lower for w in ["cylinder"]):
        return "cylinder"
    elif any(w in caption_lower for w in ["cone"]):
        return "cone"
    elif any(w in caption_lower for w in ["sphere"]):
        return "sphere"

    return None
