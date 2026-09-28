"""Google Places API (New) 장소 검색.

Text Search(`places:searchText`)로 관광지와 식당을 찾아옴.
LLM은 여기서 받아온 목록 안에서만 고르도록 프롬프트에서 제한함.
"""

from __future__ import annotations

from typing import Dict, List

import requests

SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
TIMEOUT_SEC = 20

# 필요한 필드만 요청해야 과금과 응답 크기를 줄일 수 있음
FIELD_MASK = ",".join(
    [
        "places.displayName",
        "places.formattedAddress",
        "places.rating",
        "places.userRatingCount",
        "places.googleMapsUri",
        "places.primaryTypeDisplayName",
        "places.priceLevel",
    ]
)


class PlacesError(RuntimeError):
    """장소 검색 실패."""


def search_places(
    query: str,
    api_key: str,
    language: str = "ko",
    max_results: int = 10,
    min_rating: float = 4.0,
) -> List[Dict]:
    """텍스트 검색으로 장소 목록을 돌려줌.

    Args:
        query: 검색어 (예: "서울 관광지", "부산 해운대 맛집")
        api_key: Google Places API 키
        language: 응답 언어
        max_results: 최대 결과 수
        min_rating: 이 평점 미만은 제외. 결과가 하나도 없으면 필터를 풀고 다시 담음
    """

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
    }
    body = {
        "textQuery": query,
        "languageCode": language,
        "maxResultCount": max_results,
    }

    try:
        res = requests.post(SEARCH_URL, headers=headers, json=body, timeout=TIMEOUT_SEC)
    except requests.RequestException as exc:
        raise PlacesError(f"장소 서버에 연결하지 못함: {exc}") from exc

    if res.status_code in (401, 403):
        raise PlacesError(
            "Google Places 키가 거부됨. 키가 맞는지, Cloud Console에서 "
            "'Places API (New)'가 사용 설정되어 있는지 확인 필요"
        )
    if res.status_code != 200:
        raise PlacesError(f"장소 검색 실패 (HTTP {res.status_code}): {res.text[:300]}")

    raw = res.json().get("places", [])
    parsed = [
        {
            "name": p.get("displayName", {}).get("text", "이름 없음"),
            "category": p.get("primaryTypeDisplayName", {}).get("text", ""),
            "rating": p.get("rating"),
            "review_count": p.get("userRatingCount"),
            "address": p.get("formattedAddress", ""),
            "map_url": p.get("googleMapsUri", ""),
            "price_level": p.get("priceLevel", ""),
        }
        for p in raw
    ]

    filtered = [p for p in parsed if (p["rating"] or 0) >= min_rating]
    # 평점 조건을 만족하는 곳이 없으면, 빈 목록 대신 원본을 돌려주고
    # 프롬프트에서 "평점 조건 미달"임을 LLM이 알 수 있게 함
    return filtered if filtered else parsed


def format_for_prompt(title: str, places: List[Dict]) -> str:
    """장소 목록을 프롬프트에 넣기 좋은 여러 줄 문자열로 변환."""

    if not places:
        return f"[{title}]\n- 검색 결과 없음"

    lines = [f"[{title}]"]
    for p in places:
        rating = f"{p['rating']}점" if p["rating"] else "평점 없음"
        reviews = f"리뷰 {p['review_count']}개" if p["review_count"] else "리뷰 수 없음"
        lines.append(
            f"- {p['name']} | {p['category'] or '분류 없음'} | {rating} | {reviews}\n"
            f"  주소: {p['address']}\n"
            f"  지도: {p['map_url']}"
        )
    return "\n".join(lines)
