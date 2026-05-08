# ai_service.py
import json
import os
from groq import Groq

# Load knowledge base
with open("data/medical_kb.json") as f:
    knowledge_base = json.load(f)

# Init Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def retrieve_context(symptoms: str) -> str:
    """Match symptoms against local medical KB keywords."""
    s = symptoms.lower()
    matched = []

    for item in knowledge_base:
        for keyword in item["keywords"]:
            if keyword in s:
                matched.append(f"- {item['content']}")
                break

    return "\n".join(matched) if matched else "No specific entries found in local knowledge base."


def build_system_prompt(context: str, severity: str) -> str:
    """Build the system prompt with KB context and severity."""
    urgency_note = ""
    if severity.lower() == "high":
        urgency_note = "The user has marked their severity as HIGH. Strongly emphasize seeking immediate medical attention."

    return f"""You are HealthDesk, a helpful and empathetic AI health assistant.
Your job is to provide general health guidance based on symptoms described by the user.
You are NOT a doctor and must always remind users this is not medical advice.

You have access to a local medical knowledge base. Use it to inform your response:
{context}

Guidelines:
- Be warm, clear, and concise
- Remember and refer back to what the user mentioned earlier in the conversation
- Give 2-3 practical suggestions
- Always end with a disclaimer
- If severity is high, strongly recommend seeing a doctor
{urgency_note}"""


def get_health_guidance(name: str, symptoms: str, severity: str, history: list[dict] = []) -> str:
    """
    Call Groq with full conversation history for multi-turn memory.

    history: list of previous messages in format:
             [{"role": "user", "text": "..."}, {"role": "ai", "text": "..."}, ...]
    """

    context = retrieve_context(symptoms)
    system_prompt = build_system_prompt(context, severity)

    # Build messages array for Groq — start with system prompt
    messages = [{"role": "system", "content": system_prompt}]

    # Append previous conversation history (last 10 messages to keep token count low)
    for msg in history[-10:]:
        role = "user" if msg["role"] == "user" else "assistant"  # Groq uses "assistant" not "ai"
        messages.append({"role": role, "content": msg["text"]})

    # Add current user message
    messages.append({
        "role": "user",
        "content": f"My name is {name}. I'm experiencing: {symptoms}. Severity level: {severity}."
    })

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
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