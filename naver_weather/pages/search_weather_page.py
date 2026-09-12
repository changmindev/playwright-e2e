"""네이버 검색 결과의 날씨 카드 (search.naver.com).

여기서 읽는 것은 **현재 관측값**이다.
시간별 예보·강수량은 다음 화면(TodayPage)이 담당한다.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from urllib.parse import quote

from playwright.sync_api import Page, expect

from naver_weather.pages.base_page import BasePage, ParseError, to_number

SEARCH_URL = "https://search.naver.com/search.naver?query={q}"

# 카드 안의 정의 목록(dt.term → dd). 라벨이 바뀌면 여기만 고친다.
TERM_FEELS_LIKE = "체감"
TERM_HUMIDITY = "습도"
TERM_PRECIP_PROB = "강수확률"


@dataclass
class CurrentWeather:
    region_key: str
    query: str
    title: str          # 화면이 말하는 행정구역명
    observation_point: str  # '중구 을지로1가 기준' — 어디서 잰 값인지
    region_code: str    # 상세 페이지로 넘어갈 때 쓰는 지역 코드
    temperature_c: float
    condition: str      # 흐림 · 맑음 …
    feels_like_c: float
    humidity_pct: float
    wind_ms: float
    wind_label: str     # 북동풍
    precip_prob_pct: list[float]  # 오전·오후 등 카드가 주는 순서 그대로

    def as_dict(self) -> dict:
        return asdict(self)


class SearchWeatherPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.card = page.locator("div.weather_info").first
        self.title = page.locator("h2.title").first
        self.title_area = page.locator(".title_area").first
        self.temperature = page.locator(".temperature_text").first
        self.terms = page.locator("dt.term")

    # ── 이동 ────────────────────────────────────────────────
    def open(self, query: str) -> "SearchWeatherPage":
        self.page.goto(SEARCH_URL.format(q=quote(query)), wait_until="domcontentloaded")
        # 카드가 그려질 때까지 기다린다. sleep 을 넣지 않는다 —
        # 조건이 충족되는 즉시 넘어가야 느린 날에도 깨지지 않는다.
        expect(self.temperature).to_be_visible()
        return self

    # ── 읽기 ────────────────────────────────────────────────
    def region_code(self) -> str:
        """카드가 링크로 들고 있는 지역 코드.

        이 코드로 상세 페이지 주소를 만든다. 주소를 손으로 적어 두지 않는 이유는,
        **화면이 실제로 가리키는 곳**을 따라가야 링크가 어긋났을 때 잡히기 때문이다.
        """
        href = self.page.locator("a[href*='weather.naver.com/map/']").first.get_attribute("href")
        if not href:
            raise ParseError("지역 코드: weather.naver.com 링크를 찾지 못함")
        code = href.rstrip("/").split("/")[-1].split("?")[0]
        if not code.isdigit():
            raise ParseError(f"지역 코드가 숫자가 아님 — {code!r}")
        return code

    def _term_values(self, label: str) -> list[str]:
        """dt.term 의 라벨로 찾아 바로 뒤 dd 를 읽는다.

        위치(n번째 dd)로 읽지 않는다. 항목이 하나 추가되는 순간
        **테스트는 통과하는데 다른 값을 보고 있는** 상태가 되기 때문이다.
        """
        return self.page.evaluate(
            """(label) => [...document.querySelectorAll('dt.term')]
                 .filter(dt => dt.textContent.trim().startsWith(label))
                 .map(dt => dt.nextElementSibling ? dt.nextElementSibling.textContent.trim() : null)
                 .filter(v => v !== null)""",
            label,
        )

    def _wind(self) -> tuple[str, float]:
        """'북동풍 → 1.5m/s'. 라벨 자체가 풍향이라 라벨과 값을 같이 돌려준다."""
        pair = self.page.evaluate(
            """() => {
                 const dt = [...document.querySelectorAll('dt.term')]
                   .find(d => /풍$/.test(d.textContent.trim()));
                 return dt ? [dt.textContent.trim(), dt.nextElementSibling.textContent.trim()] : null;
               }"""
        )
        if not pair:
            raise ParseError("풍향·풍속: dt.term 에서 '…풍' 항목을 찾지 못함")
        return pair[0], to_number(pair[1], field="풍속")

    def read(self, region_key: str, query: str) -> CurrentWeather:
        title_text = self.title_area.inner_text()
        # '서울특별시 / 서울특별시 / 중구 을지로1가 기준' 중 마지막 줄이 관측 지점이다.
        observation = title_text.strip().splitlines()[-1].strip()

        wind_label, wind_ms = self._wind()
        probs = [to_number(v, field="강수확률") for v in self._term_values(TERM_PRECIP_PROB)]
        if not probs:
            raise ParseError("강수확률 항목이 하나도 없음")

        feels = self._term_values(TERM_FEELS_LIKE)
        humid = self._term_values(TERM_HUMIDITY)
        if not feels or not humid:
            raise ParseError(f"체감/습도 누락 — 체감 {feels} · 습도 {humid}")

        return CurrentWeather(
            region_key=region_key,
            query=query,
            title=self.title.inner_text().strip(),
            observation_point=observation,
            region_code=self.region_code(),
            temperature_c=to_number(self.temperature.inner_text(), field="현재기온"),
            condition=self._condition(),
            feels_like_c=to_number(feels[0], field="체감"),
            humidity_pct=to_number(humid[0], field="습도"),
            wind_ms=wind_ms,
            wind_label=wind_label,
            precip_prob_pct=probs,
        )

    def _condition(self) -> str:
        """'흐림' 같은 날씨 상태.

        아이콘 이미지가 아니라 대체 텍스트를 읽는다. 아이콘만 보면
        그림이 틀려도 알 수 없고, 스크린리더 사용자가 받는 값과도 달라진다.
        """
        text = self.card.inner_text()
        for line in (ln.strip() for ln in text.splitlines()):
            if line and "온도" not in line and "오늘" not in line and not any(c.isdigit() for c in line):
                return line
        raise ParseError("날씨 상태 문구를 찾지 못함")
