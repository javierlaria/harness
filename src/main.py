import os
import dotenv

import time

from pathlib import Path
from openai import OpenAIError

import config.config as cc

dotenv.load_dotenv(Path(__file__).resolve().parent.parent / ".env")

###### Application entry point
#    ORDER OF THINGS

# load configuration
# load dataset (if any, probably wont have any)
# dependencies (already at the top)
# MAIN CHAT LOOP
# send model request
# collect response
# evaluate
# store results
# rechat?

# do not implement here, just connect

def main() -> None:
    provider = os.getenv("PROVIDER", "openrouter")
    chatting = False
    ############################################
    ############# Configuration ################
    ############################################

    # Section to choose the OpenRouter models from the list. Creates the provider
    client, model, success = cc.model_selection(provider= provider)

    messages = []

    try:
        ############  Chatting loop ##############
        # The loop starts after the setup: the model and test are chosen.
        while chatting:
            print("Connecting...")
            user_input = input("Prompt:  ")
            if user_input.lower() in ("exit", "close", "quit", "salir"):
                chatting = False
                print("\nLoop stopped, this still runs")
                if not chatting:
                    print("\nThis as well")
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

