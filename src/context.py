import pathlib
import json

###### Things to put here
# context preparation (construction)
# retrieval (selection, recheck, loop?)
# formatting (filtering, truncation and metadata)


class Context():

    def __init__(self, instructions: str = "", messages: list[dict] = None):
        self.instructions = instructions
        self.messages = messages if messages is not None else []

    def to_input(self) -> list[dict]:
        context = []

        if self.instructions:
            context.append({
                "role" : "developer",
                "content" : self.instructions
            })

        context.extend(self.messages)
        return context

    def add_message(self, role: str, content: str):
        if role not in ("user", "assistant"):
            raise ValueError(f"Context: Invalid role : {role}")

        self.messages.append({
            "role" : role, 
            "content": content
            })

    def reset(self):
        self.messages.clear()

    def save_to(self, filepath: str):
        filepath = pathlib.Path(filepath)
        filepath.parent.mkdir(parents= True, exist_ok= True)

        data = {
            "instructions" : self.instructions,
            "messages" : self.messages
        }

        with filepath.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii= False)

    @classmethod
    def load_from(cls, filepath: str):
        filepath = pathlib.Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Context: Context not found : {filepath}")

        with filepath.open("r", encoding= "utf-8") as file:
            data = json.load(file)

        return cls(
            instructions = data("instructions", ""),
            messages = data.get("messages", [])
        )

def create_context(_instructions, _messages: list[dict] = None):
    return Context(instructions=_instructions, messages= _messages)