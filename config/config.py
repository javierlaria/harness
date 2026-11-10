import os
import src.client as client

##### Things to put here
# Api configuration (OpernRouter, base url)
# model selection (default settings, temperature, sampling parameters, token limits)
# experiment execution defaults
# reproducibility settings (seed, deterministic execution settings)
# Experiment ID? 
# Prompt selection, repetitions, etc.

# Just connect things here, the setup of the experiment and everything.

##################### deterministic ###################
# model: fixed mode version
# temperature: set to 0, though it does not guarantee deterministic, openrouter requests providers and implementations can differ.
# top-p: keep fixed
# seed : fixed, same as temperature
# dataset: fixed, versioned
# prompt: version and hash
# context: identical
# evaluation: preferably rule-based instead of llm judge
# repetitions: fixed number of repetitions

# there is a difference between deterministic evaluation and deterministic generation -> evaluation can be achieved via scoring

def model_selection(provider, _model= None):
    model_list = [model.strip() for model in os.getenv("OPENROUTER_MODELS", "").split(",") if model.strip()]

    if not model_list:
        raise ValueError(f"Config: No models in list for provider {provider})")

    if _model is not None:
        if _model not in model_list:
            raise ValueError(f"Config: Model not in configuration : {_model}")
        selected_model = _model

    else:
        for i, model in enumerate(model_list):
            print(f"{i+1}: {model}")

        while True:
            try:
                user_input = int(input(f"Select model (1 - {len(model_list)}): "))
                selected_model = model_list[user_input - 1]
                break

            except (ValueError, IndexError):
                print(f"Config: Index out of range (1 - {len(model_list)})")

    api_client = client.create_client(provider)

    print("Provider: ", provider)
    print("Client: ", api_client)
    print("Model: ", selected_model)

    return api_client, selected_model


