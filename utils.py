from firebase_config import db

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

    # If mobile changed, move data
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
