"""공통 파싱 유틸.

화면 문자열 → 숫자 변환은 전부 여기를 지난다.
테스트마다 `replace("°","")` 를 흩어 놓으면, 단위가 바뀌었을 때
고칠 곳이 몇 군데인지 아무도 모르게 된다.
"""

from __future__ import annotations

import re

from playwright.sync_api import Page

NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


class ParseError(ValueError):
    """화면 문자열에서 값을 못 뽑았을 때.

    None 을 돌려주지 않는 이유: None 은 '비가 안 온다'로 읽힐 수 있다.
    '값이 없다'와 '읽지 못했다'는 다른 사실이라 예외로 구분한다.
    """


def to_number(text: str | None, *, field: str) -> float:
    """'22.2°' · '64%' · '1.5m/s' → 22.2 / 64.0 / 1.5"""
    if text is None:
        raise ParseError(f"{field}: 요소는 있으나 텍스트가 없음")
    m = NUMBER.search(text.replace(",", ""))
    if not m:
        raise ParseError(f"{field}: 숫자를 찾지 못함 — 원문 {text!r}")
    return float(m.group())


def to_number_or_none(text: str | None) -> float | None:
    """표의 '-' 처럼 **값이 없는 것이 정상**인 칸에만 쓴다.

    적설이 대표적이다. 비 오는 날 적설이 '-' 인 것은 결함이 아니다.
    """
    if text is None:
        return None
    t = text.strip()
    if t in {"", "-", "--"}:
        return None
    m = NUMBER.search(t.replace(",", ""))
    return float(m.group()) if m else None


class BasePage:
    def __init__(self, page: Page) -> None:
        self.page = page
