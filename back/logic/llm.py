import openai

def translate(text: str) -> str:
    client = OpenAI()
    translation = client.responses.create(
        model="gpt-4o",
        input=[
            {
                "role": "developer",
                "content": """You are a professional translator that translates English to Korean. 
                General rules:
                - Preserve original meaning exactly.
                - Do not add emotion, emphasis, or information.
                - Preserve emotional intensity, including profanity.
                - Choose natural Korean used by native speakers.
                - Prefer commonly used modern expressions.
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
    return response.choices[0].message.content

def lesson(grammar_vocab: str, sentence: str) -> str:
    client = OpenAI()
    lesson = client.responses.create(
        model="gpt-4o",
        input=[
            {
                "role": "developer",
                "content": """You are a professional language tutor that explains Korean grammar and vocabulary in English. 
                General rules:
                - Explain the given grammar or vocabulary in English, providing equivalent English grammar or vocabulary.
                - Give example usage of the grammar or vocabulary in English.
                - Explain the nuances and the edge cases of the grammar or vocabulary in English."""
            },
            {
                "role": "user",
                "content": f'{grammar_vocab} in the following sentence: {sentence}'
            }
        ],
    )
    return lesson.choices[0].message.content