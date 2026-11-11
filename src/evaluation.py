
import re

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

def normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())

def wrap(text: str, wrapper: dict):
    return "".join([wrapper["in"], text, wrapper["out"]])

def exact_match(response: str, expected: str, wrapper: dict) -> bool:
    if wrapper:
        expected = wrap(expected)
    return response.strip().lower() == expected.strip().lower()

def normalized_matching(response: str, expected: str, wrapper: dict) -> float:
    if wrapper:
        expected = wrap(expected)
    return float(normalize(response) == normalize(expected))

def keywords(response: str, keywords: list[str]) -> bool:
    return all(keyword.lower() in response.lower() for keyword in keywords)

def max_word_count(response: str, limit: int) -> bool:
    return len(response.split()) <= limit 

def min_word_count(response: str, limit: int) -> bool:
    return len(response.split()) >= limit 

def pattern_recognition(response: str, pattern: str) -> bool:
    return bool(re.search(pattern, response))

def evaluate_response(prompt: dict, response: str, baseline: dict | None = None) -> dict: 
    expected_answer = prompt.get("expected", None)
    wrapper = baseline.get("wrapper", None)
    score_criterions = baseline.get("criterions", None)
    result = {
        "expectance" : None,
        "score_criterions" : score_criterions or {},
        "overall_score" : None,
        "status" : "pending"
    }

    if expected_answer is not None and baseline.get("expected_asnwers", False):
        result["expectance"] = normalized_matching(response, expected_answer, wrapper)

    if score_criterions: 

        total_score = 0
        total_weight = 0

        for name, criterion in score_criterions.items():
            print(f" - Testing {name}.")
            evaluations = []
            weight = criterion.get("weight", 0.0)

            for evaluator in criterion.get("evaluators", []):
                evaluation = run_evaluation(evaluator, response, expected_answer, wrapper)
                print(f"Test: {evaluation.get("type")} -> {evaluation.get("score")}")
                evaluations.append(evaluation)

            if len(evaluations) == 0:
                print("\nNo evaluators assigned.")
                continue

            criterion_score = sum(evaluation.get("score", 0.0) for evaluation in evaluations) / len(evaluations)
            print(f"Score: {criterion_score}\n")
            
            total_score += criterion_score * weight
            total_weight += weight

        if total_weight > 0:
            result["overall_score"] = total_score / total_weight

        result["status"] = "complete"

    elif expected_answer is not None:
        result["status"] = "partially completed"

    return result

def run_evaluation(evaluator: str, response: str, expected_answer: str, wrapper) -> dict:
    evaluator_type = evaluator["type"]

    match evaluator_type:
        case "exact_match":
            target = (expected_answer if evaluator["target"] == "expected_answer" else evaluator["target"])
            if wrapper:
                target = wrap(target)
            result = exact_match(response, target)

        case "keywords":
            result = keywords(response, evaluator["keywords"])

        case "max_word_count":
            result = max_word_count(response, evaluator["limit"])

        case "min_word_count":
            result = min_word_count(response, evaluator["limit"])
        
        case "pattern":
            result = pattern_recognition(response, evaluator["pattern"])

        case _:
            raise ValueError("Evaluation: run_evaluation: Unknown evaluator type ", evaluator_type)

    return {
        "type" : evaluator_type,
        "result" : result,
        "score" : 5 if result else 0
    }
