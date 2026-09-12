"""화면이 우리와 맺은 계약이 지켜지는가.

여기서 깨지면 값이 틀린 게 아니라 **화면 구조가 바뀐 것**이다.
둘을 같은 파일에 두지 않는 이유는, 실패했을 때 어느 쪽인지 바로 갈리게 하기 위해서다.
"""

from __future__ import annotations

import pytest

from naver_weather.data.regions import MIN_HOURLY_ROWS

pytestmark = pytest.mark.contract


def test_검색한_지역의_행정구역명이_그대로_나온다(snapshot):
    """'강원도'로 검색해도 화면은 '강원특별자치도'를 말해야 한다.

    기대값을 검색어에서 만들지 않고 data/regions.py 에 따로 적어 둔 이유다.
    검색어를 그대로 기대값으로 쓰면 제품이 옛 행정구역명을 노출해도 통과한다.
    """
    assert snapshot.current.title == snapshot.region.expected_title


def test_어디서_잰_값인지_화면이_밝힌다(snapshot):
    """'경기도 19.2°'만으로는 검증이 안 된다. 경기도 어디인지가 있어야 한다."""
    point = snapshot.current.observation_point
    assert point.endswith("기준"), f"관측 지점 표기 형식이 바뀜 — {point!r}"
    assert len(point) > len("기준"), "관측 지점명이 비어 있음"


def test_상세로_넘어갈_지역코드를_카드가_들고_있다(snapshot):
    code = snapshot.current.region_code
    assert code.isdigit() and len(code) == 8, f"지역 코드 형식이 바뀜 — {code!r}"


def test_현재_관측값이_모두_채워져_있다(snapshot):
    c = snapshot.current
    assert c.condition, "날씨 상태 문구가 비어 있음"
    assert c.wind_label.endswith("풍"), f"풍향 표기가 아님 — {c.wind_label!r}"
    assert c.precip_prob_pct, "강수확률이 한 건도 없음"


def test_시간별_예보가_최소_시간_이상_온다(snapshot):
    n = len(snapshot.hourly)
    assert n >= MIN_HOURLY_ROWS, f"시간별 예보 {n}건 — 최소 {MIN_HOURLY_ROWS}건 필요"


def test_시간별_각_칸에_필수값이_있다(snapshot):
    """기온·강수확률·강수량은 값이 없으면 안 된다.

    적설은 제외한다 — 비 오는 날 '-' 인 것이 정상이라 필수로 걸면 오탐이 된다.
    """
    missing = [
        f"{p.hour_label}({'기온' if p.temperature_c is None else ''}"
        f"{'강수확률' if p.precip_prob_pct is None else ''}"
        f"{'강수량' if p.precip_mm is None else ''})"
        for p in snapshot.hourly
        if p.temperature_c is None or p.precip_prob_pct is None or p.precip_mm is None
    ]
    assert not missing, "필수값이 빈 시간대: " + ", ".join(missing[:10])
