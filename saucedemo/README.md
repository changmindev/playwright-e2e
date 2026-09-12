# saucedemo — Swag Labs 결함 탐지 E2E

> [playwright-e2e](../README.md) 저장소의 스위트 하나입니다. 대상: [Swag Labs](https://www.saucedemo.com)

Python + Playwright + pytest 로 작성한 웹 E2E 자동화입니다.
대상은 자동화 연습용으로 공개된 쇼핑몰 데모 사이트 [Swag Labs](https://www.saucedemo.com) 입니다.

해피패스만 도는 데모가 아니라, **자동화가 실제 제품 결함을 잡아내는 것까지** 확인합니다.
이 사이트는 결함이 심어진 계정(`problem_user`)을 제공하므로,
같은 검증을 계정만 바꿔 돌려 정상 동작과 결함 동작의 차이를 드러냅니다.

---

## 결과

```
44 tests — 37 passed, 7 xfailed   (약 33초, Chromium headless)
```

| 파일 | 건수 | 내용 |
|---|---|---|
| `test_login.py` | 6 | 로그인 — 동등 분할 4종 + 정상 진입 + 실패 후 재시도 |
| `test_inventory_sort.py` | 9 | 정렬 4종 · 정렬 후 상품 구성 불변 |
| `test_cart.py` | 6 | 담기/빼기 · 뱃지 정합성 · 화면 이동 후 상태 유지 |
| `test_checkout.py` | 9 | 필수값 3종 · 소계·세액·합계 역산 대조 · 주문 완료 |
| `test_defect_detection.py` | 14 | 같은 검증 7건 × (정상 계정 / 결함 계정) |

**xfailed 7건은 실패가 아닙니다.** `problem_user` 계정에서 확인된
제품 결함 5건을 `xfail(strict=True)` 로 고정해 둔 것입니다.
결함이 수정되어 통과하게 되면 그 테스트가 **실패로 바뀌어** 알려 줍니다.

### 찾은 결함 5건

| ID | 요약 | 심각도 |
|---|---|---|
| D-01 | 상품 이미지 6건 전부 404 대체 이미지 | High |
| D-02 | 정렬을 바꿔도 목록 순서가 변하지 않음 | High |
| D-03 | 장바구니 빼기가 동작하지 않음 | Critical |
| D-04 | 상품명 링크가 다른 상품 상세로 이동 (id +1 어긋남, 1건은 존재하지 않는 상품) | Critical |
| D-05 | 체크아웃 Last Name 입력이 저장되지 않음 | High |

재현 절차·기대/실제는 **[docs/DEFECTS.md](docs/DEFECTS.md)** 에 정리했습니다.

---

## 실행

**저장소 루트에서 실행합니다.** (스위트 디렉터리가 아니라)

```bash
python3 -m venv .venv
source .venv/bin/activate                    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

pytest saucedemo                             # 이 스위트만
pytest -m defect                             # 알려진 결함만
pytest saucedemo/tests/test_checkout.py -v   # 파일 단위
pytest --headed                              # 브라우저를 띄워서 확인
```

실패하면 `test-results/` 에 스크린샷·영상·trace 가 남습니다.
trace 는 실패 시점의 DOM·네트워크·콘솔을 함께 담고 있어 이렇게 열어 봅니다.

```bash
playwright show-trace test-results/<테스트명>/trace.zip
```

---

## 구조

```
.
├─ conftest.py          공통 픽스처 — 셀렉터 기준, 로그인 상태, 대기 상한
├─ pytest.ini           실행 옵션 (실패 시에만 아티팩트 저장)
├─ pages/               Page Object — 셀렉터는 전부 이 안에만 있습니다
│   ├─ base_page.py         공통 헤더 · 금액 파싱
│   ├─ login_page.py        inventory_page.py   item_detail_page.py
│   └─ cart_page.py         checkout_page.py
├─ tests/               시나리오
├─ data/                계정 · 상품 카탈로그 — 기대값의 기준
└─ docs/
    ├─ DEFECTS.md       발견 결함 리포트
    └─ DECISIONS.md     왜 이렇게 설계했는지
```

**테스트 본문에 CSS 문자열이 한 줄도 없습니다.** 셀렉터는 Page Object 안에만 둡니다.
화면이 바뀌면 고칠 곳이 한 군데입니다.

---

## 설계에서 신경 쓴 것

전체 근거는 **[docs/DECISIONS.md](docs/DECISIONS.md)** 에 있고, 요약하면 다음과 같습니다.

**① 기대값을 화면에서 만들지 않습니다.**
정렬 기대 순서와 금액은 `data/products.py` 의 카탈로그에서 계산합니다.
화면에서 읽은 목록을 다시 정렬해 비교하면, 제품이 항목을 누락한 채
정렬만 맞게 줘도 통과합니다. 금액도 화면의 소계·세액·합계를 서로 맞춰 보면
셋 다 틀려도 통과합니다. 그래서 세액은 `소계 × 0.08` 로 직접 계산해 대조합니다.
(세율 8%는 두 가지 장바구니 조합으로 실측 확인했습니다.)

**② 금액은 `Decimal` 로 다룹니다.**
float 이면 `29.99 + 9.99 = 39.980000000000004` 로 맞는 금액인데 실패합니다.
틀린 실패는 틀린 통과만큼 나쁩니다 — 몇 번 반복되면 팀이 그 테스트를 믿지 않게 됩니다.

**③ `sleep` 이 0건입니다.**
대기는 `expect()` 의 자동 재시도에 맡깁니다. 조건이 충족되는 즉시 넘어가므로
빠른 날엔 빠르고, 느린 날에도 깨지지 않습니다.

**④ 대기 상한마다 근거가 있습니다.**
`expect` 15초(응답 지연 계정 실측 5.3초 기준) / 조작 20초 / 화면 이동 45초 /
결함 확인 4초. 하나로 통일하지 않은 이유는 무엇을 기다리는지가 케이스마다 다르기 때문입니다.

**⑤ 간헐적 실패를 재시도로 덮지 않았습니다.**
실행 시간이 평소의 2배 이상으로 늘어난 날 픽스처 단계에서 시간이 초과된 적이
두 번 있습니다. 재시도 플러그인을 넣는 대신 **대기 상한을 올려** 대응했습니다.
원인이 "제품이 간헐적으로 틀린다"가 아니라 "외부 사이트가 그날 느렸다"로 보이기
때문입니다. 재시도로 덮으면 진짜 간헐 결함이 생겼을 때도 똑같이 덮입니다.
실측치는 아래 안정성 항목에 그대로 적었습니다.

---

## 안정성 실측

같은 조건에서 반복 실행한 결과입니다. 플레이키 여부는 1회 통과로 판단할 수 없어
연속 실행으로 확인했습니다.

대기 상한을 조정한 뒤 전량 실행을 21회 반복했습니다.

| | |
|---|---|
| 실행 횟수 | 21회 |
| 동일 결과 | 20회 (`37 passed, 7 xfailed`) |
| 시간 초과 | **1회** — 뒤에 따로 적었습니다 |
| 정상 실행 소요 시간 | 32.36초 ~ 35.99초 |
| 누적 테스트 실행 | 880건 (44 × 20) |
| **결과가 뒤집힌 케이스** | **0건** — 통과가 실패로, 실패가 통과로 바뀐 적 없음 |

<details>
<summary>실행 로그</summary>

```
run 01: 37 passed, 7 xfailed in 32.74s
run 02: 37 passed, 7 xfailed in 33.21s
run 03: 37 passed, 7 xfailed in 32.46s
run 04: 37 passed, 7 xfailed in 32.36s
run 05: 37 passed, 7 xfailed in 32.70s
run 06: 37 passed, 7 xfailed in 32.91s
run 07: 37 passed, 7 xfailed in 32.87s
run 08: 37 passed, 7 xfailed in 32.52s
run 09: 37 passed, 7 xfailed in 32.80s
run 10: 37 passed, 7 xfailed in 33.30s
run 11: 37 passed, 7 xfailed in 33.46s
run 12: 37 passed, 7 xfailed in 32.62s
run 13: 36 passed, 7 xfailed, 1 error in 78.50s   ← 시간 초과
run 14: 37 passed, 7 xfailed in 32.58s
run 15: 37 passed, 7 xfailed in 32.41s
run 16: 37 passed, 7 xfailed in 33.09s
run 17: 37 passed, 7 xfailed in 32.64s
run 18: 37 passed, 7 xfailed in 32.38s
run 19: 37 passed, 7 xfailed in 32.41s
run 20: 37 passed, 7 xfailed in 32.49s
run 21: 37 passed, 7 xfailed in 35.99s
```

</details>

### 시간 초과 1회 — 감추지 않고 적습니다

21회 중 13회째에서 `test_상세_화면을_다녀와도_담은_상태가_유지된다` 가 **error** 로 끝났습니다.
그 실행은 전체 78.5초가 걸렸습니다(평소 33초).

**failed 가 아니라 error 라는 점이 중요합니다.** 검증이 틀린 게 아니라
그 앞의 로그인·화면 진입 단계에서 시간이 초과됐다는 뜻입니다.
대상 사이트가 그 시점에 느렸던 것으로 보고 있습니다.

같은 증상이 대기 상한을 올리기 **전**에도 8회 중 1회 있었습니다(그때는 63초).
상한을 올려 빈도는 줄었지만(1/8 → 1/21) **없어지지는 않았습니다.**
이후 8회를 더 돌려 재현을 시도했으나 잡히지 않아 **스택 트레이스는 확보하지 못했습니다.**
원인은 위 추정에 머물러 있습니다.

재시도 플러그인으로 덮지 않은 이유와 남은 위험은
[docs/DECISIONS.md](docs/DECISIONS.md) 7번에 적어 두었습니다.
대상이 외부 공개 사이트인 이상 이 위험은 0이 되지 않습니다.

---

## 알려진 제약

- **대상이 외부 공개 사이트**라 사이트가 바뀌거나 느려지면 영향을 받습니다.
  현재는 대기 상한으로 흡수하고 있으며, 재발 여부는 계속 관찰이 필요합니다.
- 브라우저는 **Chromium 만** 실행합니다. 크로스 브라우저는 아직 범위가 아닙니다.
- 로그아웃·세션 만료, 응답 지연 계정(`performance_glitch_user`)을 쓰는 시나리오는
  아직 없습니다. 지연 계정은 대기 상한을 정하는 근거로만 사용했습니다.

## 환경

Python 3.13.0 · Playwright 1.62.0 · pytest 8.3.3 · Chromium 151.0.7922.34 · macOS 26.5.2
