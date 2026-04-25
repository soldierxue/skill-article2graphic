#!/usr/bin/env python3
"""
llm_client.py — article2graphic 本地副本。
增加 read_timeout=300s 避免大 prompt 超时。

环境变量:
  AWS_REGION (默认 us-east-1)
  AWS_PROFILE (可选)
  LLM_MODEL_ID (默认 us.anthropic.claude-opus-4-6-v1)
  LLM_MAX_TOKENS (默认 4096)
  LLM_READ_TIMEOUT (默认 600)
"""
from __future__ import annotations

import json
import os
import sys

try:
    import boto3
    from botocore.config import Config
except ImportError:
    print("错误: 请安装 boto3 — pip install boto3", file=sys.stderr)
    sys.exit(1)

DEFAULT_REGION = os.environ.get("AWS_REGION", "us-east-1")
DEFAULT_MODEL = os.environ.get("LLM_MODEL_ID", "us.anthropic.claude-opus-4-6-v1")
DEFAULT_MAX_TOKENS = int(os.environ.get("LLM_MAX_TOKENS", "4096"))
DEFAULT_READ_TIMEOUT = int(os.environ.get("LLM_READ_TIMEOUT", "600"))


def get_client():
    """创建 Bedrock Runtime 客户端（带 read timeout）。"""
    cfg = Config(read_timeout=DEFAULT_READ_TIMEOUT, retries={"max_attempts": 2})
    kwargs = {"region_name": DEFAULT_REGION, "config": cfg}
    profile = os.environ.get("AWS_PROFILE")
    if profile:
        session = boto3.Session(profile_name=profile)
        return session.client("bedrock-runtime", **kwargs)
    return boto3.client("bedrock-runtime", **kwargs)


def invoke(prompt, system="", max_tokens=DEFAULT_MAX_TOKENS, temperature=0.3):
    """调用 Bedrock Claude，返回文本。"""
    client = get_client()
    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
    }
    if system:
        body["system"] = [{"type": "text", "text": system}]
    response = client.invoke_model(
        modelId=DEFAULT_MODEL,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body),
    )
    result = json.loads(response["body"].read())
    content = result.get("content", [])
    return "\n".join(b["text"] for b in content if b.get("type") == "text")


if __name__ == "__main__":
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "返回: ok"
    print(f"Model: {DEFAULT_MODEL}", file=sys.stderr)
    print(f"Region: {DEFAULT_REGION}", file=sys.stderr)
    print(f"Timeout: {DEFAULT_READ_TIMEOUT}s", file=sys.stderr)
    print(invoke(prompt))
