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

# article2graphic — 文章信息图生成引擎

从 Markdown 文章/故事文件中提取 `infographic_spec`，调用 LLM 生成 HTML/SVG 代码，
再通过 Playwright 截图输出 PNG。

## 架构概览

```
T11-Storyline/article2graphic/
├── SKILL.md                  ← 本文件
├── assets/
│   └── qrcode_weixin_InsightsJun-small.jpg  ← 公众号二维码（可选）
├── scripts/
│   ├── gen_illustration.py   ← 核心生成脚本
│   ├── llm_client.py         ← Bedrock LLM 调用客户端
│   └── run.sh                ← 统一入口
└── output/                   ← 默认输出目录
```

## 用法

```bash
# 从故事/文章 Markdown 生成信息图
./scripts/run.sh generate --story path/to/story.md

# 指定输出目录
./scripts/run.sh generate --story path/to/story.md --output-dir my-output

# 从 JSON spec 生成（stdin）
echo '{"type":"数据对比图","title":"...","data":{}}' | \
  ./scripts/run.sh generate --from-spec --output-dir output

# 指定生成方式
./scripts/run.sh generate --story story.md --method svg

# 只生成代码不截图
./scripts/run.sh generate --story story.md --dry-run

# 强制重新生成（忽略缓存）
./scripts/run.sh generate --story story.md --force
```

## 输入格式

### 方式 A：Markdown 文件（含 infographic_spec）

文章 Markdown 中包含如下 JSON 块：

```markdown
### INFOGRAPHIC 图示规格

```json
[
  {
    "page": 1,
    "type": "数据对比图",
    "title": "图表标题",
    "color_scheme": "dark",
    "focal_point": "核心数据",
    "memory_hook": "记忆点",
    "data": { ... },
    "layout_notes": "布局说明"
  }
]
```　
```

### 方式 B：JSON spec（stdin）

直接传入 JSON 对象或数组。

## 支持的视觉风格

| style | 说明 | 适合场景 |
|-------|------|---------|
| dark | 科技暗色 | 数据对比、技术概览 |
| light | 简洁亮色 | 通用信息卡片 |
| chalkboard | 黑板粉笔风 | 教学、概念解释 |
| blueprint | 蓝图工程风 | 技术架构 |
| newspaper | 报纸杂志风 | 新闻摘要、多栏排版 |
| gradient | 渐变卡片风 | 社交媒体友好 |
| paradigm | 范式转变对照 | 新旧对比、变革 |
| dashboard | 数据仪表盘 | 多维度指标、评分 |
| timeline | 蛇形时间线 | 步骤、里程碑 |
| architecture | 云架构图 | 技术架构、流程 |

## 支持的图示类型

1. 数据对比图
2. 流程链条图
3. CSS 柱状图
4. 信息卡片阵列
5. 金句卡片
6. 时间线
7. 概念类比

## 依赖

```bash
pip install boto3 playwright
playwright install chromium
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| AWS_REGION | us-east-1 | Bedrock 区域 |
| AWS_PROFILE | (无) | AWS 配置文件 |
| LLM_MODEL_ID | us.anthropic.claude-opus-4-6-v1 | 模型 ID |
| LLM_READ_TIMEOUT | 600 | API 超时秒数 |
