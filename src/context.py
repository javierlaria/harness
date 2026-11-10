import pathlib
import json
import copy

###### Things to put here
# context preparation (construction)
# retrieval (selection, recheck, loop?)
# formatting? (filtering, truncation and metadata)


class Context():
    # Wrapper for the context is better than a list
    def __init__(self, instructions: str = "", messages: list[dict] = None) -> None:
        self.instructions = instructions
        self.messages = messages if messages is not None else []

    def to_input(self) -> list[dict]:
        return copy.deepcopy(self.messages)

    def add_message(self, role: str, content: str) -> None:
        if role not in ("user", "assistant"):
            raise ValueError(f"Context: Invalid role : {role}")

        self.messages.append({
            "role" : role, 
            "content": content
            })

    def copy(self) -> Context:
        return Context(
            instructions=self.instructions,
            messages= copy.deepcopy(self.messages)
        )

    def reset(self) -> None:
        self.messages.clear()

    def save_to(self, filepath: str) -> None:
        filepath = pathlib.Path(filepath)
        filepath.parent.mkdir(parents= True, exist_ok= True)

        data = {
            "instructions" : self.instructions,
            "messages" : self.messages
        }

        with filepath.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii= False)

    @classmethod
    def load_from(cls, filepath: str) -> Context:
        filepath = pathlib.Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(filepath)

        with filepath.open("r", encoding= "utf-8") as file:
            data = json.load(file)

        return cls(
            instructions = data("instructions", ""),
            messages = data.get("messages", [])
        )

def create_context(_instructions= "", _messages= None) -> Context:
    return Context(instructions=_instructions, messages= _messages)