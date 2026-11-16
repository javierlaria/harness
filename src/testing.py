import json
import pathlib
import os
import datetime
import uuid

import numpy as np

import src.context as ctx
import src.client as cl
import src.evaluation as ev



def extract_usage(response) -> dict:
    if response is None:
        return {
            "total_tokens" : None,
            "input_tokens" : None,
            "output_tokens" : None,
            "cached_tokens" : None,
            "reasoning_tokens" : None
        }
    if response.usage is None:
        return {
            "total_tokens" : None,
            "input_tokens" : None,
            "output_tokens" : None,
            "cached_tokens" : None,
            "reasoning_tokens" : None
        }
    return {
        "total_tokens" : response.usage.total_tokens,
        "input_tokens" : response.usage.input_tokens,
        "output_tokens" : response.usage.output_tokens,
        "cached_tokens" : response.usage.input_tokens_details.cached_tokens,
        "reasoning_tokens" : response.usage.output_tokens_details.reasoning_tokens
    }

def run_test(complete_test: dict, client, model: str, repetitions: int = 1, save: bool = False) -> dict:
    test = complete_test["test"]
    technique = complete_test["technique"]

    test_id = test["test_id"]
    technique_id = technique["technique_id"]
    print(f"Test id: {test_id}  -  Technique id: {technique_id}")

    execution = technique.get("execution", {})
    strategy = execution.get("strategy", "independent")

    if not strategy in ("independent", "sequential", "combined"):
        raise ValueError(f"Testing: Unsupported strategy: {strategy}")

    if repetitions < 1:
        raise ValueError("Testing: At least one repetition.")
    
    instructions = "\n".join([technique["context"].get("instructions", ""), technique["context"].get("problem", "")])

    initial_messages = technique["context"].get("initial_messages", [])

    base_context = ctx.create_context(instructions, initial_messages)

    baseline = test.get("baseline", None)
    if baseline:
        wrapper = baseline.get("wrapper", None)
        if wrapper:
            base_context.build_wrapper(wrapper)
    print("\nInstructions: ", base_context.instructions)
    
    prompts = technique["prompts"]

    runs = []

    for repetition in range(1, repetitions + 1):
        print(f"\nRepetition {repetition}")

        current_context = base_context.copy()
        responses = []
        saved_contexts = {}

        match strategy:

            case "independent":
                for prompt in prompts:
                    print(f"\nPrompt: {prompt.get("id", "no id")}")

                    context = base_context.copy()

                    complete_answer, response, times = cl.handle_request(
                        user_input= prompt.get("input", ""),
                        context= context,
                        client= client,
                        model= model,
                        print_answer= False
                    )

                    evaluation = ev.evaluate_response(prompt, complete_answer, baseline)

                    responses.append({
                        "prompt_id" : prompt.get("id", "noid"),
                        "input" : prompt.get("input", ""),
                        "answer" : complete_answer,
                        "usage" : extract_usage(response),
                        "times" : times,
                        "evaluation" : evaluation
                    })

                    saved_contexts[prompt.get("id", "noid")] = {
                        "instructions" : context.instructions,
                        "messages" : context.messages
                    }

            case "sequential":
                for prompt in prompts:
                    print(f"\nPrompt: {prompt.get("id", "noid")}")

                    complete_answer, response, times = cl.handle_request(
                        user_input= prompt.get("input", ""),
                        context= current_context,
                        client= client,
                        model= model,
                        print_answer= False
                    )

                    evaluation = ev.evaluate_response(prompt, complete_answer)

                    responses.append({
                        "prompt_id" : prompt.get("id", "noid"),
                        "input" : prompt.get("input", ""),
                        "answer" : complete_answer,
                        "usage" : extract_usage(response),
                        "times" : times,
                        "evaluation" : evaluation
                    })

                saved_contexts["sequential"] = {
                    "instructions" : current_context.instructions,
                    "messages" : current_context.messages
                }

            case "combined": # still working this one out, the idea is that you keep passing the prompt input and response, but not sure how to evaluate it
                combined_input = "\n\n".join(
                    (str(prompt.get("id", "noid")) +"\n"+ str(prompt.get("input", "emptyinput"))) 
                    for prompt in prompts)

                complete_answer, response, times = cl.handle_request(
                    user_input= combined_input,
                    context= current_context,
                    client= client,
                    model= model,
                    print_answer= False
                )

                # evaluation = ev.evaluate_response(prompt, complete_answer) dont evaluate

                responses.append({
                    "prompt_ids" : [prompt.get("id", "no id") for prompt in prompts],
                    "input" : combined_input,
                    "answer" : complete_answer,
                    "usage" : extract_usage(response),
                    "times" : times,
                    "evaluation" : {
                        "status" : "pending",
                        "overall_score": None
                    }
                })

                saved_contexts["combined"] = {
                    "instructions" : saved_contexts.instructions,
                    "messages" : saved_contexts.messages
                }

            case _:
                raise ValueError("Testing: Unknown strategy")

        runs.append({
            "repetition" : repetition,
            "responses" : responses,
            "contexts" : saved_contexts 
        })

    result = build_result(
        test= test,
        technique= technique,
        model= model,
        strategy= strategy,
        repetitions= repetitions,
        runs= runs
    )

    if save:
        filepath = save_result(result=result)
        print(f"Result saved in {filepath}")
    return result

def build_result(test, technique, model, strategy, repetitions, runs) -> dict:
    if model == "debug":
        return {
                "run_id": str(uuid.uuid4()),
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "test" : test,
                "technique" : technique,
                "model" : {
                    "model_id" : model
                },
                "execution" : {
                    "strategy" : strategy,
                    "repetitions" : repetitions
                },
                "runs" : runs,
                "summary" : {}
            }

    responses = [response for run in runs for response in run.get("responses")]

    input_tokens = [response["usage"]["input_tokens"] for response in responses if response["usage"]["input_tokens"] is not None]
    output_tokens = [response["usage"]["output_tokens"] for response in responses if response["usage"]["output_tokens"] is not None]
    cached_tokens = [response["usage"]["cached_tokens"] for response in responses if response["usage"]["cached_tokens"] is not None]
    reasoning_tokens = [response["usage"]["reasoning_tokens"] for response in responses if response["usage"]["reasoning_tokens"] is not None]
    total_tokens = [response["usage"]["total_tokens"] for response in responses if response["usage"]["total_tokens"] is not None]

    total_durations = [response["times"]["total"] for response in responses if response["times"]["total"] is not None]
    first_token_durations = [response["times"]["first_token"] for response in responses if response["times"]["first_token"] is not None]

    scores = [response["evaluation"]["overall_score"] for response in responses if response["evaluation"]["overall_score"] is not None]

    result_summary = {
        "average_overall_score" : np.mean(scores) if scores else None,
        "median_score" : np.median(scores) if scores else None,
        "min_score" : min(scores),
        "max_score" : max(scores),
        "num_evaluated_responses" : len(scores),
        "total_responses" : len(responses),
        "input_tokens" : sum(input_tokens),
        "average_input_tokens" : np.mean(input_tokens),
        "median_input_tokens" : np.median(input_tokens),
        "output_tokens" : sum(output_tokens),
        "average_output_tokens" : np.mean(output_tokens),
        "median_output_tokens" : np.median(output_tokens),
        "total_tokens" : sum(total_tokens),
        "total_duration" : sum(total_durations),
        "average_duration" : (sum(total_durations) / len(total_durations) if total_durations else None),
        "average_time_to_first_token" : (sum(first_token_durations) / len(first_token_durations) if first_token_durations else None),
    }

    return {
        "run_id": str(uuid.uuid4()),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "test" : test,
        "technique" : technique,
        "model" : {
            "model_id" : model
        },
        "execution" : {
            "strategy" : strategy,
            "repetitions" : repetitions
        },
        "runs" : runs,
        "summary" : result_summary
    }

def save_result(result: dict) -> pathlib.Path:
    test_id = result["test"]["test_id"]
    technique_id = result["technique"]["technique_id"]
    model_id = result["model"]["model_id"]
    print("Model id: ", model_id)
    safe_model_id = model_id.replace("/", "_").replace(":", "_").replace("-", "_")
    print("Safe model id: ", safe_model_id)
    dir = (
        pathlib.Path(os.getenv("RESULTS_FILEPATH")) / test_id / technique_id / safe_model_id
    )

    dir.mkdir(parents= True, exist_ok = True)

    filepath = dir / f"{result["run_id"]}.json"

    with filepath.open("w", encoding= "utf-8") as file:
        json.dump(result, file, indent= 4, ensure_ascii= False)

    return filepath