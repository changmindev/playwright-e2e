"""시나리오 3 — 장바구니.

담기/빼기 자체보다 "화면을 이동했다 돌아와도 상태가 남는가"가 중요하다.
목록·상세·장바구니가 각자 다른 상태를 들고 있으면 사용자는 결제 직전에야 알게 된다.
"""

from __future__ import annotations

from playwright.sync_api import expect

from saucedemo.data.products import name_of, price_of
from saucedemo.pages.cart_page import CartPage

BACKPACK = "sauce-labs-backpack"
BIKE_LIGHT = "sauce-labs-bike-light"


def test_담으면_뱃지_수량이_증가한다(inventory):
    # 빈 장바구니에서는 뱃지가 DOM 에 없다. "0" 이 아니라 부재가 정상 상태다.
    expect(inventory.cart_badge).to_have_count(0)

    inventory.add_to_cart(BACKPACK)
    expect(inventory.cart_badge).to_have_text("1")

    inventory.add_to_cart(BIKE_LIGHT)
    expect(inventory.cart_badge).to_have_text("2")


def test_빼면_뱃지_수량이_감소하고_비면_사라진다(inventory):
    inventory.add_to_cart(BACKPACK)
    inventory.add_to_cart(BIKE_LIGHT)
    expect(inventory.cart_badge).to_have_text("2")

    inventory.remove_from_cart(BIKE_LIGHT)
    expect(inventory.cart_badge).to_have_text("1")

    inventory.remove_from_cart(BACKPACK)
    expect(inventory.cart_badge).to_have_count(0)


def test_담은_상품은_버튼이_빼기로_바뀐다(inventory):
    """같은 자리의 버튼이 담기 ↔ 빼기로 토글되는지. 두 버튼이 동시에
    보이거나 둘 다 사라지는 상태가 있으면 안 된다."""
    expect(inventory.add_button(BACKPACK)).to_be_visible()
    expect(inventory.remove_button(BACKPACK)).to_have_count(0)

    inventory.add_to_cart(BACKPACK)

    expect(inventory.remove_button(BACKPACK)).to_be_visible()
    expect(inventory.add_button(BACKPACK)).to_have_count(0)


def test_장바구니_화면에_담은_상품과_가격이_그대로_나온다(inventory):
    inventory.add_to_cart(BACKPACK)
    inventory.add_to_cart(BIKE_LIGHT)
    inventory.open_cart()

    cart = CartPage(inventory.page)

    expect(cart.items).to_have_count(2)
    assert sorted(cart.names()) == sorted([name_of(BACKPACK), name_of(BIKE_LIGHT)])
    assert sorted(cart.prices()) == sorted([price_of(BACKPACK), price_of(BIKE_LIGHT)])


def test_상세_화면을_다녀와도_담은_상태가_유지된다(inventory):
    inventory.add_to_cart(BACKPACK)
    expect(inventory.cart_badge).to_have_text("1")

    inventory.open_detail_by_name(name_of(BACKPACK))
    inventory.page.go_back()

    expect(inventory.cart_badge).to_have_text("1")
    expect(inventory.remove_button(BACKPACK)).to_be_visible()


def test_장바구니에서_뺀_결과가_목록에도_반영된다(inventory):
    """두 화면이 같은 상태를 보는지 확인한다. 장바구니에서만 빠지고
    목록에는 담긴 채로 남는 것이 전형적인 상태 분리 결함이다."""
    inventory.add_to_cart(BACKPACK)
    inventory.open_cart()

    cart = CartPage(inventory.page)
    cart.remove(BACKPACK)
    expect(cart.items).to_have_count(0)

    cart.continue_shopping_button.click()

    expect(inventory.cart_badge).to_have_count(0)
    expect(inventory.add_button(BACKPACK)).to_be_visible()
