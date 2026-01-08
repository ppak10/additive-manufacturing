KEYHOLE_THRESHOLD = 1.5
# BALLING_THRESHOLD = math.pi
BALLING_THRESHOLD = 2


def keyhole(width: float, depth: float) -> bool:
    # Keyhole equation, anything below keyhold threshold is considered keyholing
    # width / depth <= KEYHOLE_THRESHOLD
    return width / depth <= KEYHOLE_THRESHOLD
    # return width / depth


def lack_of_fusion(
    hatch_spacing: float, layer_height: float, width: float, depth: float
) -> bool:
    # Lack of fusion equation, anything above 1 is considered lack of fusion
    # (hatch_spacing / width)**2 + (layer_height / depth)**2 <= 1
    return (hatch_spacing / width) ** 2 + (layer_height / depth) ** 2 > 1


def balling(length: float, width: float):
    # Balling equation, anything above threshold is considered balling
    # length / width < BALLING_THRESHOLD
    # return length / width
    return length / width > BALLING_THRESHOLD
