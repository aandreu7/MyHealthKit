"""Existing model prompts, separated from HTTP and hardware operations."""

def medicine_prompt(extracted_text):
    return [
                {
                    "role": "user",
                    "content":
                    (
                        f"I scanned a real medicine box and these are the detected words: \"{extracted_text.strip()}\".\n\n"
                        "TASK:\n"
                        "1. Identify the real active ingredient (e.g., 'Paracetamol', 'Amoxicillin') from the provided words.\n"
                        "2. Based on that name, return a structured JSON with:\n"
                        "- name: (exact name of the active drug)\n"
                        "- description: (short drug category or therapeutic use)\n"
                        "- symptoms: (main symptoms or conditions it treats)\n"
                        "- contraindications: (known contraindications or risks)\n"
                        "- url_prospect: (must be from https://www.medicines.org.uk/emc/product/<number>/smpc, or null)\n\n"
                        "IMPORTANT:\n"
                        "- The response must be based ONLY on the name found in the extracted words.\n"
                        "- Ignore brand names (e.g. Numark, Bayer).\n"
                        "- Be medically accurate and concise.\n"
                        "- Return only a valid JSON. No explanation or extra text.\n\n"
                        "EXAMPLE RESPONSE:\n"
                        "{\n"
                        "  \"name\": \"Ibuprofen\",\n"
                        "  \"description\": \"Non-steroidal anti-inflammatory drug\",\n"
                        "  \"symptoms\": \"pain, inflammation, fever\",\n"
                        "  \"contraindications\": \"gastric ulcer, kidney disease\",\n"
                        "  \"url_prospect\": \"https://www.medicines.org.uk/emc/product/5678/smpc\"\n"
                        "}"
                    )
                }
            ]

def diagnosis_prompt(existing_medicines, definedLanguage, transcribed_text):
    return [
            {
                "role": "system",
                "content": (
                    "You are a doctor. When a patient asks for a diagnosis and medicine, follow this format:\n\n"
                    "1. **State a possible diagnosis**, starting with: 'The diagnosis could be [diagnosis].'\n"
                    "2. **Then mention only the medicines that are available**, grouped naturally in a single sentence like:\n"
                    "'[medicine1], [medicine2] and [medicine3] are available.'\n"
                    "Do not say 'is available' for each medicine separately.\n"
                    "3. Do **not** mention any medicine that is not in this list: " + str(existing_medicines) + "\n"
                    "4. Do **not** say anything like 'is not available' or similar. Just ignore the unavailable ones.\n\n"
                    "At the end of the message, include **only the list of available medicines**, in the exact format:\n"
                    "['medicine1', 'medicine2'] — on a new line and nothing else.\n"
                    "If the list is empty, show [].\n\n"
                    "Respond in this language: " + definedLanguage + ".\n"
                    "Stick to this format strictly and keep the response short and to the point."
                )
            },
            {
                "role": "user",
                "content": transcribed_text
            }
    ]
