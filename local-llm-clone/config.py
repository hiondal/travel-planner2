"""환경 설정 로딩 및 사전 검증 (Local LLM 버전).

Cloud LLM 버전과 달리 LLM API 키가 필요 없음. 모델은 로컬 Ollama 런타임에서
실행되므로, 확인할 대상은 Ollama 서버 주소와 모델명임.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# 프로젝트 루트(= local-llm/ 의 상위)에 있는 .env 를 읽음
ROOT_DIR = Path(__file__).resolve().parent.parent
APP_DIR = Path(__file__).resolve().parent
PROMPT_DIR = APP_DIR / "prompts"

load_dotenv(ROOT_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    """앱이 사용하는 설정값 모음."""

    ollama_model: str
    ollama_base_url: str
    openweather_api_key: str
    google_places_api_key: str
    contact_email: str


def load_settings() -> Settings:
    return Settings(
        ollama_model=os.getenv("OLLAMA_MODEL", "gemma3:4b").strip(),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip(),
        openweather_api_key=os.getenv("OPENWEATHER_API_KEY", "").strip(),
        google_places_api_key=os.getenv("GOOGLE_PLACES_API_KEY", "").strip(),
        contact_email=os.getenv("CONTACT_EMAIL", "").strip(),
    )


class MissingKeyError(RuntimeError):
    """필수 설정값이 비어 있거나 Ollama에 연결할 수 없을 때 발생."""


def verify_settings(settings: Settings) -> None:
    """외부 API 키와 Ollama 런타임 상태를 실행 전에 확인함."""

    required = {
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

    _verify_ollama(settings)


def _verify_ollama(settings: Settings) -> None:
    """Ollama 서버가 떠 있고 모델이 받아져 있는지 확인함."""

    import requests

    try:
        res = requests.get(f"{settings.ollama_base_url}/api/tags", timeout=5)
        res.raise_for_status()
    except Exception as exc:
        raise MissingKeyError(
            f"Ollama에 연결하지 못함 ({settings.ollama_base_url}).\n"
            "  - 설치: https://ollama.com/download\n"
            "  - 설치 후 Ollama 실행 상태인지 확인 필요"
        ) from exc

    installed = [m.get("name", "") for m in res.json().get("models", [])]
    if not any(name.startswith(settings.ollama_model) for name in installed):
        raise MissingKeyError(
            f"모델 '{settings.ollama_model}' 이(가) 받아져 있지 않음.\n"
            f"  - 내려받기: ollama pull {settings.ollama_model}\n"
            f"  - 현재 설치된 모델: {', '.join(installed) or '없음'}"
        )
