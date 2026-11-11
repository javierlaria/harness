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

def select_item(items: list, label: str) -> dict:
    if not items:
        raise ValueError(f"Main: No {label}/s")

    for i, item in enumerate(items):
        print(f"{i+1} : {item.get("name", item.get("test_id"))}")

    while True:
        try:
            selection = int(input(f"Select {label}: "))

            if 1 <= selection <= len(items):
                return items[selection - 1]
        except ValueError:
            pass
        print(f"Select a correct {label}.")

def chatting(client, model, save: bool = False):
    # Im leaving chatting without any evaluations or other stuff, because thats more for testing.
    context = ctx.create_context(_instructions = "You are an assistant to a test chat. Keep all your answers short.")
    print("\nChatting. Type exit to stop")

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
        print(f"                                                               Total tokens:    {response.usage.total_tokens}")
        print(f"                                                               Total duration:  {times["total"]:.6f}")

    if not save: # just in case
        match input("\nSave? (yes or no): ").lower().strip():
            case "yes", "y", "1":
                save = True
            case _:
                save = False
    if save:
        save_name = str(input("\nChat filename (name.json): "))
        context.save_to("/".join(os.getenv("CONTEXTS_FILEPATH"), save_name + ".json"))

def testing(client, model, save: bool = False):
    tests = pr.list_tests()
    selected_test = select_item(tests, "test")
    test_id = selected_test["test_id"]

    techniques = pr.list_techniques(test_id)
    selected_technique = select_item(techniques, "technique")
    technique_id = selected_technique["technique_id"]

    experiment = pr.load_experiment(test_id, technique_id)

    while True:
        try:
            repetitions = int(input("\nNumber of repetitions: "))
            if repetitions >= 1:
                break
        except ValueError:
            pass # dont raise to keep loop
        print("Enter a value >= 1")

    if not save: # just in case
            match input("\nSave? (yes or no): ").lower().strip():
                case "yes", "y", "1":
                    save = True
                case _:
                    save = False

    result = tst.run_test(
        complete_test=experiment,
        client=client,
        model=model,
        repetitions=repetitions,
        save=save
    )
    print("Run ID: ", result["run_id"])
    print("Summary: ", result["summary"])


def main(): 
    print("\nSelect chat or test mode")
    print("1: Chatting")
    print("2: Testing")
 
    mode = input("Mode: ").strip().lower()
    if mode not in ("1", "2"):
        print("Invalid mode.")
        return
    provider = os.getenv("PROVIDER", "openrouter")
    client, model = cfg.model_selection(provider= provider)
    try:
        match mode:

            case "1":
                chatting(client, model)

            case "2":
                testing(client, model)

    except OpenAIError as error:
        print("\nMain: -- API request failed: ", {error})
    except (KeyError, ValueError, AttributeError) as error:
        print("\nMain: Execution failed:", {error})


if __name__ == "__main__":
    main()