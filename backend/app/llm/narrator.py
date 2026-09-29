"""Narator LLM provider-agnostic + timeout + validator + fallback."""

from __future__ import annotations

import json
import re

import httpx

from app.core.config import settings
from app.llm import fallback, prompts
from app.llm.validator import validate_numbers

# Non-greedy agar tidak menelan objek/kurung lain yang muncul di prosa sebelum JSON.
# Array dicoba lebih dulu karena narasi selalu diminta sebagai JSON array.
_JSON_ARRAY = re.compile(r"\[.*?\]", re.DOTALL)
_JSON_OBJECT = re.compile(r"\{.*?\}", re.DOTALL)


class Narrator:
    """Narator narasi + rekomendasi. Selalu punya fallback deterministik."""

    def __init__(self, enabled: bool | None = None) -> None:
        self.enabled = settings.llm_enabled if enabled is None else enabled

    # ---- LLM call ----
    async def _call(self, system: str, user: str) -> str | None:
        if not self.enabled:
            return None
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": settings.llm_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": settings.llm_model,
            "max_tokens": 1200,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        try:
            async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
                r = await client.post(url, headers=headers, json=payload)
                r.raise_for_status()
                data = r.json()
                blocks = data.get("content", [])
                text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
                return text or None
        except Exception:
            return None

    @staticmethod
    def _parse_json(text: str | None):
        if not text:
            return None
        for pattern in (_JSON_ARRAY, _JSON_OBJECT):
            m = pattern.search(text)
            if not m:
                continue
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                continue
        return None

    # ---- Narasi ----
    async def narrate(self, twins: list[dict]) -> list[dict]:
        """Narasi untuk semua twin. Fallback per-twin jika perlu."""
        facts_all = [prompts.facts_for_twin(t) for t in twins]
        baseline = next((t for t in twins if t.get("code") == "0"), None)
        baseline_facts = prompts.facts_for_twin(baseline) if baseline else {}

        # Bangun fallback dulu (selalu valid).
        fallback_out: list[dict] = []
        baseline_dict = baseline or {}
        for t in twins:
            fallback_out.extend(fallback.narrative_for_twin(t, baseline_dict))

        if not self.enabled:
            return fallback_out

        text = await self._call(
            prompts.SYSTEM_PROMPT,
            prompts.build_narrative_user_prompt(facts_all, baseline_facts),
        )
        parsed = self._parse_json(text)
        if not isinstance(parsed, list) or not parsed:
            return fallback_out

        # Validasi: hanya pakai entri yang angkanya cocok dengan facts.
        accepted: list[dict] = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            chunk_text = str(item.get("text", ""))
            ok, _ = validate_numbers(chunk_text, {"facts": facts_all, "baseline": baseline_facts})
            if ok:
                accepted.append(
                    {
                        "twin": item.get("twin"),
                        "horizon": item.get("horizon"),
                        "text": chunk_text,
                        "source": "llm",
                    }
                )
        if not accepted:
            return fallback_out

        # Merge: LLM menang untuk (twin,horizon) yang valid, sisanya fallback.
        merged: dict[tuple, dict] = {(f["twin"], f["horizon"]): f for f in fallback_out}
        for a in accepted:
            merged[(a["twin"], a["horizon"])] = a
        return list(merged.values())

    # ---- Rekomendasi ----
    async def recommend(self, best: dict, others: list[dict], robust: bool) -> dict:
        fb = fallback.recommendation_fallback(best, others, robust)
        if not self.enabled:
            return fb
        best_facts = prompts.facts_for_twin(best)
        others_facts = [prompts.facts_for_twin(o) for o in others]
        text = await self._call(
            prompts.RECOMMENDATION_SYSTEM,
            prompts.build_recommendation_user_prompt(best_facts, others_facts, robust),
        )
        parsed = self._parse_json(text)
        if not isinstance(parsed, dict):
            return fb
        first_step = str(parsed.get("first_step", "")).strip()
        rationale = str(parsed.get("rationale", "")).strip()
        if not first_step or not rationale:
            return fb
        facts = {"best": best_facts, "others": others_facts}
        ok1, _ = validate_numbers(first_step, facts)
        ok2, _ = validate_numbers(rationale, facts)
        if not (ok1 and ok2):
            return fb
        return {"first_step": first_step, "rationale": rationale, "source": "llm"}


narrator = Narrator()
