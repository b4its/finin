"""Loader untuk set asumsi berversi (data/assumptions/<CODE>.json)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from app.core.config import settings
from app.engine.regulatory import ruleset_from_assumptions

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "assumptions"
PRESETS = ("konservatif", "moderat", "optimis")


@dataclass
class Assumptions:
    code: str
    as_of: str
    label: str
    presets: dict[str, dict] = field(default_factory=dict)
    common: dict = field(default_factory=dict)
    regulatory: dict = field(default_factory=dict)
    sources: dict = field(default_factory=dict)
    market_context: list = field(default_factory=list)
    engine_version: str = "2.0.0"

    def preset(self, name: str) -> dict:
        key = name if name in self.presets else "moderat"
        merged = dict(self.common)
        merged.update(self.presets[key])
        merged["_preset"] = key
        return merged

    def rates_for(self, preset_name: str) -> dict:
        return dict(self.preset(preset_name).get("returns", {}))

    def ruleset(self) -> dict:
        return ruleset_from_assumptions(self.regulatory)

    def source(self, key: str) -> dict:
        src = self.sources.get(key)
        if src:
            return src
        # coba cari berdasarkan awalan (mis. returns.money_market)
        for k, v in self.sources.items():
            if key.startswith(k):
                return v
        return {"label": "Asumsi internal", "url": "", "as_of": self.as_of, "kind": "assumption"}

    def to_dict(self, preset: str = "moderat") -> dict:
        return {
            "code": self.code,
            "as_of": self.as_of,
            "label": self.label,
            "engine_version": self.engine_version,
            "preset": preset,
            "values": self.preset(preset),
            "presets": self.presets,
            "common": self.common,
            "regulatory": self.regulatory,
            "sources": self.sources,
            "market_context": self.market_context,
        }


@lru_cache
def load_assumptions(code: str | None = None) -> Assumptions:
    set_code = code or settings.assumption_set
    path = DATA_DIR / f"{set_code}.json"
    if not path.exists():
        # fallback ke set default apa pun yang tersedia
        candidates = sorted(DATA_DIR.glob("*.json"))
        if not candidates:
            raise FileNotFoundError(f"Tidak ada set asumsi di {DATA_DIR}")
        path = candidates[-1]
    raw = json.loads(path.read_text(encoding="utf-8"))
    return Assumptions(
        code=raw["code"],
        as_of=raw["as_of"],
        label=raw["label"],
        presets=raw["presets"],
        common=raw["common"],
        regulatory=raw["regulatory"],
        sources=raw["sources"],
        market_context=raw.get("market_context", []),
        engine_version=raw.get("engine_version", settings.engine_version),
    )


def monthly_rate(annual: float) -> float:
    """Konversi bunga tahunan ke bulanan: r_m = (1 + r_a)^(1/12) - 1."""
    return (1.0 + annual) ** (1.0 / 12.0) - 1.0
