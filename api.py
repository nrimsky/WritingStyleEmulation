import anthropic
import dotenv
import os
from typing import TypedDict, Literal

dotenv.load_dotenv()

MODEL = "claude-opus-4-1-20250805"
API_KEY = os.getenv("CLAUDE_API_KEY")

client = anthropic.Anthropic(
    api_key=API_KEY,
)

Message = TypedDict(
    "Message",
    {
        "role": Literal["user", "assistant"],
        "content": str,
    },
)


def sample(
    messages: list[Message], system_prompt: str = "", max_tokens: int = 5000
) -> str:
    api_messages = []
    for m in messages:
        api_messages.append(
            {
                "role": m["role"],
                "content": [
                    {
                        "type": "text",
                        "text": m["content"],
                    }
                ],
            }
        )
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        temperature=1,
        system=system_prompt,
        messages=api_messages,
    )
    try:
        return response.content[-1].text
    except Exception as e:
        print(response)
        raise e
