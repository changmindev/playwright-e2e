"""상품 기대값.

정렬·금액 검증의 기준이 되는 값이다. 화면에서 읽은 값끼리 비교하면
둘 다 틀렸을 때 통과해 버리므로, 비교 기준은 코드에 고정해 둔다.
"""

from __future__ import annotations

from decimal import Decimal

# data-test 속성에 쓰이는 슬러그 → 표시 이름·가격
CATALOG: dict[str, tuple[str, Decimal]] = {
    "sauce-labs-backpack": ("Sauce Labs Backpack", Decimal("29.99")),
    "sauce-labs-bike-light": ("Sauce Labs Bike Light", Decimal("9.99")),
    "sauce-labs-bolt-t-shirt": ("Sauce Labs Bolt T-Shirt", Decimal("15.99")),
    "sauce-labs-fleece-jacket": ("Sauce Labs Fleece Jacket", Decimal("49.99")),
    "sauce-labs-onesie": ("Sauce Labs Onesie", Decimal("7.99")),
    "test.allthethings()-t-shirt-(red)": (
        "Test.allTheThings() T-Shirt (Red)",
        Decimal("15.99"),
    ),
}

PRODUCT_COUNT = len(CATALOG)

# 세율 8%. 2회 실측으로 확인 —
#   $39.98 → $3.20   ($39.98 × 0.08 = $3.1984)
#   $73.97 → $5.92   ($73.97 × 0.08 = $5.9176)
# 둘 다 소수점 셋째 자리에서 반올림(ROUND_HALF_UP)한 값과 일치한다.
TAX_RATE = Decimal("0.08")


def name_of(slug: str) -> str:
    return CATALOG[slug][0]


def price_of(slug: str) -> Decimal:
    return CATALOG[slug][1]


def expected_order(option: str) -> list[str]:
    """정렬 옵션별 기대 순서를 카탈로그에서 직접 만든다.

    화면에서 읽은 목록을 다시 정렬해 비교하면, 제품이 항목을 빠뜨린 채 정렬만
    맞게 줘도 통과한다. 기준 목록은 코드가 들고 있어야 한다.

    가격이 같은 항목(Bolt T-Shirt · Test.allTheThings, 둘 다 $15.99)의 순서는
    실측 결과 카탈로그 순서가 유지된다. 파이썬 sorted 가 안정 정렬이라
    key 만 지정하면 같은 결과가 나온다 — reversed() 를 쓰면 어긋난다.
    """
    items = list(CATALOG.values())
    if option == "az":
        return [name for name, _ in sorted(items, key=lambda i: i[0])]
    if option == "za":
        return [name for name, _ in sorted(items, key=lambda i: i[0], reverse=True)]
    if option == "lohi":
        return [name for name, _ in sorted(items, key=lambda i: i[1])]
    if option == "hilo":
        return [name for name, _ in sorted(items, key=lambda i: -i[1])]
    raise ValueError(f"알 수 없는 정렬 옵션: {option}")
