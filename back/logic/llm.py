from openai import OpenAI

client = OpenAI()

def translate(text: str) -> dict:
    translation = client.responses.create(
        model="gpt-4o",
        input=[
            {
                "role": "developer",
                "content": """You are a professional translator that translates English to Korean. 
                General rules:
                - Preserve original meaning exactly.
                - Preserve emotional intensity, including profanity.
                - Choose natural Korean used by native speakers.
                - Respect context when choosing speech level.
                - Favor clarity over literal translation.
                - Avoid unnatural textbook phrasing."""
            },
            {
                "role": "user",
                "content": f'{text}'
            }
        ],
    )
    return {"translation": translation.output_text}

def lesson(grammar_vocab: str, sentence: str) -> dict:
    lesson = client.responses.create(
        model="gpt-4o",
        temperature=0.0,
        input=[
            {
                "role": "developer",
                "content": """You are a professional language tutor that explains Korean grammar and vocabulary in English. 
                Base the explanation on the given sentence but generalize the grammar or vocabulary to a single pattern. 
                Include the following sections:
                - pattern: all required POS + inflections (verb+ㄹ/을게요)
                - function: communicative purpose of the grammar
                - meaning: concise English meaning
                - boundary: when this does NOT apply

                Use exact Uppercase field names.
                No bullets, hyphens, or markdown.
                """
            },
            {
                "role": "user",
                "content": f'{grammar_vocab} in the following sentence: {sentence}'
            }
        ],
    )
    return {"lesson": lesson.output_text}