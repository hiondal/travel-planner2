"""LCEL 체인 구성.

흐름:
    사용자 입력 → (날씨·장소 실제 조회) → 프롬프트 → LLM(구조화 출력) → TravelPlan

외부 자료를 먼저 확정한 뒤 프롬프트에 넣기 때문에, 모델이 장소나 날씨를
지어낼 여지를 줄임.
"""

from __future__ import annotations

from typing import Dict

from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
    load_prompt,
)
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_groq import ChatGroq

from config import PROMPT_DIR, Settings
from models import TravelPlan
from tools import places as places_tool
from tools import weather as weather_tool


def build_prompt() -> ChatPromptTemplate:
    """시스템 프롬프트와 유저 프롬프트를 파일에서 읽어 하나로 합침."""

    # load_prompt: 프롬프트를 코드에서 분리해 YAML 파일로 관리
    # encoding="utf-8" 필수 — 생략하면 한글 Windows에서 cp949로 열어
    # UnicodeDecodeError가 발생함
    system_template = load_prompt(PROMPT_DIR / "system_prompt.yaml", encoding="utf-8")
    user_template = load_prompt(PROMPT_DIR / "user_prompt.yaml", encoding="utf-8")

    return ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate(prompt=system_template),
            HumanMessagePromptTemplate(prompt=user_template),
        ]
    )


def build_context(user_input: Dict, settings: Settings) -> Dict:
    """외부 API를 호출해 프롬프트에 넣을 자료를 모음."""

    city = user_input["city"]
    country = user_input["country"]
    days = user_input["days"]

    # 1) 날씨 예보
    forecast = weather_tool.fetch_forecast(
        city=city, country=country, api_key=settings.openweather_api_key, days=days
    )
    weather_block = weather_tool.format_for_prompt(forecast, days)

    # 2) 관광지
    # 검색어는 영문으로 구성함 — Places Text Search는 한글 검색어에서
    # 결과가 0건이거나 무관한 장소가 나오는 경우가 있음.
    # languageCode="ko" 덕분에 결과 이름·주소는 한글로 받음.
    attractions = places_tool.search_places(
        query=f"tourist attractions in {city}, {country}",
        api_key=settings.google_places_api_key,
    )
    attraction_block = places_tool.format_for_prompt("관광지", attractions)

    # 3) 맛집
    restaurants = places_tool.search_places(
        query=f"best restaurants in {city}, {country}",
        api_key=settings.google_places_api_key,
    )
    restaurant_block = places_tool.format_for_prompt("맛집", restaurants)

    return {
        **user_input,
        "weather_block": weather_block,
        "attraction_block": attraction_block,
        "restaurant_block": restaurant_block,
    }


def build_chain(settings: Settings) -> Runnable:
    """LCEL 파이프 연산자로 단계를 연결함."""

    llm = ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=0.3,  # 사실 기반 정리 작업이므로 낮게 유지
        # 여행 계획 JSON은 길이가 꽤 됨. 한도가 작으면 응답이 중간에 잘려
        # "Failed to parse tool call arguments as JSON" 오류가 남
        max_tokens=16384,
    )

    # with_structured_output: 응답을 TravelPlan 스키마에 맞춰 받음
    structured_llm = llm.with_structured_output(TravelPlan)

    gather = RunnableLambda(lambda x: build_context(x, settings))

    return gather | build_prompt() | structured_llm


def run(user_input: Dict, settings: Settings) -> TravelPlan:
    """체인을 동기 방식으로 실행함 (invoke)."""

    chain = build_chain(settings)
    return chain.invoke(user_input)
