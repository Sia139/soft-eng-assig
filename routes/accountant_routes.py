from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models import db, User, Student  # Import the necessary models

# from function import create_user, create_student, process_billing, search_parent_student, calculate_outstanding_balance

accountant_blueprint = Blueprint("accountant", __name__)

@accountant_blueprint.route("/dashboard")
@login_required
def accountant_dashboard():
    return render_template("dashboard.html", role="Accountant")