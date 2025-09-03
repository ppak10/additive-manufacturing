import math

KEYHOLE_THRESHOLD = 1.5
# BALLING_THRESHOLD = math.pi
BALLING_THRESHOLD = 2


def keyhole(width, depth):
    if width is None or depth is None:
        return None
    # Keyhole equation, anything below keyhold threshold is considered keyholing
    # width / depth <= KEYHOLE_THRESHOLD
    # return width / depth <= KEYHOLE_THRESHOLD
    return width / depth


def lack_of_fusion(hatch_spacing, layer_height, width, depth):
    if hatch_spacing is None or layer_height is None or width is None or depth is None:
        return None
    # Lack of fusion equation, anything above 1 is considered lack of fusion
    # (hatch_spacing / width)**2 + (layer_height / depth)**2 <= 1
    return (hatch_spacing / width) ** 2 + (layer_height / depth) ** 2 > 1


def balling(length, width):
    if length is None or width is None:
        return None
    # Balling equation, anything above threshold is considered balling
    # length / width < BALLING_THRESHOLD
    return length / width
    return length / width > BALLING_THRESHOLD
