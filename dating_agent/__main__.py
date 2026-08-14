#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dating-agent 入口
=================
用法:
    python -m dating_agent              # 启动GUI
    python -m dating_agent --help       # 帮助
    python -m dating_agent --cli        # CLI模式(留给以后)
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        prog="dating-agent",
        description="AI相亲Agent - 蒸馏自己，替你初筛",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="CLI模式(开发中)，默认启动GUI",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7861,
        help="GUI服务端口 (默认7861)",
    )
    parser.add_argument(
        "--browser-only",
        action="store_true",
        help="只用浏览器打开，不启动桌面窗口",
    )
    args = parser.parse_args()

    if args.cli:
        print("CLI模式开发中，暂不可用。请使用GUI模式。")
        sys.exit(1)

    # GUI模式
    try:
        from .gui.app import create_app
        from .gui.desktop import start_gradio_then_desktop
    except ImportError as e:
        print(f"GUI依赖缺失: {e}")
        print("请安装GUI依赖: pip install \"dating-agent[gui]\"")
        sys.exit(1)

    app = create_app()
    print("🚀 启动AI相亲Agent...")
    start_gradio_then_desktop(app, port=args.port, browser_only=args.browser_only)


if __name__ == "__main__":
    main()
