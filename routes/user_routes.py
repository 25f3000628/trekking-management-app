from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import db, Trek, Booking

user_bp = Blueprint("user", __name__, url_prefix="/user")

def check_trekker():
    """Ensure only trekkers access these routes (mirrors role_required but kept simple here)."""
    if current_user.role != "trekker":
        abort(403)
    if current_user.status == "blacklisted":
        abort(403)

@user_bp.route("/dashboard")
@login_required
def dashboard():
    check_trekker()
    difficulty = request.args.get("difficulty", "")
    location = request.args.get("location", "")
    treks_query = Trek.query.filter_by(status="Open")
    if difficulty:
        treks_query = treks_query.filter_by(difficulty=difficulty)
    if location:
        treks_query = treks_query.filter(Trek.location.ilike(f"%{location}%"))
    available_treks = treks_query.order_by(Trek.start_date.asc()).all()
    my_bookings = (
        Booking.query.filter_by(user_id=current_user.id, status="Booked")
        .order_by(Booking.booking_date.desc())
        .all()
    )
    locations = [row[0] for row in db.session.query(Trek.location).distinct()]
    return render_template(
        "user/dashboard.html",
        treks=available_treks,
        my_bookings=my_bookings,
        locations=locations,
        selected_difficulty=difficulty,
        selected_location=location,
    )

@user_bp.route("/trek/<int:trek_id>")
@login_required
def trek_detail(trek_id):
    check_trekker()
    trek = Trek.query.get_or_404(trek_id)
    already_booked = Booking.query.filter_by(
        user_id=current_user.id, trek_id=trek.id, status="Booked"
    ).first() is not None
    return render_template("user/trek_detail.html", trek=trek, already_booked=already_booked)

@user_bp.route("/trek/<int:trek_id>/book", methods=["POST"])
@login_required
def book_trek(trek_id):
    check_trekker()
    trek = Trek.query.get_or_404(trek_id)
    if trek.status != "Open":
        flash("This trek is not open for booking.", "danger")
        return redirect(url_for("user.trek_detail", trek_id=trek.id))
    if trek.available_slots <= 0:
        flash("Sorry, this trek is fully booked.", "danger")
        return redirect(url_for("user.trek_detail", trek_id=trek.id))
    existing = Booking.query.filter_by(
        user_id=current_user.id, trek_id=trek.id, status="Booked"
    ).first()
    if existing:
        flash("You have already booked this trek.", "warning")
        return redirect(url_for("user.trek_detail", trek_id=trek.id))
    new_booking = Booking(user_id=current_user.id, trek_id=trek.id, status="Booked")
    trek.available_slots -= 1
    db.session.add(new_booking)
    db.session.commit()
    flash("Trek booked successfully!", "success")
    return redirect(url_for("user.bookings"))

@user_bp.route("/bookings")
@login_required
def bookings():
    check_trekker()
    my_bookings = (
        Booking.query.filter_by(user_id=current_user.id)
        .filter(Booking.status.in_(["Booked", "Cancelled"]))
        .order_by(Booking.booking_date.desc())
        .all()
    )
    return render_template("user/bookings.html", bookings=my_bookings)

@user_bp.route("/bookings/<int:booking_id>/cancel", methods=["POST"])
@login_required
def cancel_booking(booking_id):
    check_trekker()
    booking = Booking.query.filter_by(id=booking_id, user_id=current_user.id).first_or_404()
    if booking.status != "Booked":
        flash("This booking cannot be cancelled.", "danger")
        return redirect(url_for("user.bookings"))
    booking.status = "Cancelled"
    booking.trek.available_slots += 1  
    db.session.commit()

    flash("Booking cancelled.", "info")
    return redirect(url_for("user.bookings"))

@user_bp.route("/history")
@login_required
def history():
    check_trekker()
    completed = (
        Booking.query.filter_by(user_id=current_user.id, status="Completed")
        .order_by(Booking.booking_date.desc())
        .all()
    )
    return render_template("user/history.html", bookings=completed)

@user_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    check_trekker()
    if request.method == "POST":
        current_user.name = request.form.get("name", "").strip()
        current_user.contact = request.form.get("contact", "").strip()
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("user.profile"))
    return render_template("user/profile.html")