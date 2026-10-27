import os
import dotenv

from config import create_client
from pathlib import Path
from openai import OpenAIError

dotenv.load_dotenv(Path(__file__).resolve().parent / ".env")

def main() -> None:
    provider = os.getenv("PROVIDER", "openai")
    client, model = create_client(provider)
    print("Provider: ", provider)
    print("Client: ", client)
    print("Model: ", model)

    try:
        print("Trying...")
        response = client.chat.completions.create(
            model = model,
            messages =[
                {"role": "user", "content": "Hola, prueba de conexión exitosa."}
            ],
            extra_headers={
                "HTTP-Referer": "http://localhost:3000", 
                "X-Title": "My Local Test Agent",
            }
        )
        print("\nResponse:")
        print(response.choices[0].message.content)
    except OpenAIError as error:
        print("\nAPI request failed: ", error)
    except (KeyError, ValueError) as error:
        print("Didnt work, error:")
        print(error)

if __name__ == "__main__":
    main()

