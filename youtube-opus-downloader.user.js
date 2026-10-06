// ==UserScript==
// @name         YouTube 一键下载音频（Opus）
// @namespace    local.youtube-opus-downloader
// @version      1.1.0
// @description  Chrome + Tampermonkey：在 YouTube 视频页一键下载 Opus 音频，由本机 yt-dlp + cookies.txt 完成下载
// @author       local
// @match        https://www.youtube.com/*
// @match        https://m.youtube.com/*
// @match        https://music.youtube.com/*
// @grant        GM_xmlhttpRequest
// @connect      127.0.0.1
// @connect      localhost
// @run-at       document-idle
// ==/UserScript==

(() => {
    'use strict';

    const API = 'http://127.0.0.1:8765';
    const ROOT_ID = 'yt-opus-downloader-root';

    const isVideoPage = () => {
        const p = location.pathname;
        return (p === '/watch' && new URL(location.href).searchParams.has('v'))
            || p.startsWith('/shorts/')
            || p.startsWith('/live/');
    };

    const getVideoUrl = () => {
        const u = new URL(location.href);
        // Keep only the video identifier-related part; remove playlist/navigation params.
        if (u.pathname === '/watch') {
            const v = u.searchParams.get('v');
            return `https://www.youtube.com/watch?v=${encodeURIComponent(v)}`;
        }
        return location.href.split('&list=')[0];
    };

    function requestDownload(mode = 'small') {
        if (!isVideoPage()) {
            setStatus('请先打开 YouTube 视频页面');
            return;
        }

        const url = getVideoUrl();
        setStatus('正在检查 Cookie 和视频…');
        setDisabled(true);

        GM_xmlhttpRequest({
            method: 'POST',
            url: `${API}/download`,
            headers: { 'Content-Type': 'application/json' },
            data: JSON.stringify({ url, mode }),
            timeout: 60000,
            onload: (res) => {
                try {
                    const data = JSON.parse(res.responseText || '{}');
                    if (res.status >= 200 && res.status < 300 && data.ok) {
                        setStatus(mode === 'small' ? '✓ 已启动：极省体积 Opus' : '✓ 已启动：最佳 Opus');
                    } else {
                        setStatus(`失败：${data.error || '本机服务返回错误'}`);
                    }
                } catch {
                    setStatus('失败：无法解析本机服务响应');
                } finally {
                    setDisabled(false);
                    window.setTimeout(() => setStatus(''), 7000);
                }
            },
            onerror: () => {
                setStatus('无法连接本机服务，请先运行 start_server_chrome.bat');
                setDisabled(false);
            },
            ontimeout: () => {
                setStatus('检查 YouTube Cookie 超时，请确认 yt-dlp 服务正在运行');
                setDisabled(false);
            }
        });
    }

    let buttonSmall;
    let buttonBest;
    let status;

    function setDisabled(disabled) {
        if (buttonSmall) buttonSmall.disabled = disabled;
        if (buttonBest) buttonBest.disabled = disabled;
    }

    function setStatus(text) {
        if (!status) return;
        status.textContent = text;
        status.style.opacity = text ? '1' : '0';
    }

    function makeButton(text, title, onClick) {
        const b = document.createElement('button');
        b.textContent = text;
        b.title = title;
        b.type = 'button';
        b.addEventListener('click', onClick);
        Object.assign(b.style, {
            border: '0',
            borderRadius: '10px',
            padding: '9px 12px',
            background: 'rgba(255,255,255,.12)',
            color: '#fff',
            fontSize: '13px',
            fontWeight: '600',
            cursor: 'pointer',
            backdropFilter: 'blur(10px)',
            boxShadow: '0 2px 12px rgba(0,0,0,.25)',
            transition: 'transform .15s, opacity .15s'
        });
        b.addEventListener('mouseenter', () => b.style.transform = 'translateY(-1px)');
        b.addEventListener('mouseleave', () => b.style.transform = 'translateY(0)');
        b.addEventListener('mousedown', () => b.style.transform = 'translateY(1px)');
        return b;
    }

    function createUI() {
        if (document.getElementById(ROOT_ID)) return;

        const root = document.createElement('div');
        root.id = ROOT_ID;
        Object.assign(root.style, {
            position: 'fixed',
            right: '18px',
            bottom: '18px',
            zIndex: '2147483647',
            display: 'flex',
            alignItems: 'center',
            gap: '7px',
            fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
        });

        buttonSmall = makeButton('🎧 Opus 极省', '下载当前视频的最低可用 Opus 音频，尽量减小文件体积', () => requestDownload('small'));
        buttonBest = makeButton('♫ Opus 最佳', '下载当前视频可用的最佳音频并输出为 Opus', () => requestDownload('best'));

        status = document.createElement('div');
        Object.assign(status.style, {
            maxWidth: '420px',
            padding: '8px 11px',
            borderRadius: '9px',
            background: 'rgba(0,0,0,.78)',
            color: '#fff',
            fontSize: '12px',
            lineHeight: '1.4',
            opacity: '0',
            pointerEvents: 'none',
            transition: 'opacity .2s',
            boxShadow: '0 2px 12px rgba(0,0,0,.2)',
            whiteSpace: 'pre-wrap'
        });

        root.append(buttonSmall, buttonBest, status);
        document.body.appendChild(root);
        updateVisibility();
    }

    function updateVisibility() {
        const root = document.getElementById(ROOT_ID);
        if (root) root.style.display = isVideoPage() ? 'flex' : 'none';
    }

    function start() {
        createUI();
        window.setInterval(updateVisibility, 1000);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', start, { once: true });
    } else {
        start();
    }
})();
