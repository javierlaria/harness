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

def handle_prompt(prompt: dict, base_context: ctx.Context, sequential_prompts: list, client, model: str, baseline: dict) -> dict:
    prompt_id = prompt.get("id", "noid")
    context = base_context.copy()

    responses = []
    times = []

    inputs = [{
        "input" : prompt.get("input", ""),
        "type" : "initial"
    }]

    inputs.extend([{
        "input" : seq_prompt,
        "type" : "sequential"
        } for seq_prompt in sequential_prompts
    ])

    for i, input in enumerate(inputs):
        complete_answer, response, time = cl.handle_request(
            user_input= input["input"],
            context= context,
            client= client,
            model= model,
            print_answer=False
        )
        responses.append({
                "index" : i,
                "type" : input["type"],
                "input" : input["input"],
                "answer" : complete_answer,
                "usage" : extract_usage(response),
                "times" : time,
            })
        times.append(time)

    final_answer = responses[-1]["answer"]

    evaluation = ev.evaluate_response(prompt, final_answer, baseline)

    return {
        "prompt_id" : prompt_id,
        "responses" : responses,
        "evaluation" : evaluation,
        "contexts" : {
            "instructions" : context.instructions,
            "messages" : context.messages
        },
        "times" : times
    }

def run_test(complete_test: dict, client, model: str, repetitions: int = 1, save: bool = False) -> dict:
    test = complete_test["test"]
    technique = complete_test["technique"]

    test_id = test["test_id"]
    technique_id = technique["technique_id"]

    if repetitions < 1:
        repetitions = 1 # ignore repetitions really

    print(f"Test id: {test_id}  -  Technique id: {technique_id}")  
    
    instructions = "\n".join([technique["context"].get("instructions", ""), technique["context"].get("problem", "")])

    initial_messages = technique["context"].get("initial_messages", [])

    sequential_prompts = technique["context"].get("sequential_prompts", [])

    baseline = test.get("baseline", None)

    wrapper = baseline.get("wrapper", None)

    base_context = ctx.create_context(instructions, initial_messages)

    if wrapper:
        base_context.build_wrapper(wrapper)

    print("\nInstructions: ", base_context.instructions)
    
    runs = []

    for repetition in range(1, repetitions + 1):
        print(f"\nRepetition {repetition}")

        results = []

        for prompt in technique.get("prompts"):

            print(f"\nPrompt: {prompt.get("id", "no id")}")

            result = handle_prompt(
                prompt= prompt,
                base_context= base_context,
                sequential_prompts= sequential_prompts,
                client= client,
                model= model,
                baseline= baseline
            )
            
            results.append(result)

        runs.append({
            "repetition" : repetition,
            "prompts" : results
        })
    

    result = build_result(
        test= test,
        technique= technique,
        model= model,
        repetitions= repetitions,
        runs= runs
    )

    if save:
        filepath = save_result(result=result)
        print(f"\n\nResult saved in {filepath}")
    return result

def build_result(test: dict, technique: dict, model: str, repetitions: int, runs: list) -> dict:
    print(f"reached, {model}")
    if model == "debug":
        return {
                "run_id": str(uuid.uuid4()),
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "test" : test,
                "technique" : technique,
                "model_id" : model,
                "repetitions" : repetitions,
                "runs" : runs,
                "summary" : {}
            }
    prompts = [prompt for run in runs for prompt in run.get("prompts")]

    responses = [response for prompt in prompts for response in prompt.get("responses")]

    evaluations = [prompt.get("evaluation") for prompt in prompts if prompt.get("evaluation", None) is not None]

    scores = [evaluation.get("overall_score") for evaluation in evaluations if evaluation.get("overall_score", None) is not None]

    durations = [response["times"]["total"] for response in responses if response.get("times") and response["times"].get("total") is not None]

    first_token_durations = [response["times"]["first_token"] for response in responses if response.get("times") and response["times"].get("first_token") is not None]

    token_metrics = {}

    def get_values(key: str, source = responses, section = "usage"):
        return [item[section][key] for item in source if item.get(section, {}).get(key) is not None]

    def mean(items):
        return float(np.mean(items)) if items else None
    def median(items):
        return float(np.median(items)) if items else None
    
    for key in ["input_tokens", "output_tokens", "cached_tokens", "reasoning_tokens", "total_tokens"]:
        collected = get_values(key)

        token_metrics[key] = {
            "total" : sum(collected),
            "average" : mean(collected),
            "median" : median(collected)
        }

    summary = {
        "average_overall_score": mean(scores),
        "median_score": median(scores),
        "min_score": min(scores) if scores else None,
        "max_score": max(scores) if scores else None,
        "num_evaluated_prompts": len(scores),
        "total_prompts": len(prompts),
        "total_responses": len(responses),
        "tokens": token_metrics,
        "total_duration": sum(durations),
        "average_duration": mean(durations),
        "median_duration" : median(durations),
        "average_time_to_first_token": mean(first_token_durations),
        "median_time_to_first_token" : median(first_token_durations)
    }
    return {
        "run_id": str(uuid.uuid4()),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "test" : test,
        "technique" : technique,
        "model_id" : model,
        "repetitions" : repetitions,
        "runs" : runs,
        "summary" : summary
    }

def save_result(result: dict) -> pathlib.Path:
    try: 
        test_id = result["test"]["test_id"]
        technique_id = result["technique"]["technique_id"]
        model_id = result["model_id"]
    except KeyError:
        print(f"Testing: Save_result: check the dictionaries.")
    safe_model_id = model_id.replace("/", "_").replace(":", "_").replace("-", "_")
    dir = (
        pathlib.Path(os.getenv("RESULTS_FILEPATH")) / test_id / technique_id / safe_model_id
    )

    dir.mkdir(parents= True, exist_ok = True)

    def get_filepath(dir, model_id: str, technique_id: str, test_id: str, number: int = 0):
        filepath = dir / f"{model_id}_{technique_id}_{test_id}_{number}.json"
        if os.path.exists(filepath):
            return get_filepath(dir, model_id, technique_id, test_id, number = number + 1)
        return filepath

    filepath = get_filepath(dir, safe_model_id, technique_id, test_id)

    with filepath.open("w", encoding= "utf-8") as file:
        json.dump(result, file, indent= 4, ensure_ascii= False)

    return filepath