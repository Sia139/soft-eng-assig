from flask import Blueprint, render_template, request,  redirect, url_for, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, User, Student, Fee, Payment
# from function import create_user, create_student, process_billing, search_parent_student, calculate_outstanding_balance
from sqlalchemy.orm import joinedload

admin_blueprint = Blueprint("admin", __name__)

@admin_blueprint.route("/manage-account")
@login_required
# def admin_dashboard():
def manageAccount():
    if current_user.role != "admin":
        return "Access Denied", 403

    # Fetch all users and calculate totals
    users = User.query.all()
    total_users = len(users)  # Count total users
    total_payments = Payment.query.count()  # Count total payments

    return render_template( "manageAccount.html", role="Admin" )
