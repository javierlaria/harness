import os
import time
from openai import OpenAI

import src.context as ctx

def create_client(provider: str) -> OpenAI:
    provider = provider.strip().lower()
    match provider:

        case "openrouter": # removed other providers since Im not going to use them
            return OpenAI(api_key= os.environ["OPENROUTER_API_KEY"], base_url= os.environ["OPENROUTER_BASE_URL"])
        
        case _:
            raise ValueError(f"Client: Wrong provider, not set: ", provider)


def handle_request(user_input: str, context: ctx.Context, client: OpenAI | None, model: str, print_answer: bool = True):
    context.add_message("user", user_input)

    start_time = time.perf_counter()
    
    first_response_time = None
    first_token_time = None


    complete_answer = ""
    end_message = None

    if print_answer:
        print("\n")

    if model == "debug":
        first_response_time = time.perf_counter()
        complete_answer = f"DEBUGGING, doesnt count: {user_input}"
        first_token_time = time.perf_counter()

        if print_answer:
            print("\n")
            print(complete_answer, end="", flush=True)

        end_time = time.perf_counter()

        end_message = None
    
    else: 
        response = client.responses.create(
            model = model, 
            instructions= context.instructions, 
            input = context.to_input(), 
            temperature = 0.0,
            top_p = 1.0,
            stream= True)

        for event in response:
            match event.type:

                case "response.created":
                    first_response_time = time.perf_counter()

                case "response.output_text.delta":
                    if first_token_time is None:
                        first_token_time = time.perf_counter()

                    complete_answer += event.delta
                    if print_answer:
                        print(event.delta, end="", flush= True)

                case "response.completed":
                    end_message = event.response

                case "response.failed":
                    raise RuntimeError("Client:  ", {event.response.error})

                case "error":
                    raise RuntimeError("Client:  Stream error: ", {event.message})
            
    end_time = time.perf_counter()

    context.add_message("assistant", complete_answer)

    times = {
        "confirmation" : (first_response_time - start_time if first_response_time is not None else None),
        "first_token" : (first_token_time - start_time if first_token_time is not None else None),
        "total" : (end_time - start_time)
    }

    return complete_answer, end_message, times
