# article2graphic — 文章信息图生成 Skill

[English](README-EN.md)

将 Markdown 文章自动转换为一系列高质量信息图（PNG/SVG）。

通过 AI agent 驱动生成，不需要额外配置大语言模型或 API 密钥。支持 Kiro、OpenClaw、Claude Code 三种 agent。

## ✨ 特性

- 🤖 Agent 驱动：零 LLM 配置，用户已有的 agent 就是生成引擎
- 🎨 10+ 视觉风格：dark、gradient、chalkboard、blueprint、newspaper、dashboard、timeline、paradigm、architecture 等
- 📄 7 种图示类型：数据对比图、流程链条图、CSS 柱状图、信息卡片阵列、金句卡片、时间线、概念类比
- 📱 多页分镜：每个章节一张图，统一主风格，通过图示类型变化制造视觉节奏
- 🖼️ 双模式输出：HTML+Playwright 截图（默认）或 SVG 矢量图
- 🔖 自动水印：注入公众号二维码到右上角（可选）

## 📦 安装

### 作为 Kiro Global Skill

```bash
git clone https://github.com/soldierxue/skill-article2graphic.git ~/.kiro/skills/article2graphic
```

安装后在 Kiro 对话中提到"生成信息图"等关键词时自动激活。

### 作为 Claude Code Skill

```bash
git clone https://github.com/soldierxue/skill-article2graphic.git ~/.claude/skills/article2graphic
```

安装后在 Claude Code 中通过以下方式使用：
- 对话中说"生成信息图"、"文章配图"、"infographic"等关键词自动触发
- 或显式调用 `/article2graphic`

### 作为 OpenClaw Skill

```bash
# 克隆到工作区目录
git clone https://github.com/soldierxue/skill-article2graphic.git article2graphic
```

在 OpenClaw 对话中引用：
> 请按照 article2graphic/SKILL.md 的流程，为这篇文章生成信息图

### 作为独立项目（CLI 模式）

```bash
git clone https://github.com/soldierxue/skill-article2graphic.git
cd skill-article2graphic
pip install playwright
playwright install chromium
./scripts/run.sh gen --story path/to/article.md
```

## 🔧 依赖

```bash
pip install playwright
playwright install chromium
```

不需要 boto3，不需要 AWS credentials，不需要配置模型。

## 🚀 三种使用方式

### 方式 A：Kiro / OpenClaw IDE（推荐）

安装为 Kiro global skill 后，在对话中说：

> 帮我为这篇文章生成信息图

Agent 会自动激活 SKILL.md，按流程执行：
1. 扫描文章章节结构，规划分镜 spec
2. 逐页生成 HTML（读取 `prompts/` 下的设计规范）
3. 调用 `screenshot.py` 批量截图 + 注入二维码
4. 生成朋友圈 + 小红书推广短文（`{slug}-promo.md`）

OpenClaw 同理，引用 SKILL.md 即可。

### 方式 B：CLI 模式（kiro-cli / Claude Code）

```bash
# 自动检测可用 agent（kiro-cli 优先）
./scripts/run.sh gen --story article.md

# 指定使用 Claude Code
./scripts/run.sh gen --story article.md --agent claude

# 从 JSON spec 生成
cat spec.json | ./scripts/run.sh gen --from-spec --slug my-article

# 只生成 prompt 不调用 agent（调试用）
./scripts/run.sh gen --story article.md --dry-run

# 批量截图已有 HTML
./scripts/run.sh screenshot output/ --inject-qrcode
```

### 方式 C：手动模式

1. 提取 spec：`python3 scripts/extract_spec.py article.md > spec.json`
2. 手动编写分镜 spec JSON（参考下方格式）
3. 将 prompt 粘贴给任意 AI agent 生成 HTML
4. 截图：`python3 scripts/screenshot.py --html-dir output/ --inject-qrcode`

## 📝 输入格式

### 方式 1：文章中嵌入 infographic_spec

```markdown
### INFOGRAPHIC 图示规格

```json
[
  {
    "page": 1,
    "type": "数据对比图",
    "title": "核心指标对比",
    "color_scheme": "dark",
    "focal_point": "关键差异",
    "memory_hook": "记忆点",
    "data": { ... }
  }
]
```　
```

### 方式 2：独立 spec JSON 文件

参考 `T12-MStories/ironwood-vs-trainium3-spec.json` 的格式。

### 方式 3：无 spec（agent 自动规划）

如果文章没有 `infographic_spec`，agent 会按 SKILL.md 的规则自动规划：
- 分镜数量 = 文章章节数量
- 统一主风格，通过图示类型变化制造节奏

## 🎨 视觉风格

同一内容，10 种风格。以下示例均使用 TPU Ironwood vs Trainium3 芯片规格数据生成：

| | |
|:---:|:---:|
| ![dark](examples/style-dark.png) | ![light](examples/style-light.png) |
| `dark` — 科技暗色 | `light` — 简洁亮色 |
| ![gradient](examples/style-gradient.png) | ![blueprint](examples/style-blueprint.png) |
| `gradient` — 渐变卡片风 | `blueprint` — 蓝图工程风 |
| ![dashboard](examples/style-dashboard.png) | ![newspaper](examples/style-newspaper.png) |
| `dashboard` — 数据仪表盘 | `newspaper` — 报纸杂志风 |
| ![chalkboard](examples/style-chalkboard.png) | ![paradigm](examples/style-paradigm.png) |
| `chalkboard` — 黑板粉笔风 | `paradigm` — 范式对照 |
| ![timeline](examples/style-timeline.png) | ![architecture](examples/style-architecture.png) |
| `timeline` — 蛇形时间线 | `architecture` — 云架构图 |

## 📁 目录结构

```
article2graphic/
├── SKILL.md                          ← Agent 指令（Kiro/OpenClaw 激活入口）
├── CLAUDE.md                         ← Claude Code 入口（引用 SKILL.md）
├── prompts/
│   ├── design-system-html.md         ← HTML 设计规范
│   ├── design-system-svg.md          ← SVG 设计规范
│   └── promo-writer.md               ← 推广短文写作规范
├── scripts/
│   ├── run.sh                        ← CLI 入口（调用 agent）
│   ├── extract_spec.py               ← Markdown → JSON spec（纯解析）
│   └── screenshot.py                 ← HTML → PNG 截图（纯工具）
├── assets/
│   └── qrcode_weixin_*.jpg           ← 公众号二维码（可替换）
└── output/                           ← 默认输出目录
```

## 🏗️ 架构

```
Markdown 文章
    ↓
extract_spec.py 提取 spec（或 agent 自动规划）
    ↓
run.sh 构建 prompt（设计规范 + spec 数据）
    ↓
Agent (Kiro / OpenClaw / kiro-cli / claude) 生成 HTML/SVG
    ↓
screenshot.py 截图 → PNG + 二维码水印
    ↓
Agent 生成推广短文 → {slug}-promo.md（朋友圈 + 小红书版）
```

## 🔄 自定义

- 替换 `assets/` 下的二维码图片为你自己的
- 修改 `prompts/` 下的设计规范来调整视觉风格
- 修改 `SKILL.md` 中的 `Activate when` 关键词来调整触发条件

## License

MIT
