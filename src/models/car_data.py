"""
Car physics data models for NFSU2 Car Tuning Tool.

CarPhysics is the central data object. It is populated either by the
VaultParser (from SPEED2.EXE) or from the curated NFSU2_CAR_DATABASE
when per-car binary offsets are not yet confirmed.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional
import copy


@dataclass
class EngineData:
    max_torque: float = 200.0          # Nm
    max_power: float = 150.0           # kW
    max_rpm: float = 7000.0            # RPM
    idle_rpm: float = 700.0            # RPM
    redline_rpm: float = 6800.0        # RPM
    torque_curve: list = field(default_factory=lambda: [
        (1000, 0.60), (2000, 0.75), (3000, 0.88),
        (4000, 0.95), (5000, 1.00), (6000, 0.90), (7000, 0.75)
    ])  # list of (rpm, torque_normalized) tuples


@dataclass
class TransmissionData:
    gear_ratios: list = field(default_factory=lambda: [3.32, 1.90, 1.31, 1.03, 0.82])
    final_drive: float = 3.90
    reverse_ratio: float = 3.38
    shift_time: float = 0.18           # seconds


@dataclass
class ChassisData:
    mass: float = 1300.0               # kg
    center_of_mass_x: float = 0.0      # m
    center_of_mass_y: float = -0.10    # m (negative = lower)
    center_of_mass_z: float = 0.05     # m
    inertia_x: float = 2000.0          # kg·m²
    inertia_y: float = 2500.0          # kg·m²
    inertia_z: float = 1000.0          # kg·m²


@dataclass
class TyreData:
    front_grip: float = 1.0
    rear_grip: float = 1.0
    lateral_grip: float = 1.0
    front_slip_angle: float = 8.0      # degrees
    rear_slip_angle: float = 10.0      # degrees


@dataclass
class BrakeData:
    front_bias: float = 0.62           # 0.0–1.0
    power: float = 3000.0              # N


@dataclass
class HandlingData:
    steering_lock: float = 35.0        # degrees max
    steering_ratio: float = 14.5       # steering wheel to wheel ratio
    suspension_stiffness_f: float = 20.0   # N/mm
    suspension_stiffness_r: float = 18.0
    damping_front: float = 3000.0      # N·s/m
    damping_rear: float = 2700.0
    roll_stiffness: float = 1.0
    understeer_gradient: float = 0.35


@dataclass
class AeroData:
    drag_coefficient: float = 0.32
    lift_front: float = -0.10
    lift_rear: float = -0.15
    top_speed: float = 210.0           # km/h


@dataclass
class RatingData:
    acceleration: int = 5              # 1–10
    top_speed: int = 5
    handling: int = 5
    braking: int = 5
    drift: int = 5


@dataclass
class CarPhysics:
    """
    Complete physics data for a single NFSU2 car.

    Fields map to the NFSU2 vault node types:
      PVEHICLE    → chassis
      PENGINE     → engine
      PTRANSMISSION → transmission
      PTYRES      → tyres
      PBRAKE      → brakes
      PHANDLING   → handling
      PAERO       → aero
    """
    car_id: str = ""
    display_name: str = ""
    manufacturer: str = ""
    year: int = 2003
    car_class: str = "Tuner"           # Tuner, Muscle, Exotic, SUV
    drive_type: str = "FWD"            # FWD, RWD, AWD
    engine_type: str = ""

    engine: EngineData = field(default_factory=EngineData)
    transmission: TransmissionData = field(default_factory=TransmissionData)
    chassis: ChassisData = field(default_factory=ChassisData)
    tyres: TyreData = field(default_factory=TyreData)
    brakes: BrakeData = field(default_factory=BrakeData)
    handling: HandlingData = field(default_factory=HandlingData)
    aero: AeroData = field(default_factory=AeroData)
    ratings: RatingData = field(default_factory=RatingData)

    # Internal: EXE offset map — populated by VaultParser when confirmed offsets exist.
    # Key = field path like "engine.max_torque", value = byte offset in SPEED2.EXE
    _offset_map: dict = field(default_factory=dict, repr=False, compare=False)

    def clone(self) -> CarPhysics:
        return copy.deepcopy(self)

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("_offset_map", None)
        return d

    @staticmethod
    def from_dict(d: dict) -> CarPhysics:
        cp = CarPhysics()
        cp.car_id = d.get("car_id", "")
        cp.display_name = d.get("display_name", "")
        cp.manufacturer = d.get("manufacturer", "")
        cp.year = d.get("year", 2003)
        cp.car_class = d.get("car_class", "Tuner")
        cp.drive_type = d.get("drive_type", "FWD")
        cp.engine_type = d.get("engine_type", "")

        def _merge(target, src: dict):
            for k, v in src.items():
                if hasattr(target, k):
                    setattr(target, k, v)

        if "engine" in d:
            e = EngineData()
            _merge(e, d["engine"])
            if "torque_curve" in d["engine"]:
                e.torque_curve = [tuple(p) for p in d["engine"]["torque_curve"]]
            cp.engine = e

        if "transmission" in d:
            t = TransmissionData()
            _merge(t, d["transmission"])
            cp.transmission = t

        if "chassis" in d:
            c = ChassisData()
            _merge(c, d["chassis"])
            cp.chassis = c

        if "tyres" in d:
            ty = TyreData()
            _merge(ty, d["tyres"])
            cp.tyres = ty

        if "brakes" in d:
            b = BrakeData()
            _merge(b, d["brakes"])
            cp.brakes = b

        if "handling" in d:
            h = HandlingData()
            _merge(h, d["handling"])
            cp.handling = h

        if "aero" in d:
            a = AeroData()
            _merge(a, d["aero"])
            cp.aero = a

        if "ratings" in d:
            r = RatingData()
            _merge(r, d["ratings"])
            cp.ratings = r

        return cp


# ---------------------------------------------------------------------------
# Curated NFSU2 Car Database
# ---------------------------------------------------------------------------
# Values sourced from real car specs, adjusted for NFSU2 gameplay balance.
# These are used as fallback when per-car binary offsets are not yet confirmed.
# ---------------------------------------------------------------------------

def _car(car_id, name, mfr, year, cls, drive, engine_type,
         mass, com_y, torque, power, max_rpm, idle_rpm, redline,
         gear_ratios, final_drive, f_grip, r_grip,
         steer_lock, susp_f, susp_r, drag, top_speed,
         accel, spd, hdl, brk, drift,
         torque_curve=None) -> CarPhysics:
    """Factory helper to build a CarPhysics from positional args."""
    cp = CarPhysics()
    cp.car_id = car_id
    cp.display_name = name
    cp.manufacturer = mfr
    cp.year = year
    cp.car_class = cls
    cp.drive_type = drive
    cp.engine_type = engine_type

    cp.engine.max_torque = torque
    cp.engine.max_power = power
    cp.engine.max_rpm = max_rpm
    cp.engine.idle_rpm = idle_rpm
    cp.engine.redline_rpm = redline
    if torque_curve:
        cp.engine.torque_curve = torque_curve

    cp.transmission.gear_ratios = gear_ratios
    cp.transmission.final_drive = final_drive

    cp.chassis.mass = mass
    cp.chassis.center_of_mass_y = com_y

    cp.tyres.front_grip = f_grip
    cp.tyres.rear_grip = r_grip

    cp.handling.steering_lock = steer_lock
    cp.handling.suspension_stiffness_f = susp_f
    cp.handling.suspension_stiffness_r = susp_r

    cp.aero.drag_coefficient = drag
    cp.aero.top_speed = top_speed

    cp.ratings.acceleration = accel
    cp.ratings.top_speed = spd
    cp.ratings.handling = hdl
    cp.ratings.braking = brk
    cp.ratings.drift = drift

    return cp


NFSU2_CAR_DATABASE: dict[str, CarPhysics] = {}

def _register(cp: CarPhysics):
    NFSU2_CAR_DATABASE[cp.car_id] = cp

# ─── Tuners ────────────────────────────────────────────────────────────────

_register(_car(
    "240SX", "Nissan 240SX", "Nissan", 1998,
    "Tuner", "RWD", "SR20DE",
    mass=1265.0, com_y=-0.12,
    torque=163.0, power=100.0, max_rpm=7200.0, idle_rpm=750.0, redline=7000.0,
    gear_ratios=[3.321, 1.902, 1.308, 1.031, 0.821], final_drive=3.909,
    f_grip=1.05, r_grip=0.88,
    steer_lock=33.0, susp_f=17.0, susp_r=14.0,
    drag=0.31, top_speed=190.0,
    accel=5, spd=5, hdl=7, brk=5, drift=9,
    torque_curve=[(1000,0.55),(2000,0.70),(3000,0.85),(4000,0.95),(4800,1.00),(6000,0.92),(7000,0.78)]
))

_register(_car(
    "CIVIC", "Honda Civic Si", "Honda", 2002,
    "Tuner", "FWD", "B16A2",
    mass=1117.0, com_y=-0.14,
    torque=128.0, power=93.0, max_rpm=8200.0, idle_rpm=700.0, redline=8000.0,
    gear_ratios=[3.307, 2.105, 1.458, 1.107, 0.848], final_drive=4.266,
    f_grip=1.08, r_grip=0.95,
    steer_lock=36.0, susp_f=16.0, susp_r=14.0,
    drag=0.33, top_speed=185.0,
    accel=5, spd=4, hdl=8, brk=6, drift=4,
    torque_curve=[(1000,0.50),(2500,0.70),(4000,0.88),(5500,0.98),(6500,1.00),(7500,0.95),(8000,0.85)]
))

_register(_car(
    "ECLIPSE", "Mitsubishi Eclipse GT", "Mitsubishi", 2003,
    "Tuner", "FWD", "6G72",
    mass=1454.0, com_y=-0.10,
    torque=271.0, power=162.0, max_rpm=6000.0, idle_rpm=750.0, redline=5800.0,
    gear_ratios=[3.166, 1.882, 1.296, 0.972, 0.780], final_drive=4.059,
    f_grip=1.05, r_grip=0.92,
    steer_lock=35.0, susp_f=18.0, susp_r=16.0,
    drag=0.34, top_speed=215.0,
    accel=6, spd=6, hdl=6, brk=6, drift=5,
    torque_curve=[(1000,0.55),(2000,0.75),(3000,0.92),(4000,1.00),(5000,0.98),(5500,0.90),(6000,0.80)]
))

_register(_car(
    "RSX", "Acura RSX Type-S", "Acura", 2002,
    "Tuner", "FWD", "K20A2",
    mass=1270.0, com_y=-0.13,
    torque=197.0, power=147.0, max_rpm=8000.0, idle_rpm=700.0, redline=7800.0,
    gear_ratios=[3.267, 2.130, 1.517, 1.161, 0.943], final_drive=4.400,
    f_grip=1.08, r_grip=0.96,
    steer_lock=36.0, susp_f=18.0, susp_r=16.0,
    drag=0.30, top_speed=210.0,
    accel=6, spd=6, hdl=8, brk=7, drift=4,
))

_register(_car(
    "SENTRA", "Nissan Sentra SE-R", "Nissan", 2003,
    "Tuner", "FWD", "QR25DE",
    mass=1270.0, com_y=-0.11,
    torque=226.0, power=127.0, max_rpm=6400.0, idle_rpm=750.0, redline=6200.0,
    gear_ratios=[3.461, 1.949, 1.310, 0.965, 0.762], final_drive=3.900,
    f_grip=1.02, r_grip=0.90,
    steer_lock=35.0, susp_f=16.0, susp_r=14.0,
    drag=0.34, top_speed=195.0,
    accel=5, spd=5, hdl=6, brk=5, drift=4,
))

_register(_car(
    "LANCER", "Mitsubishi Lancer", "Mitsubishi", 2003,
    "Tuner", "FWD", "4G18",
    mass=1160.0, com_y=-0.12,
    torque=134.0, power=91.0, max_rpm=6500.0, idle_rpm=750.0, redline=6300.0,
    gear_ratios=[3.461, 2.027, 1.327, 0.951, 0.785], final_drive=3.944,
    f_grip=1.03, r_grip=0.91,
    steer_lock=35.0, susp_f=15.0, susp_r=13.0,
    drag=0.34, top_speed=180.0,
    accel=4, spd=4, hdl=6, brk=5, drift=4,
))

_register(_car(
    "NEON", "Dodge Neon SRT-4", "Dodge", 2003,
    "Tuner", "FWD", "2.4T",
    mass=1312.0, com_y=-0.10,
    torque=332.0, power=186.0, max_rpm=6400.0, idle_rpm=750.0, redline=6200.0,
    gear_ratios=[2.950, 1.942, 1.354, 1.031, 0.819], final_drive=3.940,
    f_grip=1.04, r_grip=0.90,
    steer_lock=35.0, susp_f=20.0, susp_r=18.0,
    drag=0.35, top_speed=205.0,
    accel=7, spd=5, hdl=5, brk=6, drift=5,
))

_register(_car(
    "TIBURON", "Hyundai Tiburon GT", "Hyundai", 2003,
    "Tuner", "FWD", "2.7 V6",
    mass=1325.0, com_y=-0.11,
    torque=250.0, power=142.0, max_rpm=6500.0, idle_rpm=750.0, redline=6300.0,
    gear_ratios=[3.545, 2.034, 1.333, 0.978, 0.772], final_drive=4.056,
    f_grip=1.04, r_grip=0.92,
    steer_lock=35.0, susp_f=17.0, susp_r=15.0,
    drag=0.33, top_speed=200.0,
    accel=5, spd=5, hdl=6, brk=5, drift=4,
))

_register(_car(
    "TT", "Audi TT 1.8T", "Audi", 2003,
    "Tuner", "AWD", "1.8T 20V",
    mass=1305.0, com_y=-0.12,
    torque=280.0, power=165.0, max_rpm=6500.0, idle_rpm=750.0, redline=6300.0,
    gear_ratios=[3.500, 1.889, 1.179, 0.857, 0.683], final_drive=3.684,
    f_grip=1.10, r_grip=1.05,
    steer_lock=34.0, susp_f=20.0, susp_r=18.0,
    drag=0.32, top_speed=225.0,
    accel=6, spd=6, hdl=7, brk=7, drift=4,
))

_register(_car(
    "A3", "Audi A3 1.8T", "Audi", 2003,
    "Tuner", "FWD", "1.8T",
    mass=1260.0, com_y=-0.12,
    torque=210.0, power=132.0, max_rpm=6500.0, idle_rpm=750.0, redline=6300.0,
    gear_ratios=[3.500, 1.889, 1.179, 0.857, 0.683], final_drive=3.684,
    f_grip=1.05, r_grip=0.93,
    steer_lock=35.0, susp_f=18.0, susp_r=16.0,
    drag=0.31, top_speed=210.0,
    accel=5, spd=5, hdl=7, brk=6, drift=3,
))

_register(_car(
    "GOLF", "Volkswagen Golf GTI", "Volkswagen", 2003,
    "Tuner", "FWD", "2.0T",
    mass=1320.0, com_y=-0.11,
    torque=265.0, power=150.0, max_rpm=6200.0, idle_rpm=750.0, redline=6000.0,
    gear_ratios=[3.778, 2.118, 1.360, 1.031, 0.806], final_drive=3.588,
    f_grip=1.06, r_grip=0.93,
    steer_lock=35.0, susp_f=17.0, susp_r=16.0,
    drag=0.32, top_speed=210.0,
    accel=5, spd=5, hdl=7, brk=6, drift=4,
))

_register(_car(
    "CELICA", "Toyota Celica GT-S", "Toyota", 2003,
    "Tuner", "FWD", "2ZZ-GE",
    mass=1111.0, com_y=-0.14,
    torque=200.0, power=141.0, max_rpm=8500.0, idle_rpm=700.0, redline=8200.0,
    gear_ratios=[3.538, 2.063, 1.387, 1.030, 0.850], final_drive=4.312,
    f_grip=1.08, r_grip=0.96,
    steer_lock=35.0, susp_f=16.0, susp_r=14.0,
    drag=0.29, top_speed=215.0,
    accel=6, spd=6, hdl=8, brk=7, drift=4,
))

_register(_car(
    "FOCUS", "Ford Focus SVT", "Ford", 2003,
    "Tuner", "FWD", "2.0 DOHC",
    mass=1293.0, com_y=-0.11,
    torque=200.0, power=131.0, max_rpm=7500.0, idle_rpm=700.0, redline=7300.0,
    gear_ratios=[3.368, 1.895, 1.289, 0.975, 0.794], final_drive=4.063,
    f_grip=1.06, r_grip=0.93,
    steer_lock=35.0, susp_f=16.0, susp_r=14.0,
    drag=0.33, top_speed=205.0,
    accel=5, spd=5, hdl=7, brk=6, drift=4,
))

_register(_car(
    "COROLLA", "Toyota Corolla", "Toyota", 2003,
    "Tuner", "FWD", "1ZZ-FE",
    mass=1134.0, com_y=-0.12,
    torque=162.0, power=100.0, max_rpm=6800.0, idle_rpm=700.0, redline=6600.0,
    gear_ratios=[3.545, 1.904, 1.233, 0.918, 0.733], final_drive=3.722,
    f_grip=1.00, r_grip=0.90,
    steer_lock=35.0, susp_f=14.0, susp_r=12.0,
    drag=0.30, top_speed=175.0,
    accel=3, spd=3, hdl=5, brk=4, drift=3,
))

_register(_car(
    "PEUGEOT_206", "Peugeot 206", "Peugeot", 2003,
    "Tuner", "FWD", "1.6 16V",
    mass=1055.0, com_y=-0.13,
    torque=145.0, power=82.0, max_rpm=7000.0, idle_rpm=700.0, redline=6800.0,
    gear_ratios=[3.583, 2.045, 1.333, 0.939, 0.745], final_drive=3.700,
    f_grip=1.02, r_grip=0.91,
    steer_lock=27.0, susp_f=15.0, susp_r=13.0,
    drag=0.32, top_speed=185.0,
    accel=3, spd=3, hdl=6, brk=5, drift=3,
))

_register(_car(
    "PEUGEOT_106", "Peugeot 106", "Peugeot", 1999,
    "Tuner", "FWD", "1.6 GTi",
    mass=960.0, com_y=-0.14,
    torque=128.0, power=72.0, max_rpm=7000.0, idle_rpm=700.0, redline=6800.0,
    gear_ratios=[3.583, 2.045, 1.333, 0.939, 0.745], final_drive=3.700,
    f_grip=1.02, r_grip=0.91,
    steer_lock=34.0, susp_f=14.0, susp_r=12.0,
    drag=0.31, top_speed=175.0,
    accel=3, spd=3, hdl=6, brk=5, drift=3,
))

_register(_car(
    "CORSA", "Vauxhall Corsa", "Vauxhall", 2003,
    "Tuner", "FWD", "1.8 16V",
    mass=1095.0, com_y=-0.13,
    torque=165.0, power=92.0, max_rpm=6500.0, idle_rpm=700.0, redline=6300.0,
    gear_ratios=[3.583, 2.045, 1.333, 0.939, 0.745], final_drive=3.733,
    f_grip=1.02, r_grip=0.91,
    steer_lock=36.0, susp_f=15.0, susp_r=13.0,
    drag=0.32, top_speed=175.0,
    accel=3, spd=3, hdl=6, brk=5, drift=3,
))

# ─── Sports / Exotic ────────────────────────────────────────────────────────

_register(_car(
    "350Z", "Nissan 350Z Track", "Nissan", 2003,
    "Sport", "RWD", "VQ35DE",
    mass=1415.0, com_y=-0.10,
    torque=363.0, power=206.0, max_rpm=7000.0, idle_rpm=700.0, redline=6800.0,
    gear_ratios=[3.794, 2.324, 1.624, 1.271, 1.000, 0.794], final_drive=3.538,
    f_grip=1.10, r_grip=1.05,
    steer_lock=32.0, susp_f=22.0, susp_r=20.0,
    drag=0.30, top_speed=240.0,
    accel=7, spd=7, hdl=8, brk=8, drift=8,
))

_register(_car(
    "3000GT", "Mitsubishi 3000GT SL", "Mitsubishi", 1998,
    "Sport", "FWD", "6G72",
    mass=1585.0, com_y=-0.09,
    torque=279.0, power=164.0, max_rpm=6500.0, idle_rpm=750.0, redline=6300.0,
    gear_ratios=[3.166, 1.882, 1.296, 0.972, 0.780], final_drive=4.320,
    f_grip=1.05, r_grip=0.95,
    steer_lock=34.0, susp_f=19.0, susp_r=17.0,
    drag=0.32, top_speed=220.0,
    accel=6, spd=6, hdl=6, brk=6, drift=5,
))

_register(_car(
    "G35", "Infiniti G35 Coupe", "Infiniti", 2003,
    "Sport", "RWD", "VQ35DE",
    mass=1555.0, com_y=-0.10,
    torque=334.0, power=205.0, max_rpm=7000.0, idle_rpm=700.0, redline=6800.0,
    gear_ratios=[3.794, 2.324, 1.624, 1.271, 1.000, 0.794], final_drive=3.538,
    f_grip=1.08, r_grip=1.02,
    steer_lock=33.0, susp_f=21.0, susp_r=19.0,
    drag=0.29, top_speed=245.0,
    accel=7, spd=7, hdl=8, brk=8, drift=7,
))

_register(_car(
    "IS300", "Lexus IS300", "Lexus", 2003,
    "Sport", "RWD", "2JZ-GE",
    mass=1558.0, com_y=-0.09,
    torque=280.0, power=161.0, max_rpm=6600.0, idle_rpm=700.0, redline=6400.0,
    gear_ratios=[3.166, 1.882, 1.296, 0.972, 0.780], final_drive=3.769,
    f_grip=1.06, r_grip=1.00,
    steer_lock=33.0, susp_f=20.0, susp_r=18.0,
    drag=0.30, top_speed=225.0,
    accel=6, spd=6, hdl=7, brk=7, drift=7,
))

_register(_car(
    "RX8", "Mazda RX-8", "Mazda", 2003,
    "Sport", "RWD", "13B-MSP RENESIS",
    mass=1310.0, com_y=-0.12,
    torque=211.0, power=172.0, max_rpm=9000.0, idle_rpm=750.0, redline=8800.0,
    gear_ratios=[3.760, 2.269, 1.645, 1.257, 0.972, 0.796], final_drive=4.444,
    f_grip=1.10, r_grip=1.05,
    steer_lock=34.0, susp_f=21.0, susp_r=19.0,
    drag=0.30, top_speed=230.0,
    accel=6, spd=6, hdl=9, brk=8, drift=7,
))

_register(_car(
    "MIATA", "Mazda MX-5 Miata", "Mazda", 2001,
    "Sport", "RWD", "1.8 BP",
    mass=1065.0, com_y=-0.15,
    torque=163.0, power=110.0, max_rpm=7200.0, idle_rpm=750.0, redline=7000.0,
    gear_ratios=[3.136, 1.888, 1.330, 1.000, 0.814], final_drive=4.100,
    f_grip=1.08, r_grip=1.02,
    steer_lock=35.0, susp_f=18.0, susp_r=16.0,
    drag=0.38, top_speed=185.0,
    accel=5, spd=4, hdl=9, brk=7, drift=8,
))

_register(_car(
    "S2000", "Honda S2000", "Honda", 2002,
    "Sport", "RWD", "F20C",
    mass=1254.0, com_y=-0.13,
    torque=208.0, power=177.0, max_rpm=9000.0, idle_rpm=800.0, redline=8800.0,
    gear_ratios=[3.133, 2.045, 1.481, 1.161, 0.970], final_drive=4.100,
    f_grip=1.10, r_grip=1.05,
    steer_lock=34.0, susp_f=20.0, susp_r=18.0,
    drag=0.31, top_speed=235.0,
    accel=7, spd=7, hdl=9, brk=8, drift=7,
))

_register(_car(
    "RX7", "Mazda RX-7 FD", "Mazda", 1997,
    "Exotic", "RWD", "13B-REW Twin Turbo",
    mass=1280.0, com_y=-0.12,
    torque=294.0, power=206.0, max_rpm=8500.0, idle_rpm=750.0, redline=8200.0,
    gear_ratios=[3.483, 2.015, 1.391, 1.000, 0.719], final_drive=4.100,
    f_grip=1.12, r_grip=1.08,
    steer_lock=33.0, susp_f=22.0, susp_r=20.0,
    drag=0.29, top_speed=250.0,
    accel=8, spd=8, hdl=9, brk=9, drift=9,
))

_register(_car(
    "SKYLINE", "Nissan Skyline GT-R", "Nissan", 2001,
    "Exotic", "AWD", "RB26DETT",
    mass=1560.0, com_y=-0.10,
    torque=353.0, power=206.0, max_rpm=7500.0, idle_rpm=750.0, redline=7200.0,
    gear_ratios=[3.214, 2.071, 1.476, 1.163, 0.961], final_drive=4.111,
    f_grip=1.15, r_grip=1.12,
    steer_lock=32.0, susp_f=24.0, susp_r=22.0,
    drag=0.33, top_speed=250.0,
    accel=8, spd=8, hdl=9, brk=9, drift=7,
))

_register(_car(
    "SUPRA", "Toyota Supra MkIV", "Toyota", 1998,
    "Exotic", "RWD", "2JZ-GTE",
    mass=1570.0, com_y=-0.10,
    torque=451.0, power=239.0, max_rpm=7000.0, idle_rpm=700.0, redline=6800.0,
    gear_ratios=[3.626, 2.188, 1.541, 1.213, 1.000, 0.793], final_drive=3.583,
    f_grip=1.12, r_grip=1.08,
    steer_lock=33.0, susp_f=24.0, susp_r=22.0,
    drag=0.31, top_speed=255.0,
    accel=8, spd=9, hdl=8, brk=9, drift=8,
))

# ─── Muscle ─────────────────────────────────────────────────────────────────

_register(_car(
    "MUSTANGGT", "Ford Mustang GT", "Ford", 2003,
    "Muscle", "RWD", "4.6L V8",
    mass=1560.0, com_y=-0.08,
    torque=393.0, power=230.0, max_rpm=6000.0, idle_rpm=700.0, redline=5800.0,
    gear_ratios=[3.370, 1.990, 1.330, 1.000, 0.670], final_drive=3.270,
    f_grip=1.05, r_grip=0.98,
    steer_lock=32.0, susp_f=20.0, susp_r=18.0,
    drag=0.35, top_speed=230.0,
    accel=7, spd=7, hdl=6, brk=7, drift=8,
))

_register(_car(
    "GTO", "Pontiac GTO", "Pontiac", 2004,
    "Muscle", "RWD", "5.7L LS1",
    mass=1655.0, com_y=-0.08,
    torque=475.0, power=253.0, max_rpm=6000.0, idle_rpm=700.0, redline=5800.0,
    gear_ratios=[2.970, 1.630, 1.060, 0.770, 0.620], final_drive=3.460,
    f_grip=1.06, r_grip=1.00,
    steer_lock=31.0, susp_f=21.0, susp_r=19.0,
    drag=0.36, top_speed=245.0,
    accel=8, spd=8, hdl=6, brk=8, drift=7,
))

# ─── AWD Rally ───────────────────────────────────────────────────────────────

_register(_car(
    "IMPREZAWRX", "Subaru Impreza WRX", "Subaru", 2003,
    "Sport", "AWD", "EJ205 Turbo",
    mass=1430.0, com_y=-0.11,
    torque=310.0, power=160.0, max_rpm=6500.0, idle_rpm=750.0, redline=6300.0,
    gear_ratios=[3.454, 1.947, 1.296, 0.972, 0.738], final_drive=3.900,
    f_grip=1.12, r_grip=1.08,
    steer_lock=34.0, susp_f=20.0, susp_r=18.0,
    drag=0.35, top_speed=215.0,
    accel=7, spd=6, hdl=7, brk=7, drift=5,
))

_register(_car(
    "LANCEREVO8", "Mitsubishi Lancer Evo VIII", "Mitsubishi", 2003,
    "Sport", "AWD", "4G63T",
    mass=1400.0, com_y=-0.11,
    torque=380.0, power=206.0, max_rpm=7000.0, idle_rpm=750.0, redline=6800.0,
    gear_ratios=[2.923, 1.875, 1.360, 1.032, 0.820], final_drive=4.529,
    f_grip=1.14, r_grip=1.10,
    steer_lock=34.0, susp_f=22.0, susp_r=20.0,
    drag=0.34, top_speed=230.0,
    accel=8, spd=7, hdl=9, brk=9, drift=6,
))

_register(_car(
    "IMPREZA", "Subaru Impreza", "Subaru", 2003,
    "Sport", "AWD", "EJ20",
    mass=1375.0, com_y=-0.11,
    torque=186.0, power=116.0, max_rpm=6400.0, idle_rpm=750.0, redline=6200.0,
    gear_ratios=[3.454, 1.947, 1.296, 0.972, 0.738], final_drive=3.900,
    f_grip=1.10, r_grip=1.06,
    steer_lock=34.0, susp_f=18.0, susp_r=16.0,
    drag=0.35, top_speed=195.0,
    accel=5, spd=5, hdl=7, brk=6, drift=4,
))

# ─── SUV ────────────────────────────────────────────────────────────────────

_register(_car(
    "ESCALADE", "Cadillac Escalade EXT", "Cadillac", 2003,
    "SUV", "AWD", "6.0L V8",
    mass=2725.0, com_y=-0.04,
    torque=592.25, power=282.9, max_rpm=5200.0, idle_rpm=600.0, redline=5000.0,
    gear_ratios=[3.058, 1.626, 1.000, 0.696, 0.571], final_drive=3.730,
    f_grip=1.045, r_grip=0.99,
    steer_lock=28.0, susp_f=26.4, susp_r=24.2,
    drag=0.41, top_speed=185.0,
    accel=5, spd=4, hdl=3, brk=4, drift=4,
))

_register(_car(
    "HUMMER", "Hummer H2", "Hummer", 2003,
    "SUV", "AWD", "6.0L V8",
    mass=3856.0, com_y=-0.03,
    torque=515.0, power=246.0, max_rpm=5200.0, idle_rpm=600.0, redline=5000.0,
    gear_ratios=[3.058, 1.626, 1.000, 0.696, 0.571], final_drive=4.100,
    f_grip=0.90, r_grip=0.88,
    steer_lock=26.0, susp_f=28.0, susp_r=26.0,
    drag=0.55, top_speed=165.0,
    accel=4, spd=3, hdl=2, brk=3, drift=3,
))

_register(_car(
    "NAVIGATOR", "Lincoln Navigator", "Lincoln", 2003,
    "SUV", "AWD", "5.4L V8",
    mass=1650.0, com_y=-0.10,
    torque=475.0, power=224.0, max_rpm=5100.0, idle_rpm=600.0, redline=5000.0,
    gear_ratios=[2.971, 1.627, 1.000, 0.743, 0.584], final_drive=3.730,
    f_grip=0.93, r_grip=0.88,
    steer_lock=27.0, susp_f=26.0, susp_r=24.0,
    drag=0.43, top_speed=180.0,
    accel=5, spd=4, hdl=2, brk=3, drift=3,
))
