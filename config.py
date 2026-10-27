import os

from openai import OpenAI



def create_client(provider: str) -> tuple[OpenAI, str]:
    provider = provider.strip().lower()
    match provider:
        case "openai":
            return (OpenAI(api_key= os.environ["OPENAI_API_KEY"]), os.environ["OPENAI_MODEL"],)
        case "openrouter":
            return (OpenAI(api_key= os.environ["OPENROUTER_API_KEY"], base_url= "https://openrouter.ai/api/v1"), os.environ["OPENROUTER_MODEL"],)
        case "ollama":
            return (OpenAI(base_url= os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"), api_key="ollama"), os.environ["OLLAMA_MODEL"],)
        case _:
            raise ValueError(f"Wrong provider, not set: ", provider)
