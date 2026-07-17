"""
NCERT Subject Configuration - Chapter titles and diagram types for Class 11 & 12.
"""

SUBJECTS = {
    "chemistry": {
        "classes": [11, 12],
        "file_prefix": "lech",  # lech101, lech102...
        "chapters": {
            11: [
                "Some Basic Concepts of Chemistry",
                "Structure of Atom",
                "Classification of Elements and Periodicity in Properties",
                "Chemical Bonding and Molecular Structure",
                "Thermodynamics",
                "Equilibrium",
                "Redox Reactions",
                "Organic Chemistry - Some Basic Principles and Techniques",
                "Hydrocarbons",
            ],
            12: [
                "Solutions",
                "Electrochemistry",
                "Chemical Kinetics",
                "The d- and f-Block Elements",
                "Coordination Compounds",
                "Haloalkanes and Haloarenes",
                "Alcohols, Phenols and Ethers",
                "Aldehydes, Ketones and Carboxylic Acids",
                "Amines",
                "Biomolecules",
            ]
        },
        "diagram_types": [
            "beaker", "flask", "apparatus", "molecular_structure",
            "graph", "electrochemical_cell", "reaction_mechanism"
        ]
    },

    "physics": {
        "classes": [11, 12],
        "file_prefix": "keph",  # keph101, keph102...
        "chapters": {
            # Note: keph1XX files start from "Units and Measurement" as Chapter 1
            # (Physical World chapter is not included in these PDFs)
            11: [
                "Units and Measurement",
                "Motion in a Straight Line",
                "Motion in a Plane",
                "Laws of Motion",
                "Work, Energy and Power",
                "System of Particles and Rotational Motion",
                "Gravitation",
                "Mechanical Properties of Solids",
                "Mechanical Properties of Fluids",
                "Thermal Properties of Matter",
                "Thermodynamics",
                "Kinetic Theory",
                "Oscillations",
                "Waves",
            ],
            12: [
                "Electric Charges and Fields",
                "Electrostatic Potential and Capacitance",
                "Current Electricity",
                "Moving Charges and Magnetism",
                "Magnetism and Matter",
                "Electromagnetic Induction",
                "Alternating Current",
                "Electromagnetic Waves",
                "Ray Optics and Optical Instruments",
                "Wave Optics",
                "Dual Nature of Radiation and Matter",
                "Atoms",
                "Nuclei",
                "Semiconductor Electronics",
            ]
        },
        "diagram_types": [
            "circuit", "ray_diagram", "force_diagram", "vector_diagram",
            "wave", "graph", "apparatus", "field_lines", "lens_mirror"
        ]
    },

    "biology": {
        "classes": [11, 12],
        "file_prefix": "kebo",  # kebo101, kebo102...
        "chapters": {
            11: [
                "The Living World",
                "Biological Classification",
                "Plant Kingdom",
                "Animal Kingdom",
                "Morphology of Flowering Plants",
                "Anatomy of Flowering Plants",
                "Structural Organisation in Animals",
                "Cell: The Unit of Life",
                "Biomolecules",
                "Cell Cycle and Cell Division",
                "Photosynthesis in Higher Plants",
                "Respiration in Plants",
                "Plant Growth and Development",
                "Breathing and Exchange of Gases",
                "Body Fluids and Circulation",
                "Excretory Products and their Elimination",
                "Locomotion and Movement",
                "Neural Control and Coordination",
                "Chemical Coordination and Integration",
            ],
            12: [
                "Reproduction in Organisms",
                "Sexual Reproduction in Flowering Plants",
                "Human Reproduction",
                "Reproductive Health",
                "Principles of Inheritance and Variation",
                "Molecular Basis of Inheritance",
                "Evolution",
                "Human Health and Disease",
                "Strategies for Enhancement in Food Production",
                "Microbes in Human Welfare",
                "Biotechnology: Principles and Processes",
                "Biotechnology and its Applications",
                "Organisms and Populations",
                "Ecosystem",
                "Biodiversity and Conservation",
                "Environmental Issues",
            ]
        },
        "diagram_types": [
            "cell_structure", "organ_system", "plant_anatomy", "animal_anatomy",
            "flowchart", "lifecycle", "dna_rna", "ecosystem", "pedigree"
        ]
    },

    "maths": {
        "classes": [11, 12],
        "file_prefix": "kemh",  # kemh101, kemh102...
        "chapters": {
            11: [
                "Sets",
                "Relations and Functions",
                "Trigonometric Functions",
                "Complex Numbers and Quadratic Equations",
                "Linear Inequalities",
                "Permutations and Combinations",
                "Binomial Theorem",
                "Sequences and Series",
                "Straight Lines",
                "Conic Sections",
                "Introduction to Three Dimensional Geometry",
                "Limits and Derivatives",
                "Statistics",
                "Probability",
            ],
            12: [
                "Relations and Functions",
                "Inverse Trigonometric Functions",
                "Matrices",
                "Determinants",
                "Continuity and Differentiability",
                "Application of Derivatives",
                "Integrals",
                "Application of Integrals",
                "Differential Equations",
                "Vector Algebra",
                "Three Dimensional Geometry",
                "Linear Programming",
                "Probability",
            ]
        },
        "diagram_types": [
            "coordinate_graph", "geometric_figure", "venn_diagram",
            "triangle", "circle", "conic", "3d_shape", "vector"
        ]
    }
}


def detect_subject(book_code: str) -> dict:
    """Detect subject from book code like lech101, leph201."""
    prefix = book_code[:4].lower()

    for subject, config in SUBJECTS.items():
        if prefix == config["file_prefix"]:
            # Parse class and chapter from book_code like "lech101", "keph101"
            # Format: <prefix><part_digit><chapter_2digit>
            # The part_digit meaning varies by subject:
            #   - Chemistry: lech1XX = Class 12, lech2XX = Class 11
            #   - Physics: keph1XX = Class 11, keph2XX = Class 12
            try:
                part_digit = int(book_code[4])
                chapter_num = int(book_code[5:7])

                # Subject-specific class mapping based on actual PDF content
                if subject == "chemistry":
                    actual_class = 12 if part_digit == 1 else 11
                elif subject == "physics":
                    actual_class = 11 if part_digit == 1 else 12
                else:
                    # Default: part 1 = class 11, part 2 = class 12
                    actual_class = 11 if part_digit == 1 else 12

            except (ValueError, IndexError):
                actual_class = None
                chapter_num = None

            return {
                "subject": subject,
                "class": actual_class,
                "chapter": chapter_num,
                "config": config
            }

    return {"subject": "unknown", "class": None, "chapter": None, "config": None}


def get_chapter_titles(subject: str, class_num: int = None) -> list:
    """Get all chapter titles for a subject."""
    if subject not in SUBJECTS:
        return []

    config = SUBJECTS[subject]
    if class_num:
        return config["chapters"].get(class_num, [])

    # Return all chapters
    all_chapters = []
    for cls in config["classes"]:
        all_chapters.extend(config["chapters"].get(cls, []))
    return all_chapters


def get_all_chapter_titles() -> list:
    """Get all chapter titles across all subjects."""
    all_titles = []
    for subject, config in SUBJECTS.items():
        for cls in config["classes"]:
            all_titles.extend(config["chapters"].get(cls, []))
    return all_titles
