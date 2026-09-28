"""LLM이 돌려줄 응답의 구조 정의 (Structured Output 스키마).

여기 정의한 Pydantic 모델을 `with_structured_output()` 에 넘기면,
LLM이 자유 문장이 아니라 이 구조에 맞는 데이터를 돌려줌.
덕분에 화면 출력이나 후속 처리에서 문자열 파싱이 필요 없음.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Spot(BaseModel):
    """관광지 또는 맛집 한 곳."""

    name: str = Field(description="장소 이름. Google Places 결과에 있는 이름 그대로 사용")
    category: str = Field(description="장소 분류. 예: 관광지, 박물관, 한식당, 카페")
    rating: Optional[float] = Field(
        default=None, description="Google Places 평점. 자료에 없으면 비워 둠"
    )
    review_count: Optional[int] = Field(
        default=None, description="리뷰 수. 자료에 없으면 비워 둠"
    )
    address: str = Field(description="주소. Google Places 결과 그대로 사용")
    map_url: str = Field(description="Google 지도 링크. 자료에 있는 URL 그대로 사용")
    why: str = Field(description="이 시간대에 이곳을 추천하는 이유. 그날 날씨를 근거로 설명")


class Meal(BaseModel):
    """한 끼 식사 추천."""

    slot: str = Field(description="식사 시간대. 아침, 점심, 저녁 중 하나")
    place: Spot = Field(description="추천 식당")
    recommended_menu: str = Field(description="추천 메뉴 또는 주문 팁")


class DayRoute(BaseModel):
    """하루치 여행 루트."""

    day: int = Field(description="여행 며칠째인지. 1부터 시작")
    weather_summary: str = Field(description="그날 날씨 요약. 제공된 예보 자료를 근거로 작성")
    outfit_tip: str = Field(description="그날 날씨에 맞는 옷차림·준비물 조언")
    spots: List[Spot] = Field(description="그날 방문할 관광지 목록. 동선 순서대로 정렬")
    meals: List[Meal] = Field(description="아침, 점심, 저녁 식사 추천 3건")
    estimated_cost_krw: int = Field(description="1인 기준 그날 예상 지출액(원)")


class TravelPlan(BaseModel):
    """앱이 최종적으로 돌려주는 여행 계획 전체."""

    destination: str = Field(description="여행지. 도시, 국가 형식")
    party_size: int = Field(description="여행 인원수")
    total_budget_krw: int = Field(description="사용자가 입력한 총 예산(원)")
    summary: str = Field(description="이번 여행 전체를 두세 문장으로 요약")
    days: List[DayRoute] = Field(description="날짜별 루트 목록")
    notes: List[str] = Field(
        description="주의사항이나 참고사항. 자료가 부족해 추천하지 못한 항목이 있으면 여기에 명시"
    )
