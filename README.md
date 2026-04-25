# article2graphic — Kiro Skill for Article Infographic Generation

将文章/故事 Markdown 转换为高质量信息图（PNG/SVG）。

通过 AI agent（kiro-cli / claude code）生成，不需要额外配置大语言模型或 AWS credentials。

## ✨ 特性

- 🤖 Agent 驱动：通过 kiro-cli / claude code 生成，零 LLM 配置
- 🎨 10+ 视觉风格：暗色科技、黑板粉笔、蓝图、报纸、仪表盘、时间线等
- 📄 7 种图示类型：数据对比图、流程链条图、CSS 柱状图、信息卡片阵列、金句卡片、时间线、概念类比
- 🖼️ 双模式输出：HTML+Playwright 截图（默认）或 SVG 矢量图
- 📱 多页分镜：从 Markdown 中的 `infographic_spec` JSON 块批量生成
- 🔖 自动水印：注入公众号二维码到右上角（可选）

## 📦 安装为 Kiro Global Skill

```bash
git clone https://github.com/soldierxue/skill-article2graphic.git ~/.kiro/skills/article2graphic
```

安装后，在 Kiro 对话中提到"生成信息图"、"infographic"、"文章配图"等关键词时会自动激活。

## 🔧 依赖

```bash
# 截图工具（必需）
pip install playwright
playwright install chromium

# Agent（二选一）
# - kiro-cli（优先检测）
# - claude code
```

不需要 boto3，不需要 AWS credentials。

## 🚀 用法

### 命令行

```bash
cd ~/.kiro/skills/article2graphic

# 从 Markdown 文章生成信息图
./scripts/run.sh generate --story path/to/article.md

# 指定输出目录
./scripts/run.sh gen --story article.md --output-dir my-output

# 使用 SVG 模式
./scripts/run.sh gen --story article.md --method svg

# 只生成 prompt 不调用 agent（调试用）
./scripts/run.sh gen --story article.md --dry-run

# 批量截图已有 HTML
./scripts/run.sh screenshot output/ --inject-qrcode
```

### 在 Kiro 中使用

直接在 Kiro 对话中说：

> 帮我为这篇文章生成信息图

Kiro 会自动激活 article2graphic skill。

## 📝 Markdown 输入格式

文章中包含 `infographic_spec` JSON 块即可：

```markdown
### INFOGRAPHIC 图示规格

```json
[
  {
    "page": 1,
    "type": "数据对比图",
    "title": "AI 推理成本对比",
    "color_scheme": "dark",
    "focal_point": "成本差异 10x",
    "memory_hook": "一杯咖啡 vs 一顿大餐",
    "data": { "left": "传统推理", "right": "解耦推理" }
  }
]
```　
```

如果没有 `infographic_spec`，会自动使用默认配置生成一张封面图。

## 🎨 视觉风格一览

| style | 说明 | 适合场景 |
|-------|------|---------|
| `dark` | 科技暗色 | 数据对比、技术概览 |
| `light` | 简洁亮色 | 通用信息卡片 |
| `chalkboard` | 黑板粉笔风 | 教学、概念解释 |
| `blueprint` | 蓝图工程风 | 技术架构 |
| `newspaper` | 报纸杂志风 | 新闻摘要、多栏排版 |
| `gradient` | 渐变卡片风 | 社交媒体友好 |
| `paradigm` | 范式转变对照 | 新旧对比、变革 |
| `dashboard` | 数据仪表盘 | 多维度指标、评分 |
| `timeline` | 蛇形时间线 | 步骤、里程碑 |
| `architecture` | 云架构图 | 技术架构、流程 |

## 📁 目录结构

```
article2graphic/
├── SKILL.md                          ← Kiro skill 描述
├── prompts/
│   ├── design-system-html.md         ← HTML 设计规范（agent 上下文）
│   └── design-system-svg.md          ← SVG 设计规范
├── scripts/
│   ├── run.sh                        ← 统一入口（调用 agent）
│   ├── extract_spec.py               ← Markdown → JSON spec（纯解析）
│   └── screenshot.py                 ← HTML → PNG 截图（纯工具）
├── assets/
│   └── qrcode_weixin_*.jpg           ← 公众号二维码（可替换）
└── output/                           ← 默认输出目录
```

## 🏗️ 架构

```
Markdown 文章 → extract_spec.py → JSON spec
                                      ↓
                    run.sh 构建 prompt + 设计规范
                                      ↓
                    Agent (kiro-cli/claude) 生成 HTML/SVG
                                      ↓
                    screenshot.py → PNG + 二维码水印
```

与传统方式的区别：
- 旧：Python 脚本 → boto3 → Bedrock API → HTML → 截图
- 新：Shell 脚本 → Agent CLI → HTML → 截图

优势：零 LLM 配置，用户已有的 agent 就是 LLM 引擎。

## 🔄 自定义

- 替换 `assets/` 下的二维码图片为你自己的
- 修改 `prompts/` 下的设计规范来调整视觉风格
- 修改 `SKILL.md` 中的 `Activate when` 关键词来调整触发条件

## License

MIT
