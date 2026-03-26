"""코인 한글/영문 이름 매핑 (Upbit API 기반)"""
import time
import requests
import logging

logger = logging.getLogger(__name__)

_names: dict[str, dict] = {}  # ticker -> {"kr": "비트코인", "en": "Bitcoin"}
_loaded_at: float = 0


def _load():
    global _names, _loaded_at
    try:
        resp = requests.get("https://api.upbit.com/v1/market/all?is_details=false", timeout=10)
        resp.raise_for_status()
        for item in resp.json():
            market = item["market"]
            _names[market] = {
                "kr": item.get("korean_name", ""),
                "en": item.get("english_name", ""),
            }
        _loaded_at = time.time()
        logger.info(f"Loaded {len(_names)} coin names")
    except Exception as e:
        logger.error(f"Failed to load coin names: {e}")


def get_coin_name(ticker: str) -> dict:
    """{"kr": "비트코인", "en": "Bitcoin"}"""
    if time.time() - _loaded_at > 3600:  # 1시간마다 갱신
        _load()
    return _names.get(ticker, {"kr": "", "en": ""})


def get_all_names() -> dict[str, dict]:
    if time.time() - _loaded_at > 3600:
        _load()
    return _names
