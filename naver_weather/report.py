"""수집 결과 → 단일 HTML 리포트.

차트는 외부 라이브러리 없이 인라인 SVG 로 그린다.
리포트가 링크 하나로 열려야 하고, 열리는 곳이 사내 망일 수도 있기 때문이다.
"""

from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path

from naver_weather.collector import RegionSnapshot, collect_all, save_json

# 검증된 3색 카테고리 팔레트(light / dark 각각 다른 단계).
SERIES = [
    {"key": "seoul", "label": "서울", "light": "#2a78d6", "dark": "#3987e5"},
    {"key": "gangwon", "label": "강원", "light": "#eb6834", "dark": "#d95926"},
    {"key": "gyeonggi", "label": "경기", "light": "#1baf7a", "dark": "#199e70"},
]
HOURS_SHOWN = 24

W, H = 720, 190
PAD_L, PAD_R, PAD_T, PAD_B = 34, 58, 16, 26


def _scale(values: list[float], lo: float, hi: float) -> callable:
    span = hi - lo or 1.0

    def y(v: float) -> float:
        return PAD_T + (H - PAD_T - PAD_B) * (1 - (v - lo) / span)

    return y


def _x(i: int, n: int) -> float:
    inner = W - PAD_L - PAD_R
    return PAD_L + (inner * i / max(n - 1, 1))


def _line_chart(
    snapshots: dict[str, RegionSnapshot],
    *,
    field: str,
    unit: str,
    chart_id: str,
    fixed_range: tuple[float, float] | None = None,
) -> str:
    """시간축 꺾은선. 시리즈 끝에 직접 라벨을 붙인다(범례만으로 두지 않는다)."""
    series_values: dict[str, list[float]] = {}
    for s in SERIES:
        pts = snapshots[s["key"]].hourly[:HOURS_SHOWN]
        series_values[s["key"]] = [getattr(p, field) or 0.0 for p in pts]

    flat = [v for vs in series_values.values() for v in vs]
    if fixed_range is not None:
        # 백분율은 축을 0~100 으로 고정한다. 데이터에 맞춰 늘리면
        # 0~30% 인 날이 0~100% 인 날과 똑같이 가득 찬 그래프로 보인다.
        lo, hi = fixed_range
    else:
        lo, hi = min(flat), max(flat)
        if hi - lo < 4:
            hi = lo + 4  # 값이 평평한 날 선이 눌려 붙어 보이는 것을 막는다
        pad = (hi - lo) * 0.15
        lo, hi = lo - pad, hi + pad
    y = _scale(flat, lo, hi)

    hours = [p.hour_label for p in snapshots["seoul"].hourly[:HOURS_SHOWN]]
    n = len(hours)

    grid, ticks = [], []
    for frac in (0, 0.5, 1):
        val = lo + (hi - lo) * (1 - frac)
        yy = PAD_T + (H - PAD_T - PAD_B) * frac
        grid.append(f'<line class="grid" x1="{PAD_L}" y1="{yy:.1f}" x2="{W - PAD_R}" y2="{yy:.1f}"/>')
        ticks.append(f'<text class="tick" x="{PAD_L - 7}" y="{yy + 3.5:.1f}" text-anchor="end">{val:.0f}</text>')

    for i, h in enumerate(hours):
        if i % 4 == 0 or i == n - 1:
            ticks.append(
                f'<text class="tick" x="{_x(i, n):.1f}" y="{H - 8}" text-anchor="middle">'
                f'{html.escape(h.removesuffix("시"))}</text>'
            )

    paths, ends, hits = [], [], []
    # 끝점 라벨이 겹치면 이름이 서로를 덮어 어느 선인지 읽을 수 없게 된다.
    # 값은 그대로 두고 **라벨 위치만** 최소 간격만큼 밀어 둔다.
    end_ys = sorted(((y(series_values[s["key"]][-1]), i) for i, s in enumerate(SERIES)))
    label_y: dict[int, float] = {}
    last = -999.0
    for yy, i in end_ys:
        placed = max(yy, last + 13)
        label_y[i] = placed
        last = placed

    for idx, s in enumerate(SERIES, start=1):
        vs = series_values[s["key"]]
        d = " ".join(
            ("M" if i == 0 else "L") + f"{_x(i, n):.1f} {y(v):.1f}" for i, v in enumerate(vs)
        )
        paths.append(f'<path class="ln s{idx}" d="{d}"/>')
        ex, ey = _x(n - 1, n), y(vs[-1])
        ly = label_y[idx - 1]
        leader = (
            f'<line class="leader" x1="{ex + 5:.1f}" y1="{ey:.1f}" x2="{ex + 10:.1f}" y2="{ly:.1f}"/>'
            if abs(ly - ey) > 1
            else ""
        )
        ends.append(
            f'{leader}<circle class="dot s{idx}" cx="{ex:.1f}" cy="{ey:.1f}" r="4"/>'
            f'<text class="endlabel" x="{ex + 13:.1f}" y="{ly + 4:.1f}">{s["label"]}</text>'
        )

    for i in range(n):
        xx = _x(i, n)
        payload = " · ".join(
            f'{s["label"]} {series_values[s["key"]][i]:g}{unit}' for s in SERIES
        )
        hits.append(
            f'<rect class="hit" x="{xx - (W / n) / 2:.1f}" y="{PAD_T}" width="{W / n:.1f}" '
            f'height="{H - PAD_T - PAD_B}" data-label="{html.escape(hours[i])}" '
            f'data-body="{html.escape(payload)}"/>'
            f'<line class="cross" x1="{xx:.1f}" y1="{PAD_T}" x2="{xx:.1f}" y2="{H - PAD_B}"/>'
        )

    return f"""<div class="chart" id="{chart_id}">
  <svg viewBox="0 0 {W} {H}" role="img" aria-label="시간별 {field} 꺾은선 차트">
    {''.join(grid)}{''.join(ticks)}{''.join(paths)}{''.join(ends)}
    <g class="hits">{''.join(hits)}</g>
  </svg>
  <div class="tip" hidden><b></b><span></span></div>
</div>"""


def _stat_cards(snapshots: dict[str, RegionSnapshot]) -> str:
    cards = []
    for idx, s in enumerate(SERIES, start=1):
        snap = snapshots[s["key"]]
        c = snap.current
        rain = snap.total_precip_mm
        rain_state = "비 예보 있음" if rain > 0 else "24시간 내 강수 없음"
        cards.append(f"""<article class="card">
  <header><span class="swatch s{idx}"></span><h3>{html.escape(c.title)}</h3></header>
  <p class="point">{html.escape(c.observation_point)}</p>
  <div class="big"><b>{c.temperature_c:.1f}</b><span>°C</span><em>{html.escape(c.condition)}</em></div>
  <dl>
    <div><dt>체감</dt><dd>{c.feels_like_c:.1f}°</dd></div>
    <div><dt>습도</dt><dd>{c.humidity_pct:.0f}%</dd></div>
    <div><dt>{html.escape(c.wind_label)}</dt><dd>{c.wind_ms:.1f}m/s</dd></div>
    <div><dt>최대 강수확률</dt><dd>{snap.max_precip_prob:.0f}%</dd></div>
  </dl>
  <p class="rain"><b>{rain:.1f}mm</b> <span>{rain_state}</span></p>
</article>""")
    return "".join(cards)


def _table(snapshots: dict[str, RegionSnapshot]) -> str:
    """표 보기. 차트만 두면 색으로만 구분되는 정보가 생긴다."""
    hours = [p.hour_label for p in snapshots["seoul"].hourly[:HOURS_SHOWN]]
    head = "".join(f"<th>{html.escape(h)}</th>" for h in hours)
    rows = []
    for idx, s in enumerate(SERIES, start=1):
        pts = snapshots[s["key"]].hourly[:HOURS_SHOWN]
        rows.append(
            f'<tr><th scope="row"><span class="swatch s{idx}"></span>{s["label"]} 기온</th>'
            + "".join(f"<td>{(p.temperature_c or 0):.0f}°</td>" for p in pts)
            + "</tr>"
        )
        rows.append(
            f'<tr class="sub"><th scope="row">{s["label"]} 강수량</th>'
            + "".join(f"<td>{(p.precip_mm or 0):g}</td>" for p in pts)
            + "</tr>"
        )
    return f"""<div class="tablewrap"><table>
<caption>시간별 기온(°C)과 강수량(mm) — 앞 {HOURS_SHOWN}시간</caption>
<thead><tr><th scope="col">지역</th>{head}</tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>"""


def build_html(snapshots: dict[str, RegionSnapshot], template: Path) -> str:
    any_snap = next(iter(snapshots.values()))
    stamp = datetime.fromisoformat(any_snap.collected_at).strftime("%Y-%m-%d %H:%M")
    total_rain = sum(s.total_precip_mm for s in snapshots.values())
    return (
        template.read_text(encoding="utf-8")
        .replace("{{COLLECTED_AT}}", stamp)
        .replace("{{CARDS}}", _stat_cards(snapshots))
        .replace("{{CHART_TEMP}}", _line_chart(snapshots, field="temperature_c", unit="°", chart_id="c-temp"))
        .replace("{{CHART_PROB}}", _line_chart(snapshots, field="precip_prob_pct", unit="%", chart_id="c-prob", fixed_range=(0, 100)))
        .replace("{{TABLE}}", _table(snapshots))
        .replace("{{RAIN_TOTAL}}", f"{total_rain:.1f}")
        .replace("{{HOURS}}", str(HOURS_SHOWN))
    )


if __name__ == "__main__":
    from playwright.sync_api import sync_playwright

    from naver_weather.conftest import USER_AGENT

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(locale="ko-KR", timezone_id="Asia/Seoul", user_agent=USER_AGENT)
        pg = ctx.new_page()
        pg.set_default_timeout(20_000)
        pg.set_default_navigation_timeout(45_000)
        snaps = collect_all(pg)
        browser.close()

    by_key = {s.region.key: s for s in snaps}
    save_json(snaps, Path("out/snapshot.json"))
    out = Path("out/report.html")
    # 템플릿은 모듈 옆에 있다. CWD 기준으로 찾으면 저장소 루트에서 돌릴 때 못 찾는다.
    template = Path(__file__).resolve().parent / "report_template.html"
    out.write_text(build_html(by_key, template), encoding="utf-8")
    print(json.dumps({s.current.title: s.current.temperature_c for s in snaps}, ensure_ascii=False))
    print(f"→ {out}")
