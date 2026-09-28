# Travel Planner (Cloud LLM · Groq)

여행지의 **실시간 날씨**와 **실제 장소 데이터**를 근거로 하루 단위 여행 루트를 추천하는 앱임.  
LangChain LCEL 체인으로 구성하며, LLM은 Groq에서 호스팅하는 모델을 사용함.

---

## 앱 목적

아침에 "오늘 어디 가지?"를 고민하지 않도록, 그날 날씨에 맞는 관광지와 세 끼 식사를  
동선 순서대로 정리해 줌. 여행 경험이 적은 사람도 그대로 따라 움직일 수 있게 하는 것이 목표임.

## 주요 기능

| 기능 | 설명 |
|------|------|
| 조건 입력 | 국가, 도시, 몇 박 며칠, 인원수, 총예산을 대화형으로 입력받음 |
| 실시간 날씨 조회 | OpenWeatherMap 5일 예보를 일자별로 요약 (최저·최고 기온, 날씨, 강수확률) |
| 실제 장소 검색 | Google Places API (New)로 관광지·맛집 조회, 평점 4.0 이상 우선 |
| 날씨 맞춤 추천 | 비 오는 날은 실내, 맑은 날은 야외 위주로 관광지 배치 |
| 세 끼 식사 추천 | 하루마다 아침·점심·저녁 식당과 추천 메뉴 제시 |
| 지도 링크 | 모든 장소에 Google 지도 링크 포함 |
| 구조화 출력 | Pydantic 스키마로 응답을 받아 문자열 파싱 없이 바로 사용 |

### 추측 방지 설계

LLM이 없는 장소를 지어내지 않도록, **외부 API 결과를 먼저 확정한 뒤 프롬프트에 넣음**.  
시스템 프롬프트에서 "제공된 자료 안의 사실만 사용"을 명시하고, 자료가 부족하면  
억지로 채우지 말고 `notes` 항목에 이유를 적도록 지시함.

---

## 디렉토리 구조

```text
app/
├── main.py                  실행 진입점 — 입력 받기, 결과 출력
├── chain.py                 LCEL 체인 구성 (자료 수집 → 프롬프트 → LLM)
├── config.py                .env 로딩 및 필수 키 사전 검증
├── models.py                Structured Output 스키마 (Pydantic)
├── prompts/
│   ├── system_prompt.yaml   시스템 프롬프트 (역할·규칙)
│   └── user_prompt.yaml     유저 프롬프트 (여행조건·수집자료)
├── tools/
│   ├── weather.py           OpenWeatherMap 연동
│   └── places.py            Google Places API (New) 연동
├── requirements.txt
└── README.md
```

### 데이터 흐름

```text
사용자 입력
   ↓
build_context()  ── OpenWeatherMap 호출 ──┐
                 ── Google Places 호출 ───┤  실제 자료 확정
   ↓                                      │
ChatPromptTemplate  (load_prompt 로 YAML에서 읽음)
   ↓
ChatGroq.with_structured_output(TravelPlan)
   ↓
TravelPlan 객체 → 화면 출력
```

---

## 사전 준비

프로젝트 루트의 `.env` 파일에 아래 값이 채워져 있어야 함. (`.env.example` 참고)

```text
GROQ_API_KEY=gsk_...
GROQ_MODEL=openai/gpt-oss-120b
OPENWEATHER_API_KEY=...
GOOGLE_PLACES_API_KEY=...
CONTACT_EMAIL=your-id@example.com
```

| 키 | 발급처 | 비고 |
|----|--------|------|
| `GROQ_API_KEY` | https://console.groq.com/keys | 무료 티어 제공 |
| `GROQ_MODEL` | https://console.groq.com/docs/models | **계정마다 제공 모델이 다름.** 아래 확인 방법 참고 |
| `OPENWEATHER_API_KEY` | https://home.openweathermap.org/api_keys | 발급 직후 활성화까지 수십 분 소요 |
| `GOOGLE_PLACES_API_KEY` | https://console.cloud.google.com/apis/credentials | **Places API (New)** 사용 설정 필요 |

> **`GROQ_MODEL` 확인 방법** — 제공 모델은 계정·시점에 따라 다름. 아래로 현재 목록을 조회함.
>
> ```bash
> curl -s -H "Authorization: Bearer $GROQ_API_KEY" https://api.groq.com/openai/v1/models
> ```
>
> `whisper-*`(음성), `*prompt-guard*`(분류 전용)는 채팅용이 아니므로 제외하고 고름.
> 2026-09-28 기준 이 계정에서 사용 가능한 채팅 모델: `openai/gpt-oss-120b`, `openai/gpt-oss-20b`,
> `qwen/qwen3.8-27b`, `allam-2-7b`.


---

## 가상환경 설정 방법

Python **3.11 이상**을 권장함. 아래는 프로젝트 루트(`travel-planner/`)에서 실행함.

### Windows · PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> 실행 정책 오류(`... 스크립트를 실행할 수 없습니다`)가 나면 아래를 한 번 실행한 뒤 다시 시도함.
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
> ```

### Windows · Git Bash

```bash
py -3.11 -m venv .venv
source .venv/Scripts/activate
```

### macOS · zsh / bash

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 가상환경 해제 (공통)

```bash
deactivate
```

---

## 라이브러리 설치

가상환경을 활성화한 상태에서 실행함.

```bash
pip install --upgrade pip
pip install -r app/requirements.txt
```

---

## 실행 방법

`app` 디렉토리로 이동한 뒤 실행함. (프롬프트 파일을 상대 경로로 찾기 때문)

```bash
cd app
python main.py
```

### 실행 예시

```text
──────────────────────────────────────────────────────────────
🧳  하루 여행 루트 추천기
──────────────────────────────────────────────────────────────
여행 조건을 입력해 주세요. 엔터만 누르면 대괄호 안 기본값이 쓰입니다.

국가 (영문 권장) [South Korea]: Japan
도시 (영문 권장) [Seoul]: Osaka
몇 박 [2]: 2
인원수 [2]: 3
총예산(원) [600000]: 1200000

날씨와 장소를 조회하고 루트를 만드는 중입니다. 잠시만 기다려 주세요...
```

---

## 문제 해결

| 증상 | 원인과 해결 |
|------|------------|
| `.env` 값이 비어 있다는 메시지 | 루트에 `.env` 파일이 있는지, 키 이름 철자가 맞는지 확인 |
| `OpenWeatherMap 키가 거부됨(401)` | 발급 직후면 활성화 대기 중임. 수십 분 뒤 재시도 |
| `도시를 찾지 못함` | 도시명을 영문으로 입력 (예: 서울 → Seoul) |
| `Google Places 키가 거부됨` | Cloud Console에서 **Places API (New)** 사용 설정 여부 확인 |
| `UnicodeDecodeError ... cp949` | 한글 Windows에서 발생. `load_prompt(..., encoding="utf-8")` 적용됨 |
| 모델명 오류 | Groq 콘솔에서 현재 제공 중인 모델명으로 `GROQ_MODEL` 수정 |

---

## 과제 요구사항 대응표

| 요구사항 | 구현 위치 |
|---------|----------|
| LangChain 이용 | 전체 (`langchain-core`, `langchain-groq`) |
| PromptTemplate 사용 | `prompts/*.yaml` → `chain.py: build_prompt()` |
| 시스템·유저 프롬프트 분리 | `system_prompt.yaml` / `user_prompt.yaml` |
| load_prompt 사용 | `chain.py: build_prompt()` |
| Groq 모델 이용 | `chain.py: ChatGroq` |
| API Key·모델 `.env` 참조 | `config.py: load_settings()` |
| Structured Output | `chain.py: with_structured_output(TravelPlan)` |
| LCEL 체인 구성 | `chain.py: gather \| prompt \| structured_llm` |
| 동기 방식 실행 | `chain.py: chain.invoke(...)` |
| 날씨 맞춤 관광지 | `system_prompt.yaml` 규칙 4 + `tools/weather.py` |
| 아침·점심·저녁 맛집 | `models.py: DayRoute.meals` + `system_prompt.yaml` 규칙 5 |
