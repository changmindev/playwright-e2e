# 결함 리포트

대상: https://www.saucedemo.com
확인일: 2026-08-25
확인 환경: Chromium 151.0.7922.34 (headless) · Playwright 1.62.0 · Python 3.13.0 · macOS 26.5.2

재현 계정 `problem_user` 로 로그인했을 때 확인된 결함 5건이다.
정상 계정(`standard_user`)에서는 **같은 검증이 모두 통과**한다.
즉 아래 항목은 테스트 코드의 문제가 아니라 계정에 따라 달라지는 제품 동작이다.

각 결함은 `tests/test_defect_detection.py` 에 `xfail(strict=True)` 로 고정돼 있다.
결함이 수정되어 통과하게 되면 그 테스트가 **실패로 바뀌어** 알려 준다.

| ID | 요약 | 심각도 | 영향 |
|---|---|---|---|
| [D-01](#d-01) | 상품 이미지 6건 전부 404 대체 이미지 | High | 상품 식별 불가 |
| [D-02](#d-02) | 정렬을 바꿔도 목록 순서가 변하지 않음 | High | 정렬 기능 전면 무효 |
| [D-03](#d-03) | 장바구니 빼기가 동작하지 않음 | Critical | 원치 않는 상품이 결제까지 감 |
| [D-04](#d-04) | 상품명 링크가 다른 상품 상세로 이동 | Critical | 오구매 유발, 1건은 존재하지 않는 상품 |
| [D-05](#d-05) | 체크아웃 Last Name 입력이 저장되지 않음 | High | 주문 정보 누락 |

---

<a id="d-01"></a>
## D-01 · 상품 이미지 6건이 모두 404 대체 이미지로 노출된다

**심각도** High
**재현 테스트** `test_상품마다_서로_다른_이미지가_노출된다[결함 계정]`
`test_특정_상품의_이미지_경로에_상품이_식별된다[결함 계정]`

### 재현 절차
1. `problem_user` / `secret_sauce` 로 로그인한다
2. 상품 목록의 이미지 6개를 확인한다

### 기대 / 실제
| | |
|---|---|
| 기대 | 상품 6건이 각각 자기 이미지를 표시 (고유 경로 6건) |
| 실제 | 6건 전부 `/assets/sl-404-Cq1a9k9X.jpg` — **고유 경로 1건** |

정상 계정에서는 6건 모두 다른 경로다.

```
standard_user : sauce-backpack… / bike-light… / bolt-shirt… / sauce-pullover… / red-onesie… / red-tatt…
problem_user  : sl-404… ×6
```

### 검증 시 주의
`to_be_visible()` 로는 잡히지 않는다. 404 대체 이미지도 정상적으로 렌더링되기 때문이다.
**`src` 속성을 읽어서 판정해야 한다.**

---

<a id="d-02"></a>
## D-02 · 정렬 옵션을 바꿔도 목록 순서가 변하지 않는다

**심각도** High
**재현 테스트** `test_정렬을_바꾸면_목록_순서가_바뀐다[결함 계정]`

### 재현 절차
1. `problem_user` 로 로그인한다
2. 정렬 드롭다운에서 `Name (Z to A)` 를 선택한다
3. `Price (low to high)`, `Price (high to low)` 로도 반복한다

### 기대 / 실제
| | |
|---|---|
| 기대 | 선택한 기준으로 목록 순서가 재정렬됨 |
| 실제 | 드롭다운 선택값만 바뀌고 **목록은 3개 옵션 모두에서 초기 순서 그대로** |

```
선택: Name (Z to A)
기대: Test.allTheThings… → Onesie → Fleece Jacket → Bolt T-Shirt → Bike Light → Backpack
실제: Backpack → Bike Light → Bolt T-Shirt → Fleece Jacket → Onesie → Test.allTheThings…  (변화 없음)
```

가격 정렬(`lohi`/`hilo`)에서도 가격 배열이 동일하게 유지된다.

---

<a id="d-03"></a>
## D-03 · 장바구니에서 빼기가 동작하지 않는다

**심각도** Critical
**재현 테스트** `test_장바구니에서_빼면_담기_상태로_돌아온다[결함 계정]`

### 재현 절차
1. `problem_user` 로 로그인한다
2. `Sauce Labs Backpack` 을 담는다 → 버튼이 `Remove` 로 바뀐다
3. `Remove` 를 누른다

### 기대 / 실제
| | |
|---|---|
| 기대 | 장바구니에서 제거되고 버튼이 `Add to cart` 로 복귀, 뱃지 사라짐 |
| 실제 | 버튼이 **`Remove` 그대로**, 뱃지도 `1` 유지 — 제거 자체가 되지 않음 |

### 왜 Critical 인가
사용자가 담은 상품을 뺄 수 없다. 결제 화면까지 그대로 실려 가므로
**원치 않는 상품이 그대로 주문된다.** 되돌릴 경로가 화면에 없다.

---

<a id="d-04"></a>
## D-04 · 상품명 링크가 다른 상품 상세로 이동한다 (off-by-one)

**심각도** Critical
**재현 테스트** `test_목록에서_연_상세는_같은_상품이다[결함 계정]`
`test_상세로_들어가도_상품이_존재해야_한다[결함 계정]`

### 재현 절차
1. `problem_user` 로 로그인한다
2. 목록에서 상품명을 순서대로 하나씩 눌러 상세로 들어간다

### 기대 / 실제
목록 6건이 **전부** 어긋난다. 이동한 `id` 가 일관되게 **+1** 이다.

| 목록에서 누른 상품 | 실제 id | 상세에 표시된 상품 |
|---|---|---|
| Sauce Labs Backpack (id=4) | 5 | Sauce Labs Fleece Jacket |
| Sauce Labs Bike Light (id=0) | 1 | Sauce Labs Bolt T-Shirt |
| Sauce Labs Bolt T-Shirt (id=1) | 2 | Sauce Labs Onesie |
| Sauce Labs Fleece Jacket (id=5) | 6 | **ITEM NOT FOUND** |
| Sauce Labs Onesie (id=2) | 3 | Test.allTheThings() T-Shirt (Red) |
| Test.allTheThings() T-Shirt (Red) (id=3) | 4 | Sauce Labs Backpack |

정상 계정에서는 6건 모두 일치한다.

### 파생 영향
`id=5` 상품은 존재하지 않는 `id=6` 으로 이동해 **`ITEM NOT FOUND` 가 사용자에게 그대로 노출**된다.
오류 화면 처리도 없다.

### 왜 Critical 인가
사용자가 본 상품과 상세에서 담는 상품이 다르다. **잘못된 상품이 주문되며,
사용자는 결제 완료 시점까지 알아채기 어렵다.**

---

<a id="d-05"></a>
## D-05 · 체크아웃 Last Name 입력이 저장되지 않는다

**심각도** High
**재현 테스트** `test_체크아웃_입력값이_입력한_그대로_남는다[결함 계정]`

### 재현 절차
1. `problem_user` 로 로그인 후 상품을 담고 체크아웃으로 진입한다
2. First Name / Last Name / Zip 세 칸을 모두 채운다
3. 각 입력칸의 값을 다시 읽는다

### 기대 / 실제
| 입력칸 | 넣은 값 | 실제 값 | 판정 |
|---|---|---|---|
| First Name | `창민` | `창민` | OK |
| **Last Name** | `최` | `` (빈 값) | **불일치** |
| Zip/Postal Code | `06236` | `06236` | OK |

Last Name 만 선택적으로 유실된다. 화면상 필수값 오류도 뜨지 않아
**사용자는 값이 비었다는 사실을 인지하지 못한 채 진행**한다.

---

## 참고 — 결함이 아닌 것으로 판정한 항목

| 관찰 | 판정 | 근거 |
|---|---|---|
| 체크아웃에서 공백 한 칸(`" "`)이 필수값을 통과한다 | **결함으로 올리지 않음** | 정상 계정에서도 동일. 입력 정책의 문제로 별도 논의가 필요한 사안이며, 현재 동작을 `test_공백만_입력한_경우는_통과된다` 로 고정만 해 두었다. 정책이 바뀌면 그 테스트가 먼저 깨진다 |
| `performance_glitch_user` 의 로그인이 약 5.3초 걸린다 | **의도된 동작** | 대기 처리 검증용으로 제공되는 계정이다. 조사 과정에서 실측만 했고 아직 이 계정을 쓰는 테스트는 없다. 다만 기본 대기 상한 5초로는 걸리는 값이라, `conftest.py` 의 상한을 15초로 잡는 근거로 사용했다 |
