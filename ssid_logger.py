import time

from ssid_config import LOG_DIR, LOG_ENABLE, LOG_INTERVAL_SEC

_last_log_text: str = ""
_last_log_time: float = 0.0


def write_log(text: str) -> None:
    try:
        LOG_DIR.mkdir(exist_ok=True)
        log_file = LOG_DIR / f"{time.strftime('%Y-%m-%d')}.log"
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {text}\n")
    except Exception:
        pass


def maybe_write_log(text: str) -> None:
    global _last_log_text, _last_log_time
    if not LOG_ENABLE:
        return
    now = time.time()
    if text == _last_log_text and (now - _last_log_time) < LOG_INTERVAL_SEC:
        return
    write_log(text)
    _last_log_text = text
    _last_log_time = now
