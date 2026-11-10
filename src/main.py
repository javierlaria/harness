import os
import time
import dotenv


from pathlib import Path
from openai import OpenAIError

import config.config as cc
import src.client as cl

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

    ############# Configuration ################

    client, model = cc.model_selection(provider= provider)

    messages = []

    evaluating_time = True
    evaluating_tokens = True

    chatting = True 

    try:
        ############  Chatting loop ##############
        while chatting:
            user_input = input("\nPrompt:  ")

            if user_input.lower() in ("exit", "close", "quit", "salir"):
                chatting = False
                print("\nChat exit.")
                break

            complete_answer, response, times = cl.handle_request(
                user_input = user_input,
                current_context= messages,
                client= client,
                model= model
            )
            if evaluating_tokens:
                print("--  Usage  --")
                print("Total tokens:           ", response.usage.total_tokens)
                print(" - Input tokens:        ", response.usage.input_tokens)
                print(" - - Cached tokens:     ", response.usage.input_tokens_details.cached_tokens)
                print(" - Output tokens:       ", response.usage.output_tokens)
                print(" - - Reasoning tokens:  ", response.usage.output_tokens_details.reasoning_tokens)
            print("\nStatus: ", response.status)

            if evaluating_time:
                print(f"--  Duration  --")
                print("Response confirmation:  ", times["confirmation"])
                print("First token received:   ", times["first_token"])
                print("Total duration          ", times["total"])

    except OpenAIError as error:
        print("\n-- API request failed: ", error)
    except (KeyError, ValueError, AttributeError) as error:
        print("Didnt work, error:")
        print(error)


if __name__ == "__main__":
    main()

