# Travel Planner (Local LLM · Ollama gemma3:4b)

[Cloud LLM 버전](../app/README.md)과 같은 기능을, **내 PC에서 돌아가는 모델**로 수행하는 앱임.  
LLM API 키가 필요 없고 요청 내용이 외부 LLM 서비스로 나가지 않음.

---

## 앱 목적

아침에 "오늘 어디 가지?"를 고민하지 않도록, 그날 날씨에 맞는 관광지와 세 끼 식사를  
동선 순서대로 정리해 줌. Cloud 버전과 목적·출력 형식은 동일함.

## 주요 기능

| 기능 | 설명 |
|------|------|
| 조건 입력 | 국가, 도시, 몇 박 며칠, 인원수, 총예산을 대화형으로 입력받음 |
| 실시간 날씨 조회 | OpenWeatherMap 5일 예보를 일자별로 요약 |
| 실제 장소 검색 | Google Places API (New)로 관광지·맛집 조회, 평점 4.0 이상 우선 |
| 날씨 맞춤 추천 | 비 오는 날은 실내, 맑은 날은 야외 위주로 관광지 배치 |
| 세 끼 식사 추천 | 하루마다 아침·점심·저녁 식당과 추천 메뉴 제시 |
| 로컬 실행 | Ollama 런타임의 `gemma3:4b` 사용. LLM API 키 불필요 |
| 사전 점검 | 실행 전 Ollama 연결 상태와 모델 설치 여부를 확인하고 안내 |

## Cloud LLM 버전과의 차이

| 항목 | Cloud (`app/`) | Local (`local-llm/`) |
|------|----------------|----------------------|
| 모델 | Groq 호스팅 모델 | Ollama `gemma3:4b` |
| LLM API 키 | `GROQ_API_KEY` 필요 | 불필요 |
| 구조화 출력 방식 | 도구 호출 (기본값) | `method="json_schema"` |
| 장소 후보 수 | 10개 | 6개 (작은 모델의 컨텍스트 부담 완화) |
| 속도 | 빠름 | PC 사양에 따라 느릴 수 있음 |
| 비용 | 토큰당 과금 | 없음 (전기요금 제외) |

> `gemma3:4b`는 4B 규모의 작은 모델임. 항목 누락이나 형식 오류가 Cloud 버전보다 잦을 수 있음.
> 품질이 부족하면 `.env`의 `OLLAMA_MODEL`을 더 큰 모델(예: `gemma3:12b`)로 바꿔 볼 수 있음.

---

## 디렉토리 구조

```text
local-llm/
├── main.py                  실행 진입점 — 입력 받기, 결과 출력
├── chain.py                 LCEL 체인 구성 (ChatOllama 사용)
├── config.py                .env 로딩 + Ollama 연결·모델 설치 확인
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

---

## 사전 준비

### 1. Ollama 설치

**Windows**

https://ollama.com/download 에서 설치 파일을 받아 설치함.

**macOS / Linux**

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. 모델 내려받기

```bash
ollama pull gemma3:4b
```

설치 확인:

```bash
ollama list
```

### 3. `.env` 설정

> ⚠️ `.env`의 API 키 실제값은 개인 발급분이라 저장소에 등록하지 않음.  
> `.env.example`을 복사해 본인 키로 채울 것 — 자세한 내용은 [루트 README](../README.md#사전-준비--api-키-발급) 참고.

프로젝트 루트의 `.env`에 아래 값이 필요함. LLM API 키는 필요 없음.

```text
OPENWEATHER_API_KEY=...
GOOGLE_PLACES_API_KEY=...
OLLAMA_MODEL=gemma3:4b
OLLAMA_BASE_URL=http://localhost:11434
```

---

## 가상환경 설정 방법

Python **3.11 이상**을 권장함. 아래는 프로젝트 루트(`travel-planner/`)에서 실행함.

### Windows · PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> 실행 정책 오류가 나면 아래를 한 번 실행한 뒤 다시 시도함.
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

```bash
pip install --upgrade pip
pip install -r local-llm/requirements.txt
```

---

## 실행 방법

```bash
cd local-llm
python main.py
```

---

## 문제 해결

| 증상 | 원인과 해결 |
|------|------------|
| `Ollama에 연결하지 못함` | Ollama가 실행 중인지 확인. Windows는 트레이 아이콘, 터미널은 `ollama list` |
| `모델 ... 이(가) 받아져 있지 않음` | `ollama pull gemma3:4b` 실행 |
| 응답이 오래 걸림 | 4B 모델도 CPU만으로는 느림. GPU 사용 여부 확인 |
| 항목이 비거나 형식이 깨짐 | 작은 모델의 한계. `OLLAMA_MODEL`을 더 큰 모델로 변경해 재시도 |
| `UnicodeDecodeError ... cp949` | 한글 Windows에서 발생. `load_prompt(..., encoding="utf-8")` 적용됨 |

---

## 과제 요구사항 대응표

| 요구사항 | 구현 위치 |
|---------|----------|
| LangChain 이용 | 전체 (`langchain-core`, `langchain-ollama`) |
| PromptTemplate 사용 | `prompts/*.yaml` → `chain.py: build_prompt()` |
| 시스템·유저 프롬프트 분리 | `system_prompt.yaml` / `user_prompt.yaml` |
| load_prompt 사용 | `chain.py: build_prompt()` |
| gemma3:4b 모델 이용 | `chain.py: ChatOllama` |
| AI Runtime: Ollama | `config.py: OLLAMA_BASE_URL` |
| Structured Output | `chain.py: with_structured_output(TravelPlan, method="json_schema")` |
| LCEL 체인 구성 | `chain.py: gather \| prompt \| structured_llm` |
| 동기 방식 실행 | `chain.py: chain.invoke(...)` |
| 날씨 맞춤 관광지 | `system_prompt.yaml` 규칙 4 + `tools/weather.py` |
| 아침·점심·저녁 맛집 | `models.py: DayRoute.meals` + `system_prompt.yaml` 규칙 5 |
