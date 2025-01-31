# function.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import *
from werkzeug.security import generate_password_hash
from sqlalchemy.orm import joinedload
from datetime import datetime
from decimal import Decimal

""" -------------------------------------------------------------------------------------------------- """  

def create_student():
    # Ensure only teachers or admins can access this route
    if current_user.role not in ["teacher", "admin"]:
        flash("Access denied. Only teachers and admins can add students.", "danger")
        return redirect(url_for("initial page"))

    # if request.method == "POST":

    name = request.form.get("name")
    grade = request.form.get("grade")
    dob = request.form.get("dob")  # Expected in 'YYYY-MM-DD' format
    guardian_id = request.form.get("guardian_id")  # Guardian ID from the hidden input
    transport = request.form.get("transport") == "true"  # Convert to boolean

    # Validate inputs
    if not name or not grade or not dob or not guardian_id:
        flash("All fields are required.", "danger")
        return False
        # return redirect(url_for("teacher.add_student"))
            
    try:
        dob = datetime.strptime(dob, "%Y-%m-%d").date()
        guardian_id = int(guardian_id)
        
    except ValueError:
        flash("Invalid input provided.", "danger")
        # return redirect(url_for("teacher.add_student"))
        return False   
        
   
    # Ensure guardian exists and is a parent
    guardian = User.query.filter_by(id=guardian_id, role="parent").first()
    if not guardian:
        flash("Selected guardian is invalid.", "danger")
        return False
        # return redirect(url_for("teacher.add_student"))
            
    # Create and save the new student
    student = Student(
        name=name,
        grade=grade,
        dob=dob,
        transport=transport,
        user_id=guardian.id,
    )
        
    try:
        db.session.add(student)
        db.session.commit()
        flash(f"Student {name} added successfully!", "success")
        return True
        # return redirect(url_for("teacher.add_student"))
            
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding student: {str(e)}", "danger")
        return False
        # return redirect(url_for("teacher.add_student"))
        
""" -------------------------------------------------------------------------------------------------- """  
 
def search_parent_student(query, role=None):
    """
    General search function for searching parents or students.
    :param query: The search term.
    :param role: The role to search for ("parent" or None for students).
    :return: A list of matching parents or students based on the role.
    """
    if role == "parent":
        # Search for parents based on username
        users = User.query.filter(
            User.role == "parent", 
            User.username.ilike(f"%{query}%")
        ).all()
        
        # Prepare the response with the ID and username of each parent
        users_data = [{"id": user.id, "username": user.username} for user in users]
        
    else:
        # Search for students based on name (if no role specified, assume students)
        students = Student.query.filter(
            Student.name.ilike(f"%{query}%")
        ).all()
        
        # Prepare the response with the ID and name of each student
        users_data = [{"id": student.id, "name": student.name, "grade": student.grade} for student in students]
    
    return users_data 

""" -------------------------------------------------------------------------------------------------- """  

def create_user():
    if current_user.role == "parent":
        return {"status": "error", "message": "Access denied. Parent cannot add user"}

    # Retrieve form data
    username = request.form["username"]
    password = request.form["password"]
    role = request.form["role"]
    email = request.form.get("email")  # Optional email

    # Validate inputs
    if not username or not password or not role:
        return {"status": "error", "message": "Username, Password, and Role are required."}

    # Check if username exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return {"status": "error", "message": "Username already taken. Please choose another."}

    # Create the new user
    new_user = User(
        username=username,
        password=generate_password_hash(password),
        role=role,
        email=email
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return {"status": "success", "message": "User created successfully!"}
        
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": f"An error occurred: {str(e)}"}

""" -------------------------------------------------------------------------------------------------- """

from flask_login import current_user
from models import db, Fee, Student  # Prevent circular imports
from decimal import Decimal

def create_fees_for_grade(grade, fee_details, due_date):
    try:
        students = Student.query.filter_by(grade=grade).all()
        if not students:
            return False, "No students found in this grade."
        
        # Convert due_date string to a date object
        try:
            due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
        except ValueError:
            return False, "Invalid date format. Please use YYYY-MM-DD."

        fees_to_add = []
        for student in students:
            for fee_type, amount in fee_details.items():
                if fee_type == "transport" and not student.transport:
                    # Skip adding transport fee if student does not have transport
                    continue

                if amount:
                    try:
                        amount_decimal = Decimal(amount)
                    except ValueError:
                        return False, f"Invalid amount for {fee_type}."

                    fee = Fee(
                        student_id=student.id,
                        due_date=due_date,
                        amount=amount_decimal,
                        fee_type=fee_type,
                        status='unpaid',
                    )
                    fees_to_add.append(fee)

        db.session.bulk_save_objects(fees_to_add)
        db.session.commit()
        return True, f"Fees created successfully for {len(students)} students."

    except Exception as e:
        db.session.rollback()
        return False, f"Error creating fees: {str(e)}"

