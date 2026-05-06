import json
import os
from groq import Groq

# load knowledge base
with open("data/medical_kb.json") as f:
    knowledge_base = json.load(f)

# init Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def retrieve_context(symptoms: str) -> str:
    s = symptoms.lower()
    matched = []

    for item in knowledge_base:
        for keyword in item["keywords"]:
            if keyword in s:
                matched.append(f"- {item['content']}")
                break

    if matched:
        return "\n".join(matched)
    return "No specific entries found in local knowledge base for these symptoms."


def get_health_guidance(name: str, symptoms: str, severity: str) -> str:

    context = retrieve_context(symptoms)

    urgency_note = ""
    if severity.lower() == "high":
        urgency_note = "The user has marked their severity as HIGH. Emphasize seeking immediate medical attention."

    system_prompt = f"""You are HealthDesk, a helpful and empathetic AI health assistant.
Your job is to provide general health guidance based on symptoms described by the user.
You are NOT a doctor and must always remind users this is not medical advice.

You have access to a local medical knowledge base. Use it to inform your response:
{context}

Guidelines:
- Be warm, clear, and concise
- Give 2-3 practical suggestions
- Always end with a disclaimer
- If severity is high, strongly recommend seeing a doctor
{urgency_note}
"""

    user_message = f"My name is {name}. I'm experiencing: {symptoms}. Severity level: {severity}."

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=400,
            temperature=0.6
        )
        return response.choices[0].message.content

    except Exception as e:
        return (
            f"Hello {name},\n\n"
            f"I wasn't able to reach the AI service right now (Error: {str(e)}).\n\n"
            f"Based on your symptoms ({symptoms}), please stay hydrated, rest, and "
            f"consult a healthcare professional if symptoms persist.\n\n"
            f"⚕️ This is not medical advice."
        )