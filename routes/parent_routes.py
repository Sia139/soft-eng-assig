from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import Fee, Student, db
# from function import view_fee_details, process_payment

parent_blueprint = Blueprint("parent", __name__)

@parent_blueprint.route("/dashboard")
@login_required
def parent_dashboard():
    students = Student.query.filter_by(user_id=current_user.id).all()
    student_fees = []
    for student in students:
        fees = Fee.query.filter_by(student_id=student.id, status='unpaid').all()
        for fee in fees:
            student_fees.append({
                'student': student,
                'overdue': fee.amount,  # Assuming 'overdue' means unpaid amount
                'due_date': fee.due_date
            })
    return render_template("dashboard.html", role="Parent", student_fees=student_fees)

""" -------------------------------------------------------------------------------------------------- """  

@parent_blueprint.route("/notification")
@login_required
def notification():
    return render_template("notifications.html", role="Parent")