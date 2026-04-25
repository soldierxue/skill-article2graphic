#!/usr/bin/env python3
"""
extract_spec.py — 从 Markdown 文章中提取 infographic_spec 和故事上下文。

纯解析工具，不依赖 LLM。

用法:
  python3 scripts/extract_spec.py story.md
  # 输出 JSON 到 stdout: {"specs": [...], "context": {...}}
"""
from __future__ import annotations

import json
import os
import sys


def extract_infographic_spec(content: str) -> list[dict]:
    """从 markdown 中提取 infographic_spec JSON 块。"""
    in_infographic = False
    in_json = False
    json_lines = []
    for line in content.split("\n"):
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
                return [result]
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass
    return []


def extract_story_context(content: str) -> dict:
    """从 markdown 提取标题、主线、数据点等上下文。"""
    ctx = {"title": "", "storyline": "", "data_points": [], "category": ""}
    for line in content.split("\n"):
        if line.startswith("# ") and not ctx["title"]:
            ctx["title"] = line[2:].strip()
        if line.startswith("title:"):
            ctx["title"] = line.split(":", 1)[1].strip().strip('"')
        if line.startswith("category:"):
            ctx["category"] = line.split(":", 1)[1].strip()
    # 故事主线
    in_storyline = False
    for line in content.split("\n"):
        if "## 故事主线" in line:
            in_storyline = True
            continue
        if in_storyline and line.startswith("## "):
            break
        if in_storyline and line.strip():
            ctx["storyline"] += line.strip() + " "
    # 关键数据点
    in_data = False
    for line in content.split("\n"):
        if "关键数据点" in line or "key_data_points" in line:
            in_data = True
            continue
        if in_data and line.startswith("- "):
            ctx["data_points"].append(line[2:].strip())
        elif in_data and not line.startswith("- ") and line.strip():
            in_data = False
    return ctx


def main():
    if len(sys.argv) < 2:
        print("用法: python3 scripts/extract_spec.py <markdown-file>", file=sys.stderr)
        sys.exit(1)

    md_path = sys.argv[1]
    if not os.path.isfile(md_path):
        print(f"❌ 文件不存在: {md_path}", file=sys.stderr)
        sys.exit(1)

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    specs = extract_infographic_spec(content)
    ctx = extract_story_context(content)

    if not specs:
        specs = [{
            "page": 1, "role": "cover",
            "type": "信息卡片阵列",
            "title": ctx.get("title", ""),
            "color_scheme": "dark",
            "focal_point": "核心数据",
            "memory_hook": "关键数字",
        }]
        print("⚠️ 未找到 infographic_spec，使用默认配置", file=sys.stderr)

    print(json.dumps({"specs": specs, "context": ctx}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
