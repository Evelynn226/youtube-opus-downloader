#!/usr/bin/env python3
"""Local bridge for the YouTube Tampermonkey Opus downloader.

Chrome-only browser integration:
- YouTube page: Tampermonkey userscript
- Authentication: a user-provided cookies.txt file
- Download engine: yt-dlp + FFmpeg
"""
from __future__ import annotations

import configparser
import json
import os
import shutil
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

HOST = "127.0.0.1"
PORT = 8765
BASE_DIR = Path(__file__).resolve().parent


def load_config() -> tuple[Path, Path]:
    """Load download and cookies paths from config.ini."""
    default_download = Path.home() / "Downloads" / "YouTube Audio"
    default_cookies = BASE_DIR / "cookies.txt"
    config_path = BASE_DIR / "config.ini"
    if not config_path.exists():
        return default_download, default_cookies

    parser = configparser.RawConfigParser()
    try:
        parser.read(config_path, encoding="utf-8")
        download_raw = parser.get("download", "path", fallback="").strip()
        cookies_raw = parser.get("cookies", "path", fallback="cookies.txt").strip()
    except (configparser.Error, OSError):
        return default_download, default_cookies

    if not download_raw:
        download_raw = str(default_download)
    if not cookies_raw:
        cookies_raw = "cookies.txt"

    download_raw = os.path.expandvars(os.path.expanduser(download_raw))
    cookies_raw = os.path.expandvars(os.path.expanduser(cookies_raw))

    download_dir = Path(download_raw)
    if not download_dir.is_absolute():
        download_dir = BASE_DIR / download_dir

    cookies_file = Path(cookies_raw)
    if not cookies_file.is_absolute():
        cookies_file = BASE_DIR / cookies_file

    return download_dir, cookies_file


DOWNLOAD_DIR, COOKIES_FILE = load_config()

os.environ["PATH"] = str(BASE_DIR) + os.pathsep + os.environ.get("PATH", "")


def find_ytdlp() -> list[str]:
    for candidate in (BASE_DIR / "yt-dlp.exe", BASE_DIR / "yt-dlp"):
        if candidate.exists():
            return [str(candidate)]
    for name in ("yt-dlp.exe", "yt-dlp"):
        found = shutil.which(name)
        if found:
            return [found]
    try:
        import yt_dlp  # noqa: F401
        return [sys.executable, "-m", "yt_dlp"]
    except ImportError as exc:
        raise FileNotFoundError(
            "找不到 yt-dlp。请把 yt-dlp.exe 放到本脚本同目录，或加入 PATH。"
        ) from exc


def find_ffmpeg() -> str | None:
    local = BASE_DIR / "ffmpeg.exe"
    if local.exists():
        return str(local)
    return shutil.which("ffmpeg")


def cookie_args() -> list[str]:
    if not COOKIES_FILE.is_file():
        raise FileNotFoundError(
            "找不到 cookies.txt：\n"
            f"{COOKIES_FILE}\n\n"
            "请在 config.ini 的 [cookies] path= 中填写正确的 cookies.txt 路径。"
        )

    # yt-dlp expects Mozilla/Netscape cookie format for --cookies.
    try:
        first_nonempty = ""
        with COOKIES_FILE.open("r", encoding="utf-8-sig", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line:
                    first_nonempty = line
                    break
        if first_nonempty not in {"# HTTP Cookie File", "# Netscape HTTP Cookie File"}:
            raise ValueError(
                "cookies.txt 看起来不是 Mozilla/Netscape 格式。\n"
                "文件第一行应为 # HTTP Cookie File 或 # Netscape HTTP Cookie File。"
            )
    except UnicodeDecodeError as exc:
        raise ValueError("cookies.txt 无法按文本方式读取，请确认文件没有损坏。") from exc

    return ["--cookies", str(COOKIES_FILE)]


def build_args(url: str, mode: str) -> list[str]:
    # Prefer native Opus. Fall back to the requested audio quality and let FFmpeg encode to Opus.
    fmt = (
        "bestaudio[acodec=opus]/bestaudio"
        if mode == "best"
        else "worstaudio[acodec=opus]/worstaudio"
    )
    quality = "0" if mode == "best" else "9"
    output_template = str(DOWNLOAD_DIR / "%(title)s [%(id)s].%(ext)s")
    ytdlp = find_ytdlp()
    return ytdlp + [
        "--no-playlist",
        *cookie_args(),
        "--windows-filenames",
        "--newline",
        "-f", fmt,
        "-x",
        "--audio-format", "opus",
        "--audio-quality", quality,
        "-o", output_template,
        url,
    ]


def validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or parsed.hostname not in {
        "youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be",
    }:
        raise ValueError("只允许 YouTube URL")


def preflight(url: str) -> tuple[bool, str]:
    """Check cookies + extractor access before starting the actual download."""
    args = find_ytdlp() + [
        "--no-playlist",
        *cookie_args(),
        "--skip-download",
        "--no-warnings",
        "--print", "%(_type)s|%(id)s|%(title)s",
        url,
    ]
    try:
        p = subprocess.run(
            args,
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=45,
        )
    except subprocess.TimeoutExpired:
        return False, "预检查超时。YouTube 响应较慢，请稍后再试。"

    output = ((p.stdout or "") + (p.stderr or "")).strip()
    if p.returncode == 0:
        return True, output.splitlines()[-1] if output else "ok"

    lower = output.lower()
    if "sign in to confirm you're not a bot" in lower:
        return False, (
            "YouTube 仍要求登录/验证。请重新导出当前 Chrome 会话的 cookies.txt，"
            "并确保 cookies.txt 是最近导出的有效文件。"
        )
    if "invalid netscape format cookies file" in lower:
        return False, (
            "cookies.txt 格式无效。请使用 Mozilla/Netscape 格式导出；"
            "第一行应为 # HTTP Cookie File 或 # Netscape HTTP Cookie File。"
        )
    if "http error 400" in lower and "cookie" in lower:
        return False, (
            "cookies.txt 可能存在换行格式问题。Windows 下建议保存为 CRLF 的文本文件，"
            "并重新导出。"
        )
    return False, output[-2000:] or f"yt-dlp 预检查失败，退出码 {p.returncode}"


class Handler(BaseHTTPRequestHandler):
    server_version = "YouTubeOpusLocal/3.0"

    def _send_json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/download":
            self._send_json(404, {"ok": False, "error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 16_384:
                raise ValueError("请求数据无效")
            body = self.rfile.read(length)
            payload = json.loads(body.decode("utf-8"))
            url = str(payload.get("url", "")).strip()
            mode = str(payload.get("mode", "small")).strip().lower()
            validate_url(url)
            if mode not in {"small", "best"}:
                mode = "small"

            DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
            ok, msg = preflight(url)
            if not ok:
                self._send_json(400, {"ok": False, "error": msg})
                return

            args = build_args(url, mode)
            subprocess.Popen(args, cwd=str(BASE_DIR))
            self._send_json(202, {
                "ok": True,
                "message": "下载任务已启动",
                "mode": mode,
                "download_dir": str(DOWNLOAD_DIR),
            })
        except FileNotFoundError as exc:
            self._send_json(500, {"ok": False, "error": str(exc)})
        except Exception as exc:
            self._send_json(400, {"ok": False, "error": str(exc)})

    def log_message(self, fmt: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {fmt % args}")


def main() -> None:
    print("=" * 68)
    print("YouTube Opus 本机下载服务 V6")
    print(f"监听：http://{HOST}:{PORT}")
    print(f"下载目录：{DOWNLOAD_DIR}")
    print(f"Cookie 文件：{COOKIES_FILE}")
    print("浏览器模式：Chrome（Tampermonkey）")
    print("=" * 68)

    try:
        find_ytdlp()
    except FileNotFoundError as exc:
        print(f"错误：{exc}")
        input("按 Enter 退出…")
        return

    ffmpeg = find_ffmpeg()
    if ffmpeg is None:
        print("警告：未检测到 ffmpeg。输出 Opus 需要 FFmpeg。建议把 ffmpeg.exe 放到本目录。")

    if not COOKIES_FILE.is_file():
        print("警告：cookies.txt 当前不存在，请先修改 config.ini 中的 [cookies] path=。")

    server = ThreadingHTTPServer((HOST, PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n正在退出…")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
