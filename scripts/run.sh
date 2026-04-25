#!/usr/bin/env bash
# run.sh — article2graphic 统一入口（agent 模式）
#
# 通过 kiro-cli / claude code / openclaw 等 agent 生成信息图，
# 不需要额外配置大语言模型。
#
# 用法:
#   ./scripts/run.sh generate --story path/to/story.md
#   ./scripts/run.sh generate --story path/to/story.md --output-dir my-output
#   ./scripts/run.sh generate --story path/to/story.md --method svg
#   ./scripts/run.sh generate --story path/to/story.md --dry-run
#   ./scripts/run.sh screenshot output/           # 批量截图已有 HTML
#   ./scripts/run.sh help

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DEFAULT_OUTPUT="$SKILL_DIR/output"
PY="${PYTHON:-python3}"

# ─── Agent 检测 ───
detect_agent() {
  if command -v kiro-cli &>/dev/null; then
    echo "kiro-cli"
  elif command -v claude &>/dev/null; then
    echo "claude"
  else
    echo "none"
  fi
}

# ─── 构建 agent prompt ───
build_prompt() {
  local spec_json="$1"
  local output_dir="$2"
  local method="${3:-html}"
  local page_num="${4:-1}"
  local slug="${5:-illustration}"
  local design_prompt_file

  if [ "$method" = "svg" ]; then
    design_prompt_file="$SKILL_DIR/prompts/design-system-svg.md"
  else
    design_prompt_file="$SKILL_DIR/prompts/design-system-html.md"
  fi

  local output_file="$output_dir/${slug}-P${page_num}"

  if [ "$method" = "svg" ]; then
    cat <<PROMPT
请按照以下设计规范生成一张 SVG 信息图。

## 设计规范
$(cat "$design_prompt_file")

## 图示规格
$spec_json

## 输出要求
1. 生成完整的 SVG 代码
2. 将 SVG 代码写入文件: ${output_file}.svg
3. 只写 SVG 代码到文件，不要包含任何解释文字、markdown 标记
PROMPT
  else
    cat <<PROMPT
请按照以下设计规范生成一张 HTML 信息图。

## 设计规范
$(cat "$design_prompt_file")

## 图示规格
$spec_json

## 输出要求
1. 生成完整的 HTML+CSS 代码（包含 <html><head><body>）
2. 将 HTML 代码写入文件: ${output_file}.html
3. 只写 HTML 代码到文件，不要包含任何解释文字、markdown 标记
4. 根容器 div 必须有 style="width:900px; margin:0 auto; padding:48px; box-sizing:border-box;"
PROMPT
  fi
}

# ─── 通过 agent 生成单页 ───
generate_page_via_agent() {
  local agent="$1"
  local prompt="$2"

  case "$agent" in
    kiro-cli)
      echo "$prompt" | kiro-cli chat --no-interactive --trust-all-tools
      ;;
    claude)
      claude -p "$prompt" --allowedTools "Write,Edit"
      ;;
    *)
      echo "❌ 未找到可用的 agent (kiro-cli / claude)" >&2
      echo "   请安装 kiro-cli 或 claude code" >&2
      exit 1
      ;;
  esac
}

cmd="${1:-help}"
shift || true

case "$cmd" in
  generate|gen|g)
    # 解析参数
    STORY="" FROM_SPEC="" METHOD="auto" OUTPUT_DIR="" SLUG="" DRY_RUN="" FORCE=""
    while [ $# -gt 0 ]; do
      case "$1" in
        --story) STORY="$2"; shift 2 ;;
        --from-spec) FROM_SPEC="yes"; shift ;;
        --method) METHOD="$2"; shift 2 ;;
        --output-dir) OUTPUT_DIR="$2"; shift 2 ;;
        --slug) SLUG="$2"; shift 2 ;;
        --dry-run) DRY_RUN="yes"; shift ;;
        --force) FORCE="yes"; shift ;;
        *) echo "未知参数: $1" >&2; exit 1 ;;
      esac
    done

    OUTPUT_DIR="${OUTPUT_DIR:-$DEFAULT_OUTPUT}"
    mkdir -p "$OUTPUT_DIR"

    # 提取 spec
    if [ -n "$FROM_SPEC" ]; then
      SPEC_JSON=$(cat)
      SLUG="${SLUG:-illustration}"
    elif [ -n "$STORY" ]; then
      if [ ! -f "$STORY" ]; then
        echo "❌ 文件不存在: $STORY" >&2
        exit 1
      fi
      SPEC_JSON=$($PY "$SCRIPT_DIR/extract_spec.py" "$STORY")
      SLUG="${SLUG:-$(basename "$STORY" .md)}"
    else
      echo "用法: ./scripts/run.sh generate --story <file> [options]" >&2
      exit 1
    fi

    # 解析 specs 数组（兼容 specs / pages 两种字段名）
    TOTAL_PAGES=$($PY -c "import json,sys; d=json.loads(sys.stdin.read()); specs=d.get('specs',d.get('pages',d if isinstance(d,list) else [d])); print(len(specs))" <<< "$SPEC_JSON")
    TITLE=$($PY -c "import json,sys; d=json.loads(sys.stdin.read()); print(d.get('context',d.get('story_context',{})).get('title',''))" <<< "$SPEC_JSON" 2>/dev/null || echo "")

    echo "🎨 生成信息图: ${TITLE:-$SLUG} (${TOTAL_PAGES} 张分镜)" >&2

    AGENT=$(detect_agent)
    echo "🤖 使用 agent: $AGENT" >&2

    # 逐页生成
    for i in $(seq 0 $((TOTAL_PAGES - 1))); do
      PAGE_NUM=$((i + 1))
      # 提取单页 spec（含 context 信息）
      PAGE_SPEC=$($PY -c "
import json, sys
d = json.loads(sys.stdin.read())
specs = d.get('specs', d.get('pages', d if isinstance(d, list) else [d]))
ctx = d.get('context', d.get('story_context', {}))
spec = specs[$i]
spec['story_context'] = ctx
print(json.dumps(spec, ensure_ascii=False, indent=2))
" <<< "$SPEC_JSON")

      PAGE_METHOD="$METHOD"
      if [ "$PAGE_METHOD" = "auto" ]; then
        GM=$($PY -c "import json,sys; print(json.loads(sys.stdin.read()).get('generation_method','html_screenshot'))" <<< "$PAGE_SPEC" 2>/dev/null || echo "html_screenshot")
        [ "$GM" = "svg" ] && PAGE_METHOD="svg" || PAGE_METHOD="html"
      fi

      PAGE_TITLE=$($PY -c "import json,sys; print(json.loads(sys.stdin.read()).get('title','?'))" <<< "$PAGE_SPEC" 2>/dev/null || echo "?")
      PAGE_TYPE=$($PY -c "import json,sys; print(json.loads(sys.stdin.read()).get('type','?'))" <<< "$PAGE_SPEC" 2>/dev/null || echo "?")

      echo "" >&2
      echo "  📄 P${PAGE_NUM}: ${PAGE_TITLE} [${PAGE_TYPE}] (${PAGE_METHOD})" >&2

      PROMPT=$(build_prompt "$PAGE_SPEC" "$OUTPUT_DIR" "$PAGE_METHOD" "$PAGE_NUM" "$SLUG")

      if [ -z "$DRY_RUN" ]; then
        generate_page_via_agent "$AGENT" "$PROMPT"
      else
        echo "    [dry-run] prompt 已生成，跳过 agent 调用" >&2
        echo "$PROMPT" > "$OUTPUT_DIR/${SLUG}-P${PAGE_NUM}.prompt.txt"
      fi
    done

    # 截图（如果是 HTML 模式且非 dry-run）
    if [ -z "$DRY_RUN" ]; then
      echo "" >&2
      echo "📸 截图..." >&2
      $PY "$SCRIPT_DIR/screenshot.py" --html-dir "$OUTPUT_DIR" --inject-qrcode
    fi

    echo "" >&2
    echo "✅ 完成: ${TOTAL_PAGES} 张信息图 → $OUTPUT_DIR" >&2
    ;;

  screenshot|ss)
    DIR="${1:-$DEFAULT_OUTPUT}"
    shift || true
    INJECT_QR=""
    for arg in "$@"; do
      [ "$arg" = "--inject-qrcode" ] && INJECT_QR="--inject-qrcode"
    done
    echo "📸 批量截图: $DIR" >&2
    $PY "$SCRIPT_DIR/screenshot.py" --html-dir "$DIR" $INJECT_QR
    ;;

  help|*)
    echo "article2graphic — 文章信息图生成引擎（agent 模式）"
    echo ""
    echo "通过 kiro-cli / claude code 等 agent 生成信息图，"
    echo "不需要额外配置大语言模型。"
    echo ""
    echo "用法: ./scripts/run.sh <command> [options]"
    echo ""
    echo "命令:"
    echo "  generate    生成信息图（别名: gen, g）"
    echo "  screenshot  批量截图 HTML → PNG（别名: ss）"
    echo "  help        显示帮助"
    echo ""
    echo "generate 选项:"
    echo "  --story <file>       Markdown 文件路径"
    echo "  --from-spec          从 stdin 读取 JSON spec"
    echo "  --method <m>         生成方式: html | svg | auto（默认 auto）"
    echo "  --output-dir <dir>   输出目录（默认 output/）"
    echo "  --slug <name>        输出文件名前缀"
    echo "  --dry-run            只生成 prompt 不调用 agent"
    echo "  --force              强制重新生成"
    echo ""
    echo "screenshot 选项:"
    echo "  <dir>                HTML 文件所在目录"
    echo "  --inject-qrcode      注入公众号二维码"
    echo ""
    echo "支持的 agent（自动检测）:"
    echo "  - kiro-cli (优先)"
    echo "  - claude code"
    echo ""
    echo "示例:"
    echo "  ./scripts/run.sh gen --story article.md"
    echo "  ./scripts/run.sh gen --story article.md --method svg"
    echo "  ./scripts/run.sh gen --story article.md --dry-run"
    echo "  ./scripts/run.sh ss output/ --inject-qrcode"
    ;;
esac
