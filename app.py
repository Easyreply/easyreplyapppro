from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import os
from utils import (
    check_login, get_user, get_all_users,
    add_user, update_user, delete_user,
    generate_reply, deduct_credit
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret")
ADMIN_MOBILE = "8830720742"

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        mobile = request.form["mobile"]
        password = request.form["password"]
        user = check_login(mobile, password)
        if user:
            session["mobile"] = mobile
            session["username"] = user.get("name", "")
            session["is_admin"] = (mobile == ADMIN_MOBILE)
            session["credits"] = user.get("credits", 0)
            return redirect("/admin" if mobile == ADMIN_MOBILE else f"/{user.get('name')}")
        else:
            error = "Invalid mobile number or password."
    return render_template("login.html", error=error)

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/admin")
def admin():
    if not session.get("is_admin"):
        return redirect(url_for("login"))
    users = get_all_users()
    return render_template("admin.html", users=users)

@app.route("/add_user", methods=["POST"])
def add_user_route():
    if not session.get("is_admin"):
        return redirect(url_for("login"))
    data = {
        "name": request.form["name"],
        "mobile": request.form["mobile"],
        "password": request.form["password"],
        "credits": request.form["credits"]
    }
    add_user(data)
    return redirect("/admin")

@app.route("/update_user", methods=["POST"])
def update_user_route():
    if not session.get("is_admin"):
        return redirect(url_for("login"))
    original_mobile = request.form["original_mobile"]
    updated_data = {
        "name": request.form["name"],
        "mobile": request.form["mobile"],
        "password": request.form["password"],
        "credits": request.form["credits"]
    }
    update_user(original_mobile, updated_data)
    return redirect("/admin")

@app.route("/delete_user", methods=["POST"])
def delete_user_route():
    if not session.get("is_admin"):
        return redirect(url_for("login"))
    mobile = request.form["mobile"]
    delete_user(mobile)
    return redirect("/admin")

@app.route("/<username>")
def user_dashboard(username):
    if not session.get("mobile") or session.get("is_admin"):
        return redirect(url_for("login"))
    if session.get("username") != username:
        return "Unauthorized access", 403
    user = get_user(session["mobile"])
    credits = user.get("credits", 0)
    return render_template("user.html", username=username, credits=credits)

@app.route("/generate_reply", methods=["POST"])
def generate_reply_route():
    if not session.get("mobile") or session.get("is_admin"):
        return jsonify({"error": "Unauthorized"}), 403

    mobile = session["mobile"]
    user = get_user(mobile)

    if not user or int(user.get("credits", 0)) < 1:
        return jsonify({"error": "Insufficient credits"}), 402

    data = request.get_json()
    reply = generate_reply(
        review_text=data.get("review_text", ""),
        tone=data.get("tone", "Professional"),
        reply_length=data.get("reply_length", "Medium"),
        business_name=data.get("business_name", ""),
        seo_keywords=data.get("seo_keywords", ""),
        signature=data.get("signature", ""),
        cta_enabled=data.get("cta_enabled", False),
        cta_type=data.get("cta_type", ""),
        cta_link=data.get("cta_link", "")
    )

    deduct_credit(mobile)  # 🔁 Deduct 1 credit after reply
    updated_user = get_user(mobile)
    session["credits"] = updated_user.get("credits", 0)

    return jsonify({
        "reply": reply,
        "credits": session["credits"]
    })
