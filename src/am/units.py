from dataclasses import dataclass


@dataclass(frozen=True)
class UnitSystem:
    name: str
    length: str
    mass: str
    time: str
    angle: str


MMGS = UnitSystem(
    "mmgs", length="millimeter", mass="gram", time="second", angle="degree"
)
IPS = UnitSystem("ips", length="inch", mass="pound", time="second", angle="degree")
