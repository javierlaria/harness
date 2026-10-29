import os
import dotenv

from pathlib import Path
from openai import OpenAIError

from config.config import create_client

dotenv.load_dotenv(Path(__file__).resolve().parent.parent / ".env")

def main() -> None:
    provider = os.getenv("PROVIDER", "openai")
    client, model = create_client(provider)
    print("Provider: ", provider)
    print("Client: ", client)
    print("Model: ", model)

    messages = [{
        "role": "system",
        "content": "You are an assistant. All your replies must contain random low amount of unserious cat purrs and nyas."
    }]

    try:
        print("Trying...")
        while True:
            user_input = input("Prompt:  ")
            if user_input.lower() in ("exit", "close", "quit", "salir"):
                break

            messages.append({"role": "user", "content": user_input})

            response = client.chat.completions.create(
                model = model,
                messages = messages,
                extra_headers={
                    "HTTP-Referer": "http://localhost:3000", 
                    "X-Title": "My Local Test Agent",
                }
            )
            answer = response.choices[0].message.content or ""
            print("Response:  ", answer)

            messages.append({"role": "system", "content": answer})

    except OpenAIError as error:
        print("\nAPI request failed: ", error)
    except (KeyError, ValueError) as error:
        print("Didnt work, error:")
        print(error)

if __name__ == "__main__":
    main()

