import unittest

from wzj_signin.http_client import (
    ACTIVE_SIGNS_PATH,
    SIGN_IN_PATH,
    SignTarget,
    build_request_config,
    get_active_signs,
    make_session,
    submit_sign_in,
)


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.raise_called = False

    def raise_for_status(self):
        self.raise_called = True

    def json(self):
        return self._payload


class _FakeSession:
    def __init__(self):
        self.get_calls = []
        self.post_calls = []

    def get(self, url, timeout):
        self.get_calls.append({"url": url, "timeout": timeout})
        return _FakeResponse([{"signId": 1}])

    def post(self, url, data, timeout):
        self.post_calls.append({"url": url, "data": data, "timeout": timeout})
        return _FakeResponse({"ok": True})


class HttpClientTests(unittest.TestCase):
    def test_build_request_config_extracts_openid_and_base_url(self):
        config = build_request_config(
            open_id=r"https://v18.teachermate.cn/wechat-pro-ssr/\?openid\=abc123\&from\=wzj",
            api_base_url=None,
            connect_timeout=5.0,
            read_timeout=15.0,
            request_retries=2,
            retry_backoff=1.0,
        )

        self.assertEqual(config.open_id, "abc123")
        self.assertEqual(config.api_base_url, "https://v18.teachermate.cn")
        self.assertEqual(config.timeout, (5.0, 15.0))

    def test_build_request_config_requires_openid_query_param(self):
        with self.assertRaisesRegex(ValueError, "missing openid"):
            build_request_config(
                open_id="https://v18.teachermate.cn/wechat-pro-ssr/?from=wzj",
                api_base_url=None,
                connect_timeout=5.0,
                read_timeout=15.0,
                request_retries=2,
                retry_backoff=1.0,
            )

    def test_make_session_sets_headers_and_connect_retry_policy(self):
        config = build_request_config(
            open_id="abc123",
            api_base_url="https://example.com",
            connect_timeout=5.0,
            read_timeout=15.0,
            request_retries=2,
            retry_backoff=1.0,
        )

        session = make_session("ua-test", config)
        adapter = session.get_adapter("https://example.com")

        self.assertEqual(session.headers["User-Agent"], "ua-test")
        self.assertEqual(session.headers["openId"], "abc123")
        self.assertEqual(adapter.max_retries.connect, 2)
        self.assertEqual(adapter.max_retries.read, 0)
        self.assertEqual(adapter.max_retries.backoff_factor, 1.0)
        self.assertEqual(adapter.max_retries.allowed_methods, frozenset({"GET", "POST"}))

    def test_get_active_signs_uses_configured_url_and_timeout(self):
        config = build_request_config(
            open_id="abc123",
            api_base_url="https://example.com",
            connect_timeout=3.0,
            read_timeout=9.0,
            request_retries=1,
            retry_backoff=0.5,
        )
        session = _FakeSession()

        payload = get_active_signs(session, config)

        self.assertEqual(payload, [{"signId": 1}])
        self.assertEqual(
            session.get_calls,
            [{"url": f"https://example.com{ACTIVE_SIGNS_PATH}", "timeout": (3.0, 9.0)}],
        )

    def test_submit_sign_in_uses_configured_url_payload_and_timeout(self):
        config = build_request_config(
            open_id="abc123",
            api_base_url="https://example.com",
            connect_timeout=3.0,
            read_timeout=9.0,
            request_retries=1,
            retry_backoff=0.5,
        )
        session = _FakeSession()

        payload = submit_sign_in(
            session,
            config,
            SignTarget("test", 101, 202, ("113.1", "22.2")),
        )

        self.assertEqual(payload, {"ok": True})
        self.assertEqual(
            session.post_calls,
            [
                {
                    "url": f"https://example.com{SIGN_IN_PATH}",
                    "data": {
                        "courseId": 101,
                        "signId": 202,
                        "lon": "113.1",
                        "lat": "22.2",
                    },
                    "timeout": (3.0, 9.0),
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
