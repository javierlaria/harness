


#### Things to put here

###  metrics 
# time, tokens input/output
# precision, recall and f1 if applicable
# semantic similarity?

### scoring
# answer/reference comparison
# invalid or missing handle
# deterministic evaluation rules

### analysis
# aggregate scores
# techinique comparison
# confusion matrix?
# experiment summaries

def evaluate_response(prompt: dict, response: str):
    expected = prompt.get("expected")

    results = {
        "prompt_id" : prompt["id"],
        "response" : response,
        "evaluated" : False,
        "score" : None
    }

    if expected is None:
        return results

    results["evaluated"] = True
    results["score"] = (1 if response.strip() == expected.strip() else 0 )

    return results

def summarize_results(results: list[dict]):
    evaluated = [result for result in results if result["evaluated"]]

    if not evaluated:
        return {
            "total" : len(results),
            "evaluated" : 0,
            "average_score" : None
        }

    average_score = sum(result["score"] for result in evaluated) / len(evaluated)

    return {
        "total" : len(results),
        "evaluated" : len(evaluated),
        "average_score" : average_score
    }