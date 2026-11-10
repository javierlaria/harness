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

def model_selection(provider, _model: str = None):
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
                    elif i >= len(model_list):
                        print("Config - Model selection: given model parameter not in list")
                        _model = None

        except (ValueError, IndexError):
            print(f"Select a proper model (1 - {len(model_list)})")
            
    client, model = client.create_client(provider, selected_model)
    print("Provider: ", provider)
    print("Client: ", client)
    print("Model: ", model)
    return client, model, True

