# YouTube Opus Downloader / YouTube Opus 下载器

<p>
  <b>English</b> · <a href="#中文说明">中文说明</a>
</p>

One-click download of YouTube video audio as **Opus** (Opus 极省 / Opus 最佳), entirely on your local machine.
一键将 YouTube 视频音频以 **Opus** 格式下载到本地（极省体积 / 最佳音质），全流程仅在本机完成。

A Tampermonkey userscript adds download buttons to the YouTube page; a local Python bridge server invokes **yt-dlp + FFmpeg** with your own exported `cookies.txt`. No third-party download sites, no cloud services, no browser cookie database access.

Tampermonkey 油猴脚本在 YouTube 页面添加下载按钮；本机 Python 桥接服务调用 **yt-dlp + FFmpeg**，使用你自己导出的 `cookies.txt` 完成下载。不经过第三方下载站，没有云服务，不读取浏览器 Cookie 数据库。

---

## ✨ Features / 特性

| | |
|---|---|
| 🎧 **Opus 极省 (Minimal)** | Lowest available Opus bitrate (e.g. ~58–70 kbps, itag 249) — smallest file size. 最低可用 Opus 码率，文件体积最小。 |
| ♫ **Opus 最佳 (Best)** | Best available audio, output as Opus via FFmpeg. 最佳可用音频，经 FFmpeg 输出为 Opus。 |
| 🖥️ **Fully local / 全本地** | Bridge server listens on `127.0.0.1:8765` only. 桥接服务仅监听 `127.0.0.1:8765`。 |
| 🔐 **Your own cookies / 自有 Cookie** | Authentication via a user-exported Netscape-format `cookies.txt` — no automatic browser cookie DB reading (V6). 通过用户导出的 Netscape 格式 `cookies.txt` 认证（V6 起不再自动读取浏览器 Cookie 数据库）。 |
| ✅ **Pre-flight check / 下载前预检查** | Verifies cookies & video access with `yt-dlp --skip-download` before starting, with friendly Chinese error messages. 正式下载前用 `yt-dlp --skip-download` 预检 Cookie 与视频可访问性，并给出可读的错误提示。 |
| 🧹 **Clean filenames / 规范命名** | `Title [videoId].opus` via `%(title)s [%(id)s].%(ext)s`. 输出文件名自动为 `标题 [视频ID].opus`。 |

## 🏗️ Architecture / 架构

```
YouTube page (Chrome)
   │  Tampermonkey userscript:  🎧 Opus 极省 | ♫ Opus 最佳
   ▼
POST http://127.0.0.1:8765/download   { url, mode: "small" | "best" }
   ▼
youtube_opus_server.py  ──►  preflight (yt-dlp --skip-download)
   ▼
yt-dlp --cookies cookies.txt -x --audio-format opus
   ▼
FFmpeg  ──►  Download/Title [videoId].opus
```

## 📁 Files / 文件说明

| File | Description |
|---|---|
| `youtube-opus-downloader.user.js` | Tampermonkey userscript (the in-page download buttons) / 油猴脚本（页面下载按钮） |
| `youtube_opus_server.py` | Local bridge HTTP server / 本机桥接下载服务 |
| `config.ini` | Download directory & cookies.txt path / 下载目录与 Cookie 文件路径配置 |
| `start_server_chrome.bat` | One-click launcher for the server / 一键启动服务 |
| `yt-dlp.exe` | Download engine (**not** included in this repo) / 下载引擎（**不**包含在仓库中） |
| `ffmpeg.exe` | Audio transcoding to Opus (**not** included in this repo) / 转码 Opus 所需（**不**包含在仓库中） |
| `cookies.txt` | ⚠️ Your exported YouTube session cookies — **NEVER commit this file** / ⚠️ 你导出的 YouTube 登录 Cookie — **绝不可提交到仓库** |

## 📦 Requirements / 环境要求

- **Windows** (the launcher is a `.bat`; the server itself is plain Python and works on macOS/Linux too) / Windows（启动器为 bat；服务端为纯 Python，macOS/Linux 亦可运行）
- **Python 3.9+** — only stdlib, no pip install needed / 仅需标准库，无需 pip 安装
- **yt-dlp** — put `yt-dlp.exe` in this folder, add to `PATH`, or `pip install yt-dlp` / 放到本目录、加入 PATH、或 pip 安装
- **FFmpeg** — put `ffmpeg.exe` in this folder (required for Opus output) / 放到本目录（输出 Opus 必需）
- **Chrome + Tampermonkey** — for the userscript / 用于加载油猴脚本
- **A logged-in YouTube session** in Chrome, exported as `cookies.txt` / Chrome 中已登录 YouTube 的会话，导出为 `cookies.txt`

## 🚀 Quick Start / 快速开始

### 1. Get the binaries / 准备外部程序

Download `yt-dlp.exe` and `ffmpeg.exe` and place them in this folder:

- yt-dlp: <https://github.com/yt-dlp/yt-dlp/releases/latest> (`yt-dlp.exe`)
- FFmpeg: <https://www.gyan.dev/ffmpeg/builds/> (essentials build, rename `ffmpeg.exe`)

### 2. Export cookies.txt / 导出 Cookie

Export cookies from your **logged-in Chrome YouTube session** in Netscape/Mozilla format. Any cookie-export extension works (e.g. "Get cookies.txt LOCALLY"), as long as the file starts with:

```
# Netscape HTTP Cookie File
```
or
```
# HTTP Cookie File
```

Save it as `cookies.txt` next to this project (or point `config.ini` to your preferred location).

从**已登录 YouTube 的 Chrome 会话**导出 Netscape/Mozilla 格式 Cookie（可用任意导出扩展，如 "Get cookies.txt LOCALLY"），文件首行须为上方注释之一，保存到项目目录（或在 `config.ini` 中指向你的路径）。

> ⚠️ `cookies.txt` contains your login credentials. Keep it private — never upload, share, or commit it.
> ⚠️ `cookies.txt` 包含登录凭据，请勿上传、分享或提交。

### 3. Configure / 配置

Edit `config.ini`:

```ini
[download]
path=B:\youtube_opus_downloader\Download

[cookies]
path=cookies.txt
```

- Relative paths resolve against the project folder / 相对路径相对项目目录解析
- Environment variables are supported: `path=%USERPROFILE%\Downloads\YouTube Audio` / 支持环境变量

### 4. Start the server / 启动服务

Double-click `start_server_chrome.bat`, or run:

```bash
python youtube_opus_server.py
```

You should see:

```
====================================================================
YouTube Opus 本机下载服务 V6
监听：http://127.0.0.1:8765
下载目录：B:\youtube_opus_downloader\Download
Cookie 文件：B:\youtube_opus_downloader\cookies.txt
====================================================================
```

### 5. Install the userscript / 安装油猴脚本

1. Install [Tampermonkey](https://www.tampermonkey.net/) in Chrome.
2. Create a new userscript, paste the whole content of `youtube-opus-downloader.user.js`, save.
3. Open any YouTube **video** page (`watch` / `shorts` / `live`) — two buttons appear at the bottom-right:
   **🎧 Opus 极省** and **♫ Opus 最佳**.
4. Click one → the download starts, output lands in the configured download folder.

## ⚙️ How quality is chosen / 音质选择逻辑

The server asks yt-dlp for:

| Mode | yt-dlp format | Audio quality |
|---|---|---|
| `small` (极省) | `worstaudio[acodec=opus]/worstaudio` | `--audio-quality 9` |
| `best` (最佳) | `bestaudio[acodec=opus]/bestaudio` | `--audio-quality 0` |

Native Opus streams (e.g. itag 249/251) are preferred; if only other codecs are available, FFmpeg transcodes to Opus.
优先原生 Opus 流（如 itag 249/251）；若无原生 Opus，则由 FFmpeg 转码为 Opus。

## 🛠️ Troubleshooting / 故障排查

| Symptom | Cause & fix |
|---|---|
| `Sign in to confirm you're not a bot` | Re-export `cookies.txt` from a currently logged-in Chrome session; a fresh export fixes it. / 从当前已登录的 Chrome 会话重新导出 cookies.txt（用较新的导出文件）。 |
| `invalid Netscape format cookies file` | The file is not Netscape format — check the first line, re-export. / 检查首行注释，用 Netscape 格式重新导出。 |
| `HTTP Error 400` + `cookie` | Line-ending issue — save `cookies.txt` with CRLF on Windows, or re-export. / Windows 下换行问题：以 CRLF 保存或重新导出。 |
| `找不到 cookies.txt` | Fix `[cookies] path=` in `config.ini`. / 修改 `config.ini` 中的路径。 |
| `无法连接本机服务` | The server isn't running — start `start_server_chrome.bat` first. / 服务未启动：先运行启动脚本。 |
| No buttons on the page | Buttons only show on video pages (`/watch?v=`, `/shorts/`, `/live/`), and Tampermonkey must be enabled for `youtube.com`. / 按钮仅在视频页显示，且需 Tampermonkey 已启用。 |
| Opus output fails / 无法输出 Opus | FFmpeg missing — put `ffmpeg.exe` in this folder. / 缺少 FFmpeg：把 `ffmpeg.exe` 放到本目录。 |

## 🔒 Privacy & Security / 隐私与安全

- The bridge server binds to `127.0.0.1` only — nothing is exposed to the network. / 桥接服务仅监听本机回环地址，不对网络暴露。
- Video URLs never pass through any third-party service. / 视频 URL 不经过任何第三方。
- Cookies are read only by local yt-dlp. / Cookie 只由本机 yt-dlp 读取。
- `cookies.txt` is included in `.gitignore` — make sure it never reaches a public repo. / `cookies.txt` 已列入 `.gitignore`，切勿进入公开仓库。

## ⚖️ Disclaimer / 免责声明

This project is a personal-use tool for downloading audio you have access to. You are responsible for complying with the YouTube Terms of Service and copyright law in your jurisdiction. Use it for content you own, is licensed for such use, or falls under your local fair-use allowances.

本项目为个人使用工具，用于下载你有权访问的音频。使用者需自行遵守 YouTube 服务条款及所在地区的版权法规，建议仅用于自有内容、授权内容或当地合理使用范围内的场景。

## 📄 License

Provided as-is for personal use, without warranty of any kind. You may freely copy and adapt it for personal purposes.
以"现状"提供，供个人使用，无任何担保；可自由复制与修改用于个人目的。

---

<a id="中文说明"></a>

# 中文说明（完整版）

## 这是什么 / What

**YouTube Opus 下载器 V6** 是一套「浏览器按钮 → 本机服务 → yt-dlp」的 YouTube 音频下载方案：

- 浏览器端：Tampermonkey 脚本在 YouTube 视频页右下角加两个按钮 —— **🎧 Opus 极省**（最低码率 Opus，体积最小）、**♫ Opus 最佳**（最佳音质输出为 Opus）。
- 本机端：`youtube_opus_server.py` 在 `127.0.0.1:8765` 起一个只做下载的中转服务，先预检（`yt-dlp --skip-download`），成功后调用 yt-dlp 下载并用 FFmpeg 转成 `.opus` 文件。
- 认证方式：V6 起**不再自动读取浏览器 Cookie 数据库**，改用你自己导出的 Netscape 格式 `cookies.txt`，由 config.ini 指定路径。

## 文件清单

| 文件 | 说明 |
|---|---|
| `youtube-opus-downloader.user.js` | Tampermonkey 油猴脚本 |
| `youtube_opus_server.py` | 本机下载服务（纯 Python 标准库） |
| `config.ini` | 下载目录、cookies.txt 路径 |
| `start_server_chrome.bat` | 一键启动 |
| `yt-dlp.exe` / `ffmpeg.exe` | 外部依赖，需自行下载放入本目录（仓库不含） |
| `cookies.txt` | ⚠️ 你的登录 Cookie，**绝不能提交到 Git 仓库** |

## 快速开始（五步）

1. **准备程序**：下载 [yt-dlp.exe](https://github.com/yt-dlp/yt-dlp/releases/latest) 和 [ffmpeg.exe](https://www.gyan.dev/ffmpeg/builds/) 放到项目目录。
2. **导出 Cookie**：在已登录 YouTube 的 Chrome 里用 Cookie 导出扩展（如 Get cookies.txt LOCALLY）导出 Netscape 格式 `cookies.txt` 放到项目目录。
3. **改配置**：编辑 `config.ini` 的 `[download] path=` 与 `[cookies] path=`（支持相对路径和 `%USERPROFILE%` 等环境变量）。
4. **启动服务**：双击 `start_server_chrome.bat`（需要系统已安装 Python 3.9+）。
5. **装脚本**：Chrome 安装 Tampermonkey → 新建脚本 → 粘贴 `youtube-opus-downloader.user.js` 全部内容 → 保存 → 打开任意 YouTube 视频页即可看到按钮。

## 常见问题

- **Sign in to confirm you're not a bot** → Cookie 失效，重新导出当前 Chrome 会话的 `cookies.txt`。
- **invalid Netscape format cookies file** → 首行必须是 `# HTTP Cookie File` 或 `# Netscape HTTP Cookie File`。
- **HTTP Error 400 + cookie** → 换行格式问题，Windows 下用 CRLF 保存或重新导出。
- **页面上没有按钮** → 只在 `/watch?v=`、`/shorts/`、`/live/` 页面显示；确认 Tampermonkey 已启用且脚本已保存。
- **提示无法连接本机服务** → 先运行 `start_server_chrome.bat`。

## 隐私说明

- 服务只监听 `127.0.0.1`，不对外网开放。
- 视频地址不经过任何第三方下载网站。
- Cookie 只被本机 yt-dlp 读取。
- 仓库已提供 `.gitignore` 排除 `cookies.txt`、下载目录与外部 exe。

## 免责声明

本工具仅供个人使用，用于下载你有权访问的音频。请遵守 YouTube 服务条款与你所在地区的版权法规。
