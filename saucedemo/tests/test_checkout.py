"""시나리오 4·5 — 체크아웃 필수값 검증과 금액 계산.

금액은 화면에 나온 소계·세액·합계를 서로 비교하지 않는다.
상품 가격에서 소계를 직접 더하고, 세액을 직접 계산해 대조한다.
화면값끼리 맞춰 보면 서버가 셋 다 틀리게 줘도 통과한다.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import expect

from saucedemo.data.products import name_of, price_of
from saucedemo.pages.cart_page import CartPage
from saucedemo.pages.checkout_page import (
    CheckoutCompletePage,
    CheckoutInfoPage,
    CheckoutSummaryPage,
)

BACKPACK = "sauce-labs-backpack"
BIKE_LIGHT = "sauce-labs-bike-light"
FLEECE = "sauce-labs-fleece-jacket"

VALID_FORM = ("창민", "최", "06236")


@pytest.fixture()
def checkout_info(inventory) -> CheckoutInfoPage:
    """상품 2개를 담고 정보 입력 화면까지 진입한 상태."""
    inventory.add_to_cart(BACKPACK)
    inventory.add_to_cart(BIKE_LIGHT)
    inventory.open_cart()
    CartPage(inventory.page).checkout()

    info = CheckoutInfoPage(inventory.page)
    expect(info.continue_button).to_be_visible()
    return info


# ── 시나리오 4 · 필수값 ──────────────────────────────────────────
@pytest.mark.parametrize(
    ("label", "first", "last", "postal", "expected_message"),
    [
        ("이름 누락", "", "최", "06236", "Error: First Name is required"),
        ("성 누락", "창민", "", "06236", "Error: Last Name is required"),
        ("우편번호 누락", "창민", "최", "", "Error: Postal Code is required"),
    ],
    ids=["이름 누락", "성 누락", "우편번호 누락"],
)
def test_필수값이_비면_진행이_차단되고_해당_항목이_지목된다(
    checkout_info, label, first, last, postal, expected_message
):
    checkout_info.submit(first, last, postal)

    expect(checkout_info.error).to_have_text(expected_message)
    expect(checkout_info.page).to_have_url(CheckoutInfoPage.URL)


def test_공백만_입력한_경우는_통과된다(checkout_info):
    """현재 제품은 공백 한 칸을 유효한 입력으로 받아들인다.

    막아야 한다고 단정하지 않고, 지금 동작이 무엇인지를 고정해 둔다.
    정책이 바뀌면 이 테스트가 먼저 깨져서 알려 준다."""
    checkout_info.submit(" ", " ", " ")

    expect(checkout_info.page).to_have_url(CheckoutSummaryPage.URL)


def test_모든_필수값을_채우면_요약_화면으로_넘어간다(checkout_info):
    checkout_info.submit(*VALID_FORM)

    summary = CheckoutSummaryPage(checkout_info.page)
    expect(checkout_info.page).to_have_url(CheckoutSummaryPage.URL)
    expect(summary.title_text).to_have_text("Checkout: Overview")


# ── 시나리오 5 · 금액 계산 ───────────────────────────────────────
def test_소계는_담은_상품_가격의_합과_일치한다(checkout_info):
    checkout_info.submit(*VALID_FORM)
    summary = CheckoutSummaryPage(checkout_info.page)

    expected_subtotal = price_of(BACKPACK) + price_of(BIKE_LIGHT)

    assert sorted(summary.names()) == sorted([name_of(BACKPACK), name_of(BIKE_LIGHT)])
    assert summary.subtotal() == expected_subtotal


def test_세액과_합계가_소계로부터_다시_계산한_값과_일치한다(checkout_info):
    checkout_info.submit(*VALID_FORM)
    summary = CheckoutSummaryPage(checkout_info.page)

    subtotal = summary.subtotal()
    expected_tax = CheckoutSummaryPage.expected_tax(subtotal)

    assert summary.tax() == expected_tax
    assert summary.total() == subtotal + expected_tax


def test_상품_구성이_달라져도_금액_계산_규칙은_같다(inventory):
    """반올림이 걸리는 다른 조합으로 한 번 더 확인한다.
    $73.97 × 0.08 = $5.9176 → $5.92 로 올림되는 케이스."""
    for slug in (FLEECE, "sauce-labs-onesie", "sauce-labs-bolt-t-shirt"):
        inventory.add_to_cart(slug)
    inventory.open_cart()
    CartPage(inventory.page).checkout()

    info = CheckoutInfoPage(inventory.page)
    info.submit(*VALID_FORM)
    summary = CheckoutSummaryPage(inventory.page)

    subtotal = summary.subtotal()
    assert subtotal == sum(
        price_of(s) for s in (FLEECE, "sauce-labs-onesie", "sauce-labs-bolt-t-shirt")
    )
    assert summary.tax() == CheckoutSummaryPage.expected_tax(subtotal)
    assert summary.total() == subtotal + summary.tax()


def test_주문을_완료하면_완료_화면이_뜨고_장바구니가_비워진다(checkout_info):
    checkout_info.submit(*VALID_FORM)
    summary = CheckoutSummaryPage(checkout_info.page)
    summary.finish()

    complete = CheckoutCompletePage(checkout_info.page)
    expect(complete.page).to_have_url(CheckoutCompletePage.URL)
    expect(complete.header).to_have_text("Thank you for your order!")
    # 결제가 끝났는데 장바구니가 남아 있으면 중복 주문으로 이어진다.
    expect(complete.cart_badge).to_have_count(0)
