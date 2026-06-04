"""Send collected diagnostics to Claude and get a structured root-cause analysis.

Supports two interchangeable backends, selected by config.AI_PROVIDER:
  - "anthropic": the Anthropic API via the `anthropic` SDK.
  - "bedrock":   Amazon Bedrock via boto3's Converse API (AWS-native).
The prompt and parsing are identical; only the transport differs.
"""
from __future__ import annotations

import json
from . import config

SYSTEM = """You are a senior Site Reliability Engineer triaging a Kubernetes pod failure.
You are given a pod's status, recent events, and log tail. Reply with ONLY a JSON
object (no prose, no markdown fences) with these keys:
  "summary":      one sentence describing what is wrong,
  "root_cause":   the most likely underlying cause,
  "severity":     one of "low", "medium", "high", "critical",
  "remediation":  array of 2-4 concrete steps to fix it,
  "kubectl":      array of kubectl commands an engineer could run to investigate.
Base your answer on the evidence; if logs are missing, say so in the summary."""


def _prompt(incident: dict) -> str:
    events = "\n".join(incident.get("events", [])) or "(none)"
    logs = (incident.get("logs") or "(none)")[-4000:]
    return (
        f"Pod: {incident['namespace']}/{incident['pod']}\n"
        f"Reason: {incident['reason']}   Phase: {incident.get('phase')}   "
        f"Restarts: {incident.get('restart_count')}\n\n"
        f"EVENTS:\n{events}\n\nLOG TAIL:\n{logs}"
    )


def analyze(incident: dict) -> dict:
    raw = _bedrock(incident) if config.AI_PROVIDER == "bedrock" else _anthropic(incident)
    return _parse(raw)


def _anthropic(incident: dict) -> str:
    from anthropic import Anthropic
    client = Anthropic()  # reads ANTHROPIC_API_KEY from env
    resp = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=700,
        system=SYSTEM,
        messages=[{"role": "user", "content": _prompt(incident)}],
    )
    return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")


def _bedrock(incident: dict) -> str:
    import boto3
    client = boto3.client("bedrock-runtime", region_name=config.AWS_REGION)
    resp = client.converse(
        modelId=config.BEDROCK_MODEL_ID,
        system=[{"text": SYSTEM}],
        messages=[{"role": "user", "content": [{"text": _prompt(incident)}]}],
        inferenceConfig={"maxTokens": 700},
    )
    return resp["output"]["message"]["content"][0]["text"]


def _parse(raw: str) -> dict:
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        s, e = raw.find("{"), raw.rfind("}")
        data = json.loads(raw[s:e + 1]) if s != -1 and e != -1 else {}
    data.setdefault("summary", "Analysis unavailable.")
    data.setdefault("root_cause", "unknown")
    data.setdefault("severity", "medium")
    data.setdefault("remediation", [])
    data.setdefault("kubectl", [])
    return data
