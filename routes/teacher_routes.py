from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from models import db, User, Student  # Import the necessary models
# from function import create_user, create_student, process_billing, search_parent_student, calculate_outstanding_balance
from function import create_student, search_parent_student
from sqlalchemy.orm import joinedload

teacher_blueprint = Blueprint("teacher", __name__)

""" -------------------------------------------------------------------------------------------------- """  

#add student
@teacher_blueprint.route("/addStudent", methods=["GET", "POST"])
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

@teacher_blueprint.route("/feeOverview")
@login_required
def feeOverview():
    
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
    
    return render_template("feeOverview.html", students=students, search_name=search_name, filter_grade=filter_grade)