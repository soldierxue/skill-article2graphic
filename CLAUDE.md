# article2graphic

当用户要求生成信息图、配图、infographic 时，请按照 `SKILL.md` 中定义的流程执行。

核心流程：
1. 用 `python3 scripts/extract_spec.py <文件>` 提取 spec
2. 如果 spec 为默认（1 张），按文章章节数规划完整分镜（读取 SKILL.md 中的规则）
3. 读取 `prompts/design-system-html.md` 作为设计规范
4. 逐页生成 HTML 写入 `output/` 目录
5. 用 `python3 scripts/screenshot.py --html-dir output/ --inject-qrcode` 截图
6. 读取 `prompts/promo-writer.md`，生成推广短文写入 `output/{slug}-promo.md`

详细规则见 `SKILL.md`。
