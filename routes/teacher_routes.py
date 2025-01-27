from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from models import db, User, Student  # Import the necessary models
# from function import create_user, create_student, process_billing, search_parent_student, calculate_outstanding_balance
from function import create_student, search_parent_student
from sqlalchemy.orm import joinedload

teacher_blueprint = Blueprint("teacher", __name__)

""" -------------------------------------------------------------------------------------------------- """  

#add student
@teacher_blueprint.route("/add-student", methods=["GET", "POST"])
@login_required
def addStudent():
    if current_user.role != "teacher":
        return "Access Denied", 403

    if request.method == "POST":
        create_student()
            
    # Get parents for the dropdown search in the form
    parents = search_parents_route()
    return render_template("addStudent.html")

""" -------------------------------------------------------------------------------------------------- """  

#cause of (AJAX)
@teacher_blueprint.route("/search-parents", methods=["GET"])
@login_required
def search_parents_route():
    # Ensure the user has the right role (admin or teacher)
    if current_user.role not in ["teacher", "admin"]:
        return "Access Denied", 403

    query = request.args.get("query", "").lower()  # Get the search query

    # Call search_parents from function.py
    parents = search_parent_student(query, role="parent")

    return jsonify(parents)

""" -------------------------------------------------------------------------------------------------- """  

# @teacher_blueprint.route("/view-students")
# @login_required
# def viewStudents():
#     from datetime import datetime
#     students = Student.query.options(joinedload(Student.guardian)).all()
#     now = datetime.now()
#     return render_template('studentDetail.html', students=students, now=now)

""" -------------------------------------------------------------------------------------------------- """  

@teacher_blueprint.route("/view-students")
@login_required
def viewStudents():
    if current_user.role != "teacher":
        return "Access Denied", 403
    
    search_name = request.args.get("name", "")
    filter_grade = request.args.get("grade", "")
    
    # Filter students based on query parameters
    query = Student.query.options(joinedload(Student.fees))
    if search_name:
        query = query.filter(Student.name.ilike(f"%{search_name}%"))
    if filter_grade:
        query = query.filter_by(grade=filter_grade)

    students = query.all()

    return render_template('studentDetail.html', students=students, search_name=search_name, filter_grade=filter_grade)

""" -------------------------------------------------------------------------------------------------- """  