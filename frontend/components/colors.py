# ----------------- Paleta para Benchmarks (10 colores) -----------------

BENCHMARK_COLORS = [
    "#38BDF8", "#A855F7", "#22C55E", "#F97316", "#E11D48",
    "#14B8A6", "#FACC15", "#0EA5E9", "#9333EA", "#34D399"
]

# ----------------- Paleta para Activos (30 colores) -----------------

ASSET_COLORS = [
    "#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F",
    "#EDC949", "#AF7AA1", "#FF9DA7", "#9C755F", "#BAB0AC",
    "#1F77B4", "#FF7F0E", "#2CA02C", "#D62728", "#9467BD",
    "#8C564B", "#E377C2", "#7F7F7F", "#BCBD22", "#17BECF",
    "#6B7280", "#FCD34D", "#34D399", "#60A5FA", "#F87171",
    "#A78BFA", "#4ADE80", "#FB923C", "#22D3EE", "#F472B6"
]


def generate_color_map(items, palette):
    """
    Asigna colores deterministas a elementos.
    Si hay más elementos que colores, la paleta se repite.
    """
    items = list(dict.fromkeys(items))  # unique y orden
    n = len(palette)
    return {item: palette[i % n] for i, item in enumerate(items)}
