
import re
import json
import ast # apparently used to parse python code into readable abstract trees.

#### Things to put here

###  metrics 
# time, tokens input/output
# precision, recall and f1 if applicable
# semantic similarity?

### scoring
# answer/reference (expectance) comparison
# invalid or missing handle
# deterministic evaluation rules

### analysis
# aggregate scores
# technique comparison
# confusion matrix?
# experiment summaries

#### New evaluators to think about:
# classification -> match (bool), f1 (bool), precision (aggregate), recall (aggregate), keywords (bool), wrapper (bool), max_word_count (bool)
# info_extract -> json_valid (bool), exact_match (bool), required_keys (aggregate), field_match (aggregate), max_size (bool)
# coding -> code_output_match (bool), syntax_check (bool), required_funcs (aggregate), pattern (bool)

def normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())

def extract_wrapped_content(response: str, wrapper: dict) -> str:
    if not wrapper:
        return response.strip()

    if response.strip().startswith(wrapper["in"]) and response.strip().endswith(wrapper["out"]):
        return response.strip()[len(wrapper["in"]):-len(wrapper["out"])].strip()

    return response.strip()

def valid_json(response: str, wrapper: dict) -> bool:
    extracted = extract_wrapped_content(response, wrapper)
    try:
        json.loads(extracted)
        return True
    except (json.JSONDecodeError, TypeError):
        return False

def required_json_keys(response: str, keys: list, wrapper: dict) -> tuple[bool, float]:
    extracted = extract_wrapped_content(response, wrapper)
    if not keys:
        raise ValueError
    try:
        loaded_json = json.loads(extracted)
        if isinstance(loaded_json, dict):
            score = 0.0
            weight = 1.0 / len(keys)
            for key in keys:
                if key in loaded_json:
                    score += weight
            return True, score
    except (json.JSONDecodeError, TypeError, ValueError):
        return False, 0.0

def proper_values(response: str, values: dict, wrapper: dict) -> tuple[bool, float]:
    extracted = extract_wrapped_content(response, wrapper)
    if not values:
        raise ValueError
    try:
        loaded_json = json.loads(extracted)
        if isinstance(loaded_json, dict):
            score = 0.0
            weight = 1.0 / len(values)
            for key, value in values.items():
                if loaded_json.get(key) == value:
                    score += weight
            return True, score
    except (json.JSONDecodeError, TypeError, ValueError):
        return False, 0.0

def max_json_size(response: str, limit: int, wrapper: dict) -> bool:
    extracted = extract_wrapped_content(response, wrapper)
    if extracted is None:
        return False
    return len(extracted) <= limit

def syntax_check(response: str, wrapper: dict) -> bool:
    code = extract_wrapped_content(response, wrapper)
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False

def required_funcs(response: str, func_names: list, wrapper: dict) -> tuple[bool, float]:
    code = extract_wrapped_content(response, wrapper)
    if not func_names:
        return True, 1.0
    try:
        parsed_code = ast.parse(code)
        score = 0.0
        weight = 1.0 / len(func_names) if func_names else 1.0
        funcs = {node.name for node in ast.walk(parsed_code) if isinstance(node, ast.FunctionDef)}
        for func in funcs:
            if func in func_names:
                score += weight
        return True, score
    except SyntaxError:
        return False, 0.0

def required_loops(response: str, loops: dict, wrapper: dict) -> tuple[bool, float]:
    code = extract_wrapped_content(response, wrapper)
    if not loops:
        raise ValueError
    try:
        parsed_code = ast.parse(code)
        found = {
            "for" : 0,
            "while" : 0
        }
        for node in ast.walk(parsed_code):
            if isinstance(node, ast.For):
                found["for"] += 1
            elif isinstance(node, ast.While):
                found["while"] += 1
        if (found["for"] <= loops["for"] and found["while"] <= loops["while"]):
            return True, 1.0
        return True, 0.0
    except (SyntaxError, ValueError):
        return False, 0.0

def execute_response_code(response: str, wrapper: dict, target_name: str, args, expected_output) -> bool:
    code = extract_wrapped_content(response, wrapper)
    try:
        parsed_code = ast.parse(code)
        code_object = compile(parsed_code, file_name = "try_code", mode= "exec")
        namespace = {}
        exec(code_object, namespace)

        func_to_run = namespace.get(target_name)
        if callable(func_to_run):
            result = func_to_run(*args)
            return result == expected_output

        return False
    except SyntaxError:
        return False

def wrap(text: str, wrapper: dict):
    return "".join([wrapper["in"], text, wrapper["out"]])

def exact_match(response: str, expected: str, wrapper: dict) -> bool:
    if wrapper:
        expected = wrap(expected, wrapper)
    return response.strip().lower() == expected.strip().lower()

def normalized_matching(response: str, expected: str, wrapper: dict) -> float:
    if wrapper:
        expected = wrap(expected, wrapper)
    return float(normalize(response) == normalize(expected))

def keywords(response: str, keywords: list[str]) -> bool:
    return all(keyword.lower() in response.lower() for keyword in keywords)

def max_word_count(response: str, limit: int) -> bool:
    return len(response.split()) <= limit 

def min_word_count(response: str, limit: int) -> bool:
    return len(response.split()) >= limit 

def pattern_recognition(response: str, pattern: str) -> bool:
    return bool(re.search(pattern, response))

def evaluate_response(prompt: dict, response: str, baseline: dict | None) -> dict: 
    if baseline is None:
        print("Evaluation: evaluate_response: No baseline")
        return {
                "expectance" : None,
                "evaluations" : {},
                "overall_score" : None,
                "status" : "No baseline to evaluate"
            }
    expected_answer = prompt.get("expected", None)
    wrapper = baseline.get("wrapper", None)
    score_criterions = baseline.get("criterions", None)
    result = {
        "expectance" : None,
        "evaluations" : {},
        "overall_score" : None,
        "status" : "pending"
    }

    if expected_answer is not None and baseline.get("expected_answers", False):
        result["expectance"] = normalized_matching(response, expected_answer, wrapper)

    if score_criterions: 

        total_score = 0
        total_weight = 0

        print("")
        for name, criterion in score_criterions.items():
            print(f" - Testing {name}.")
            evaluations = []
            weight = criterion.get("weight", 0.0)

            for evaluator in criterion.get("evaluators", []):
                evaluation = run_evaluation(evaluator, response, prompt, expected_answer, wrapper)
                print(f"Test: {evaluation.get("type")} -> {evaluation.get("score")}")
                evaluations.append(evaluation)

            if not evaluations:
                print("No evaluators assigned.\n")
                continue

            result["evaluations"][name] = evaluations

            criterion_score = sum(evaluation.get("score", 0.0) for evaluation in evaluations) / len(evaluations)

            total_score += criterion_score * weight
            total_weight += weight

            print(f"Score: {criterion_score} * {weight} = {total_score}\n")
            
        if total_weight > 0:
            result["overall_score"] = total_score / total_weight
            result["status"] = "complete"
            print(f"Overall score: {result["overall_score"]}")
        else:
            result["status"] = "No evaluators"

    return result

def run_evaluation(evaluator: dict, response: str, prompt: dict, expected_answer: str, wrapper: dict) -> dict:
    evaluator_type = evaluator["type"]

    match evaluator_type:
        case "exact_match":
            target = (expected_answer if evaluator["target"] == "expected_answer" else evaluator["target"])
            result = exact_match(response, target, wrapper)

        case "normalized_match":
            target = (expected_answer if evaluator["target"] == "expected_answer" else evaluator["target"])
            result = normalized_matching(response, target, wrapper)

        case "keywords":
            result = keywords(response, evaluator["keywords"])

        case "max_word_count":
            result = max_word_count(response, evaluator["limit"])

        case "min_word_count":
            result = min_word_count(response, evaluator["limit"])
        
        case "pattern":
            result = pattern_recognition(response, evaluator["pattern"])

        case "json_valid":
            result = valid_json(response, wrapper)

        case "required_json_keys":
            result = required_json_keys(response, evaluator["keys"], wrapper)

        case "proper_values":
            result = proper_values(response, evaluator["values"], wrapper)

        case "syntax_check":
            result = syntax_check(response, wrapper)

        case "required_funcs":
            result = required_funcs(response, evaluator["func_names"], wrapper)

        case "required_loops":
            loops = prompt.get("evaluation", {}).get("loops", None)
            result = required_loops(response, loops, wrapper)

        case "execute_response_code":
            prompt_evaluation = prompt.get("evaluation", {})

            target_func = prompt_evaluation.get("target_func")
            test_cases = prompt_evaluation.get("tests_cases", [])

            if not target_func or not test_cases:
                result = False
            else:
                passed_tests = 0

                for test_case in test_cases:
                    res = execute_response_code(
                        response= response,
                        wrapper= wrapper,
                        target_name= target_func,
                        args= test_case["arguments"],
                        expected_output= test_case["expected_output"]
                    )
                    if res:
                        passed_tests += 1
                result = (True, passed_tests / len(test_cases))
        
        case _:
            raise ValueError(f"Evaluation: run_evaluation: Unknown evaluator type {evaluator_type}")

    return {
        "type" : evaluator_type,
        "result_valid" : result if isinstance(result, bool) else result[0],
        "score" : result[1] if isinstance(result, tuple) else 1.0 if result else 0.0
    }
