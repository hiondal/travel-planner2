"""환경 설정 로딩 및 사전 검증.

`.env` 파일에서 API 키와 모델명을 읽어오고, 앱 실행 전에 필수 값이
채워져 있는지 확인함. 키가 없으면 실행 중간이 아니라 시작 시점에
바로 알려주기 위함.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# 프로젝트 루트(= app/ 의 상위)에 있는 .env 를 읽음
ROOT_DIR = Path(__file__).resolve().parent.parent
APP_DIR = Path(__file__).resolve().parent
PROMPT_DIR = APP_DIR / "prompts"

load_dotenv(ROOT_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    """앱이 사용하는 설정값 모음."""

    groq_api_key: str
    groq_model: str
    openweather_api_key: str
    google_places_api_key: str
    contact_email: str


def load_settings() -> Settings:
    return Settings(
        groq_api_key=os.getenv("GROQ_API_KEY", "").strip(),
        groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip(),
        openweather_api_key=os.getenv("OPENWEATHER_API_KEY", "").strip(),
        google_places_api_key=os.getenv("GOOGLE_PLACES_API_KEY", "").strip(),
        contact_email=os.getenv("CONTACT_EMAIL", "").strip(),
    )


class MissingKeyError(RuntimeError):
    """필수 API 키가 비어 있을 때 발생."""


def verify_settings(settings: Settings) -> None:
    """필수 키가 비어 있으면 무엇을 어디서 받아야 하는지 알려주고 중단함."""

    required = {
        "GROQ_API_KEY": (settings.groq_api_key, "https://console.groq.com/keys"),
        "OPENWEATHER_API_KEY": (
            settings.openweather_api_key,
            "https://home.openweathermap.org/api_keys",
        ),
        "GOOGLE_PLACES_API_KEY": (
            settings.google_places_api_key,
            "https://console.cloud.google.com/apis/credentials",
        ),
    }

    missing = [(name, url) for name, (value, url) in required.items() if not value]
    if missing:
        lines = ["`.env` 파일에 아래 값이 비어 있어 실행할 수 없음:"]
        lines += [f"  - {name}  → 발급: {url}" for name, url in missing]
        raise MissingKeyError("\n".join(lines))
