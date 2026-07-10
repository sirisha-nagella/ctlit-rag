
import random

MODELS = {
    "nova_micro": "amazon.nova-micro-v1:0",
    "haiku": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
}
    

def pick_model():
    model_key = random.choice(list(MODELS.keys()))
    return model_key, MODELS[model_key]

