import os
import time
import dotenv


from pathlib import Path
from openai import OpenAIError

import config.config as cfg

import src.client as cl
import src.context as ctx
import src.loader as l
import src.evaluation as ev
import src.testing as tst

dotenv.load_dotenv(Path(__file__).resolve().parent.parent / ".env")

def select_item(items: list, label: str, set_selection: int = None) -> dict:
    if not items:
        raise ValueError(f"Main: No {label}/s")
    print("")
    for i, item in enumerate(items):
        print(f"{i+1} : {item.get("name", item.get("test_id"))}")
    if set_selection:
        try:
            selection = set_selection
            if 1 <= selection <= len(items):
                print(f"Set selection: {set_selection}")
                return items[selection - 1]
        except ValueError:
            print(f"Select a correct {label}.")
    while True:
        try:
            selection = input(f"Select {label}: ")
            if selection.lower() in ("exit", "close", "quit", "salir", "q"):
                raise KeyboardInterrupt
            if 1 <= int(selection) <= len(items):
                print(items[int(selection) - 1].get("name", item.get("test_id")))
                return items[int(selection) - 1]
        except ValueError:
            pass
        print(f"Select a correct {label}.")

def chatting(client, model):
    # Im leaving chatting without any evaluations or other stuff, because thats more for testing.
    context = ctx.create_context(_instructions = "You are an assistant to a test chat. Keep all your answers short.")
    print("\nChatting. Type exit to stop")

    while True:
        user_input = input("\nPrompt:  ")

        if user_input.lower() in ("exit", "close", "quit", "salir", "q"):
            raise KeyboardInterrupt
        
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

def testing(client, model, save: bool = False):

    tests = l.list_tests()
    selected_test = select_item(tests, "test")
    test_id = selected_test["test_id"]

    techniques = l.list_techniques(test_id)
    selected_technique = select_item(techniques, "technique")
    technique_id = selected_technique["technique_id"]

    if test_id is None or technique_id is None:
        print("Main: No test_id or technique_id found")
        return

    experiment = l.load_experiment(test_id, technique_id)

    while True:
        try:
            repetitions = int(input("\nNumber of repetitions: "))
            if repetitions >= 1:
                break
        except ValueError:
            pass # dont raise to keep loop
        print("Enter a value >= 1")

    if not save: # just in case
            save_check = save_check = input("\nSave? (yes or no): ").lower().strip()
            match save_check:
                case "yes" | "y" | "1":
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

def debug_testing(client = None, model = "debug", save: bool = False, set_selection: int = 1):
    tests = l.list_tests()
    selected_test = select_item(tests, "test")
    test_id = selected_test["test_id"]

    techniques = l.list_techniques(test_id)
    selected_technique = select_item(techniques, "technique")
    technique_id = selected_technique["technique_id"]

    if test_id is None or technique_id is None:
        print("Main: No test_id or technique_id found")
        return
    
    experiment = l.load_experiment(test_id, technique_id)

    repetitions = 1

    if not save: # just in case
            save_check = input("\nSave? (yes or no): ").lower().strip()
            match save_check:
                case "yes" | "y" | "1":
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
    usage = cfg.get_usage()
    print("")
    print(f"                                                                                 Used:      {usage["used"]}")
    print(f"                                                                                 Limit:     {usage["limit"]}")
    print(f"                                                                                 Remaining: {usage["remaining"]}")

    if usage["remaining"] < 9: # number of prompts in a test
        print(f"                                                                                 Not enough for a test")

    print("\nSelect chat or test mode")
    print("1: Chatting")
    print("2: Testing")
    print("3: Debug offline")
 
    mode = input("Mode: ").strip().lower()
    if mode not in ("1", "2", "3"):
        print("Invalid mode.")
        raise KeyboardInterrupt
    provider = os.getenv("PROVIDER", "openrouter")
    client, model = cfg.model_selection(provider= provider, _model = "debug" if mode == "3" else None)
    try:
        match mode:

            case "1":
                chatting(client, model)

            case "2":
                testing(client, model)

            case "3":
                debug_testing(client, model, set_selection=1)

    except OpenAIError as error:
        print(f"\nMain: API request failed: {error}")
    except (KeyError, ValueError, AttributeError) as error:
        print(f"\nMain: Execution failed: {error}")
    except (KeyboardInterrupt):
        print("\nMain: Quit.")


if __name__ == "__main__":
    main()