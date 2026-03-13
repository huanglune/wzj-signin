<div align="center">

# wzj-signin

**Auto sign-in tool for TeacherMate (微助教)**

[![PyPI](https://img.shields.io/pypi/v/wzj-signin.svg)](https://pypi.org/project/wzj-signin/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/wzj-signin.svg)](https://pypi.org/project/wzj-signin/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/huanglune/wzj-signin/blob/main/LICENSE)

English | [中文](https://github.com/huanglune/wzj-signin/blob/main/README.zh-CN.md)

</div>

---

## Features

- **Normal sign-in** — fully automatic
- **GPS sign-in** — auto sign-in with configured coordinates, with random jitter to avoid detection
- **QR sign-in** — displays QR code in terminal for scanning
- **Email notification** — sends alerts on sign-in success/failure

## Installation

```bash
pip install wzj-signin
```

Or run directly without installing:

```bash
uvx wzj-signin
```

## Quick Start

### Environment Variables (Recommended)

```bash
OPEN_ID=xxx COURSE_ID=123 STUDENT_ID=456 wzj-signin
```

You can also pass the full TeacherMate URL as OPEN_ID:

```bash
OPEN_ID="https://v18.teachermate.cn/wechat-pro-ssr/?openid=xxx&from=wzj" COURSE_ID=123 uvx wzj-signin
```

### Config File

Place a `config.toml` in the working directory (see [config.toml.example](https://github.com/huanglune/wzj-signin/blob/main/config.toml.example)):

```toml
[default]
openId = "xxx"
courseId = "123"
studentId = "456"
pollInterval = 10

# GPS coordinates (optional)
gps_lon = 113.999877
gps_lat = 22.595876

# Email notification (optional)
[email]
enable_send_email = false
smtp_server = "smtp.qq.com"
sender = "your@qq.com"
password = "your_smtp_password"
receiver = "notify@example.com"
```

> Environment variables take priority over config file values.

## Environment Variables

| Variable | Description | Required |
|:---------|:------------|:--------:|
| `OPEN_ID` | TeacherMate openId or full URL | ✅ |
| `COURSE_ID` | Course ID | ✅ |
| `STUDENT_ID` | Student ID (required for QR sign-in) | — |
| `POLL_INTERVAL` | Polling interval in seconds (default: `10`) | — |
| `GPS_LON` | GPS longitude | — |
| `GPS_LAT` | GPS latitude | — |
| `ENABLE_SEND_EMAIL` | Enable email notification (`true` / `1`) | — |
| `SMTP_SERVER` | SMTP server (default: `smtp.qq.com`) | — |
| `EMAIL_SENDER` | Sender email address | — |
| `EMAIL_PASSWORD` | SMTP authorization code | — |
| `EMAIL_RECEIVER` | Receiver email address | — |

## Tutorial

<details>
<summary><b>Get OpenId</b></summary>

1. Tap "All (A)" in the TeacherMate WeChat service account

   ![Enter TeacherMate](https://raw.githubusercontent.com/huanglune/wzj-signin/main/docs/enter-wzj.png)

2. Copy the URL from the browser address bar

   ![Copy link](https://raw.githubusercontent.com/huanglune/wzj-signin/main/docs/copy-link.png)

   ![Get link](https://raw.githubusercontent.com/huanglune/wzj-signin/main/docs/get-link.png)

3. The part after `openid=` in the URL is your OpenId:

   ```
   https://v18.teachermate.cn/wechat-pro-ssr/?openid=52279xxxxxxxxx81803b6cc9bb1cd24f&from=wzj
   ```

   You can also use the full URL as `OPEN_ID` directly — the program will extract it automatically.

</details>

<details>
<summary><b>Get Course ID</b></summary>

1. Open the TeacherMate course page and launch browser DevTools (F12)

   ![Open course](https://raw.githubusercontent.com/huanglune/wzj-signin/main/docs/open-course.png)

   ![DevTools](https://raw.githubusercontent.com/huanglune/wzj-signin/main/docs/devtools.png)

2. Find the course-related API request in the Network tab to get the `courseId`

   ![View request](https://raw.githubusercontent.com/huanglune/wzj-signin/main/docs/view-request.png)

   ![Find courseId](https://raw.githubusercontent.com/huanglune/wzj-signin/main/docs/find-course-id.png)

   ![courseId details](https://raw.githubusercontent.com/huanglune/wzj-signin/main/docs/course-id-detail.png)

   ![Confirm courseId](https://raw.githubusercontent.com/huanglune/wzj-signin/main/docs/confirm-course-id.png)

</details>

<details>
<summary><b>Configure config.toml</b></summary>

1. Copy the example config to your working directory:

   ```bash
   cp config.toml.example config.toml
   ```

2. Edit `config.toml` with your information:

   ```toml
   [default]
   openId = "your OpenId"
   courseId = "your Course ID"
   studentId = "your Student ID"  # required for QR sign-in
   pollInterval = 10               # polling interval (seconds)

   # GPS coordinates (optional, remove if not needed)
   gps_lon = 113.999877
   gps_lat = 22.595876
   ```

3. To enable email notifications, configure the `[email]` section:

   ```toml
   [email]
   enable_send_email = true
   smtp_server = "smtp.qq.com"
   sender = "your@qq.com"
   password = "your SMTP authorization code"
   receiver = "notification@example.com"
   ```

4. Run:

   ```bash
   wzj-signin
   ```

</details>

## Demo

After starting, the program polls for active sign-ins and handles normal, GPS, and QR sign-ins automatically:

![Running](https://raw.githubusercontent.com/huanglune/wzj-signin/main/docs/running.png)

Email notification:

![Email notification](https://raw.githubusercontent.com/huanglune/wzj-signin/main/docs/email-notification.png)

## Reference

- [zn-cn/wzj-sign-in-weixin](https://github.com/zn-cn/wzj-sign-in-weixin)

## License

[MIT](https://github.com/huanglune/wzj-signin/blob/main/LICENSE)
