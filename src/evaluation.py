


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

def evaluate_expected(response: str, expected: str) -> float:
    return float(normalize(response) == normalize(expected))

def evaluate_response(prompt: dict, response: str, score_criterions: dict | None = None) -> dict: 
    expected = prompt.get("expected_answer", None)

    result = {
        "expectance" : None,
        "score_criterions" : score_criterions or {},
        "overall_score" : None,
        "status" : "pending"
    }

    if expected is not None:
        result["expectance"] = evaluate_expected(response, expected)

    if score_criterions: 
        result["status"] = "complete"

    elif expected is not None:
        result["status"] = "partially completed"

    return result

def calculate_weighted_scores(score_criterions: dict, criterion: dict) -> float | None:
    scores = {name : score for name, score in score_criterions.items() if name in criterion}

    if not scores: # nothing to score on
        return None

    total_weight = sum(criterion[name]["weight"] for name in scores.keys())

    if total_weight == 0: # weights shouldnt really be 0 
        return None

    return sum(score * criterion[name]["weight"] for name, score in scores.items()) / total_weight # weighted sum
