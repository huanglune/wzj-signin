<div align="center">

# wzj-signin

**微助教自动签到工具**

[![PyPI](https://img.shields.io/pypi/v/wzj-signin.svg)](https://pypi.org/project/wzj-signin/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/wzj-signin.svg)](https://pypi.org/project/wzj-signin/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/huanglune/wzj-signin/blob/main/LICENSE)

[English](https://github.com/huanglune/wzj-signin/blob/main/README.md) | 中文

</div>

---

## 功能

- **普通签到** — 自动完成
- **GPS 签到** — 配置经纬度后自动完成，坐标自动微调防检测
- **二维码签到** — 终端展示二维码，扫码完成签到
- **邮件通知** — 签到成功/失败时发送邮件提醒

## 安装

```bash
pip install wzj-signin
```

或使用 uvx 免安装运行：

```bash
uvx wzj-signin
```

## 快速开始

### 环境变量方式（推荐）

```bash
OPEN_ID=xxx COURSE_ID=123 STUDENT_ID=456 wzj-signin
```

也支持直接填微助教链接作为 OPEN_ID：

```bash
OPEN_ID="https://v18.teachermate.cn/wechat-pro-ssr/?openid=xxx&from=wzj" COURSE_ID=123 uvx wzj-signin
```

### 配置文件方式

在运行目录放置 `config.toml`（参考 [config.toml.example](https://github.com/huanglune/wzj-signin/blob/main/config.toml.example)）：

```toml
[default]
openId = "xxx"
courseId = "123"
studentId = "456"
pollInterval = 10

# GPS 签到坐标（可选）
gps_lon = 113.999877
gps_lat = 22.595876

# 邮件通知（可选）
[email]
enable_send_email = false
smtp_server = "smtp.qq.com"
sender = "your@qq.com"
password = "your_smtp_password"
receiver = "notify@example.com"
```

> 环境变量优先级高于配置文件。
>
> 如果 `OPEN_ID` 直接填写的是完整微助教链接，程序现在会同时自动提取其中的 `openid` 和对应域名作为 API 地址。

## 环境变量

| 变量 | 说明 | 必填 |
|:-----|:-----|:----:|
| `OPEN_ID` | 微助教 openId 或完整链接 | ✅ |
| `COURSE_ID` | 课程 ID | ✅ |
| `STUDENT_ID` | 学号（二维码签到需要） | — |
| `POLL_INTERVAL` | 轮询间隔秒数（默认：`10`） | — |
| `API_BASE_URL` | 覆盖 API 基础地址；如果 `OPEN_ID` 是完整链接，会自动复用其中的域名 | — |
| `CONNECT_TIMEOUT` | 连接超时秒数（默认：`5`） | — |
| `READ_TIMEOUT` | 响应读取超时秒数（默认：`15`） | — |
| `REQUEST_RETRIES` | 建连阶段失败的重试次数（默认：`2`） | — |
| `RETRY_BACKOFF` | 重试退避系数秒数（默认：`1.0`） | — |
| `GPS_LON` | GPS 签到经度 | — |
| `GPS_LAT` | GPS 签到纬度 | — |
| `ENABLE_SEND_EMAIL` | 启用邮件通知（`true` / `1`） | — |
| `SMTP_SERVER` | SMTP 服务器（默认：`smtp.qq.com`） | — |
| `EMAIL_SENDER` | 发件人邮箱 | — |
| `EMAIL_PASSWORD` | SMTP 授权码 | — |
| `EMAIL_RECEIVER` | 收件人邮箱 | — |

## 教程

<details>
<summary><b>获取 OpenId</b></summary>

1. 点击微助教服务号中的「全部(A)」

   ![进入微助教](https://raw.githubusercontent.com/huanglune/wzj-signin/main/docs/enter-wzj.png)

2. 进入后复制浏览器地址栏中的链接

   ![复制链接](https://raw.githubusercontent.com/huanglune/wzj-signin/main/docs/copy-link.png)

   ![获取链接](https://raw.githubusercontent.com/huanglune/wzj-signin/main/docs/get-link.png)

3. 链接中 `openid=` 后面的部分即为你的 OpenId：

   ```
   https://v18.teachermate.cn/wechat-pro-ssr/?openid=52279xxxxxxxxx81803b6cc9bb1cd24f&from=wzj
   ```

   也可以直接将整个链接作为 `OPEN_ID` 使用，程序会自动提取。

</details>

<details>
<summary><b>获取课程 ID</b></summary>

1. 进入微助教课程页面，打开浏览器开发者工具（F12）

   ![打开课程](https://raw.githubusercontent.com/huanglune/wzj-signin/main/docs/open-course.png)

   ![开发者工具](https://raw.githubusercontent.com/huanglune/wzj-signin/main/docs/devtools.png)

2. 在网络请求中找到课程相关接口，从中获取 `courseId`

   ![查看请求](https://raw.githubusercontent.com/huanglune/wzj-signin/main/docs/view-request.png)

   ![找到courseId](https://raw.githubusercontent.com/huanglune/wzj-signin/main/docs/find-course-id.png)

   ![courseId详情](https://raw.githubusercontent.com/huanglune/wzj-signin/main/docs/course-id-detail.png)

   ![确认courseId](https://raw.githubusercontent.com/huanglune/wzj-signin/main/docs/confirm-course-id.png)

</details>

<details>
<summary><b>配置 config.toml</b></summary>

1. 复制示例配置文件到运行目录：

   ```bash
   cp config.toml.example config.toml
   ```

2. 编辑 `config.toml`，填入你获取到的信息：

   ```toml
   [default]
   openId = "你的 OpenId"
   courseId = "你的课程 ID"
   studentId = "你的学号"       # 二维码签到需要
   pollInterval = 10            # 轮询间隔（秒）

   # GPS 签到坐标（可选，不需要 GPS 签到可删除）
   gps_lon = 113.999877
   gps_lat = 22.595876
   ```

3. 如需邮件通知，配置 `[email]` 部分：

   ```toml
   [email]
   enable_send_email = true
   smtp_server = "smtp.qq.com"
   sender = "your@qq.com"
   password = "你的 SMTP 授权码"
   receiver = "接收通知的邮箱"
   ```

   以 QQ 邮箱为例，需要在 QQ 邮箱设置中开启 SMTP 服务并获取授权码。

4. 配置完成后直接运行即可：

   ```bash
   wzj-signin
   ```

</details>

## 运行效果

程序启动后会自动轮询签到，依次处理普通签到、GPS 签到和二维码签到：

![运行过程](https://raw.githubusercontent.com/huanglune/wzj-signin/main/docs/running.png)

邮件通知效果：

![邮件通知](https://raw.githubusercontent.com/huanglune/wzj-signin/main/docs/email-notification.png)

## 参考链接

- [zn-cn/wzj-sign-in-weixin](https://github.com/zn-cn/wzj-sign-in-weixin)

## 许可证

[MIT](https://github.com/huanglune/wzj-signin/blob/main/LICENSE)
