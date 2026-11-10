import os
from openai import OpenAI


def create_client(provider: str, model: str) -> tuple[OpenAI, str]:
    provider = provider.strip().lower()
    match provider:
        case "openrouter": # removed other providers since Im not going to use them
            return (OpenAI(api_key= os.environ["OPENROUTER_API_KEY"], base_url= os.environ["OPENROUTER_BASE_URL"]), model,)
        case _:
            raise ValueError(f"Wrong provider, not set: ", provider)