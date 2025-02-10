from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from models import Fee, Invoice, Notification, db, User, Student  # Import the necessary models
# from function import create_user, create_student, process_billing, search_parent_student, calculate_outstanding_balance
from function import create_student, is_action_allowed, search_parent_student
from sqlalchemy.orm import joinedload

teacher_blueprint = Blueprint("teacher", __name__)

""" -------------------------------------------------------------------------------------------------- """  

#add student
@teacher_blueprint.route("/addStudent", methods=["GET", "POST"])
@login_required
def addStudent():
    allowed = is_action_allowed(current_user.role, "add_student")
    print(f"Permission check: {allowed}")
    
    if not allowed:
        return render_template('403.html')
    
    if current_user.role != "teacher":
        return "Access Denied", 403

    if request.method == "POST":
        result = create_student()
        return jsonify(result)
            
    # Get parents for the dropdown search in the form
    return render_template("addStudent.html")

""" -------------------------------------------------------------------------------------------------- """  

#cause of (AJAX)
@teacher_blueprint.route("/searchParents", methods=["GET"])
@login_required
def search_parents_route():
    if current_user.role not in ["teacher", "admin"]:
        return "Access Denied", 403

    query = request.args.get("query", "").lower()
    parents = search_parent_student(query, role="parent")
    return jsonify(parents)

""" -------------------------------------------------------------------------------------------------- """  

@teacher_blueprint.route("/viewStudents")
@login_required
def viewStudents():
    allowed = is_action_allowed(current_user.role, "view_student_details")
    print(f"Permission check: {allowed}")
    
    if not allowed:
        return render_template('403.html')
    
    if current_user.role != "teacher":
        return "Access Denied", 403
    
    search_name = request.args.get("name", "").strip()
    filter_grade = request.args.get("grade", "").strip()
    
    # Filter students based on query parameters
    query = Student.query
    if search_name:
        query = query.filter(Student.name.ilike(f"%{search_name}%"))
    if filter_grade:
        query = query.filter_by(grade=filter_grade)

    students = query.all()

    return render_template('studentDetail.html', students=students, search_name=search_name, filter_grade=filter_grade)

""" -------------------------------------------------------------------------------------------------- """  

# @teacher_blueprint.route("/feeOverview")
# @login_required
# def feeOverview():
    
#     if current_user.role != "teacher":
#         return "Access Denied", 403
    
#     search_name = request.args.get("name", "").strip()
#     filter_grade = request.args.get("grade", "").strip()
    
#     # Filter students based on query parameters
#     query = Student.query
#     if search_name:
#         query = query.filter(Student.name.ilike(f"%{search_name}%"))
#     if filter_grade:
#         query = query.filter_by(grade=filter_grade)

#     students = query.all()
    
#     return render_template("feeOverview.html", students=students, search_name=search_name, filter_grade=filter_grade)

@teacher_blueprint.route("/feeOverview", methods=["GET"])
@login_required
def feeOverview():
    allowed = is_action_allowed(current_user.role, "fee_overview")
    print(f"Permission check: {allowed}")
    
    if not allowed:
        return render_template('403.html')
    
    # Get query parameters
    student_name = request.args.get("name")  # Fixed parameter for student name search
    grade = request.args.get("grade")
    status = request.args.get("status")  # Paid/Unpaid filter
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    # Build the query
    query = Invoice.query.join(Fee).join(Student)

    # Filter by student name
    if student_name:
        query = query.filter(Student.name.ilike(f"%{student_name}%"))

    # Filter by grade
    if grade:
        query = query.filter(Student.grade == grade)

    # Filter by payment status (paid/unpaid)
    if status == "paid":
        query = query.filter(Fee.status == "paid")
    elif status == "unpaid":
        query = query.filter(Fee.status == "unpaid")

    # Date filtering (optional)
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Fee.due_date >= start_date)
        except ValueError:
            flash("Invalid start date format", "error")

    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Fee.due_date <= end_date)
        except ValueError:
            flash("Invalid end date format", "error")

    # Retrieve and sort invoices
    invoices = query.options(
        joinedload(Invoice.fees).joinedload(Fee.student)
    ).order_by(Invoice.id.desc()).all()

    return render_template(
        "feeOverview.html",
        invoices=invoices,
        filter_status=status,
        filter_grade=grade,
        search_name=student_name
    )

""" -------------------------------------------------------------------------------------------------- """  

@teacher_blueprint.route("/send-notification", methods=["POST"])
@login_required
def send_notification():
    if current_user.role != "teacher":
        return "Access Denied", 403

    data = request.json
    parent_username = data.get("parent")
    student_name = data.get("student")
    amount = data.get("amount")

    if not parent_username or not student_name or not amount:
        return jsonify({"success": False, "message": "Invalid data"}), 400

    # Find the parent user
    parent = User.query.filter_by(username=parent_username).first()
    if not parent:
        return jsonify({"success": False, "message": "Parent not found"}), 404

    # Create notification message
    message = f"Reminder: Your child, {student_name}, has an outstanding fee of ${amount}. Please make the payment."

    # Store notification in the database
    new_notification = Notification(user_id=parent.id, message=message)

    try:
        db.session.add(new_notification)
        db.session.commit()
        print("Notification successfully saved!")
        return jsonify({"success": True, "message": "Notification sent successfully!"})
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({"success": False, "message": "Database error"}), 500