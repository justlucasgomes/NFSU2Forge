"""Preset load/save/apply logic."""
from __future__ import annotations
import logging
from pathlib import Path
from src.models.preset import Preset
from src.models.car_data import CarPhysics

log = logging.getLogger(__name__)

BUILTIN_PRESET_DIR = Path(__file__).parent.parent.parent / "presets"
USER_PRESET_DIR = Path.home() / ".nfsu2_tuning" / "presets"


class PresetManager:
    def __init__(self):
        USER_PRESET_DIR.mkdir(parents=True, exist_ok=True)

    def list_presets(self) -> list[Preset]:
        presets = []
        for directory in (BUILTIN_PRESET_DIR, USER_PRESET_DIR):
            if directory.exists():
                for p in sorted(directory.glob("*.json")):
                    try:
                        presets.append(Preset.load(p))
                    except Exception as exc:
                        log.warning("Failed to load preset %s: %s", p, exc)
        return presets

    def save_user_preset(self, preset: Preset) -> Path:
        safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in preset.name)
        path = USER_PRESET_DIR / f"{safe_name}.json"
        preset.save(path)
        log.info("Preset saved: %s", path)
        return path

    def apply_preset(self, preset: Preset, physics: CarPhysics) -> CarPhysics:
        """Apply preset overrides to a CarPhysics object (returns modified copy)."""
        result = physics.clone()

        def _apply(target, overrides: dict):
            for k, v in overrides.items():
                if hasattr(target, k):
                    setattr(target, k, v)

        _apply(result.engine, preset.engine)
        _apply(result.transmission, preset.transmission)
        _apply(result.chassis, preset.chassis)
        _apply(result.tyres, preset.tyres)
        _apply(result.brakes, preset.brakes)
        _apply(result.handling, preset.handling)
        _apply(result.aero, preset.aero)

        return result

    def physics_to_preset(self, name: str, physics: CarPhysics, description: str = "") -> Preset:
        """Convert full CarPhysics into a saveable Preset."""
        from dataclasses import asdict
        p = Preset(name=name, description=description)
        p.engine = asdict(physics.engine)
        p.transmission = asdict(physics.transmission)
        p.chassis = asdict(physics.chassis)
        p.tyres = asdict(physics.tyres)
        p.brakes = asdict(physics.brakes)
        p.handling = asdict(physics.handling)
        p.aero = asdict(physics.aero)
        return p
