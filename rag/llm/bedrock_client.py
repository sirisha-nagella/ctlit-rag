import boto3
import time

from botocore.exceptions import ClientError

REGION = "us-east-1"
THROTTLE_ERRORS = {"ThrottlingException", "ServiceUnavailableException", "ModelTimeoutException"}

_client = boto3.client("bedrock-runtime", region_name=REGION)

def invoke(model_id, system, messages):
    converse_messages = [
        {"role": m["role"], "content": [{"text": m["content"]}]}
        for m in messages
    ]

    def _call():
        return _client.converse(
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
        
    return response["output"]["message"]["content"][0]["text"].strip(), response["usage"]["inputTokens"], response["usage"]["outputTokens"]



