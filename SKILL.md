---
name: article2graphic
description: >
  将文章/故事 Markdown 转换为高质量信息图（PNG/SVG）。
  支持 HTML+Playwright 截图和 SVG 两种生成方式，
  内置 10+ 视觉风格（暗色科技、黑板粉笔、蓝图、报纸、仪表盘、时间线等），
  自动注入公众号二维码水印，支持多页分镜批量生成。
  Activate when: 生成信息图, 生成配图, infographic, illustration,
  article to graphic, 文章配图, 图文生成, 数据可视化图, 生成图片。
---

# article2graphic — 文章信息图生成引擎（Agent 模式）

通过 AI agent（kiro-cli / claude code / openclaw）生成信息图，
不需要额外配置大语言模型或 AWS credentials。

## 架构

```
用户提供 Markdown 文章
    ↓
extract_spec.py 提取 infographic_spec + 故事上下文
    ↓
run.sh 逐页构建 prompt（含设计规范）
    ↓
Agent (kiro-cli / claude) 生成 HTML/SVG 代码并写入文件
    ↓
screenshot.py 用 Playwright 截图为 PNG + 注入二维码
    ↓
输出: output/*.png
```

## 目录结构

```
article2graphic/
├── SKILL.md                          ← 本文件
├── prompts/
│   ├── design-system-html.md         ← HTML 信息图设计规范
│   └── design-system-svg.md          ← SVG 信息图设计规范
├── scripts/
│   ├── run.sh                        ← 统一入口（调用 agent）
│   ├── extract_spec.py               ← 从 Markdown 提取 spec（纯解析）
│   └── screenshot.py                 ← Playwright 截图工具（纯工具）
├── assets/
│   └── qrcode_weixin_*.jpg           ← 公众号二维码（可选）
└── output/                           ← 默认输出目录
```

## 用法

```bash
# 从 Markdown 文章生成信息图
./scripts/run.sh generate --story path/to/article.md

# 指定输出目录和方法
./scripts/run.sh gen --story article.md --output-dir pics --method svg

# 只生成 prompt 不调用 agent（调试用）
./scripts/run.sh gen --story article.md --dry-run

# 批量截图已有 HTML
./scripts/run.sh screenshot output/ --inject-qrcode
```

## Agent 生成流程（当 Kiro 激活本 skill 时）

当用户在 Kiro 中说"帮我生成信息图"时，请按以下步骤执行：

### Step 0: 分镜规划（关键步骤）

如果文章中没有 `infographic_spec` JSON 块，agent 必须先规划分镜。

**核心规则：**

1. **分镜数量 = 文章章节数量。** 逐一扫描文章的所有一级/二级章节标题，每个章节对应一张信息图，不要跳过或合并章节。一篇 10 章节的文章应产出 10 张分镜，而非 5 张"精选"。

2. **一篇文章统一主风格。** 所有分镜共享同一个 `color_scheme`（如 `dark`），保持配色、字体、背景的一致性，让整组图有系列感。通过**图示类型的变化**（数据对比图、柱状图、卡片阵列、时间线、范式对照等）来制造视觉节奏，而不是切换完全不同的视觉体系。允许个别特殊页面（如封面、总结页）微调风格，但主色调必须一致。

3. 将规划结果写入 spec JSON 文件，然后通过 `--from-spec` 管道传入 `run.sh`。

### Step 1: 提取 spec
```bash
python3 scripts/extract_spec.py <markdown-file>
```
输出 JSON 包含 `specs`（分镜数组）和 `context`（故事上下文）。
如果返回默认 spec（1 张），说明文章没有 `infographic_spec`，需要执行 Step 0。

### Step 2: 逐页生成
对每个 spec 页面：
1. 读取 `prompts/design-system-html.md`（或 svg 版本）
2. 结合 spec 中的类型、风格、数据等信息
3. 生成完整的 HTML/SVG 代码
4. 将代码写入 `output/{slug}-P{n}.html`（或 .svg）

### Step 3: 截图
```bash
python3 scripts/screenshot.py --html-dir output/ --inject-qrcode
```

## 设计规范

详见 `prompts/design-system-html.md` 和 `prompts/design-system-svg.md`。

核心原则：
- 10+ 视觉风格：dark, light, chalkboard, blueprint, newspaper, gradient, paradigm, dashboard, timeline, architecture
- 7 种图示类型：数据对比图、流程链条图、CSS 柱状图、信息卡片阵列、金句卡片、时间线、概念类比
- 反 AI Slop：非对称布局、打破常规的视觉元素、明确的记忆点

## 依赖

- Agent: kiro-cli 或 claude code（自动检测）
- 截图: `pip install playwright && playwright install chromium`
- 无需 boto3、无需 AWS credentials
