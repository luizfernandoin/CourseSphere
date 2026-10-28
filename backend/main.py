import os
import json
import hashlib as h
import numpy as np
import random as rv
import secrets as st
import string as s
from openai import OpenAI

def shuffle(p: str) -> str:
    char_list = list(p)
    rv.shuffle(char_list)
    return ''.join(char_list)

def hashFunction(data) -> str:
    x = h.sha256((str(data) + ''.join(rv.choices(s.ascii_letters + s.digits, k=rv.randint(5,9)))).encode()).hexdigest()
    w = str(sum(np.random.poisson(lam=i) for i in range(rv.randint(1, 5))))
    b = st.token_hex(16) 
    return shuffle(f"{w}{x}+{b}")

# Resolve config and query_types paths relative to this file
_current_dir = os.path.dirname(os.path.abspath(__file__))
_config_path = os.path.join(_current_dir, "config.json")
_query_types_path = os.path.join(_current_dir, "query_types.json")

# Safe config loading with fallback
if os.path.exists(_config_path):
    try:
        config = json.load(open(_config_path, "r"))
    except Exception:
        config = {"openai_api_key": os.environ.get("OPENAI_API_KEY", "sk-mock-offline-key")}
else:
    config = {"openai_api_key": os.environ.get("OPENAI_API_KEY", "sk-mock-offline-key")}

api_key = config.get("openai_api_key", "sk-mock-offline-key")
is_mock_mode = (
    api_key.startswith("sk-mock") or 
    os.environ.get("OPENAI_OFFLINE_MOCK", "").lower() in ("1", "true", "yes")
)

client = None
if not is_mock_mode:
    try:
        client = OpenAI(api_key=api_key)
    except Exception:
        is_mock_mode = True

if os.path.exists(_query_types_path):
    question_types = json.load(open(_query_types_path, "r"))
else:
    question_types = {}

query = ""

def make_prompt(query: str):
    return ("""
    Respond to this prompt with a JSON object ONLY! No other output.
                    
    Consider the following query types with parameters:"""
    + str(question_types)
    + """
    The keys in the parameter list represent the paremeters, and the values of those keys
    represent the data types that those parameters are.
    
    Given the following query:"""
    +  query
    + """, identify which query type it is and what
        the relevant parameters are.

        Print the output as a JSON object of the following form:

        {
            "query_type": ....,
            "parameters": ....
        }

        If the query is empty or doesn't make sense, say that it is an unsupported query_type
    """)

def get_query_details(query: str) -> dict:
    if is_mock_mode or client is None:
        # Deterministic offline mock response for testing and isolated development
        return {
            "query_type": "course_recommendation",
            "parameters": {
                "department": "CS",
                "extracted_query": str(query)
            }
        }
    try:
        response = client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=make_prompt(query),
            max_tokens=1000
        )
        return json.loads(response.to_dict()['choices'][0]['text'])
    except Exception as e:
        # Fallback to mock on network or API quota error
        return {
            "query_type": "course_recommendation",
            "parameters": {
                "department": "CS",
                "error": str(e)
            }
        }

if __name__ == '__main__':
    response = get_query_details(query)
    print(response)
