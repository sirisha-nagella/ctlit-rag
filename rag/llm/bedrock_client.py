import time

import boto3
from botocore.exceptions import BotoCoreError, ClientError

REGION = "us-east-1"
THROTTLE_ERRORS = {"ThrottlingException", "ServiceUnavailableException", "ModelTimeoutException"}

_client = None


def _get_client():
    # Built lazily (not at import time) so importing this module - which
    # rag/generator.py does unconditionally - doesn't require AWS config
    # when LLM_BACKEND=ollama.
    global _client
    if _client is None:
        _client = boto3.client("bedrock-runtime", region_name=REGION)
    return _client


def invoke(model_id, system, messages):
    converse_messages = [
        {"role": m["role"], "content": [{"text": m["content"]}]}
        for m in messages
    ]

    def _call():
        return _get_client().converse(
            modelId=model_id,
            system=[{"text": system}],
            messages=converse_messages,
            inferenceConfig={"temperature": 0.2},
        )

    try:
        response = _call()
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code in THROTTLE_ERRORS:
            time.sleep(2)
            response = _call()
        else:
            raise
    except BotoCoreError:
        # client-side failure (e.g. read/connect timeout) - one retry,
        # same as the throttling case above
        time.sleep(2)
        response = _call()

    return (
        response["output"]["message"]["content"][0]["text"].strip(),
        response["usage"]["inputTokens"],
        response["usage"]["outputTokens"],
    )
