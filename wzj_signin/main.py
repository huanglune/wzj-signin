import os
import sys
import time
import tomllib
from pathlib import Path

import requests

from wzj_signin.email import send_email
from wzj_signin.http_client import (
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_READ_TIMEOUT,
    DEFAULT_RETRY_BACKOFF,
    DEFAULT_REQUEST_RETRIES,
    RequestConfig,
    SignTarget,
    build_request_config,
    get_active_signs,
    make_session,
    submit_sign_in,
)
from wzj_signin.logger import log
from wzj_signin.qrsign import QRSign
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
    poll_interval = _parse_int(
        os.environ.get("POLL_INTERVAL") or file_cfg.get("pollInterval", 10),
        "POLL_INTERVAL",
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

    try:
        request_config = build_request_config(
            open_id=open_id,
            api_base_url=os.environ.get("API_BASE_URL") or file_cfg.get("apiBaseUrl"),
            connect_timeout=_parse_float(
                os.environ.get("CONNECT_TIMEOUT")
                or file_cfg.get("connectTimeout", DEFAULT_CONNECT_TIMEOUT),
                "CONNECT_TIMEOUT",
            ),
            read_timeout=_parse_float(
                os.environ.get("READ_TIMEOUT")
                or file_cfg.get("readTimeout", DEFAULT_READ_TIMEOUT),
                "READ_TIMEOUT",
            ),
            request_retries=_parse_int(
                os.environ.get("REQUEST_RETRIES")
                or file_cfg.get("requestRetries", DEFAULT_REQUEST_RETRIES),
                "REQUEST_RETRIES",
            ),
            retry_backoff=_parse_float(
                os.environ.get("RETRY_BACKOFF")
                or file_cfg.get("retryBackoff", DEFAULT_RETRY_BACKOFF),
                "RETRY_BACKOFF",
            ),
        )
    except ValueError as exc:
        log.error(str(exc))
        sys.exit(1)

    return {
        "courseId": course_id,
        "studentId": student_id,
        "pollInterval": poll_interval,
        "positions": positions,
        "requestConfig": request_config,
    }


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
)

signed_ids: set[int] = set()


def _parse_int(value: str | int, name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc


def _parse_float(value: str | float, name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a number") from exc


def sign_in_one(
    session: requests.Session,
    request_config: RequestConfig,
    sign_target: SignTarget,
) -> bool:
    result = submit_sign_in(session, request_config, sign_target)
    if "errorCode" in result:
        if result.get("errorCode") == 305:
            log.info(
                "%s already signed signId=%s: %s",
                sign_target.course_name,
                sign_target.sign_id,
                result.get("msgClient"),
            )
            return True
        log.warning(
            "%s sign-in failed signId=%s: %s",
            sign_target.course_name,
            sign_target.sign_id,
            result.get("msgClient", result),
        )
        return False
    log.info(
        "%s sign-in success signId=%s rank:%s",
        sign_target.course_name,
        sign_target.sign_id,
        result.get("studentRank"),
    )
    return True


def process_signs(
    session: requests.Session,
    request_config: RequestConfig,
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

            elif sign_in_one(
                session,
                request_config,
                SignTarget(course_name, course_id, sign_id, positions),
            ):
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
        if sign_in_one(
            session,
            request_config,
            SignTarget(course_name, course_id, sign_id),
        ):
            signed_ids.add(sign_id)
            send_email("Sign-in Success", f"{course_name} normal sign-in success signId={sign_id}")


def main() -> None:
    config = _load_config()
    request_config = config["requestConfig"]
    session = make_session(USER_AGENT, request_config)
    student_id = config["studentId"]
    poll_interval = config["pollInterval"]
    positions = config["positions"]

    log.info(
        "Sign-in monitor started, polling every %d seconds (connect timeout %.1fs, read timeout %.1fs, retries %d)",
        poll_interval,
        request_config.connect_timeout,
        request_config.read_timeout,
        request_config.request_retries,
    )
    consecutive_errors = 0

    while True:
        try:
            signs = get_active_signs(session, request_config)
            consecutive_errors = 0
            if signs:
                process_signs(session, request_config, signs, student_id, positions)
            else:
                log.debug("No active sign-ins")
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 401:
                log.error("openId expired, please update config")
                send_email("Monitor Error", "openId expired, please update config")
                return
            consecutive_errors += 1
            log.error("Request error (consecutive #%d): %s", consecutive_errors, e)
        except requests.ConnectTimeout as e:
            consecutive_errors += 1
            log.error(
                "Connect timeout to %s (consecutive #%d, timeout %.1fs, retries %d): %s",
                request_config.api_base_url,
                consecutive_errors,
                request_config.connect_timeout,
                request_config.request_retries,
                e,
            )
        except requests.ReadTimeout as e:
            consecutive_errors += 1
            log.error(
                "Read timeout from %s (consecutive #%d, timeout %.1fs): %s",
                request_config.api_base_url,
                consecutive_errors,
                request_config.read_timeout,
                e,
            )
        except requests.RequestException as e:
            consecutive_errors += 1
            log.error("Request error (consecutive #%d): %s", consecutive_errors, e)
        except Exception:
            log.exception("Unknown error")
        time.sleep(poll_interval)
