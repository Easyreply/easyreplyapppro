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
        # Ensure credits are stored as int
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

# ---------------- OPENAI PROMPT LOGIC ----------------
PROMPT_TEMPLATE = """
You are a smart assistant that writes helpful, human-like replies to customer reviews.

Instructions:
- Understand the sentiment of the review (positive, neutral, negative)
- Reply in the desired tone: **{tone}**
- Reply length: {reply_length} (short, medium, or long — adjust naturally)
- Mention business name if provided: **{business_name}**
- Optionally use SEO keywords: **{seo_keywords}**
- Add reply signature at the end if available: **{signature}**
- If CTA is enabled, add at the end: **{cta_type}: {cta_link}**

Constraints:
- Don't repeat the original review
- Don't mention you're an AI
- Keep replies human, natural, and brand-safe
- Always end with a complete sentence

Now write a reply to this review:
"{review_text}"
"""

def generate_reply(review_text, tone="Professional", reply_length="Medium",
                   business_name="", seo_keywords="", signature="",
                   cta_enabled=False, cta_type="", cta_link=""):
    prompt = PROMPT_TEMPLATE.format(
        tone=tone,
        reply_length=reply_length,
        business_name=business_name,
        seo_keywords=seo_keywords,
        signature=signature,
        cta_type=cta_type,
        cta_link=cta_link,
        review_text=review_text
    )

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You're a professional reply writer for reviews."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=700
    )

    return response['choices'][0]['message']['content'].strip()
