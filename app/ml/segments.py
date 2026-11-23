"""ARCADE / SYNTAX-score coronary segment definitions (AHA 25-segment model)."""

# Order follows the ARCADE syntax category ids 1..25.
ARCADE_SEGMENTS = [
    ("1", "RCA proximal"), ("2", "RCA mid"), ("3", "RCA distal"), ("4", "Posterior descending (R-PDA)"),
    ("5", "Left main"), ("6", "LAD proximal"), ("7", "LAD mid"), ("8", "LAD distal"),
    ("9", "1st diagonal"), ("9a", "1st diagonal a"), ("10", "2nd diagonal"), ("10a", "2nd diagonal a"),
    ("11", "Circumflex proximal"), ("12", "Intermediate / anterolateral"), ("12a", "Obtuse marginal a"),
    ("13", "Circumflex distal"), ("14", "Left posterolateral"), ("14a", "Left posterolateral a"),
    ("15", "Posterior descending (L-PDA)"), ("16", "Posterolateral from RCA"),
    ("16a", "Posterolateral a (RCA)"), ("16b", "Posterolateral b (RCA)"), ("16c", "Posterolateral c (RCA)"),
    ("12b", "Obtuse marginal b"), ("14b", "Left posterolateral b"),
]

NUM_SEG_CLASSES = len(ARCADE_SEGMENTS) + 1  # + background


def segment_label(class_id: int) -> str:
    if class_id <= 0 or class_id > len(ARCADE_SEGMENTS):
        return "Unlabelled vessel"
    code, name = ARCADE_SEGMENTS[class_id - 1]
    return f"Seg {code} - {name}"


def segment_color(class_id: int) -> tuple:
    """Deterministic distinct BGR color per segment class."""
    import colorsys

    if class_id <= 0:
        return (0, 0, 0)
    h = (class_id * 0.61803398875) % 1.0
    r, g, b = colorsys.hsv_to_rgb(h, 0.75, 0.95)
    return (int(b * 255), int(g * 255), int(r * 255))
