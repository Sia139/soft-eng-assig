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
        
        try:
            due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
        except ValueError:
            return False, "Invalid date format. Please use YYYY-MM-DD."

        # Process each student
        for student in students:
            fees_for_student = []
            total_amount = Decimal('0.00')

            # Create fees for this student
            for fee_type, amount in fee_details.items():
                if fee_type == "transport" and not student.transport:
                    continue

                if amount:
                    try:
                        amount_decimal = Decimal(amount)
                        total_amount += amount_decimal
                    except ValueError:
                        return False, f"Invalid amount for {fee_type}."

                    fee = Fee(
                        student_id=student.id,
                        due_date=due_date,
                        amount=amount_decimal,
                        fee_type=fee_type,
                        status='unpaid',
                    )
                    fees_for_student.append(fee)

            # If we have fees for this student, create them and an invoice
            if fees_for_student:
                # Create invoice first
                invoice = Invoice(
                    total_amount=total_amount
                )
                db.session.add(invoice)
                db.session.flush()  # This assigns an ID to the invoice

                # Now link the fees to the invoice
                for fee in fees_for_student:
                    fee.invoice_id = invoice.id
                    db.session.add(fee)

        db.session.commit()
        return True, f"Fees and invoices created successfully for {len(students)} students."

    except Exception as e:
        db.session.rollback()
        return False, f"Error creating fees and invoices: {str(e)}"

""" -------------------------------------------------------------------------------------------------- """

def view_billing(student_name=None, grade=None, status=None, start_date=None, end_date=None):
    """
    Generic function to view and filter billing information
    Returns filtered fees query that can be used by any route
    """
    # Start with a base query
    fees_query = Fee.query.join(Student)

    # Apply filters if provided
    if student_name and student_name.strip():
        fees_query = fees_query.filter(Student.name.ilike(f"%{student_name.strip()}%"))
    if grade and grade.strip():
        fees_query = fees_query.filter(Student.grade == grade.strip())
    if status and status.strip():
        fees_query = fees_query.filter(Fee.status == status.strip())

    # Add date range filter by due_date
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            fees_query = fees_query.filter(Fee.due_date >= start_date)
        except ValueError:
            return None, "Invalid start date format"

    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            fees_query = fees_query.filter(Fee.due_date <= end_date)
        except ValueError:
            return None, "Invalid end date format"

    try:
        fees = fees_query.all()
        return fees, None  # Return fees and no error
    except Exception as e:
        return None, str(e)  # Return no fees and error message

def update_fee(fee_id, data):
    """
    Generic function to update fee information
    Returns tuple of (success, message)
    """
    try:
        fee = Fee.query.get_or_404(fee_id)
        
        # Update fields with validation
        if 'fee_type' in data:
            fee.fee_type = data['fee_type']
        if 'amount' in data:
            try:
                fee.amount = Decimal(str(data['amount']))
            except (ValueError, TypeError):
                return False, "Invalid amount format"
        if 'due_date' in data:
            try:
                fee.due_date = datetime.strptime(data['due_date'], "%Y-%m-%d").date()
            except ValueError:
                return False, "Invalid date format"
        if 'status' in data:
            if data['status'] not in ['paid', 'unpaid']:
                return False, "Invalid status"
            fee.status = data['status']

        db.session.commit()
        return True, "Fee updated successfully"

    except Exception as e:
        db.session.rollback()
        return False, str(e)

def delete_fee(fee_id):
    """
    Generic function to delete a fee
    Returns tuple of (success, message)
    """
    try:
        fee = Fee.query.get_or_404(fee_id)
        db.session.delete(fee)
        db.session.commit()
        return True, "Fee deleted successfully"
    except Exception as e:
        db.session.rollback()
        return False, str(e)
    

def create_single_fee(student_id, fee_type, amount, due_date):
    """
    Create a single fee and its associated invoice for a student
    """
    try:
        # Validate student exists
        student = Student.query.get(student_id)
        if not student:
            return False, "Student not found"
            
        # Convert amount to Decimal
        try:
            amount_decimal = Decimal(str(amount))
            if amount_decimal <= 0:
                return False, "Amount must be greater than zero"
        except:
            return False, "Invalid amount format"
            
        # Convert due date string to date object
        try:
            due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
        except ValueError:
            return False, "Invalid date format. Please use YYYY-MM-DD"
            
        # Create invoice first
        invoice = Invoice(
            total_amount=amount_decimal
        )
        db.session.add(invoice)
        db.session.flush()  # This assigns an ID to the invoice
        
        # Create the fee
        fee = Fee(
            student_id=student.id,
            fee_type=fee_type,
            amount=amount_decimal,
            due_date=due_date,
            status='unpaid',
            invoice_id=invoice.id
        )
        
        db.session.add(fee)
        db.session.commit()
        
        return True, f"Fee created successfully for {student.name}"
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error creating fee: {str(e)}"
    
    
def get_invoice_details(invoice_id):
    
    invoice = Invoice.query.options(
        joinedload(Invoice.fees).joinedload(Fee.student)
    ).get(invoice_id)
    
    # if not invoice:
    #     return None, "Invoice not found"
        # return redirect(url_for("accountant.viewInvoice"))
     
    return invoice