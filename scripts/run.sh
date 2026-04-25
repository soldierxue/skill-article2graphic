#!/usr/bin/env bash
# run.sh — article2graphic 统一入口
#
# 用法:
#   ./scripts/run.sh generate --story path/to/story.md
#   ./scripts/run.sh generate --story path/to/story.md --output-dir my-output
#   ./scripts/run.sh generate --story path/to/story.md --method svg
#   ./scripts/run.sh generate --story path/to/story.md --dry-run
#   ./scripts/run.sh generate --story path/to/story.md --force
#   echo '{"type":"数据对比图",...}' | ./scripts/run.sh generate --from-spec --output-dir output
#   ./scripts/run.sh help

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DEFAULT_OUTPUT="$SKILL_DIR/output"
PY="${PYTHON:-python3}"

cmd="${1:-help}"
shift || true

case "$cmd" in
  generate|gen|g)
    # 如果没有指定 --output-dir，使用默认输出目录
    HAS_OUTPUT_DIR=""
    for arg in "$@"; do
      [ "$arg" = "--output-dir" ] && HAS_OUTPUT_DIR="yes"
    done
    if [ -z "$HAS_OUTPUT_DIR" ]; then
      mkdir -p "$DEFAULT_OUTPUT"
      $PY "$SCRIPT_DIR/gen_illustration.py" --output-dir "$DEFAULT_OUTPUT" "$@"
    else
      $PY "$SCRIPT_DIR/gen_illustration.py" "$@"
    fi
    ;;

  help|*)
    echo "article2graphic — 文章信息图生成引擎"
    echo ""
    echo "用法: ./scripts/run.sh <command> [options]"
    echo ""
    echo "命令:"
    echo "  generate    生成信息图（别名: gen, g）"
    echo "  help        显示帮助"
    echo ""
    echo "选项:"
    echo "  --story <file>       故事/文章 markdown 文件路径"
    echo "  --from-spec          从 stdin 读取 JSON spec"
    echo "  --method <m>         生成方式: html | svg | auto（默认 auto）"
    echo "  --output-dir <dir>   输出目录（默认 output/）"
    echo "  --slug <name>        输出文件名前缀"
    echo "  --dry-run            只生成代码不截图"
    echo "  --force              强制重新生成（忽略缓存）"
    echo ""
    echo "示例:"
    echo "  ./scripts/run.sh generate --story ../gen-stories/stories/S001-xxx.md"
    echo "  ./scripts/run.sh gen --story article.md --method svg --output-dir pics"
    echo "  echo '{\"type\":\"金句卡片\",\"title\":\"...\"}' | ./scripts/run.sh gen --from-spec"
    ;;
esac
