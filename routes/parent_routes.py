from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import Fee, Student, db
# from function import view_fee_details, process_payment

parent_blueprint = Blueprint("parent", __name__)

@parent_blueprint.route("/dashboard")
@login_required
def parent_dashboard():
    return render_template("dashboard.html", role="Parent")
