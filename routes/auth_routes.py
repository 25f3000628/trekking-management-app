from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        role = request.form.get("role")  # 'staff' or 'trekker' only

        # Backend validation
        if not all([name, email, password, confirm_password, role]):
            flash("All fields are required.", "danger")
            return redirect(url_for("auth.register"))

        if role not in ("staff", "trekker"):
            flash("Invalid role selected.", "danger")
            return redirect(url_for("auth.register"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.register"))

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return redirect(url_for("auth.register"))

        # Staff start as 'pending' (need admin approval), trekkers start 'active'
        status = "pending" if role == "staff" else "active"

        new_user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role=role,
            status=status,
        )
        db.session.add(new_user)
        db.session.commit()

        if role == "staff":
            flash("Registration successful. Please wait for admin approval before logging in.", "info")
        else:
            flash("Registration successful. You can now log in.", "success")

        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect_by_role(current_user)

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth.login"))

        if user.role == "staff" and user.status == "pending":
            flash("Your account is awaiting admin approval.", "warning")
            return redirect(url_for("auth.login"))

        if user.status == "blacklisted":
            flash("Your account has been blacklisted. Contact admin.", "danger")
            return redirect(url_for("auth.login"))

        login_user(user)
        flash(f"Welcome back, {user.name}!", "success")
        return redirect_by_role(user)

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


def redirect_by_role(user):
    if user.role == "admin":
        return redirect(url_for("admin.dashboard"))
    elif user.role == "staff":
        return redirect(url_for("staff.dashboard"))
    else:
        return redirect(url_for("user.dashboard"))