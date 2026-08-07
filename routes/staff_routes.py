from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import db, Trek, Booking
from decorators import role_required

staff_bp = Blueprint("staff", __name__, url_prefix="/staff")


@staff_bp.route("/dashboard")
@login_required
@role_required("staff")
def dashboard():
    my_treks = Trek.query.filter_by(assigned_staff_id=current_user.id).order_by(Trek.id.desc()).all()

    total_participants = 0
    open_treks_count = 0
    trek_data = []

    for trek in my_treks:
        participant_count = Booking.query.filter_by(trek_id=trek.id, status="Booked").count()
        total_participants += participant_count
        if trek.status == "Open":
            open_treks_count += 1
        trek_data.append({"trek": trek, "participant_count": participant_count})

    return render_template(
        "staff/dashboard.html",
        trek_data=trek_data,
        assigned_count=len(my_treks),
        total_participants=total_participants,
        open_treks_count=open_treks_count,
    )


@staff_bp.route("/trek/<int:trek_id>", methods=["GET", "POST"])
@login_required
@role_required("staff")
def manage_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    # Enforce: only the assigned staff member can manage this trek
    if trek.assigned_staff_id != current_user.id:
        abort(403)

    if request.method == "POST":
        action = request.form.get("action")

        if action == "update_details":
            new_slots = request.form.get("available_slots")
            new_status = request.form.get("status")

            try:
                new_slots = int(new_slots)
            except (TypeError, ValueError):
                flash("Invalid slot value.", "danger")
                return redirect(url_for("staff.manage_trek", trek_id=trek.id))

            if new_slots < 0 or new_slots > trek.total_slots:
                flash(f"Slots must be between 0 and {trek.total_slots}.", "danger")
                return redirect(url_for("staff.manage_trek", trek_id=trek.id))

            trek.available_slots = new_slots
            # Staff can only toggle between Open/Closed, not admin-only statuses
            if new_status in ("Open", "Closed"):
                trek.status = new_status

            db.session.commit()
            flash("Trek details updated.", "success")

        elif action == "mark_started":
            trek.status = "Open"
            db.session.commit()
            flash("Trek marked as started (Open).", "success")

        elif action == "mark_completed":
            trek.status = "Completed"
            # Mark all active bookings for this trek as completed too
            Booking.query.filter_by(trek_id=trek.id, status="Booked").update({"status": "Completed"})
            db.session.commit()
            flash("Trek marked as completed.", "success")

        return redirect(url_for("staff.manage_trek", trek_id=trek.id))

    participants = (
        db.session.query(Booking)
        .filter_by(trek_id=trek.id)
        .order_by(Booking.booking_date.desc())
        .all()
    )

    return render_template("staff/manage_trek.html", trek=trek, participants=participants)