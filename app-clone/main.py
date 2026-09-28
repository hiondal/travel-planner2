"""Travel Planner (Cloud LLM) 실행 진입점.

사용법:
    python main.py
"""

from __future__ import annotations

import sys

from chain import run
from config import MissingKeyError, load_settings, verify_settings
from models import TravelPlan
from tools.places import PlacesError
from tools.weather import WeatherError

LINE = "─" * 62


def ask(question: str, default: str = "") -> str:
    """한 줄 입력을 받음. 그냥 엔터를 치면 기본값을 사용."""

    suffix = f" [{default}]" if default else ""
    answer = input(f"{question}{suffix}: ").strip()
    return answer or default


def ask_int(question: str, default: int) -> int:
    """숫자 입력을 받음. 숫자가 아니면 다시 물어봄."""

    while True:
        raw = ask(question, str(default))
        try:
            value = int(raw.replace(",", ""))
            if value < 0:
                print("  0 이상의 숫자를 입력해 주세요.")
                continue
            return value
        except ValueError:
            print("  숫자만 입력해 주세요. 예: 3")


def collect_input() -> dict:
    """여행 조건을 사용자에게 물어봄."""

    print(LINE)
    print("🧳  하루 여행 루트 추천기")
    print(LINE)
    print("여행 조건을 입력해 주세요. 엔터만 누르면 대괄호 안 기본값이 쓰입니다.\n")

    country = ask("국가 (영문 권장)", "South Korea")
    city = ask("도시 (영문 권장)", "Seoul")
    nights = ask_int("몇 박", 2)
    party_size = ask_int("인원수", 2)
    budget = ask_int("총예산(원)", 600000)

    return {
        "country": country,
        "city": city,
        "nights": nights,
        "days": nights + 1,
        "party_size": party_size,
        "budget_krw": budget,
    }


def render(plan: TravelPlan) -> None:
    """결과를 사람이 읽기 좋게 출력함."""

    print()
    print(LINE)
    print(f"📍  {plan.destination}  |  {plan.party_size}명  |  예산 {plan.total_budget_krw:,}원")
    print(LINE)
    print(plan.summary)

    for day in plan.days:
        print()
        print(f"── {day.day}일차 " + "─" * 48)
        print(f"🌤  날씨   : {day.weather_summary}")
        print(f"👕 옷차림 : {day.outfit_tip}")
        print(f"💰 예상비용: 1인 {day.estimated_cost_krw:,}원")

        if day.spots:
            print("\n  [관광지]")
            for index, spot in enumerate(day.spots, start=1):
                rating = f" ⭐{spot.rating}" if spot.rating else ""
                reviews = f" (리뷰 {spot.review_count})" if spot.review_count else ""
                print(f"  {index}. {spot.name}{rating}{reviews}")
                print(f"     {spot.why}")
                print(f"     📌 {spot.address}")
                print(f"     🗺  {spot.map_url}")

        if day.meals:
            print("\n  [식사]")
            for meal in day.meals:
                place = meal.place
                rating = f" ⭐{place.rating}" if place.rating else ""
                print(f"  · {meal.slot} — {place.name}{rating}")
                print(f"     추천메뉴: {meal.recommended_menu}")
                print(f"     🗺  {place.map_url}")

    if plan.notes:
        print("\n" + LINE)
        print("ℹ️  참고사항")
        for note in plan.notes:
            print(f"  - {note}")

    print(LINE)


def main() -> int:
    settings = load_settings()

    try:
        verify_settings(settings)
    except MissingKeyError as exc:
        print(f"\n[설정 오류]\n{exc}\n")
        return 1

    user_input = collect_input()

    print("\n날씨와 장소를 조회하고 루트를 만드는 중입니다. 잠시만 기다려 주세요...")
    try:
        plan = run(user_input, settings)
    except WeatherError as exc:
        print(f"\n[날씨 조회 실패] {exc}\n")
        return 1
    except PlacesError as exc:
        print(f"\n[장소 검색 실패] {exc}\n")
        return 1
    except Exception as exc:  # 모델 호출 등 그 밖의 오류
        print(f"\n[실행 실패] {type(exc).__name__}: {exc}\n")
        return 1

    render(plan)
    return 0


if __name__ == "__main__":
    sys.exit(main())
