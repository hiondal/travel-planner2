"""OpenWeatherMap 날씨 조회.

무료 플랜에서 제공하는 5일 / 3시간 단위 예보(`/data/2.5/forecast`)를 사용함.
LLM이 추측하지 않도록, 여기서 받아온 실제 예보만 프롬프트에 넣어줌.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

import requests

FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
TIMEOUT_SEC = 15


class WeatherError(RuntimeError):
    """날씨 조회 실패."""


def fetch_forecast(city: str, country: str, api_key: str, days: int) -> List[Dict]:
    """도시의 일자별 날씨 요약을 돌려줌.

    Args:
        city: 도시 이름 (예: "Seoul")
        country: 국가 이름 또는 ISO 코드 (예: "KR", "South Korea")
        api_key: OpenWeatherMap API 키
        days: 필요한 일수. 무료 플랜 한계로 최대 5일까지만 채워짐

    Returns:
        [{"day": 1, "date": "2026-09-28", "temp_min": 18.2, "temp_max": 26.0,
          "description": "구름 조금", "rain_prob_max": 0.3}, ...]
    """

    query = f"{city},{country}" if country else city
    params = {
        "q": query,
        "appid": api_key,
        "units": "metric",  # 섭씨
        "lang": "kr",       # 한국어 설명
    }

    try:
        res = requests.get(FORECAST_URL, params=params, timeout=TIMEOUT_SEC)
    except requests.RequestException as exc:
        raise WeatherError(f"날씨 서버에 연결하지 못함: {exc}") from exc

    if res.status_code == 401:
        raise WeatherError(
            "OpenWeatherMap 키가 거부됨(401). 키가 맞는지, 발급 직후라면 "
            "활성화(보통 수십 분)가 끝났는지 확인 필요"
        )
    if res.status_code == 404:
        raise WeatherError(f"도시를 찾지 못함: {query}. 영문 도시명으로 입력 필요")
    if res.status_code != 200:
        raise WeatherError(f"날씨 조회 실패 (HTTP {res.status_code}): {res.text[:200]}")

    payload = res.json()
    buckets: Dict[str, List[Dict]] = defaultdict(list)
    for slot in payload.get("list", []):
        date = slot["dt_txt"][:10]  # "2026-09-28 12:00:00" → "2026-09-28"
        buckets[date].append(slot)

    summaries: List[Dict] = []
    for index, date in enumerate(sorted(buckets)[:days], start=1):
        slots = buckets[date]
        temps = [s["main"]["temp"] for s in slots]
        # 하루 중 가장 많이 나온 날씨 설명을 대표값으로 사용
        descriptions = [s["weather"][0]["description"] for s in slots]
        representative = max(set(descriptions), key=descriptions.count)
        rain_probs = [s.get("pop", 0) for s in slots]

        summaries.append(
            {
                "day": index,
                "date": date,
                "temp_min": round(min(temps), 1),
                "temp_max": round(max(temps), 1),
                "description": representative,
                "rain_prob_max": round(max(rain_probs), 2) if rain_probs else 0.0,
            }
        )

    if not summaries:
        raise WeatherError(f"예보 자료가 비어 있음: {query}")

    return summaries


def format_for_prompt(summaries: List[Dict], days: int) -> str:
    """예보를 프롬프트에 넣기 좋은 여러 줄 문자열로 변환."""

    lines = []
    for item in summaries:
        lines.append(
            f"- {item['day']}일차 ({item['date']}): {item['description']}, "
            f"{item['temp_min']}°C ~ {item['temp_max']}°C, "
            f"강수확률 최대 {int(item['rain_prob_max'] * 100)}%"
        )

    if days > len(summaries):
        lines.append(
            f"- {len(summaries) + 1}일차 이후: 예보 자료 없음"
            " (무료 플랜은 5일까지만 제공). 날씨 기반 추천 불가로 명시할 것"
        )

    return "\n".join(lines)
