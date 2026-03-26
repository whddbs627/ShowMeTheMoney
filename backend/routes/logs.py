import asyncio
from fastapi import APIRouter
from backend.engine import bot_manager
from backend.auth import get_current_user
from fastapi import Depends

router = APIRouter(tags=["logs"])

# In-memory log buffer per user (last 200 entries)
_log_buffers: dict[int, list[str]] = {}
MAX_LOG_SIZE = 200


def add_log(user_id: int, message: str):
    if user_id not in _log_buffers:
        _log_buffers[user_id] = []
    buf = _log_buffers[user_id]
    from datetime import datetime, timezone, timedelta
    KST = timezone(timedelta(hours=9))
    ts = datetime.now(KST).strftime("%H:%M:%S")
    buf.append(f"[{ts}] {message}")
    if len(buf) > MAX_LOG_SIZE:
        _log_buffers[user_id] = buf[-MAX_LOG_SIZE:]


@router.get("/logs")
async def get_logs(user: dict = Depends(get_current_user)):
    """Get backend logs + docker container logs"""
    import subprocess
    try:
        result = await asyncio.to_thread(
            subprocess.run,
            ["docker", "logs", "--tail", "100", "app-backend-1"],
            capture_output=True, text=True, timeout=5,
        )
        container_logs = result.stdout[-3000:] if result.stdout else result.stderr[-3000:]
    except Exception:
        container_logs = "Cannot read container logs"

    user_logs = _log_buffers.get(user["id"], [])

    return {
        "user_logs": user_logs[-100:],
        "system_logs": container_logs.split("\n")[-50:],
    }
