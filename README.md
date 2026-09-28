# Travel Planner

여행지의 **실시간 날씨**와 **실제 장소 데이터**를 근거로 하루 단위 여행 루트를 추천하는 앱임.  
같은 기능을 **Cloud LLM(Groq)** 과 **Local LLM(Ollama gemma3:4b)** 두 가지 방식으로 구현하여 비교함.

AI 업무자동화 과정 7회차 과제 산출물임.

---

## 앱 목적 및 주요 기능

여행 중 아침에 "오늘 어디 가지?"를 고민하지 않도록, 그날 날씨에 맞는 관광지와  
아침·점심·저녁 식사를 동선 순서대로 정리해 줌.

| 기능 | 설명 |
|------|------|
| 조건 입력 | 국가, 도시, 몇 박 며칠, 인원수, 총예산 |
| 실시간 날씨 | OpenWeatherMap 5일 예보를 일자별 요약 (기온·날씨·강수확률) |
| 실제 장소 검색 | Google Places API (New)로 관광지·맛집 조회, 평점 4.0 이상 우선 |
| 날씨 맞춤 배치 | 비 오는 날은 실내, 맑은 날은 야외 위주 |
| 세 끼 식사 추천 | 하루마다 아침·점심·저녁 식당 + 추천 메뉴 |
| 지도 링크 | 모든 장소에 Google 지도 링크 포함 |
| 구조화 출력 | Pydantic 스키마로 응답 수신, 문자열 파싱 불필요 |

### 추측 방지 설계

외부 API 결과를 **먼저 확정한 뒤** 프롬프트에 넣음. LLM은 주어진 목록 안에서 고르고  
배치하는 역할만 함. 자료가 부족하면 억지로 채우지 않고 `notes`에 이유를 적도록 지시함.

---

## 디렉토리 구조

```text
travel-planner/
├── AGENTS.md                공통 지침 (팀 구성·작업 규칙)
├── CLAUDE.md                @AGENTS.md
├── README.md                본 문서
├── .env                     API 키 (git 제외 대상)
├── .env.example             .env 작성 예시
├── .gitignore
│
├── app/                     Travel Planner — Cloud LLM (Groq)
│   ├── main.py              실행 진입점
│   ├── chain.py             LCEL 체인
│   ├── config.py            .env 로딩·키 검증
│   ├── models.py            Structured Output 스키마
│   ├── prompts/             system_prompt.yaml, user_prompt.yaml
│   ├── tools/               weather.py, places.py
│   ├── requirements.txt
│   └── README.md
│
├── app-clone/               클론 코딩 결과 (app/ 과 동일 구성)
│
├── local-llm/               Travel Planner — Local LLM (Ollama gemma3:4b)
│   └── (app/ 과 같은 구성, chain.py·config.py 만 Ollama용)
│
├── local-llm-clone/         클론 코딩 결과 (local-llm/ 과 동일 구성)
│
├── prompts/                 과제 수행용 프롬프트 (8섹션 표준)
├── docs/                    느낀점·배운점 기록
└── images/                  실행 화면 캡처
```

---

## 사전 준비 — API 키 발급

프로젝트 루트에 `.env` 파일을 만들고 아래 값을 채움. `.env.example`을 복사해 쓰면 편함.

```text
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile
OPENWEATHER_API_KEY=...
GOOGLE_PLACES_API_KEY=...
CONTACT_EMAIL=your-id@example.com
OLLAMA_MODEL=gemma3:4b
OLLAMA_BASE_URL=http://localhost:11434
```

| 키 | 발급처 | 주의사항 |
|----|--------|---------|
| `GROQ_API_KEY` | https://console.groq.com/keys | 무료 티어 제공 |
| `GROQ_MODEL` | https://console.groq.com/docs/models | 제공 모델명이 자주 바뀜. 콘솔에서 현재 값 확인 |
| `OPENWEATHER_API_KEY` | https://home.openweathermap.org/api_keys | 발급 직후 활성화까지 수십 분 소요 |
| `GOOGLE_PLACES_API_KEY` | https://console.cloud.google.com/apis/credentials | **Places API (New)** 를 별도로 사용 설정해야 함 |

> ⚠️ `.env`는 `.gitignore`에 등록되어 있음. 절대 커밋하지 말 것.  
> 커밋 전 확인: `git check-ignore -v .env`

---

## 가상환경 설정 방법

Python **3.11 이상** 권장. 프로젝트 루트(`travel-planner/`)에서 실행함.

### Windows · PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> 실행 정책 오류(`이 시스템에서 스크립트를 실행할 수 없으므로`)가 나면 아래를 한 번 실행한 뒤 재시도함.
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

## 라이브러리 설치 및 실행

### Cloud LLM 버전

```bash
pip install -r app/requirements.txt
```

```bash
cd app
python main.py
```

### Local LLM 버전

Ollama 설치(https://ollama.com/download) 후 모델을 내려받음.

```bash
ollama pull gemma3:4b
```

```bash
pip install -r local-llm/requirements.txt
```

```bash
cd local-llm
python main.py
```

### 클론 코딩 버전

`app-clone/`, `local-llm-clone/`은 원본과 동일한 구성임. 실행 방법도 같음.

```bash
cd app-clone
python main.py
```

---

## 과제 요구사항 대응표

| 요구사항 | 구현 위치 |
|---------|----------|
| LangChain 이용 | `app/`, `local-llm/` 전체 |
| PromptTemplate 사용 | `prompts/*.yaml` → `chain.py: build_prompt()` |
| 시스템·유저 프롬프트 분리 | `system_prompt.yaml` / `user_prompt.yaml` |
| load_prompt 사용 | `chain.py: build_prompt()` |
| Structured Output | `chain.py: with_structured_output(TravelPlan)` |
| LCEL 체인 구성 | `chain.py: gather \| prompt \| structured_llm` |
| 동기 방식 실행 | `chain.py: chain.invoke(...)` |
| API Key·모델 `.env` 참조 | `config.py: load_settings()` |
| 날씨 맞춤 관광지 | `system_prompt.yaml` 규칙 4 + `tools/weather.py` |
| 아침·점심·저녁 맛집 | `models.py: DayRoute.meals` |
| 평점 4.0 이상 우선 | `tools/places.py: search_places(min_rating=4.0)` |
| Google 지도 링크 | `tools/places.py: googleMapsUri` → `models.py: Spot.map_url` |

---

## 참고 문서

- [Cloud LLM 버전 상세 README](app/README.md)
- [Local LLM 버전 상세 README](local-llm/README.md)
- [느낀점·배운점](docs/느낀점-배운점.md)
