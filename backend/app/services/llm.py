import json

from openai import OpenAI

from .. import config


class LLMUnavailable(RuntimeError):
    pass


def providers() -> list[tuple[OpenAI, str]]:
    found = []
    if config.GROQ_API_KEY:
        found.append((OpenAI(api_key=config.GROQ_API_KEY, base_url="https://api.groq.com/openai/v1"), config.GROQ_MODEL))
    if config.OPENAI_API_KEY:
        found.append((OpenAI(api_key=config.OPENAI_API_KEY), config.OPENAI_MODEL))
    return found


def chat_json(system: str, messages: list[dict]) -> dict:
    """Ask the language model for a JSON object. Tries Groq first, then OpenAI."""
    last_error = None
    for client, model in providers():
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system}, *messages],
                response_format={"type": "json_object"},
            )
            return json.loads(response.choices[0].message.content)
        except Exception as error:
            last_error = error
    raise LLMUnavailable(str(last_error) if last_error else "No language-model key is configured")
