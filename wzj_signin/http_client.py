from dataclasses import dataclass
from urllib.parse import parse_qs, urlsplit

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


DEFAULT_API_BASE_URL = "https://v18.teachermate.cn"
DEFAULT_CONNECT_TIMEOUT = 5.0
DEFAULT_READ_TIMEOUT = 15.0
DEFAULT_REQUEST_RETRIES = 2
DEFAULT_RETRY_BACKOFF = 1.0
ACTIVE_SIGNS_PATH = "/wechat-api/v1/class-attendance/student/active_signs"
SIGN_IN_PATH = "/wechat-api/v1/class-attendance/student-sign-in"


@dataclass(frozen=True)
class RequestConfig:
    open_id: str
    api_base_url: str
    connect_timeout: float
    read_timeout: float
    request_retries: int
    retry_backoff: float

    @property
    def timeout(self) -> tuple[float, float]:
        return (self.connect_timeout, self.read_timeout)

    def api_url(self, path: str) -> str:
        return f"{self.api_base_url.rstrip('/')}/{path.lstrip('/')}"


@dataclass(frozen=True)
class SignTarget:
    course_name: str
    course_id: int
    sign_id: int
    positions: tuple[str, str] | None = None


def build_request_config(
    open_id: str,
    api_base_url: str | None,
    connect_timeout: float,
    read_timeout: float,
    request_retries: int,
    retry_backoff: float,
) -> RequestConfig:
    normalized = _normalize_open_id(open_id)
    extracted_open_id, derived_base_url = _extract_open_id_and_base_url(normalized)
    selected_base_url = (api_base_url or derived_base_url or DEFAULT_API_BASE_URL).rstrip("/")
    _validate_timeouts(connect_timeout, read_timeout)
    _validate_retry_settings(request_retries, retry_backoff)
    return RequestConfig(
        open_id=extracted_open_id,
        api_base_url=selected_base_url,
        connect_timeout=connect_timeout,
        read_timeout=read_timeout,
        request_retries=request_retries,
        retry_backoff=retry_backoff,
    )


def make_session(user_agent: str, request_config: RequestConfig) -> requests.Session:
    session = requests.Session()
    # TeacherMate 是国内 API，禁用 HTTPS_PROXY 等环境变量避免被本地代理拦截。
    session.trust_env = False
    session.headers.update({"User-Agent": user_agent, "openId": request_config.open_id})
    adapter = HTTPAdapter(max_retries=_build_retry(request_config))
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def get_active_signs(
    session: requests.Session,
    request_config: RequestConfig,
) -> list[dict]:
    response = session.get(
        request_config.api_url(ACTIVE_SIGNS_PATH),
        timeout=request_config.timeout,
    )
    response.raise_for_status()
    return response.json()


def submit_sign_in(
    session: requests.Session,
    request_config: RequestConfig,
    sign_target: SignTarget,
) -> dict:
    data = {"courseId": sign_target.course_id, "signId": sign_target.sign_id}
    if sign_target.positions:
        data["lon"] = sign_target.positions[0]
        data["lat"] = sign_target.positions[1]

    response = session.post(
        request_config.api_url(SIGN_IN_PATH),
        data=data,
        timeout=request_config.timeout,
    )
    response.raise_for_status()
    return response.json()


def _build_retry(request_config: RequestConfig) -> Retry:
    return Retry(
        total=None,
        connect=request_config.request_retries,
        read=0,
        status=0,
        other=0,
        allowed_methods=frozenset({"GET", "POST"}),
        backoff_factor=request_config.retry_backoff,
        raise_on_status=False,
    )


def _extract_open_id_and_base_url(open_id: str) -> tuple[str, str | None]:
    if not open_id.startswith(("http://", "https://")):
        return open_id, None

    parsed = urlsplit(open_id)
    open_id_values = parse_qs(parsed.query).get("openid")
    if not open_id_values:
        raise ValueError("OPEN_ID URL missing openid parameter")
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    return open_id_values[0], base_url


def _normalize_open_id(open_id: str) -> str:
    return open_id.replace(r"\?", "?").replace(r"\=", "=").replace(r"\&", "&").strip()


def _validate_timeouts(connect_timeout: float, read_timeout: float) -> None:
    if connect_timeout <= 0:
        raise ValueError("CONNECT_TIMEOUT must be greater than 0")
    if read_timeout <= 0:
        raise ValueError("READ_TIMEOUT must be greater than 0")


def _validate_retry_settings(request_retries: int, retry_backoff: float) -> None:
    if request_retries < 0:
        raise ValueError("REQUEST_RETRIES cannot be negative")
    if retry_backoff < 0:
        raise ValueError("RETRY_BACKOFF cannot be negative")
