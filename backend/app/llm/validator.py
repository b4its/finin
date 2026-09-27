"""Validator angka: pastikan semua angka di narasi LLM ada di FACTS."""

from __future__ import annotations

import re

# Tangkap angka termasuk format Indonesia "Rp12.400.000", "12,4", "6 bulan"
_NUM_RE = re.compile(r"\d[\d.,]*")


def _normalize_number(token: str) -> str:
    """Normalisasi token angka ke bentuk digit-only agar bisa dibandingkan.

    "12.400.000" -> "12400000"; "12,4" -> "12.4"; "6" -> "6".
    """
    t = token.strip().rstrip(".,")
    if not t:
        return ""
    # Heuristik: pemisah ribuan Indonesia = '.', desimal = ','
    if "," in t and t.count(",") == 1 and len(t.split(",")[-1]) <= 2:
        t = t.replace(".", "").replace(",", ".")
    else:
        t = t.replace(".", "").replace(",", "")
    try:
        val = float(t)
    except ValueError:
        return t
    if val.is_integer():
        return str(int(val))
    return f"{val:.4f}".rstrip("0").rstrip(".")


def extract_numbers(text: str) -> set[str]:
    out: set[str] = set()
    for m in _NUM_RE.finditer(text):
        n = _normalize_number(m.group())
        if n:
            out.add(n)
    return out


def numbers_from_facts(facts: dict | list) -> set[str]:
    """Kumpulkan semua angka (ternormalisasi) dari struktur FACTS."""
    acc: set[str] = set()

    def walk(node) -> None:  # noqa: ANN001
        if isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
        elif isinstance(node, str):
            acc.update(extract_numbers(node))
        elif isinstance(node, (int, float)):
            acc.update(extract_numbers(str(node)))

    walk(facts)
    return acc


def validate_numbers(text: str, facts: dict | list) -> tuple[bool, list[str]]:
    """True jika setiap angka di `text` ada di `facts`.

    Mengembalikan (valid, angka_yang_tidak_cocok).
    """
    allowed = numbers_from_facts(facts)
    used = extract_numbers(text)
    missing = sorted(n for n in used if n not in allowed)
    return (len(missing) == 0, missing)
