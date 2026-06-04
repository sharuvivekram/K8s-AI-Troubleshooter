"""Central configuration, read from environment variables."""
import os


def _bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).lower() in ("1", "true", "yes")


# Which AI backend to use: "anthropic" (direct API) or "bedrock" (AWS-native).
AI_PROVIDER = os.getenv("AI_PROVIDER", "anthropic").lower()

# Anthropic direct API
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")

# AWS Bedrock. The exact model ID varies by region and changes over time —
# copy the current one from the Bedrock console (Model access page).
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-haiku-4-5-v1:0")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# What to watch
NAMESPACES = [n.strip() for n in os.getenv("WATCH_NAMESPACES", "default").split(",") if n.strip()]
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "30"))
LOG_TAIL_LINES = int(os.getenv("LOG_TAIL_LINES", "60"))

# Notifications (all optional; console output is always on)
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", "")

# When True, run one pass and exit (good for CronJob / local testing).
RUN_ONCE = _bool("RUN_ONCE")

# Prometheus metrics endpoint (served only in continuous mode).
METRICS_PORT = int(os.getenv("METRICS_PORT", "8000"))
