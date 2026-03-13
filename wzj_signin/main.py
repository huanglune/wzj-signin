import os
import sys
import time
import tomllib
from pathlib import Path

import requests

from wzj_signin.qrsign import QRSign
from wzj_signin.logger import log
from wzj_signin.email import send_email
from wzj_signin.utils import jitter_position


def _load_config() -> dict:
    """Load config: env vars take priority, config.toml as fallback."""
    file_cfg = {}
    config_path = Path.cwd() / "config.toml"
    if config_path.exists():
        with open(config_path, "rb") as f:
            file_cfg = tomllib.load(f).get("default", {})

    open_id = os.environ.get("OPEN_ID") or file_cfg.get("openId")
    course_id = os.environ.get("COURSE_ID") or file_cfg.get("courseId")
    student_id = os.environ.get("STUDENT_ID") or file_cfg.get("studentId", "")
    poll_interval = int(
        os.environ.get("POLL_INTERVAL") or file_cfg.get("pollInterval", 10)
    )
    gps_lon = os.environ.get("GPS_LON") or file_cfg.get("gps_lon", "")
    gps_lat = os.environ.get("GPS_LAT") or file_cfg.get("gps_lat", "")
    positions = jitter_position(gps_lon, gps_lat) if gps_lon and gps_lat else None

    if not open_id:
        log.error("Missing OPEN_ID, set env var or provide config.toml")
        sys.exit(1)
    if not course_id:
        log.error("Missing COURSE_ID, set env var or provide config.toml")
        sys.exit(1)

    # https://v18.teachermate.cn/wechat-pro-ssr/\?openid\=97352238a0bb10f19d912ade240511ec\&from\=wzj
    # https://v18.teachermate.cn/wechat-pro-ssr/?openid=97352238a0bb10f19d912ade240511ec&from=wzj
    # Support pasting the full URL as openId, auto-extract the openid param
    if open_id.startswith("https://"):
        open_id = open_id.replace(r"\?", "?").replace(r"\=", "=").replace(r"\&", "&")
        open_id = open_id.split("openid=")[-1].split("&")[0]

    return {
        "openId": open_id,
        "courseId": course_id,
        "studentId": student_id,
        "pollInterval": poll_interval,
        "positions": positions,
    }


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
)

signed_ids: set[int] = set()


def _make_session(open_id: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "openId": open_id})
    return s


def get_active_signs(session: requests.Session) -> list[dict]:
    url = (
        "https://v18.teachermate.cn/wechat-api/v1/class-attendance/student/active_signs"
    )
    resp = session.get(url, timeout=15)
    resp.raise_for_status()
    return resp.json()


def sign_in_one(
    session: requests.Session,
    course_name: str,
    course_id: int,
    sign_id: int,
    positions: tuple[str, str] = None,
) -> bool:
    url = "https://v18.teachermate.cn/wechat-api/v1/class-attendance/student-sign-in"
    data = {"courseId": course_id, "signId": sign_id}
    if positions:
        data["lon"] = positions[0]
        data["lat"] = positions[1]

    resp = session.post(url, data=data, timeout=15)
    resp.raise_for_status()
    result = resp.json()
    if "errorCode" in result:
        if result.get("errorCode") == 305:
            log.info(
                "%s already signed signId=%s: %s",
                course_name,
                sign_id,
                result.get("msgClient"),
            )
            return True
        log.warning(
            "%s sign-in failed signId=%s: %s",
            course_name,
            sign_id,
            result.get("msgClient", result),
        )
        return False
    log.info(
        "%s sign-in success signId=%s rank:%s", course_name, sign_id, result.get("studentRank")
    )
    return True


def process_signs(
    session: requests.Session,
    signs: list[dict],
    student_id: str,
    positions: tuple[str, str] | None,
) -> None:
    for sign in signs:
        sign_id = sign["signId"]
        course_id = sign["courseId"]
        course_name = sign.get("name", "")
        name = sign.get("name", "")

        if sign_id in signed_ids:
            continue

        if sign.get("isGPS") == 1:
            log.info("GPS sign-in found: %s (signId=%s)", name, sign_id)
            if not positions:
                log.warning("GPS coordinates not configured, cannot sign in")
                send_email(
                    "GPS Sign-in Failed",
                    f"{course_name} GPS sign-in signId={sign_id}, but GPS coordinates not configured",
                )
                signed_ids.add(sign_id)

            elif sign_in_one(session, course_name, course_id, sign_id, positions):
                send_email(
                    "Sign-in Success", f"{course_name} GPS sign-in success signId={sign_id}"
                )
                signed_ids.add(sign_id)

            continue

        if sign.get("isQR") == 1:
            log.info("QR sign-in found: %s (signId=%s)", name, sign_id)

            send_email(
                "QR Sign-in Found",
                f"{course_name} QR sign-in signId={sign_id}, please scan the QR code ASAP...",
            )
            qr = QRSign(str(course_id), sign_id, student_id)
            if qr.start():
                signed_ids.add(sign_id)
                send_email(
                    "Sign-in Success", f"{course_name} QR sign-in success signId={sign_id}"
                )
            continue

        log.info("Normal sign-in found: %s (signId=%s)", name, sign_id)
        if sign_in_one(session, course_name, course_id, sign_id):
            signed_ids.add(sign_id)
            send_email("Sign-in Success", f"{course_name} normal sign-in success signId={sign_id}")


def main() -> None:
    config = _load_config()
    session = _make_session(config["openId"])
    student_id = config["studentId"]
    poll_interval = config["pollInterval"]
    positions = config["positions"]

    log.info("Sign-in monitor started, polling every %d seconds", poll_interval)
    consecutive_errors = 0

    while True:
        try:
            signs = get_active_signs(session)
            consecutive_errors = 0
            if signs:
                process_signs(session, signs, student_id, positions)
            else:
                log.debug("No active sign-ins")
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 401:
                log.error("openId expired, please update config")
                send_email("Monitor Error", "openId expired, please update config")
                return
            consecutive_errors += 1
            log.error("Request error (consecutive #%d): %s", consecutive_errors, e)
        except requests.RequestException as e:
            consecutive_errors += 1
            log.error("Request error (consecutive #%d): %s", consecutive_errors, e)
        except Exception:
            log.exception("Unknown error")
        time.sleep(poll_interval)
