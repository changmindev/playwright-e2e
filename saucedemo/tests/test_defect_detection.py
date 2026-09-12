"""시나리오 6 — 결함 탐지.

앞선 시나리오와 **같은 검증**을 계정만 바꿔 돌린다.
정상 계정에서는 통과하고 결함 계정에서는 실패한다면, 그 차이가 곧 결함이다.

결함 계정 케이스는 `xfail(strict=True)` 로 고정한다. 이유는 두 가지다.
  · 이미 알고 있는 결함 때문에 전체 실행이 빨간불이 되면, 새로 생긴 결함이 묻힌다.
  · strict 이므로 **제품이 고쳐져서 통과해 버리면 그때는 실패로 뜬다.**
    결함이 사라진 사실도 자동으로 알림이 온다.

발견한 결함의 재현 절차·기대/실제는 docs/DEFECTS.md 에 정리했다.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import expect

from saucedemo.data.products import PRODUCT_COUNT, expected_order, name_of
from saucedemo.data.users import PROBLEM, STANDARD
from saucedemo.pages.cart_page import CartPage
from saucedemo.pages.checkout_page import CheckoutInfoPage
from saucedemo.pages.item_detail_page import ItemDetailPage

BACKPACK = "sauce-labs-backpack"

# 이 파일의 확인들은 이미 그려진 화면이 즉시 반응하는지를 본다.
# 결함이 있는 쪽에서 기본 상한(15초)을 그대로 기다릴 이유가 없어 짧게 둔다.
DEFECT_TIMEOUT_MS = 4_000


def for_both_users(defect_id: str, reason: str):
    """같은 검증을 정상 계정 / 결함 계정 두 번 돌리는 데코레이터.

    이름표를 `pytest.param(id=...)` 로 주지 않고 `ids=` 로 주는 이유:
    전자는 pytest 가 파라미터를 만드는 시점에 무조건 ascii 이스케이프해서
    실행 결과에 `\\uacb0\\ud568 \\uacc4\\uc815` 로 찍힌다. 후자만
    `disable_test_id_escaping...` 설정(pytest.ini)을 따라 한글 그대로 나온다.
    어느 쪽이 실패했는지 결과만 보고 알 수 있어야 한다.
    """
    return pytest.mark.parametrize(
        "user",
        [
            pytest.param(STANDARD),
            pytest.param(
                PROBLEM,
                marks=[
                    pytest.mark.defect,
                    pytest.mark.xfail(strict=True, reason=f"{defect_id} — {reason}"),
                ],
            ),
        ],
        ids=["정상 계정", "결함 계정"],
    )


@for_both_users("D-01", "상품 이미지 6건이 모두 404 대체 이미지로 나온다")
def test_상품마다_서로_다른_이미지가_노출된다(logged_in, user):
    inventory = logged_in(user)

    sources = inventory.image_sources()

    assert len(sources) == PRODUCT_COUNT
    assert len(set(sources)) == PRODUCT_COUNT, (
        f"고유 이미지 {len(set(sources))}건 / 상품 {PRODUCT_COUNT}건 — "
        f"중복 경로: {sorted(set(sources))}"
    )


@for_both_users("D-02", "정렬을 바꿔도 목록 순서가 그대로다")
def test_정렬을_바꾸면_목록_순서가_바뀐다(logged_in, user):
    inventory = logged_in(user)

    inventory.sort_by("za")

    expect(inventory.item_names).to_have_text(
        expected_order("za"), timeout=DEFECT_TIMEOUT_MS
    )


@for_both_users("D-03", "빼기 버튼을 눌러도 장바구니에서 제거되지 않는다")
def test_장바구니에서_빼면_담기_상태로_돌아온다(logged_in, user):
    inventory = logged_in(user)

    inventory.add_to_cart(BACKPACK)
    expect(inventory.cart_badge).to_have_text("1")

    inventory.remove_from_cart(BACKPACK)

    expect(inventory.cart_badge).to_have_count(0, timeout=DEFECT_TIMEOUT_MS)
    expect(inventory.add_button(BACKPACK)).to_be_visible(timeout=DEFECT_TIMEOUT_MS)


@for_both_users("D-04", "상품명 링크가 다른 상품 상세로 이동한다")
def test_목록에서_연_상세는_같은_상품이다(logged_in, user):
    inventory = logged_in(user)
    detail = ItemDetailPage(inventory.page)

    listed = inventory.names()
    mismatches = []

    for index, expected_name in enumerate(listed):
        inventory.open_detail_by_index(index)
        actual_name = detail.name_text()
        if actual_name != expected_name:
            mismatches.append(
                f"[{index}] 목록={expected_name!r} → 상세={actual_name!r} "
                f"(id={detail.item_id()})"
            )
        inventory.page.go_back()
        expect(inventory.items).to_have_count(PRODUCT_COUNT)

    assert not mismatches, "목록과 상세가 어긋난 항목:\n  " + "\n  ".join(mismatches)


@for_both_users("D-05", "체크아웃 Last Name 입력이 저장되지 않는다")
def test_체크아웃_입력값이_입력한_그대로_남는다(logged_in, user):
    inventory = logged_in(user)

    inventory.add_to_cart(BACKPACK)
    inventory.open_cart()
    CartPage(inventory.page).checkout()

    info = CheckoutInfoPage(inventory.page)
    expect(info.continue_button).to_be_visible()
    info.fill_form("창민", "최", "06236")

    assert info.entered_values() == ("창민", "최", "06236")


@for_both_users("D-04", "상품명 링크가 다른 상품 상세로 이동한다")
def test_상세로_들어가도_상품이_존재해야_한다(logged_in, user):
    """D-04 의 파생 영향.

    링크가 어긋나면서 마지막 상품은 존재하지 않는 id 로 이동한다.
    사용자에게는 'ITEM NOT FOUND' 가 그대로 노출된다."""
    inventory = logged_in(user)
    detail = ItemDetailPage(inventory.page)

    not_found = []
    for index in range(PRODUCT_COUNT):
        inventory.open_detail_by_index(index)
        if detail.name_text() == "ITEM NOT FOUND":
            not_found.append(f"[{index}] id={detail.item_id()}")
        inventory.page.go_back()
        expect(inventory.items).to_have_count(PRODUCT_COUNT)

    assert not not_found, "존재하지 않는 상품으로 이동한 항목: " + ", ".join(not_found)


@for_both_users("D-01", "이미지가 404 대체 이미지다")
def test_특정_상품의_이미지_경로에_상품이_식별된다(logged_in, user):
    """이미지가 화면에 뜨는지가 아니라, 그 상품의 이미지가 맞는지를 본다.

    404 대체 이미지도 정상적으로 렌더링되므로 to_be_visible 로는 잡히지 않는다."""
    inventory = logged_in(user)

    src = inventory.image_src(BACKPACK)

    assert "404" not in src, f"{name_of(BACKPACK)} 이미지가 대체 이미지다: {src}"
