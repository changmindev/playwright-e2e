"""시나리오 2 — 상품 정렬.

기대 순서는 화면에서 읽은 목록을 다시 정렬해 만들지 않는다.
카탈로그(data/products.py)에서 만든 고정 목록과 대조한다.
화면값을 자기 자신과 비교하면, 항목이 빠진 채 정렬만 맞아도 통과한다.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import expect

from saucedemo.data.products import CATALOG, PRODUCT_COUNT, expected_order
from saucedemo.pages.inventory_page import SORT_OPTIONS


def test_기본_진입시_이름_오름차순으로_보인다(inventory):
    expect(inventory.items).to_have_count(PRODUCT_COUNT)
    expect(inventory.item_names).to_have_text(expected_order("az"))


@pytest.mark.parametrize("option", list(SORT_OPTIONS), ids=list(SORT_OPTIONS.values()))
def test_정렬을_바꾸면_실제_순서가_그대로_바뀐다(inventory, option):
    inventory.sort_by(option)

    # to_have_text 는 목록 전체가 기대와 맞을 때까지 재시도한다.
    # 정렬 후 다시 그려지는 동안의 경합을 sleep 없이 그대로 흡수한다.
    expect(inventory.item_names).to_have_text(expected_order(option))


@pytest.mark.parametrize("option", list(SORT_OPTIONS), ids=list(SORT_OPTIONS.values()))
def test_정렬을_바꿔도_상품_구성과_가격은_변하지_않는다(inventory, option):
    """정렬은 순서만 바꾸는 동작이다. 항목이 사라지거나 가격이 달라지면
    정렬이 아니라 조회 조건을 건드리고 있다는 뜻이다."""
    inventory.sort_by(option)
    expect(inventory.item_names).to_have_text(expected_order(option))

    expected = {name: price for name, price in CATALOG.values()}
    actual = dict(zip(inventory.names(), inventory.prices()))

    assert actual == expected
