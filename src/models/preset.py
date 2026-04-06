"""Preset data model."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import json
from pathlib import Path


@dataclass
class Preset:
    name: str
    description: str = ""
    author: str = "User"
    version: str = "1.0"
    tags: list = field(default_factory=list)
    # Partial overrides — only fields present will be applied
    engine: dict = field(default_factory=dict)
    transmission: dict = field(default_factory=dict)
    chassis: dict = field(default_factory=dict)
    tyres: dict = field(default_factory=dict)
    brakes: dict = field(default_factory=dict)
    handling: dict = field(default_factory=dict)
    aero: dict = field(default_factory=dict)

    def save(self, path: Path) -> None:
        path.write_text(json.dumps({
            "name": self.name,
            "description": self.description,
            "author": self.author,
            "version": self.version,
            "tags": self.tags,
            "engine": self.engine,
            "transmission": self.transmission,
            "chassis": self.chassis,
            "tyres": self.tyres,
            "brakes": self.brakes,
            "handling": self.handling,
            "aero": self.aero,
        }, indent=2), encoding="utf-8")

    @staticmethod
    def load(path: Path) -> Preset:
        data = json.loads(path.read_text(encoding="utf-8"))
        p = Preset(name=data.get("name", path.stem))
        p.description = data.get("description", "")
        p.author = data.get("author", "Unknown")
        p.version = data.get("version", "1.0")
        p.tags = data.get("tags", [])
        p.engine = data.get("engine", {})
        p.transmission = data.get("transmission", {})
        p.chassis = data.get("chassis", {})
        p.tyres = data.get("tyres", {})
        p.brakes = data.get("brakes", {})
        p.handling = data.get("handling", {})
        p.aero = data.get("aero", {})
        return p
