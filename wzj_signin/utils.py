import random
import sys
import time


def jitter_position(
    lon: str, lat: str, jitter_range: float = 0.0001
) -> tuple[str, str]:
    try:
        lon_f = float(lon)
        lat_f = float(lat)
    except ValueError:
        return lon, lat

    jittered_lon = lon_f + random.uniform(-jitter_range, jitter_range)
    jittered_lat = lat_f + random.uniform(-jitter_range, jitter_range)
    return f"{jittered_lon:.6f}", f"{jittered_lat:.6f}"


def sleep_with_progress(seconds: int, label: str = "Next poll in") -> None:
    # 非 TTY（重定向、nohup）下退化成纯 sleep，避免 \r 把日志文件刷成乱码。
    if seconds <= 0 or not sys.stderr.isatty():
        time.sleep(max(seconds, 0))
        return

    width = 24
    deadline = time.monotonic() + seconds
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            elapsed = seconds - remaining
            filled = int(width * elapsed / seconds)
            bar = "█" * filled + "░" * (width - filled)
            sys.stderr.write(f"\r{label} [{bar}] {int(elapsed):>2d}/{seconds}s")
            sys.stderr.flush()
            time.sleep(min(1.0, remaining))
    finally:
        sys.stderr.write("\r\033[K")
        sys.stderr.flush()


if __name__ == "__main__":
    original_lon = "116.397181"
    original_lat = "39.916575"
    for _ in range(5):
        new_lon, new_lat = jitter_position(original_lon, original_lat)
        print(
            f"Original: ({original_lon}, {original_lat}) -> Jittered: ({new_lon}, {new_lat})"
        )
