import os
import dotenv

from pathlib import Path
from openai import OpenAIError

from config.config import create_client

dotenv.load_dotenv(Path(__file__).resolve().parent.parent / ".env")

def main() -> None:
    provider = os.getenv("PROVIDER", "openrouter")
    config = True
    chatting = False
    while config:
        model_list = os.getenv("OPENROUTER_MODELS")
        for i, model in enumerate(model_list):
            print(f"{i + 1}: {model}")
        model_selection = input(f"Select Model (1 - {len(model_list) + 1}): ")
        if model_list[model_selection]:
            chatting = True
            config = False
            selected_model = model_list[model_selection]
        else:
            print(f"Select a proper model (1 - {len(model_list) + 1})")
    client, model = create_client(provider, selected_model)
    print("Provider: ", provider)
    print("Client: ", client)
    print("Model: ", model)

    messages = [{
        "role": "system",
        "content": "You are an assistant."
    }]
    
    try:
        while chatting:
            print("Connecting...")
            user_input = input("Prompt:  ")
            if user_input.lower() in ("exit", "close", "quit", "salir"):
                break

            messages.append({"role": "user", "content": user_input})
            response = client.responses.create(   
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
                        response_id = event.response.id
                        print(f"Response started: {response_id}")
                    case "response.output_text.delta":
                        complete_answer += event.delta
                        print(event.delta, end="", flush= True)
                    case "response.completed":
                        end_message = event.response
                        print("Response complete.")
                    case "response.failed":
                        print("Response failed: ", event.response.error)
                    case "error":
                        print("Stream error: ", event.message)
                # event types for each thing, probably unnecessary:
                # created, in_progress, output_item.added (new output generated), content_part.added (content part started),
                # output_text.delta (new text from response), output_text.done (response finished),
                # output_item.done (output finished), completed (done)
                
                # They are parts of the lifecycle of the response
            messages.append({"role": "system", "content": complete_answer})
            
            if end_message:
                print(" --- ")
                print("Model: ", end_message.model)
                print("Usage: ", end_message.usage)
                print("Status: ", end_message.status)

    except OpenAIError as error:
        print("\n-- API request failed: ", error)
    except (KeyError, ValueError) as error:
        print("Didnt work, error:")
        print(error)

if __name__ == "__main__":
    main()

