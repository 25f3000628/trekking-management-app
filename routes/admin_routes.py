from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, User, Trek, Booking
from decorators import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/dashboard")
@login_required
@role_required("admin")
def dashboard():
    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role="trekker").count()
    total_staff = User.query.filter_by(role="staff").count()
    total_bookings = Booking.query.count()
    recent_bookings = (Booking.query.order_by(Booking.booking_date.desc()).limit(5).all())
    return render_template(
        "admin/dashboard.html",
        total_treks=total_treks,
        total_users=total_users,
        total_staff=total_staff,
        total_bookings=total_bookings,
        recent_bookings=recent_bookings,
    )


@admin_bp.route("/treks")
@login_required
@role_required("admin")
def treks():
    query = request.args.get("q", "").strip()
    treks_query = Trek.query
    if query:
        treks_query = treks_query.filter((Trek.name.ilike(f"%{query}%")) | (Trek.location.ilike(f"%{query}%")))
    all_treks = treks_query.order_by(Trek.id.desc()).all()
    return render_template("admin/treks.html", treks=all_treks, query=query)

@admin_bp.route("/treks/add", methods=["GET", "POST"])
@login_required
@role_required("admin")
def add_trek():
    staff_list = User.query.filter_by(role="staff", status="approved").all()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        location = request.form.get("location", "").strip()
        difficulty = request.form.get("difficulty")
        duration = request.form.get("duration_days")
        slots = request.form.get("available_slots")
        staff_id = request.form.get("assigned_staff_id") or None
        status = request.form.get("status", "Pending")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        description = request.form.get("description", "").strip()

        if not all([name, location, difficulty, duration, slots, start_date, end_date]):
            flash("Please fill all required fields.", "danger")
            return redirect(url_for("admin.add_trek"))

        try:
            duration = int(duration)
            slots = int(slots)
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid number or date format.", "danger")
            return redirect(url_for("admin.add_trek"))

        if end_date_obj < start_date_obj:
            flash("End date cannot be before start date.", "danger")
            return redirect(url_for("admin.add_trek"))

        if slots < 0:
            flash("Available slots cannot be negative.", "danger")
            return redirect(url_for("admin.add_trek"))

        new_trek = Trek(
            name=name,
            location=location,
            difficulty=difficulty,
            duration_days=duration,
            total_slots=slots,
            available_slots=slots,
            assigned_staff_id=int(staff_id) if staff_id else None,
            status=status,
            start_date=start_date_obj,
            end_date=end_date_obj,
            description=description,
        )
        db.session.add(new_trek)
        db.session.commit()
        flash("Trek created successfully.", "success")
        return redirect(url_for("admin.treks"))

    return render_template("admin/trek_form.html", staff_list=staff_list, trek=None)


@admin_bp.route("/treks/edit/<int:trek_id>", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    staff_list = User.query.filter_by(role="staff", status="approved").all()

    if request.method == "POST":
        trek.name = request.form.get("name", "").strip()
        trek.location = request.form.get("location", "").strip()
        trek.difficulty = request.form.get("difficulty")
        trek.duration_days = int(request.form.get("duration_days"))
        trek.total_slots = int(request.form.get("available_slots"))
        trek.available_slots = trek.total_slots  
        staff_id = request.form.get("assigned_staff_id") or None
        trek.assigned_staff_id = int(staff_id) if staff_id else None
        trek.status = request.form.get("status")
        trek.start_date = datetime.strptime(request.form.get("start_date"), "%Y-%m-%d").date()
        trek.end_date = datetime.strptime(request.form.get("end_date"), "%Y-%m-%d").date()
        trek.description = request.form.get("description", "").strip()

        db.session.commit()
        flash("Trek updated successfully.", "success")
        return redirect(url_for("admin.treks"))

    return render_template("admin/trek_form.html", staff_list=staff_list, trek=trek)


@admin_bp.route("/treks/delete/<int:trek_id>", methods=["POST"])
@login_required
@role_required("admin")
def delete_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    db.session.delete(trek)
    db.session.commit()
    flash("Trek deleted.", "info")
    return redirect(url_for("admin.treks"))

@admin_bp.route("/staff")
@login_required
@role_required("admin")
def staff():
    tab = request.args.get("tab", "pending") 
    status_map = {"pending": "pending", "approved": "approved", "blacklisted": "blacklisted"}
    status = status_map.get(tab, "pending")
    staff_list = User.query.filter_by(role="staff", status=status).order_by(User.id.desc()).all()
    counts = {
        "pending": User.query.filter_by(role="staff", status="pending").count(),
        "approved": User.query.filter_by(role="staff", status="approved").count(),
        "blacklisted": User.query.filter_by(role="staff", status="blacklisted").count(),
    }

    return render_template("admin/staff.html", staff_list=staff_list, tab=tab, counts=counts)


@admin_bp.route("/staff/<int:staff_id>/approve", methods=["POST"])
@login_required
@role_required("admin")
def approve_staff(staff_id):
    staff_member = User.query.filter_by(id=staff_id, role="staff").first_or_404()
    staff_member.status = "approved"
    db.session.commit()
    flash(f"{staff_member.name} approved.", "success")
    return redirect(url_for("admin.staff", tab="pending"))


@admin_bp.route("/staff/<int:staff_id>/reject", methods=["POST"])
@login_required
@role_required("admin")
def reject_staff(staff_id):
    staff_member = User.query.filter_by(id=staff_id, role="staff").first_or_404()
    db.session.delete(staff_member)
    db.session.commit()
    flash("Staff request rejected.", "info")
    return redirect(url_for("admin.staff", tab="pending"))


@admin_bp.route("/staff/<int:staff_id>/blacklist", methods=["POST"])
@login_required
@role_required("admin")
def blacklist_staff(staff_id):
    staff_member = User.query.filter_by(id=staff_id, role="staff").first_or_404()
    staff_member.status = "blacklisted"
    Trek.query.filter_by(assigned_staff_id=staff_member.id).update({"assigned_staff_id": None})
    db.session.commit()
    flash(f"{staff_member.name} has been blacklisted.", "warning")
    return redirect(url_for("admin.staff", tab="blacklisted"))


@admin_bp.route("/staff/<int:staff_id>/reinstate", methods=["POST"])
@login_required
@role_required("admin")
def reinstate_staff(staff_id):
    staff_member = User.query.filter_by(id=staff_id, role="staff").first_or_404()
    staff_member.status = "approved"
    db.session.commit()
    flash(f"{staff_member.name} reinstated.", "success")
    return redirect(url_for("admin.staff", tab="approved"))


@admin_bp.route("/users")
@login_required
@role_required("admin")
def users():
    query = request.args.get("q", "").strip()

    users_query = User.query.filter_by(role="trekker")
    if query:
        users_query = users_query.filter((User.name.ilike(f"%{query}%")) | (User.email.ilike(f"%{query}%")))
    all_users = users_query.order_by(User.id.desc()).all()
    return render_template("admin/users.html", users=all_users, query=query)


@admin_bp.route("/users/<int:user_id>/blacklist", methods=["POST"])
@login_required
@role_required("admin")
def blacklist_user(user_id):
    user = User.query.filter_by(id=user_id, role="trekker").first_or_404()
    user.status = "blacklisted"
    db.session.commit()
    flash(f"{user.name} has been blacklisted.", "warning")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/reinstate", methods=["POST"])
@login_required
@role_required("admin")
def reinstate_user(user_id):
    user = User.query.filter_by(id=user_id, role="trekker").first_or_404()
    user.status = "active"
    db.session.commit()
    flash(f"{user.name} reinstated.", "success")
    return redirect(url_for("admin.users"))