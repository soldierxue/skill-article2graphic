#!/usr/bin/env python3
"""
gen_illustration.py — 为文章/故事生成信息图（独立 skill 版本）。

支持两种生成方式：
  A) HTML+Playwright 截图（默认，适合数据对比/金句/信息概览）
  B) SVG 代码生成（适合技术架构图/精确计算图）

用法:
  # 从故事文件生成信息图
  python3 scripts/gen_illustration.py \
    --story path/to/story.md \
    --output-dir output

  # 从 JSON spec 生成
  echo '{"type":"数据对比图","title":"...","data":{}}' | \
  python3 scripts/gen_illustration.py --from-spec --output-dir output

  # 指定生成方式
  python3 scripts/gen_illustration.py \
    --story path/to/story.md \
    --method svg \
    --output-dir output

依赖:
  pip install boto3 playwright
  playwright install chromium
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# llm_client 在同目录下
sys.path.insert(0, SCRIPT_DIR)

TZ_CST = timezone(timedelta(hours=8))

# ─── Design System Prompt（HTML+截图方式）───

DESIGN_SYSTEM_PROMPT = """你是一位顶级信息图设计师，为中文科技公众号「薛以致用」制作配图。

## 技术约束
- 输出纯 HTML+CSS 代码，用 <div> 作为根容器
- 根 div 宽度固定 900px，高度自适应内容（不要设固定高度）
- 通过 Google Fonts CDN 加载字体：
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700;900&family=Noto+Serif+SC:wght@700;900&family=Caveat:wght@400;700&family=Permanent+Marker&display=swap" rel="stylesheet">
- 所有视觉效果用纯 CSS 实现（渐变、圆角、阴影、径向光晕、border、box-shadow），不使用外部图片
- 可以用 emoji 作为图标
- 用 CSS 的 ::before / ::after 伪元素制造装饰效果

## 视觉风格（根据 color_scheme 字段选择）

### style: "dark" — 科技暗色
- 背景：#1A1A2E 或 #0F0F1A，深蓝/深紫渐变
- 文字：#F0F0F5（主）、#B0B0C5（次）、#707085（辅）
- 强调色：霓虹蓝 #00D4FF、霓虹绿 #00FF88、警告红 #FF4444
- 质感：微妙的网格线背景、发光边框、径向光晕

### style: "light" — 简洁亮色
- 背景：#FAFBFC 或 #F8F9FA
- 文字：#1A1A2E（主）、#4A4A6A（次）、#8A8AAA（辅）
- 强调色：根据语义（红=警告，绿=方案，紫=技术，蓝=数据）
- 质感：干净的卡片阴影、细线分隔

### style: "chalkboard" — 黑板粉笔风
- 背景：#2C2C2C 带微妙噪点纹理（用 CSS radial-gradient 模拟）
- 边框：用 CSS box-shadow 模拟木质相框（#8B6914, #A0822A 渐变）
- 字体：Caveat 或 Permanent Marker（手写风格），中文用 Noto Sans SC
- 文字颜色：#FFFFFF（白色粉笔）、#FFD700（黄色粉笔）、#FF6B6B（红色粉笔）、#87CEEB（蓝色粉笔）、#98FB98（绿色粉笔）
- 箭头和连接线：用 border-bottom + dashed 模拟粉笔线条
- 底部装饰：用彩色圆形 div 模拟粉笔头（红蓝黄绿）
- 关键效果：文字加 text-shadow: 0 0 2px rgba(255,255,255,0.3) 模拟粉笔质感

### style: "blueprint" — 蓝图/工程图纸风
- 背景：#1B3A5C 深蓝，叠加 CSS 网格线（白色 opacity 0.05）
- 文字：#FFFFFF、#87CEEB
- 线条：白色虚线、圆角矩形边框
- 质感：工程图纸的精确感，等宽字体用于数据

### style: "newspaper" — 报纸/杂志排版风
- 背景：#FFF8F0 米白色，带微妙纸张纹理
- 字体：Noto Serif SC 为主（衬线体），标题加粗
- 布局：多栏排版（2-3 栏），分隔线，引用框
- 强调：红色下划线、黑色粗体、灰色引用块

### style: "gradient" — 渐变卡片风
- 背景：大面积渐变（紫→蓝、橙→粉、青→绿）
- 卡片：毛玻璃效果（backdrop-filter: blur + 半透明白色背景）
- 文字：白色为主，阴影增强可读性
- 质感：现代、年轻、社交媒体友好

### style: "paradigm" — 范式转变对照风（适合新旧对比/前后变革/认知翻转）
- 背景：白色或极浅灰 #F8FAFC
- 布局：三栏结构——左栏（旧范式）| 中间（转变箭头）| 右栏（新范式）
- 顶部标题栏：三段式
  - 左：旧范式标题（深蓝 #1E3A5F，衬线体）
  - 中：转变主题（小标签 + 大标题，如"PARADIGM SHIFT · 范式转变"）
  - 右：新范式标题（深蓝，衬线体）
- 左栏（旧）：浅灰背景卡片（#F1F5F9），左侧 3px 灰色边条，编号用灰色圆圈（①②③）
  - 文字简短，一句话描述旧做法，灰色调，暗示"过时"
- 中间：蓝色实心箭头（→），用 CSS border 或 ▶ 字符，每行一个，与左右卡片对齐
- 右栏（新）：白色卡片，左侧 3px 橙色边条，编号用橙色实心圆（❶❷❸）
  - 粗体标题（橙色或深蓝）+ 一句话说明（灰色正文）
  - 比左栏内容更丰富，体现"升级感"
- 底部总结栏：深蓝背景条，白色文字，一句话总结核心转变（旧 → 新），右侧标注来源
- 分隔线：每行之间用 1px 浅灰线分隔
- 适合：政策对比、技术演进、组织变革、商业模式转型、认知升级

### style: "dashboard" — 数据仪表盘风（适合多维度指标/评分/对比概览）
- 背景：深色（#0F172A 或 #111827），微妙的网格线（1px rgba(255,255,255,0.03)）
- 布局：卡片网格（2-3 列），上方标题栏 + 标签徽章，下方卡片阵列
- 标题栏：左侧大标题（关键词用亮色高亮，如蓝 #60A5FA 或橙 #F59E0B），右侧圆角标签徽章（边框样式）
- 副标题行：⚡ 图标 + 一句话摘要 + 右侧彩色胶囊标签（如 PARADIGM SHIFT）
- 指标卡片：深色半透明背景（rgba(30,41,59,0.8)），圆角 16px，顶部 3px 彩色边条（每张卡片不同色）
  - 卡片头部：编号圆圈（彩色渐变）+ 粗体标题 + 副标题
  - 进度条：CSS 实现的水平进度条，显示百分比（如"颠覆程度指数 85%"），渐变填充
  - 洞察标签：小圆角矩形，⚡ + 文字，彩色背景
  - 底部：▶ 一句话说明，小字灰色
- 颜色循环：蓝 #3B82F6 → 绿 #10B981 → 紫 #8B5CF6 → 橙 #F97316 → 青 #06B6D4
- 进度条实现：外层 div（深灰背景 rounded），内层 div（渐变色 width:N%）
- 适合：多维度评分、竞品对比、政策要点评估、技术成熟度评级、财报指标概览

### style: "timeline" — 蛇形时间线风（适合 N 大要点/步骤/里程碑）
- 背景：深色渐变（#0F1629 → #1A1A2E），或纯深蓝 #111827
- 核心元素：垂直中轴线（2-3px 宽，渐变色或半透明白色），左右交替排列内容卡片
- 节点：中轴线上的彩色圆形编号（渐变色圆 40-50px，白色数字 font-weight 900）
  - 颜色循环：橙 #F97316 → 紫 #8B5CF6 → 蓝 #3B82F6 → 绿 #10B981 → 红 #EF4444
- 内容卡片：深色半透明背景（rgba(30,40,60,0.8)），圆角 12px，左侧或右侧有 4px 彩色边条（与节点同色）
  - 卡片内：粗体标题 18-20px → 副标题/标签 12px → 正文 14px
  - 标签用小圆角矩形：如 ⚡反直觉 用橙色背景
- 蛇形布局：奇数节点卡片在右侧，偶数在左侧，通过中轴线串联
- 顶部：标题区，超大字号标题 + 副标题 + 装饰性下划线
- 底部：可选总结区或来源标注
- 连接线：从节点到卡片用短横线或 CSS border 连接
- 适合：政策要点、产品特性、发展阶段、对比分析中的多个维度

### style: "architecture" — 云架构图风（类似 AWS 架构图）
- 背景：纯白 #FFFFFF，干净无装饰
- 布局：编号步骤纵向排列（❶❷❸❹❺❻），每步一个独立区块
- 区块结构：左中右三栏对比（如 GCP vs AWS vs Azure），或左右两栏流程
- 箭头：用 CSS border + transform:rotate 制作实心箭头，颜色区分方向（绿=正向，红=问题，蓝=数据流）
- 图标：用 emoji 或 CSS 圆角矩形+文字模拟服务图标（如 🪣 S3、☁️ Cloud、🖥️ VM、📦 Container）
- 服务框：圆角矩形，浅色填充（#E8F4FD 蓝底、#FFF3E0 橙底、#E8F5E9 绿底），1px 实线边框
- 标题：每步用大号编号圆圈（背景色圆 + 白色数字）+ 粗体标题
- 对比标注：红色 "Poor Performance" / 绿色 "High Performance" 标签
- 连接线：用 border-left/border-top + dashed 模拟，灰色 #CCC
- 字体：Noto Sans SC，正文 13-14px，紧凑排版
- 关键效果：信息密度高，每个区块自成一体但通过编号串联成完整叙事

## 字体层次（每张图至少 4 级）
- 冲击数字：40-56px, font-weight 900
- 标题：22-26px, font-weight 700
- 正文：14-16px, font-weight 400
- 标注/来源：11-13px, font-weight 400, color 较浅

## 反 AI Slop 原则
❌ 禁止：蓝白双色 + 居中对齐 + 均匀分布的模板化输出
✅ 要求：
- 非对称布局优先
- 至少一个打破常规的视觉元素
- 每张图有一个明确的"记忆点"
- 相邻页面的风格要有变化（不要每页都一样）

## 7 种图示类型
1. 数据对比图：左右或上下对比，用色彩区分正负
2. 流程链条图：步骤间用箭头或连接线串联
3. CSS 柱状图：用 div 高度/宽度模拟柱状图
4. 信息卡片阵列：2-4 列卡片网格
5. 金句卡片：大字号金句 + 装饰性背景
6. 时间线：垂直或水平时间轴
7. 概念类比：用生活化图示解释技术概念

## 输出格式
只输出 HTML 代码，不要任何解释文字。HTML 必须是完整的，包含 <html><head><body>。
根容器 div 必须有 style="width:900px; margin:0 auto; padding:48px; box-sizing:border-box;"。
不要设固定高度，让内容自适应。"""


# ─── SVG Design System Prompt ───

SVG_SYSTEM_PROMPT = """你是一位 SVG 信息图设计师，为中文科技公众号制作精确的矢量图。

## SVG 规范
- 画布：viewBox="0 0 900 {height}"，高度按内容调整（400-680px）
- 背景：<rect width="900" height="{height}" rx="16" fill="#F8FAFC"/>
- 字体：font-family="system-ui, -apple-system, sans-serif"

## 配色体系
| 语义 | 主色 | 浅色填充 | 边框 |
|------|------|---------|------|
| 问题/警告 | #991B1B | #FEE2E2 | #FCA5A5 |
| 解决方案 | #166534 | #D1FAE5 | #86EFAC |
| 技术/算法 | #5B21B6 | #EDE9FE | #C4B5FD |
| 数据/信息 | #1E40AF | #DBEAFE | #93C5FD |
| 中性 | #92400E | #FEF3C7 | #F59E0B |

## 排版
- 标题：font-size="18" font-weight="700" fill="#1E293B"
- 区块标题：font-size="13-14" font-weight="700"
- 正文：font-size="10-11" fill="#475569"
- 辅助：font-size="9-10" fill="#94A3B8"

## 组件
- 外框：rx="12" fill="white" stroke="颜色" stroke-width="1.5"
- 内部卡片：rx="8" fill="浅色"
- 箭头：用 <marker> 定义

## 输出
只输出 SVG 代码，不要任何解释文字。必须是完整的 <svg> 标签。"""


def extract_infographic_spec(story_content: str) -> list[dict]:
    """从故事 markdown 中提取 infographic_spec JSON 块（数组格式）。"""
    in_infographic = False
    in_json = False
    json_lines = []
    for line in story_content.split("\n"):
        if "### INFOGRAPHIC" in line or "图示规格" in line:
            in_infographic = True
        if in_infographic and line.strip().startswith("```json"):
            in_json = True
            continue
        if in_json and line.strip() == "```":
            in_json = False
            break
        if in_json:
            json_lines.append(line)
    if json_lines:
        try:
            result = json.loads("\n".join(json_lines))
            if isinstance(result, dict):
                return [result]  # 兼容旧的单对象格式
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass
    return []


def extract_story_context(story_content: str) -> dict:
    """从故事 markdown 提取标题、主线、数据点等上下文。"""
    ctx = {"title": "", "storyline": "", "data_points": [], "category": ""}
    for line in story_content.split("\n"):
        if line.startswith("# ") and not ctx["title"]:
            ctx["title"] = line[2:].strip()
        if line.startswith("title:"):
            ctx["title"] = line.split(":", 1)[1].strip().strip('"')
        if line.startswith("category:"):
            ctx["category"] = line.split(":", 1)[1].strip()
    # 提取故事主线
    in_storyline = False
    for line in story_content.split("\n"):
        if "## 故事主线" in line:
            in_storyline = True
            continue
        if in_storyline and line.startswith("## "):
            break
        if in_storyline and line.strip():
            ctx["storyline"] += line.strip() + " "
    # 提取关键数据点
    in_data = False
    for line in story_content.split("\n"):
        if "关键数据点" in line or "key_data_points" in line:
            in_data = True
            continue
        if in_data and line.startswith("- "):
            ctx["data_points"].append(line[2:].strip())
        elif in_data and not line.startswith("- ") and line.strip():
            in_data = False
    return ctx


def build_html_prompt(spec: dict, story_ctx: dict) -> str:
    """构建 HTML 信息图生成 prompt。"""
    return f"""为以下故事生成一张信息图的 HTML+CSS 代码。

## 故事信息
标题：{story_ctx.get('title', '')}
类别：{story_ctx.get('category', '')}
主线：{story_ctx.get('storyline', '')}
关键数据：{json.dumps(story_ctx.get('data_points', []), ensure_ascii=False)}

## 图示规格
类型：{spec.get('type', '数据对比图')}
标题：{spec.get('title', story_ctx.get('title', ''))}
视觉风格：{spec.get('color_scheme', 'dark')}
主视觉焦点：{spec.get('focal_point', '')}
记忆点：{spec.get('memory_hook', '')}
数据：{json.dumps(spec.get('data', {}), ensure_ascii=False)}
布局说明：{spec.get('layout_notes', '')}

## 设计三问（请先思考再动手）
1. 读者扫一眼要记住什么？→ {spec.get('focal_point', '待确定')}
2. 最适合什么图示类型？→ {spec.get('type', '待确定')}
3. 记忆点是什么？→ {spec.get('memory_hook', '待确定')}

请使用 "{spec.get('color_scheme', 'dark')}" 视觉风格生成完整的 HTML 代码。"""


def build_svg_prompt(spec: dict, story_ctx: dict) -> str:
    """构建 SVG 信息图生成 prompt。"""
    return f"""为以下故事生成一张 SVG 信息图。

## 故事信息
标题：{story_ctx.get('title', '')}
主线：{story_ctx.get('storyline', '')}
关键数据：{json.dumps(story_ctx.get('data_points', []), ensure_ascii=False)}

## 图示规格
类型：{spec.get('type', '数据对比图')}
标题：{spec.get('title', story_ctx.get('title', ''))}
数据：{json.dumps(spec.get('data', {}), ensure_ascii=False)}
布局说明：{spec.get('layout_notes', '')}

请生成完整的 SVG 代码，viewBox 宽度 900px。"""


def _load_qrcode_base64() -> str:
    """加载公众号二维码并转为 base64 data URI。"""
    import base64
    # 优先查找本 skill 的 assets 目录
    qr_path = os.path.join(SCRIPT_DIR, "..", "assets", "qrcode_weixin_InsightsJun-small.jpg")
    if not os.path.isfile(qr_path):
        return ""
    with open(qr_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/jpeg;base64,{data}"


def _inject_qrcode(html: str) -> str:
    """在 HTML 的根容器右上角注入公众号二维码。"""
    qr_uri = _load_qrcode_base64()
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
        html = html.replace("</body>", qr_html + "\n</body>", 1)
    else:
        html += qr_html
    return html


def generate_html(spec: dict, story_ctx: dict) -> str:
    """调用 LLM 生成 HTML 信息图代码。"""
    import llm_client
    prompt = build_html_prompt(spec, story_ctx)
    raw = llm_client.invoke(prompt, system=DESIGN_SYSTEM_PROMPT, max_tokens=8192,
                            temperature=0.4)
    # 提取 HTML 代码
    html = raw.strip()
    if "```html" in html:
        html = html.split("```html", 1)[1]
        if "```" in html:
            html = html.split("```", 1)[0]
    elif "```" in html:
        parts = html.split("```")
        if len(parts) >= 3:
            html = parts[1]
    # 确保有完整的 HTML 结构
    if "<html" not in html.lower():
        html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700;900&family=Noto+Serif+SC:wght@700;900&display=swap" rel="stylesheet">
</head><body style="margin:0;padding:0;background:#fff;">
{html}
</body></html>"""
    # 注入公众号二维码到右上角
    html = _inject_qrcode(html)
    return html


def generate_svg(spec: dict, story_ctx: dict) -> str:
    """调用 LLM 生成 SVG 信息图代码。"""
    import llm_client
    prompt = build_svg_prompt(spec, story_ctx)
    raw = llm_client.invoke(prompt, system=SVG_SYSTEM_PROMPT, max_tokens=8192,
                            temperature=0.3)
    svg = raw.strip()
    if "```svg" in svg or "```xml" in svg:
        svg = re.split(r"```(?:svg|xml)?", svg)[1]
        if "```" in svg:
            svg = svg.split("```")[0]
    elif "<svg" in svg:
        start = svg.index("<svg")
        end = svg.rindex("</svg>") + 6
        svg = svg[start:end]
    return svg.strip()


def screenshot_html(html: str, output_path: str, retries: int = 1) -> bool:
    """用 Playwright 将 HTML 截图为 PNG，自适应内容高度。"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ 请安装 playwright: pip3 install playwright && python3 -m playwright install chromium",
              file=sys.stderr)
        return False

    for attempt in range(retries + 1):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page(viewport={"width": 1000, "height": 800})
                page.set_content(html)
                page.wait_for_timeout(2500)  # 等待 Google Fonts 加载

                # 获取实际内容高度，调整 viewport 避免空白
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

                # 截取全页（包含 fixed 定位的二维码）
                page.screenshot(path=output_path, full_page=True)
                browser.close()
            print(f"  ✅ 截图成功: {output_path}", file=sys.stderr)
            return True
        except Exception as e:
            if attempt < retries:
                print(f"  ⚠️ 截图失败（重试 {attempt+1}）: {e}", file=sys.stderr)
            else:
                print(f"  ❌ 截图失败: {e}", file=sys.stderr)
    return False


def main():
    parser = argparse.ArgumentParser(description="为文章/故事生成信息图")
    parser.add_argument("--story", help="故事/文章 markdown 文件路径")
    parser.add_argument("--from-spec", action="store_true",
                        help="从 stdin 读取 JSON spec")
    parser.add_argument("--method", choices=["html", "svg", "auto"], default="auto",
                        help="生成方式: html(截图), svg, auto(自动选择)")
    parser.add_argument("--output-dir", required=True, help="图示输出目录")
    parser.add_argument("--slug", help="输出文件名前缀（默认从故事 ID 提取）")
    parser.add_argument("--dry-run", action="store_true", help="只生成代码不截图")
    parser.add_argument("--force", action="store_true", help="强制重新生成（忽略缓存）")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # 获取 spec 和上下文
    if args.from_spec:
        raw_spec = json.loads(sys.stdin.read())
        if isinstance(raw_spec, list):
            specs = raw_spec
        elif "pages" in raw_spec:
            specs = raw_spec["pages"]
        else:
            specs = [raw_spec]
        story_ctx = raw_spec.get("story_context", {"title": "", "storyline": "", "data_points": []}) if isinstance(raw_spec, dict) else {}
        slug = args.slug or "illustration"
    elif args.story:
        if not os.path.isfile(args.story):
            print(f"❌ 故事文件不存在: {args.story}", file=sys.stderr)
            sys.exit(1)
        with open(args.story, "r", encoding="utf-8") as f:
            content = f.read()
        specs = extract_infographic_spec(content)
        story_ctx = extract_story_context(content)
        slug = args.slug or os.path.basename(args.story).replace(".md", "")
        if not specs:
            print("⚠️ 故事文件中未找到 infographic_spec，使用默认单张配置", file=sys.stderr)
            specs = [{
                "page": 1, "role": "cover",
                "type": "信息卡片阵列",
                "title": story_ctx.get("title", ""),
                "color_scheme": "dark",
                "focal_point": "核心数据",
                "memory_hook": "关键数字",
            }]
    else:
        parser.print_help()
        sys.exit(1)

    print(f"🎨 生成信息图: {story_ctx.get('title', slug)} ({len(specs)} 张分镜)", file=sys.stderr)

    # 变化检测：计算 specs 的 hash，与上次生成对比
    specs_hash = hashlib.sha256(json.dumps(specs, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]
    hash_file = os.path.join(args.output_dir, ".specs_hash")
    if os.path.isfile(hash_file):
        with open(hash_file, "r") as f:
            old_hash = f.read().strip()
        if old_hash == specs_hash and not args.force:
            all_exist = True
            for spec in specs:
                pn = spec.get("page", 0)
                ps = f"{slug}-P{pn}"
                if not (os.path.isfile(os.path.join(args.output_dir, f"{ps}.png")) or
                        os.path.isfile(os.path.join(args.output_dir, f"{ps}.svg"))):
                    all_exist = False
                    break
            if all_exist:
                print(f"  ⏭️  内容未变化且图片已存在，跳过生成（用 --force 强制重新生成）", file=sys.stderr)
                existing = []
                for spec in specs:
                    pn = spec.get("page", 0)
                    ps = f"{slug}-P{pn}"
                    png = os.path.join(args.output_dir, f"{ps}.png")
                    svg = os.path.join(args.output_dir, f"{ps}.svg")
                    if os.path.isfile(png):
                        existing.append({"page": pn, "method": "html", "png_path": png})
                    elif os.path.isfile(svg):
                        existing.append({"page": pn, "method": "svg", "svg_path": svg})
                print(json.dumps({"slug": slug, "total_pages": len(existing),
                                  "pages": existing, "skipped": True}, ensure_ascii=False, indent=2))
                return

    results = []
    for spec in specs:
        page_num = spec.get("page", len(results) + 1)
        page_slug = f"{slug}-P{page_num}"
        method = args.method
        if method == "auto":
            gen_method = spec.get("generation_method", "html_screenshot")
            method = "svg" if gen_method == "svg" else "html"

        print(f"\n  📄 P{page_num}: {spec.get('title', '?')} [{spec.get('type', '?')}] ({method})", file=sys.stderr)

        if method == "html":
            html = generate_html(spec, story_ctx)
            html_path = os.path.join(args.output_dir, f"{page_slug}.html")
            png_path = os.path.join(args.output_dir, f"{page_slug}.png")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)
            if not args.dry_run:
                ok = screenshot_html(html, png_path)
                if ok:
                    fsize = os.path.getsize(png_path)
                    print(f"    📐 {fsize / 1024:.1f} KB", file=sys.stderr)
            else:
                print(f"    [dry-run] 跳过截图", file=sys.stderr)
            results.append({"page": page_num, "method": "html",
                           "html_path": html_path, "png_path": png_path})

        elif method == "svg":
            svg = generate_svg(spec, story_ctx)
            svg_path = os.path.join(args.output_dir, f"{page_slug}.svg")
            png_path = os.path.join(args.output_dir, f"{page_slug}.png")
            with open(svg_path, "w", encoding="utf-8") as f:
                f.write(svg)
            print(f"    💾 {svg_path}", file=sys.stderr)
            if not args.dry_run:
                svg_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#fff;position:relative;">
{svg}
</body></html>"""
                svg_html = _inject_qrcode(svg_html)
                ok = screenshot_html(svg_html, png_path)
                if ok:
                    fsize = os.path.getsize(png_path)
                    print(f"    📐 PNG: {fsize / 1024:.1f} KB", file=sys.stderr)
            results.append({"page": page_num, "method": "svg",
                           "svg_path": svg_path, "png_path": png_path})

    # 保存 specs hash
    with open(hash_file, "w") as f:
        f.write(specs_hash)

    print(f"\n✅ 完成: {len(results)} 张信息图", file=sys.stderr)
    print(json.dumps({"slug": slug, "total_pages": len(results), "pages": results},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
