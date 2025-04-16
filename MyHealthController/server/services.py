def get_completion(client, message, temperature=0.2, max_tokens=150):
    return client.chat.completions.create(
        extra_body={
            "temperature": temperature, # Controlls model creativity.
            "max_tokens": max_tokens # Output length in tokens.
        },
        model="nvidia/llama-3.3-nemotron-super-49b-v1:free",
        messages=message
    )