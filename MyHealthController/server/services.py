import re

def get_completion(client, message, temperature=0.2, max_tokens=150):
    return client.chat.completions.create(
        extra_body={
            "temperature": temperature, # Controlls model creativity.
            "max_tokens": max_tokens # Output length in tokens.
        },
        model="nvidia/llama-3.3-nemotron-super-49b-v1:free",
        messages=message
    )

def extract_medicines_list(answer):
    """
    Extracts the list of medicines from the last line of the provided answer string by the LLM.
    """
    # Divides the message into lines and obtains the last line (where the list of medicines is expected to be)
    lines = answer.strip().split("\n")
    last_line = lines[-1]
    
    # Validate the format of the last line to ensure it is a list of strings
    pattern = r"^\[(?:'[^']*',\s*)*'[^']*'\]$"
    
    if re.match(pattern, last_line):
        medicines = eval(last_line)
        return medicines
    else:
        raise ValueError("LLM has not provided a list of medicines in its last message.")