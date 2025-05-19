from firebase_config import db
import openai
import os
import json

openai.api_key = os.environ.get("OPENAI_API_KEY")

# ---------------- FIREBASE USER FUNCTIONS ----------------
def get_user(mobile):
    ref = db.reference(f"users/{mobile}")
    return ref.get()

def get_all_users():
    ref = db.reference("users")
    return ref.get() or {}

def add_user(data):
    mobile = data.get("mobile")
    if not mobile:
        return False
    ref = db.reference(f"users/{mobile}")
    ref.set({
        "name": data.get("name"),
        "password": data.get("password"),
        "credits": int(data.get("credits", 0))  # safe cast
    })
    return True

def update_user(original_mobile, updated_data):
    if not original_mobile:
        return False
    old_ref = db.reference(f"users/{original_mobile}")
    user_data = old_ref.get()
    if not user_data:
        return False
    new_mobile = updated_data.get("mobile")
    if new_mobile and new_mobile != original_mobile:
        db.reference(f"users/{new_mobile}").set(updated_data)
        old_ref.delete()
    else:
        if "credits" in updated_data:
            updated_data["credits"] = int(updated_data["credits"])
        old_ref.update(updated_data)
    return True

def delete_user(mobile):
    ref = db.reference(f"users/{mobile}")
    ref.delete()
    return True

def check_login(mobile, password):
    ref = db.reference(f"users/{mobile}")
    user = ref.get()
    if user and user.get("password") == password:
        return user
    return None

def deduct_credit(mobile):
    ref = db.reference(f"users/{mobile}/credits")
    current = ref.get()
    try:
        current = int(current)
    except (TypeError, ValueError):
        return False

    if current > 0:
        ref.set(current - 1)
        return True
    return False

# ---------------- SMART REPLY PROMPT LOGIC ----------------

def get_length_instruction(length):
    length = (length or "").lower()
    if length == "short":
        return "Keep the reply concise: maximum 2–3 sentences."
    elif length == "medium":
        return "Keep the reply informative: 4–6 sentences recommended."
    elif length == "long":
        return "You can elaborate more, up to 8+ sentences if needed."
    return "Keep the reply clear and easy to read."

def generate_reply(review_text, tone="Professional", reply_length="Short",
                   business_name="", seo_keywords="", signature="",
                   cta_enabled=False, cta_type="", cta_link=""):

    prompt_lines = [
        "You are a smart assistant that writes helpful, brand-safe, and human-like replies to customer reviews.",
        "",
        f"- Respond in a {tone.lower()} tone.",
        f"- {get_length_instruction(reply_length)}",
        "- Analyze the sentiment of the review (positive, neutral, negative) and adjust tone accordingly.",
        "- If additional fields like business name, SEO keywords, or CTA are provided, include them only if they naturally fit into the reply length.",
    ]

    if business_name:
        prompt_lines.append(f"- Mention business name if helpful: {business_name}")
    if seo_keywords:
        prompt_lines.append(f"- Try to include these key phrases if appropriate: {seo_keywords}")
    if signature:
        prompt_lines.append(f"- Close with this signature if space allows: {signature}")
    if cta_enabled and cta_type and cta_link:
        prompt_lines.append(f"- Add this CTA at the end if appropriate: {cta_type}: {cta_link}")

    prompt_lines += [
        "",
        "Constraints:",
        "- Do not repeat the review text.",
        "- Do not ask follow-up questions.",
        "- Do not mention that you are an AI or assistant.",
        "- End with a complete sentence. Avoid vague or generic sign-offs.",
        "",
        f"Now write a reply to this review:\n\"{review_text}\""
    ]

    prompt = "\n".join(prompt_lines)

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a professional review reply writer for businesses."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=600
    )

    return response['choices'][0]['message']['content'].strip()
