import pathlib
import json


###### Things to put here
# prompt templates (5 types, 3 prompts per type) - ZERO SHOT, FEW-SHOT, CoT, ROLE-BASED, SELF-CONSISTENCY?, TREE-OF-THOUGHT, PROMPT-CHAINING

# json structures probably

# prompt versioning, metadata and construction

# consistent interface!


# for now a loader

def load_prompts(filepath:str):

    filepath = pathlib.Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"Prompts: prompt file not found : {filepath}")

    with filepath.open("r", encoding="utf-8") as file:
        test = json.load(file)

    if "prompts" not in test:
        raise ValueError(f"Prompts: No prompts in loaded test : {filepath}")

    return test