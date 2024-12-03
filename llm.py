from litellm import completion
import os
from dotenv import load_dotenv

load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

def call_llm(model="gpt-4o-mini", messages=[], max_tokens=None, temperature=0.0, response_format=None):
    response = completion(
        model=model, 
        messages=messages,
        temperature=temperature,
        response_format=response_format
    )
    return response