"""
Randomly jitter coordinates to avoid identical positions on each sign-in.
"""

import random


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


if __name__ == "__main__":
    # test
    original_lon = "116.397181"
    original_lat = "39.916575"
    for _ in range(5):
        new_lon, new_lat = jitter_position(original_lon, original_lat)
        print(
            f"Original: ({original_lon}, {original_lat}) -> Jittered: ({new_lon}, {new_lat})"
        )
