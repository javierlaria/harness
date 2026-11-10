import os

from openai import OpenAI

def create_client(provider: str, model: str) -> tuple[OpenAI, str]:
    provider = provider.strip().lower()
    match provider:
        case "openrouter": # removed other providers since Im not going to use them
            return (OpenAI(api_key= os.environ["OPENROUTER_API_KEY"], base_url= "https://openrouter.ai/api/v1"), model,)
        case _:
            raise ValueError(f"Wrong provider, not set: ", provider)

def model_selection(provider, _model = None):
    success = False
    while not success:
        try:
            if _model == None:
                model_list = os.getenv("OPENROUTER_MODELS", "").split(",")
                model_list = [model.strip() for model in model_list if model.strip()]
                for i, model in enumerate(model_list):
                    print(f"{i + 1}: {model}")
                model_selection = int(input(f"Select Model (1 - {len(model_list)}): ")) - 1
                if model_list[model_selection]:
                    selected_model = model_list[model_selection]
                    success = True
    
            else:
                for i, model in enumerate(model_list):
                    if model == _model:
                        selected_model = model
                        success = True
                    if i >= len(model_list):
                        print("Config - Model selection: given model parameter not in list")
                        _model = None

        except (ValueError, IndexError):
            print(f"Select a proper model (1 - {len(model_list)})")
    client, model = create_client(provider, selected_model)
    print("Provider: ", provider)
    print("Client: ", client)
    print("Model: ", model)

