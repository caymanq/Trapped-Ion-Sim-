"""JSON helpers for git-friendly U-channel geometry presets."""

from __future__ import annotations

import json
from pathlib import Path

from .models import GeometryPreset


def preset_to_json(preset: GeometryPreset) -> str:
    return preset.model_dump_json(indent=2)


def preset_from_json(contents: str) -> GeometryPreset:
    return GeometryPreset.model_validate_json(contents)


def save_preset(path: str | Path, preset: GeometryPreset) -> None:
    Path(path).write_text(preset_to_json(preset), encoding="utf-8")


def load_preset(path: str | Path) -> GeometryPreset:
    return preset_from_json(Path(path).read_text(encoding="utf-8"))


def preset_to_dict(preset: GeometryPreset) -> dict:
    return json.loads(preset_to_json(preset))
