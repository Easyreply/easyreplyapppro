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
        "credits": int(data.get("credits", 0))
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
    current = ref.get() or 0
    if current > 0:
        ref.set(current - 1)
        return True
    return False

# ---------------- OPENAI PROMPT LOGIC ----------------
PROMPT_TEMPLATE = """
You are a smart business assistant that writes helpful and brand-safe replies to customer reviews.

Your responsibilities:
1. Understand the sentiment of the review: is it positive, neutral, or negative?
2. Based on that, adjust your opening and tone while staying aligned with the desired tone: **{tone}**
3. Reply length should be: **{reply_length}**.
   Use these guidelines:
   - Short: 20–40 words
   - Medium: 50–80 words
   - Long: 80–120 words
4. You may mention the business name if provided: **{business_name}**
5. Use these SEO keywords naturally if provided: **{seo_keywords}**
6. Add this signature at the end if available: **{signature}**
7. If CTA is enabled, add this to the end:
   → **{cta_type}: {cta_link}**

Constraints:
- Your response must sound polite, customer-friendly, and brand-safe.
- Do NOT mention or reference tone, sentiment, length, or instruction itself.
- Do NOT repeat the original review.
- Do NOT ask follow-up questions.
- Always provide a clean and direct reply in the specified tone.

Now write a reply to this customer review:
\"{review_text}\"
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
        max_tokens=400
    )

    return response['choices'][0]['message']['content'].strip()
