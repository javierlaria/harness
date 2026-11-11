import os
import time
import dotenv


from pathlib import Path
from openai import OpenAIError

import config.config as cfg

import src.client as cl
import src.context as ctx
import src.prompts as pr
import src.evaluation as ev
import src.testing as tst

dotenv.load_dotenv(Path(__file__).resolve().parent.parent / ".env")

def select_items(items: list, label: str) -> dict:
    if not items:
        raise ValueError("Main: No ", label)

    for i, item in enumerate(items):
        print(f"{i+1} : {item.get("name", item.get("test_id"))}")

    while True:
        try:
            selection = int(input(f"Select {label}: "))

            if 1 <= selection <= len(items):
                return items[selection - 1]
        except ValueError:
            pass
        print("Select a correct label.")

def chatting(client, model, save: bool = False):
    # Im leaving chatting without any evaluations or other stuff, because thats more for testing.
    context = ctx.create_context(_instructions = "You are an assistant to an experiment. Keep all your answers short.")
    print("Chatting. Type exit to stop")

    while True:
        user_input = input("\nPrompt:  ")

        if user_input.lower() in ("exit", "close", "quit", "salir", "q"):
            break
        
        complete_answer, response, times = cl.handle_request(
            user_input = user_input,
            context= context,
            client= client,
            model= model,
            print_answer= True
        )

        print("\n")
        print(f"                                                             Total tokens:   {response.usage.total_tokens}")
        print(f"                                                             Total duration: {times["total"]}")
    if save:
        save_name = input("\nChat filename (name.json): ")
        context.save_to(str(os.getenv("CONTEXTS_FILEPATH"))+str(save_name)+".json")

def testing(client, model, save: bool = False):
    # Actual test and evaluation

    test = pr.load_prompts(os.getenv("PROMPTS_FILEPATH"))

    test_id = test["test_id"]

    context = ctx.Context.load_from(str(os.getenv("CONTEXTS_FILEPATH"))+str(test_id)+".json")

    results = []

    for prompt in test["prompts"]:
        print(f"Testing: {prompt["id"]}")

        complete_answer, response, times = cl.handle_request(
            user_input = prompt["input"],
            context= context,
            client= client,
            model= model,
            print_answer= False
        )

        evaluation = ev.evaluate_response(prompt, complete_answer)

        evaluation["times"] = times
        evaluation["usage"] = {
            "total" : {
                "" : response.usage.total_tokens,
                "input_output" : {
                    "input": {
                        "" : response.usage.input_tokens,
                        "cached" : response.usage.input_tokens_details.cached_tokens
                        },
                    "output" : {
                        "" : response.usage.output_tokens,
                        "reasoning" : response.usage.output_tokens_details.reasoning_tokens
                        }
                    }
                }
            }
        
        results.append(evaluation)

    if save:
        context.save_to(str(os.getenv("RESULTS_FILEPATH"))+"run_test_"+str(test_id)+".json")

    summary = ev.summarize_results(results)

    print("\nResults: ")
    print(summary)


def main(): 
    provider = os.getenv("PROVIDER", "openrouter")

    client, model = cfg.model_selection(provider= provider)
    
    while True:
        try:
            print("\nSelect chat or test mode")
            print("1: Chatting")
            print("2: Testing")
            print("3: Return")

            mode = input("Mode: ").strip().lower()
            save_data = input("Save data? (yes, no): ").strip().lower()

            match save_data:
                case "yes":
                    save = True
                case _:
                    save = False

            match mode:
                case "1":
                    chatting(client, model, save)
                case "2":
                    testing(client, model, save)
                case "3", "quit", "exit", "salir", "q", "close":
                    print("\nQuit")
                    break
                case _:
                    print("Invalid mode.")

        except OpenAIError as error:
            print("\nMain: -- API request failed: ", {error})
        except (KeyError, ValueError, AttributeError) as error:
            print("\nMain: Didnt work, error:", {error})


if __name__ == "__main__":
    main()