import os
import logging

from dotenv import load_dotenv
from pydantic import BaseModel

from google import genai
import openai
from openai import AzureOpenAI, OpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

DOTENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.env"))
load_dotenv(DOTENV_PATH)

# check env
use_azure = os.getenv("USE_AZURE", "false").lower()
if use_azure == "true":
    if not os.getenv("AZURE_CHATCOMPLETION_ENDPOINT"):
        raise RuntimeError("AZURE_CHATCOMPLETION_ENDPOINT environment variable is not set")
    if not os.getenv("AZURE_CHATCOMPLETION_DEPLOYMENT_NAME"):
        raise RuntimeError("AZURE_CHATCOMPLETION_DEPLOYMENT_NAME environment variable is not set")
    if not os.getenv("AZURE_CHATCOMPLETION_API_KEY"):
        raise RuntimeError("AZURE_CHATCOMPLETION_API_KEY environment variable is not set")
    if not os.getenv("AZURE_CHATCOMPLETION_VERSION"):
        raise RuntimeError("AZURE_CHATCOMPLETION_VERSION environment variable is not set")
    if not os.getenv("AZURE_EMBEDDING_ENDPOINT"):
        raise RuntimeError("AZURE_EMBEDDING_ENDPOINT environment variable is not set")
    if not os.getenv("AZURE_EMBEDDING_API_KEY"):
        raise RuntimeError("AZURE_EMBEDDING_API_KEY environment variable is not set")
    if not os.getenv("AZURE_EMBEDDING_VERSION"):
        raise RuntimeError("AZURE_EMBEDDING_VERSION environment variable is not set")
    if not os.getenv("AZURE_EMBEDDING_DEPLOYMENT_NAME"):
        raise RuntimeError("AZURE_EMBEDDING_DEPLOYMENT_NAME environment variable is not set")

@retry(
    wait=wait_exponential(multiplier=1, min=2, max=20),
    stop=stop_after_attempt(3),
    reraise=True,
)
def request_to_azure_chatcompletion(
    messages: list[dict],
    is_json: bool = False,
) -> dict:
    azure_endpoint = os.getenv("AZURE_CHATCOMPLETION_ENDPOINT")
    deployment = os.getenv("AZURE_CHATCOMPLETION_DEPLOYMENT_NAME")
    api_key = os.getenv("AZURE_CHATCOMPLETION_API_KEY")
    api_version = os.getenv("AZURE_CHATCOMPLETION_VERSION")

    client = AzureOpenAI(
        api_version=api_version,
        azure_endpoint=azure_endpoint,
        api_key=api_key,
    )

    if is_json:
        response_format = {"type": "json_object"}
    else:
        response_format = None

    try:
        response = client.chat.completions.create(
            model=deployment,
            messages=messages,
            temperature=0,
            n=1,
            seed=0,
            response_format=response_format,
            timeout=30,
        )

        return response.choices[0].message.content
    except openai.RateLimitError as e:
        logging.warning(f"OpenAI API rate limit hit: {e}")
        raise
    except openai.AuthenticationError as e:
        logging.error(f"OpenAI API authentication error: {str(e)}")
        raise
    except openai.BadRequestError as e:
        logging.error(f"OpenAI API bad request error: {str(e)}")
        raise

# 作りかけ
def request_to_gemini(
    messages: list[dict],
    model: str = "gemini-2.0-flash",
    is_json: bool = False,
) -> dict:

    api_key = os.getenv("GEMINI_API_KEY")

    client = OpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/"
    )

    if is_json:
        response_format = {"type": "json_object"}
    else:
        response_format = None

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
        n=1,
        response_format=response_format,
        timeout=30,
    )

    return response.choices[0].message.content


def request_to_chat_llm(
    messages: list[dict],
    model: str = "gpt-4o",
    is_json: bool = False,
) -> dict:
    use_azure = os.getenv("USE_AZURE", "false").lower()
    if use_azure == "true":
        return request_to_azure_chatcompletion(messages, is_json)
    else:
        return request_to_gemini(messages, model, is_json)


EMBDDING_MODELS = [
    "text-embedding-3-large",
    "text-embedding-3-small",
    "gemini-embedding-exp-03-07"
]


def _validate_model(model):
    if model not in EMBDDING_MODELS:
        raise RuntimeError(f"Invalid embedding model: {model}, available models: {EMBDDING_MODELS}")


def request_to_embed(args, model):
    use_azure = os.getenv("USE_AZURE", "false").lower()
    if use_azure == "true":
        return request_to_azure_embed(args, model)

    else:
        _validate_model(model)
        api_key = os.getenv("GEMINI_API_KEY")
        client = genai.Client(api_key=api_key)
        result = client.models.embed_content(
        model="gemini-embedding-exp-03-07",
        contents=args,
)

        embeds = result.embeddings
    return embeds


def request_to_azure_embed(args, model):
    azure_endpoint = os.getenv("AZURE_EMBEDDING_ENDPOINT")
    api_key = os.getenv("AZURE_EMBEDDING_API_KEY")
    api_version = os.getenv("AZURE_EMBEDDING_VERSION")
    deployment = os.getenv("AZURE_EMBEDDING_DEPLOYMENT_NAME")
    assert azure_endpoint and deployment and api_key and api_version

    client = AzureOpenAI(
        api_version=api_version,
        azure_endpoint=azure_endpoint,
        api_key=api_key,
    )

    response = client.embeddings.create(input=args, model=deployment)
    return [item.embedding for item in response.data]


def _test():
    # messages = [
    #     {"role": "system", "content": "英訳せよ"},
    #     {"role": "user", "content": "これはテストです"},
    # ]
    # response = request_to_chat_llm(messages=messages, model="gpt-4o", is_json=False)
    # print(response)
    # print(request_to_embed("Hello", "text-embedding-3-large"))
    print(request_to_azure_embed("Hello", "text-embedding-3-large"))


if __name__ == "__main__":
    _test()