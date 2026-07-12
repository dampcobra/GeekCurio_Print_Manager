from geekcurio_print_manager.utils.formatting import format_duration_hm


# ── format_duration_hm: ceiling-to-minute rounding ───────────────────────────

def test_exact_minutes_unchanged():
    assert format_duration_hm(5400) == "1h 30m"   # 90m exactly


def test_seconds_remainder_rounds_up():
    assert format_duration_hm(6057) == "1h 41m"   # 1h 40m 57s


def test_one_second_over_rounds_up():
    assert format_duration_hm(6001) == "1h 41m"   # 1h 40m 01s


def test_sub_hour_rounds_up():
    assert format_duration_hm(2364) == "40m"       # 39m 24s


def test_sub_hour_exact_minutes():
    assert format_duration_hm(2400) == "40m"       # 40m 00s


def test_zero_seconds():
    assert format_duration_hm(0) == "0m"


def test_exactly_one_hour():
    assert format_duration_hm(3600) == "1h 00m"


def test_one_second_rounds_to_one_minute():
    assert format_duration_hm(1) == "1m"
