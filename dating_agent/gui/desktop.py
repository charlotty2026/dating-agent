#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
桌面窗口封装
============
pywebview 封装 + 端口自动探测 + 浏览器回退。
复用 bid-toolkit 的 desktop.py 架构。
"""

import socket
import sys
import threading
import time
import webbrowser


def find_available_port(start=7861, max_tries=20):
    """从指定端口开始扫描，找到可用端口。"""
    for port in range(start, start + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except socket.OSError:
                continue
    raise RuntimeError(
        f"端口 {start}-{start + max_tries - 1} 全部被占用，"
        f"请手动指定端口：python -m dating_agent.gui --port 8080"
    )


def _get_window_geometry():
    """获取窗口尺寸和位置（居中）。"""
    default_size = (1024, 768, None, None)
    try:
        import screeninfo
        monitors = screeninfo.get_monitors()
        if monitors:
            monitor = monitors[0]
            width = min(1024, int(monitor.width * 0.8))
            height = min(768, int(monitor.height * 0.8))
            x = int((monitor.width - width) / 2)
            y = int((monitor.height - height) / 2)
            return (width, height, x, y)
    except (ImportError, Exception):
        pass
    return default_size


def launch_desktop(url, title="AI相亲Agent"):
    """启动桌面窗口或回退到浏览器。"""
    try:
        import webview
        width, height, x, y = _get_window_geometry()
        window_kwargs = {"width": width, "height": height, "title": title}
        if x is not None and y is not None:
            window_kwargs["x"] = x
            window_kwargs["y"] = y
        print(f"启动桌面窗口: {title} ({width}x{height})")
        webview.create_window(title=title, url=url, **window_kwargs)
        webview.start()
    except ImportError:
        print("pywebview 未安装，使用系统浏览器打开...")
        webbrowser.open(url)
        print(f"已在浏览器中打开: {url}")
        print("如需桌面窗口体验，请运行: pip install pywebview")
        print("按 Ctrl+C 退出...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n已退出")
            sys.exit(0)
    except Exception as e:
        print(f"桌面窗口启动失败: {e}")
        print("回退到系统浏览器...")
        webbrowser.open(url)
        print(f"已在浏览器中打开: {url}")
        print("按 Ctrl+C 退出...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n已退出")
            sys.exit(0)


def start_gradio_then_desktop(gradio_app, port=7861, browser_only=False):
    """启动 Gradio 服务，然后打开桌面窗口。"""
    actual_port = find_available_port(port)
    if actual_port != port:
        print(f"端口 {port} 被占用，自动切换到 {actual_port}")

    url = f"http://127.0.0.1:{actual_port}"

    if browser_only:
        print(f"启动 Web 服务: {url}")
        gradio_app.launch(server_port=actual_port, inbrowser=True)
        return

    def _run_gradio():
        gradio_app.launch(server_port=actual_port, inbrowser=False, prevent_thread_lock=True)

    gradio_thread = threading.Thread(target=_run_gradio, daemon=True)
    gradio_thread.start()

    print(f"正在启动服务...", end="")
    for _ in range(30):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", actual_port)) == 0:
                break
        print(".", end="", flush=True)
        time.sleep(0.5)
    print(f" ready")

    launch_desktop(url, title="AI相亲Agent")
