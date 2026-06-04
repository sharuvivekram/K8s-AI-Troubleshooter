"""Deliver an analysis to the console, and optionally Slack and AWS SNS."""
from __future__ import annotations

import json
import requests
from . import config

SEV_ICON = {"low": "·", "medium": "!", "high": "!!", "critical": "🔥"}


def _format(incident: dict, rca: dict) -> str:
    steps = "\n".join(f"  {i}. {s}" for i, s in enumerate(rca["remediation"], 1))
    cmds = "\n".join(f"  $ {c}" for c in rca["kubectl"])
    return (
        f"[{rca['severity'].upper()}] {incident['namespace']}/{incident['pod']} "
        f"— {incident['reason']}\n"
        f"Summary:    {rca['summary']}\n"
        f"Root cause: {rca['root_cause']}\n"
        f"Fix:\n{steps}\n"
        f"Investigate:\n{cmds}"
    )


def notify(incident: dict, rca: dict) -> None:
    text = _format(incident, rca)
    print("\n" + text + "\n" + "-" * 60)

    if config.SLACK_WEBHOOK_URL:
        try:
            requests.post(config.SLACK_WEBHOOK_URL, json={"text": text}, timeout=10)
        except Exception as e:  # noqa: BLE001
            print(f"[slack] failed: {e}")

    if config.SNS_TOPIC_ARN:
        try:
            import boto3
            sns = boto3.client("sns", region_name=config.AWS_REGION)
            sns.publish(
                TopicArn=config.SNS_TOPIC_ARN,
                Subject=f"KubeSage: {incident['pod']} {incident['reason']}"[:99],
                Message=text,
            )
        except Exception as e:  # noqa: BLE001
            print(f"[sns] failed: {e}")
