#!/usr/bin/env python3
"""
screenshot.py — 纯 Playwright 截图工具（不依赖 LLM）。

用法:
  python3 scripts/screenshot.py input.html output.png
  python3 scripts/screenshot.py input.html output.png --inject-qrcode
  python3 scripts/screenshot.py --html-dir output/ --inject-qrcode

依赖:
  pip install playwright
  playwright install chromium
"""
from __future__ import annotations

import argparse
import base64
import glob
import os
import sys


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def load_qrcode_base64() -> str:
    """加载公众号二维码并转为 base64 data URI。"""
    qr_path = os.path.join(SCRIPT_DIR, "..", "assets", "qrcode_weixin_InsightsJun-small.jpg")
    if not os.path.isfile(qr_path):
        return ""
    with open(qr_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/jpeg;base64,{data}"


def inject_qrcode(html: str) -> str:
    """在 HTML 右上角注入公众号二维码。"""
    qr_uri = load_qrcode_base64()
    if not qr_uri:
        return html
    qr_html = f'''<div style="position:fixed;top:20px;right:50px;z-index:9999;
        background:rgba(255,255,255,0.92);border-radius:12px;padding:10px 10px 6px 10px;
        box-shadow:0 2px 16px rgba(0,0,0,0.2);">
        <img src="{qr_uri}" style="width:88px;height:88px;display:block;border-radius:6px;" alt="薛以致用">
        <div style="font-size:11px;color:#444;text-align:center;margin-top:5px;
            font-family:'Noto Sans SC',sans-serif;line-height:1;font-weight:500;">薛以致用</div>
    </div>'''
    if "</body>" in html:
        return html.replace("</body>", qr_html + "\n</body>", 1)
    return html + qr_html


def screenshot_html(html_path: str, png_path: str, do_inject_qr: bool = False) -> bool:
    """用 Playwright 将 HTML 文件截图为 PNG。"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ 请安装 playwright: pip3 install playwright && python3 -m playwright install chromium",
              file=sys.stderr)
        return False

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    if do_inject_qr:
        html = inject_qrcode(html)
        # 回写注入后的 HTML
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1000, "height": 800})
            page.set_content(html)
            page.wait_for_timeout(2500)  # 等待 Google Fonts 加载

            content_height = page.evaluate("""() => {
                const body = document.body;
                const html = document.documentElement;
                return Math.max(
                    body.scrollHeight, body.offsetHeight,
                    html.clientHeight, html.scrollHeight, html.offsetHeight
                );
            }""")
            page.set_viewport_size({"width": 1000, "height": content_height + 20})
            page.wait_for_timeout(300)
            page.screenshot(path=png_path, full_page=True)
            browser.close()
        fsize = os.path.getsize(png_path)
        print(f"✅ {png_path} ({fsize / 1024:.1f} KB)", file=sys.stderr)
        return True
    except Exception as e:
        print(f"❌ 截图失败: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="HTML → PNG 截图工具")
    parser.add_argument("input", nargs="?", help="输入 HTML 文件路径")
    parser.add_argument("output", nargs="?", help="输出 PNG 文件路径")
    parser.add_argument("--inject-qrcode", action="store_true",
                        help="注入公众号二维码水印")
    parser.add_argument("--html-dir", help="批量截图：目录下所有 .html → .png")
    args = parser.parse_args()

    if args.html_dir:
        html_files = sorted(glob.glob(os.path.join(args.html_dir, "*.html")))
        if not html_files:
            print(f"⚠️ {args.html_dir} 下没有 .html 文件", file=sys.stderr)
            sys.exit(1)
        ok_count = 0
        for hf in html_files:
            pf = hf.replace(".html", ".png")
            if screenshot_html(hf, pf, args.inject_qrcode):
                ok_count += 1
        print(f"\n✅ 完成: {ok_count}/{len(html_files)} 张截图", file=sys.stderr)
    elif args.input:
        out = args.output or args.input.replace(".html", ".png")
        screenshot_html(args.input, out, args.inject_qrcode)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
