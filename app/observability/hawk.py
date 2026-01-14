from __future__ import annotations

from hawk_python_sdk.modules.fastapi import HawkFastapi

from app.core.config import settings

_hawk: HawkFastapi | None = None


def init_hawk(app) -> None:
    global _hawk

    params: dict[str, object] = {
        "app_instance": app,
        "token": settings.HAWK_TOKEN,
    }

    _hawk = HawkFastapi(params)


def capture_exception(exc: Exception) -> None:
    if _hawk is None:
        return

    try:
        _hawk.capture_exception(exc)
    except Exception:
        return
