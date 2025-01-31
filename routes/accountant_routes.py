# accountant_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Fee, Student
from function import create_fees_for_grade, update_fee, delete_fee  

accountant_blueprint = Blueprint("accountant", __name__)

""" -------------------------------------------------------------------------------------------------- """  

@accountant_blueprint.route("/billBunch", methods=["GET", "POST"])
@login_required
def billBunch():
    if request.method == "POST":
        grade = request.form.get("grade")
        fee_details = {
            "tuition": request.form.get("price1"),
            "lunch": request.form.get("price2"),
            "transport": request.form.get("price3")
        }
        due_date = request.form.get("dueDate")

        if not grade or not due_date or not any(fee_details.values()):
            flash("All fields are required.", "danger")
            return redirect(url_for("accountant.billBunch"))

        # Call function without author (it uses current_user)
        success, message = create_fees_for_grade(grade, fee_details, due_date)

        if success:
            flash("Fees created successfully!", "success")
        else:
            flash(f"Error: {message}", "danger")

    return render_template("billBunch.html")

""" -------------------------------------------------------------------------------------------------- """  

# accountant_routes.py
@accountant_blueprint.route("/viewBilling", methods=["GET"])
@login_required
def viewBilling():
    # Fetch query parameters for filtering (if any)
    student_name = request.args.get("student_name")
    grade = request.args.get("grade")
    status = request.args.get("status")

    # Start with a base query
    fees_query = Fee.query.join(Student)  # Join with Student to filter by student attributes

    # Apply filters if provided
    if student_name and student_name.strip():
        fees_query = fees_query.filter(Student.name.ilike(f"%{student_name.strip()}%"))
    if grade and grade.strip():
        fees_query = fees_query.filter(Student.grade == grade.strip())
    if status and status.strip():
        fees_query = fees_query.filter(Fee.status == status.strip())


    # Fetch the filtered fees
    fees = fees_query.all()
    print("Fees fetched:", fees)  # Debug print

    # Render the template with the fees
    return render_template("viewBilling.html", fees=fees)

@accountant_blueprint.route("/update_fee/<int:fee_id>", methods=["POST"])
@login_required
def update_fee_route(fee_id):
    data = request.json
    return update_fee(fee_id, data)

@accountant_blueprint.route("/delete_fee/<int:fee_id>", methods=["DELETE"])
@login_required
def delete_fee_route(fee_id):
    return delete_fee(fee_id)