# article2graphic — Kiro Skill for Article Infographic Generation

将文章/故事 Markdown 转换为高质量信息图（PNG/SVG）。

支持 HTML+Playwright 截图和 SVG 两种生成方式，内置 10+ 视觉风格，
自动注入公众号二维码水印，支持多页分镜批量生成。

## ✨ 特性

- 🎨 10+ 视觉风格：暗色科技、黑板粉笔、蓝图、报纸、仪表盘、时间线、渐变卡片、范式对照、云架构图等
- 📄 7 种图示类型：数据对比图、流程链条图、CSS 柱状图、信息卡片阵列、金句卡片、时间线、概念类比
- 🖼️ 双模式输出：HTML+Playwright 截图（默认）或 SVG 矢量图
- 📱 多页分镜：从 Markdown 中的 `infographic_spec` JSON 块批量生成
- 🔖 自动水印：注入公众号二维码到右上角（可选）
- ⚡ 增量生成：基于 spec hash 的缓存机制，内容不变则跳过

## 📦 安装为 Kiro Global Skill

```bash
# 克隆仓库到 Kiro 全局 skills 目录
git clone https://github.com/soldierxue/article2graphic.git ~/.kiro/skills/article2graphic
```

安装后，在 Kiro 对话中提到"生成信息图"、"infographic"、"文章配图"等关键词时会自动激活。

## 🔧 依赖

```bash
pip install boto3 playwright
playwright install chromium
```

## ⚙️ 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `AWS_REGION` | `us-east-1` | Bedrock 区域 |
| `AWS_PROFILE` | _(无)_ | AWS 配置文件 |
| `LLM_MODEL_ID` | `us.anthropic.claude-opus-4-6-v1` | 模型 ID |
| `LLM_READ_TIMEOUT` | `600` | API 超时秒数 |

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

# 从 JSON spec 生成（stdin）
echo '{"type":"数据对比图","title":"AI 能耗对比","data":{"left":"传统","right":"AI"}}' | \
  ./scripts/run.sh gen --from-spec

# 只生成 HTML/SVG 代码不截图
./scripts/run.sh gen --story article.md --dry-run

# 强制重新生成（忽略缓存）
./scripts/run.sh gen --story article.md --force
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
├── SKILL.md                  ← Kiro skill 描述（含 front-matter）
├── assets/
│   └── qrcode_weixin_*.jpg   ← 公众号二维码（可替换为你自己的）
├── scripts/
│   ├── gen_illustration.py   ← 核心生成脚本
│   ├── llm_client.py         ← Bedrock LLM 客户端
│   └── run.sh                ← 统一入口
└── output/                   ← 默认输出目录
```

## 🔄 自定义

- 替换 `assets/` 下的二维码图片为你自己的公众号二维码
- 修改 `SKILL.md` 中的 `Activate when` 关键词来调整触发条件
- 修改 `llm_client.py` 中的默认模型 ID 来切换 LLM

## License

MIT
