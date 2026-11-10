import os
import dotenv

import time

from pathlib import Path
from openai import OpenAIError

from config.config import create_client

dotenv.load_dotenv(Path(__file__).resolve().parent.parent / ".env")

def main() -> None:
    provider = os.getenv("PROVIDER", "openrouter")
    config = True
    chatting = False
    ############################################
    ############# Configuration ################
    ############################################

    # Section to choose the OpenRouter models from the list. Creates the provider
    while config:
        model_list = os.getenv("OPENROUTER_MODELS", "").split(",")
        model_list = [model.strip() for model in model_list if model.strip()]
        for i, model in enumerate(model_list):
            print(f"{i + 1}: {model}")
        try:
            model_selection = int(input(f"Select Model (1 - {len(model_list)}): ")) - 1
            if model_list[model_selection]:
                selected_model = model_list[model_selection]
                chatting = True
                config = False
        except (ValueError, IndexError):
            print(f"Select a proper model (1 - {len(model_list)})")
    client, model = create_client(provider, selected_model)
    print("Provider: ", provider)
    print("Client: ", client)
    print("Model: ", model)

    messages = []

    try:
        ############  Chatting loop ##############
        # The loop starts after the setup: the model and test are chosen.
        while chatting:
            print("Connecting...")
            user_input = input("Prompt:  ")
            if user_input.lower() in ("exit", "close", "quit", "salir"):
                break

            messages.append({"role": "user", "content": user_input})
            start_time = time.perf_counter()
            response = client.responses.create(   # responses is the recommended api, and the newest.
                    model = model,
                    input = messages,
                    stream = True, # fractured response
                )

            complete_answer = ""
            end_message = None
            response_id = None

            for event in response:
                match event.type:
                    case "response.created":
                        first_response_time = time.perf_counter()
                        response_id = event.response.id
                        print(f"Response started: {response_id}\n")
                    case "response.output_text.delta":
                        first_token_time = time.perf_counter()
                        complete_answer += event.delta
                        print(event.delta, end="", flush= True)
                    case "response.completed":
                        end_message = event.response
                        print("\n\nResponse complete.\n")
                    case "response.failed":
                        print("Response failed: ", event.response.error)
                    case "error":
                        print("Stream error: ", event.message)
                # event types for each thing, probably unnecessary:
                # created, in_progress, output_item.added (new output generated), content_part.added (content part started),
                # output_text.delta (new text from response), output_text.done (response finished),
                # output_item.done (output finished), completed (done)
                
                # They are parts of the lifecycle of the response
            
            end_time = time.perf_counter()

            messages.append({"role": "system", "content": complete_answer})
            
            if end_message:
                print("Model: ", end_message.model)
                print("--  Usage  --")
                print("Total tokens:           ", end_message.usage.total_tokens)
                print(" - Input tokens:        ", end_message.usage.input_tokens)
                print(" - - Cached tokens:     ", end_message.usage.input_tokens_details.cached_tokens)
                print(" - Output tokens:       ", end_message.usage.output_tokens)
                print(" - - Reasoning tokens:  ", end_message.usage.output_tokens_details.reasoning_tokens)
                print("\nStatus: ", end_message.status)
                print(f"--  Duration  --")
                print("Response confirmation:  ", first_response_time - start_time)
                print("First token received:   ", first_token_time - start_time)
                print("Total duration          ", end_time - start_time)
    except OpenAIError as error:
        print("\n-- API request failed: ", error)
    except (KeyError, ValueError, AttributeError) as error:
        print("Didnt work, error:")
        print(error)


if __name__ == "__main__":
    main()

