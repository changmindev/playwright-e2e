"""값이 물리적으로 가능한 범위인가.

'화면에 숫자가 떴다'는 통과 조건이 아니다. 파싱이 어긋나면
습도 자리에서 풍속을 읽고도 숫자라는 이유로 통과할 수 있다.
"""

from __future__ import annotations

import pytest

from naver_weather.data.regions import (
    HUMIDITY_RANGE,
    PRECIP_MM_MAX,
    PRECIP_PROB_RANGE,
    TEMP_MAX_C,
    TEMP_MIN_C,
    WIND_MS_MAX,
)

pytestmark = pytest.mark.range


def test_현재기온이_국내_관측_범위_안에_있다(snapshot):
    t = snapshot.current.temperature_c
    assert TEMP_MIN_C <= t <= TEMP_MAX_C, f"기온 {t}° — 국내 극값 범위를 벗어남"


def test_습도가_백분율이다(snapshot):
    h = snapshot.current.humidity_pct
    lo, hi = HUMIDITY_RANGE
    assert lo <= h <= hi, f"습도 {h}% — 0~100 범위 밖"


def test_풍속이_현실적인_값이다(snapshot):
    w = snapshot.current.wind_ms
    assert 0 <= w <= WIND_MS_MAX, f"풍속 {w}m/s — 태풍 기록 범위를 벗어남"


def test_강수확률이_전부_백분율이다(snapshot):
    lo, hi = PRECIP_PROB_RANGE
    bad = [p for p in snapshot.current.precip_prob_pct if not lo <= p <= hi]
    assert not bad, f"강수확률 범위 밖: {bad}"


def test_시간별_값이_전부_범위_안에_있다(snapshot):
    """한 칸이라도 어긋나면 어느 시간대인지 같이 알려 준다.

    '실패'만 알려 주는 테스트는 결국 사람이 다시 브라우저를 열게 만든다.
    """
    problems: list[str] = []
    for p in snapshot.hourly:
        if p.temperature_c is not None and not TEMP_MIN_C <= p.temperature_c <= TEMP_MAX_C:
            problems.append(f"{p.hour_label} 기온 {p.temperature_c}°")
        if p.precip_prob_pct is not None and not 0 <= p.precip_prob_pct <= 100:
            problems.append(f"{p.hour_label} 강수확률 {p.precip_prob_pct}%")
        if p.precip_mm is not None and not 0 <= p.precip_mm <= PRECIP_MM_MAX:
            problems.append(f"{p.hour_label} 강수량 {p.precip_mm}mm")
        if p.humidity_pct is not None and not 0 <= p.humidity_pct <= 100:
            problems.append(f"{p.hour_label} 습도 {p.humidity_pct}%")
    assert not problems, "범위를 벗어난 값:\n  " + "\n  ".join(problems[:10])
