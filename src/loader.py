import pathlib
import json
import os


def load_json(filepath:str) -> dict:

    filepath = pathlib.Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(filepath)

    with filepath.open("r", encoding="utf-8") as file:
        return json.load(file)

def list_tests() -> list[dict]:
    path = pathlib.Path(os.getenv("TESTS_FILEPATH"))

    tests = []

    for filepath in path.glob("*/test.json"):
        test = load_json(filepath)
        tests.append(test)

    return tests

def list_techniques(test_id: str) -> list[dict]:
    path = pathlib.Path(os.getenv("TESTS_FILEPATH")) / test_id / "techniques"

    techniques = []

    for filepath in path.glob("*.json"):
        technique = load_json(filepath)
        techniques.append(technique)

    return techniques

def load_experiment(test_id: str, technique_id: str) -> dict:
    path = pathlib.Path(os.getenv("TESTS_FILEPATH")) / test_id

    test = load_json(path / "test.json")

    technique = load_json(path / "techniques" / f"{technique_id}.json")

    print(f"Technique path: {path / "test.json"}")
    print(f"Technique path: {path / "techniques" / f"{technique_id}.json"}")

    return {
        "test" : test,
        "technique" : technique
    }

