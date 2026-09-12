"""시나리오 1 — 로그인.

기법: 동등 분할(정상 / 잠김 / 미입력 / 자격증명 불일치).
실패는 "로그인이 안 된다"로 뭉뜽그리지 않고, 클래스마다 다른 메시지가
나가는지까지 본다. 사용자가 무엇을 고쳐야 할지 알 수 없으면 그것도 결함이다.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import expect

from saucedemo.data.products import PRODUCT_COUNT
from saucedemo.data.users import LOGIN_CASES, STANDARD
from saucedemo.pages.inventory_page import InventoryPage


def test_정상_계정으로_로그인하면_상품_목록으로_이동한다(login_page):
    login_page.login_as(STANDARD)

    inventory = InventoryPage(login_page.page)
    expect(login_page.page).to_have_url(InventoryPage.URL)
    expect(inventory.title_text).to_have_text("Products")
    expect(inventory.items).to_have_count(PRODUCT_COUNT)


@pytest.mark.parametrize(
    ("label", "username", "password", "expected_message"),
    LOGIN_CASES,
    ids=[case[0] for case in LOGIN_CASES],
)
def test_로그인_실패시_원인별로_다른_메시지가_노출된다(
    login_page, label, username, password, expected_message
):
    login_page.submit(username, password)

    expect(login_page.error).to_have_text(expected_message)
    # 화면 전환이 없어야 한다. 메시지만 띄우고 넘어가 버리면 그게 더 큰 결함이다.
    expect(login_page.page).to_have_url(login_page.URL)


def test_로그인_실패_후_다시_시도하면_성공한다(login_page):
    """실패 상태가 남아 다음 시도를 막지 않는지 확인한다."""
    login_page.submit(STANDARD.username, "wrong_password")
    expect(login_page.error).to_be_visible()

    login_page.login_as(STANDARD)

    expect(login_page.page).to_have_url(InventoryPage.URL)
