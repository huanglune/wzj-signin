import os
import smtplib
import tomllib
from email.header import Header
from email.mime.text import MIMEText
from pathlib import Path

from wzj_signin.logger import log


def _load_email_config() -> dict:
    """Load email config: env vars take priority, config.toml [email] as fallback."""
    file_cfg = {}
    config_path = Path.cwd() / "config.toml"
    if config_path.exists():
        with open(config_path, "rb") as f:
            file_cfg = tomllib.load(f).get("email", {})

    return {
        "enable": (
            os.environ.get("ENABLE_SEND_EMAIL", "").lower() in ("1", "true")
            or file_cfg.get("enable_send_email", False)
        ),
        "smtp_server": os.environ.get("SMTP_SERVER")
        or file_cfg.get("smtp_server", "smtp.qq.com"),
        "sender": os.environ.get("EMAIL_SENDER") or file_cfg.get("sender", ""),
        "password": os.environ.get("EMAIL_PASSWORD") or file_cfg.get("password", ""),
        "receiver": os.environ.get("EMAIL_RECEIVER") or file_cfg.get("receiver", ""),
    }


cfg = _load_email_config()
if cfg["enable"]:
    if not all([cfg["sender"], cfg["password"], cfg["receiver"]]):
        log.error("Email notification enabled but config incomplete, check sender/password/receiver")
        raise SystemExit(1)
    try:
        server = smtplib.SMTP_SSL(cfg["smtp_server"], 465, timeout=10)
        server.login(cfg["sender"], cfg["password"])
        server.quit()
        log.info("Email notification enabled, SMTP verified, sending to: %s", cfg["receiver"])
    except Exception as e:
        log.error("SMTP login verification failed: %s", e)
        raise SystemExit(1)
else:
    log.info("Email notification disabled")


def send_email(subject: str, content: str) -> bool:
    """Send email notification. Returns True on success."""
    if not cfg["enable"]:
        return False

    subject = "[wzj-signin] " + subject
    message = MIMEText(content, "plain", "utf-8")
    message["From"] = cfg["sender"]
    message["To"] = cfg["receiver"]
    message["Subject"] = Header(subject, "utf-8")

    try:
        server = smtplib.SMTP_SSL(cfg["smtp_server"], 465)
        server.login(cfg["sender"], cfg["password"])
        server.sendmail(cfg["sender"], [cfg["receiver"]], message.as_string())
        server.quit()
        log.info("Email sent: %s", subject)
        return True
    except Exception as e:
        log.error("Email send failed: %s", e)
        return False
