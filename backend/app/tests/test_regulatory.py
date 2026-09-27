"""Test aturan regulasi OJK (Fase 1)."""

from app.engine import regulatory as reg


def test_cap_tenor_6_boundary():
    # tenor tepat 6 bulan -> masih pakai cap 0,3%
    assert reg.cap_for(6) == (0.003, 0.003)


def test_cap_tenor_7_over_boundary():
    # tenor 7 bulan -> pindah ke cap 0,2%
    assert reg.cap_for(7) == (0.002, 0.002)


def test_cap_tenor_1():
    assert reg.cap_for(1) == (0.003, 0.003)


def test_above_cap_triggers_red():
    flags = reg.check_pinjol(2_000_000, 3, 0.005, income_monthly=6_000_000)
    codes = {f.code for f in flags}
    assert "ABOVE_OJK_CAP" in codes
    red = [f for f in flags if f.code == "ABOVE_OJK_CAP"][0]
    assert red.level == "red"


def test_at_cap_no_red():
    flags = reg.check_pinjol(2_000_000, 3, 0.003, income_monthly=6_000_000)
    assert all(f.code != "ABOVE_OJK_CAP" for f in flags)


def test_dsr_over_30_triggers_orange():
    # 3 juta pokok, tenor 3, 0.3%/hari -> cicilan ~1.27jt > 30% dari 3jt? income 3jt -> 42% -> flag
    flags = reg.check_pinjol(3_000_000, 3, 0.003, income_monthly=3_000_000)
    codes = {f.code for f in flags}
    assert "DSR_OVER_30" in codes


def test_dsr_under_30_no_flag():
    flags = reg.check_pinjol(1_000_000, 6, 0.001, income_monthly=10_000_000)
    assert all(f.code != "DSR_OVER_30" for f in flags)


def test_lock_cap_never_exceeded():
    # bunga astronomis -> dibatasi 100% pokok
    total = reg.total_fee(1_000_000, 0.05, 12)
    assert total == 1_000_000


def test_lock_cap_partial():
    total = reg.total_fee(1_000_000, 0.001, 3)
    assert total < 1_000_000
    assert total > 0


def test_penalty_above_cap():
    flags = reg.check_pinjol(1_000_000, 3, 0.001, 5_000_000, penalty_daily=0.01)
    assert any(f.code == "PENALTY_ABOVE_OJK_CAP" for f in flags)


def test_ruleset_from_assumptions_default_caps():
    rs = reg.ruleset_from_assumptions(None)
    assert rs["version"] == "SEOJK-19-2025"
    assert rs["dsr_cap"] == 0.30
    assert reg.cap_for(12, rs) == (0.002, 0.002)


def test_installment_flat():
    # (pokok + bunga) / tenor
    inst = reg.installment_for(1_200_000, 0.0, 3)
    assert abs(inst - 400_000) < 1e-6
