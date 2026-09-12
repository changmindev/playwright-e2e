# playwright-e2e

**외부 웹사이트를 대상으로 한 Playwright E2E 자동화 저장소.**

내가 통제할 수 없는 사이트를 대상으로 삼습니다. 화면이 언제든 바뀌고, 고쳐 달라고 할 수 없습니다.
그래서 여기서 다루는 건 "테스트를 통과시키는 법"이 아니라 **깨졌을 때 무엇이 깨졌는지 말할 수 있는 구조**입니다.

> 내가 만든 제품을 대상으로 한 E2E 는 별도 저장소에 있습니다 → [loyalhub-e2e](https://github.com/changmindev/loyalhub-e2e)
> 대상을 고칠 권한이 있느냐 없느냐에 따라 테스트 설계가 달라지기 때문에 저장소를 나눴습니다.

---

## 스위트

```
97 tests — 90 passed, 7 xfailed   (약 44초, Chromium headless)
```

| 스위트 | 대상 | 결과 |
|---|---|---|
| **[`saucedemo/`](saucedemo/README.md)** | [Swag Labs](https://www.saucedemo.com) | 44 — 37 passed, **7 xfailed** |
| **[`naver_weather/`](naver_weather/README.md)** | 네이버 날씨 (서울 · 강원 · 경기) | 53 — 53 passed |

**[`saucedemo/`](saucedemo/README.md)** — 해피패스만 도는 데모가 아닙니다.
결함이 심어진 계정(`problem_user`)으로 같은 검증을 한 번 더 돌려
**자동화가 실제 제품 결함을 잡아내는지**까지 확인합니다.
`xfailed` 7건이 그 결과입니다 — 통과한 게 아니라 **결함을 결함으로 고정해 둔 것**입니다.

**[`naver_weather/`](naver_weather/README.md)** — 검색 카드와 상세 화면 두 곳을 건너가며 실시간 값을
수집하고, 그 값이 **쓸 수 있는 값인지** 세 갈래(계약 · 범위 · 상호 일관성)로 판정합니다.

---

## 실행

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

pytest                              # 전체 (97건)
pytest saucedemo                    # 스위트별
pytest -m defect                    # 마커별 — defect · contract · range · consistency
pytest --headed                     # 브라우저를 띄워서
```

실패하면 `test-results/` 에 스크린샷 · 영상 · trace 가 남습니다.

---

## 구조를 이렇게 잡은 이유

```
playwright-e2e/
├── pytest.ini          # 루트 하나. pythonpath = . · 마커 전부 여기 모임
├── requirements.txt
├── saucedemo/          # 스위트 = 파이썬 패키지
│   ├── pages/  data/  tests/  docs/
│   └── README.md
└── naver_weather/
    ├── pages/  data/  tests/
    └── README.md
```

**스위트를 패키지로 둡니다.** 스위트마다 `pages/` · `data/` 를 각자 갖는데,
각 스위트 디렉터리를 통째로 `sys.path` 에 넣으면 `pages` 라는 이름이 겹칩니다.
먼저 올라간 쪽이 이기고 다른 스위트는 **조용히 남의 페이지 객체를 import** 합니다 —
에러도 안 나고 테스트만 이상하게 실패하는, 찾기 아주 어려운 종류의 고장입니다.
그래서 `saucedemo.pages` · `naver_weather.pages` 처럼 스위트 이름으로 한정합니다.

⚠️ **전역 상태는 따로 조심합니다.** `saucedemo` 는 `get_by_test_id` 가 볼 속성을
`data-test` 로 바꾸는데, 이 설정은 **프로세스 전역**이라 세션이 끝날 때까지 남습니다.
지금은 `naver_weather` 가 `get_by_test_id` 를 쓰지 않아 문제가 없지만,
`data-testid` 를 쓰는 스위트를 새로 넣으면 여기서 충돌합니다 (`saucedemo/conftest.py` 에 적어 뒀습니다).

---

## CI 가 테스트를 '실행'하지 않는 이유

`.github/workflows/ci.yml` 은 **문법 검사와 테스트 수집까지만** 합니다.

대상이 내가 통제할 수 없는 외부 사이트이기 때문입니다. CI 러너는 해외 IP 에서 돌고,
대상 사이트는 지역 · 시간대 · 접속 환경에 따라 다른 화면을 줍니다.
그대로 돌리면 **내 코드가 멀쩡한데도 빨간불**이 뜨고, 빨간불이 일상이 되는 순간
CI 는 아무도 안 보는 장식이 됩니다.

그래서 CI 는 "코드가 깨졌는가"만 봅니다 — import 가 끊겼는지, 문법이 맞는지, 수집은 되는지.
**실제 실행은 사람이 의도를 갖고 돌립니다.**

---

## 스택

```
Python · pytest · Playwright (sync API) · Page Object Model
```
