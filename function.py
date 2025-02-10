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
        return {"status": "error", "message": "Access denied. Only teachers and admins can add students."}

    name = request.form.get("name")
    grade = request.form.get("grade")
    dob = request.form.get("dob")  # Expected in 'YYYY-MM-DD' format
    guardian_id = request.form.get("guardian_id")  # Guardian ID from the hidden input
    transport = request.form.get("transport") == "true"  # Convert to boolean

    # Validate inputs
    if not name or not grade or not dob or not guardian_id:
        return {"status": "error", "message": "All fields are required."}
            
    try:
        dob = datetime.strptime(dob, "%Y-%m-%d").date()
        guardian_id = int(guardian_id)
        
    except ValueError:
        return {"status": "error", "message": "Invalid input provided."}
   
    # Ensure guardian exists and is a parent
    guardian = User.query.filter_by(id=guardian_id, role="parent").first()
    if not guardian:
        return {"status": "error", "message": "Selected guardian is invalid."}
            
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
        return {"status": "success", "message": f"Student {name} added successfully!"}
            
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": f"Error adding student: {str(e)}"}
        
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

""" -------------------------------------------------------------------------------------------------- """

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

""" -------------------------------------------------------------------------------------------------- """

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

""" -------------------------------------------------------------------------------------------------- """

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
    
""" -------------------------------------------------------------------------------------------------- """
    
def get_invoice_details(invoice_id):
    
    invoice = Invoice.query.options(
        joinedload(Invoice.fees).joinedload(Fee.student)
    ).get(invoice_id)
    
    # if not invoice:
    #     return None, "Invoice not found"
        # return redirect(url_for("accountant.viewInvoice"))
     
    return invoice

""" -------------------------------------------------------------------------------------------------- """

def is_action_allowed(role, function_name):
    permission = RolePermission.query.filter_by(role=role, function_name=function_name).first()
    return permission.is_allowed if permission else False

""" -------------------------------------------------------------------------------------------------- """

# from datetime import date, timedelta
# from flask import current_app

# def check_and_update_invoices():
#     """Check invoices for discount eligibility or penalty application on login."""
#     with current_app.app_context():
#         today = date.today()
#         discount_value = FeeSetting.query.filter_by(detail="discount_amount").first()
#         discount_period = FeeSetting.query.filter_by(detail="discount_period").first()
#         penalty_amount = FeeSetting.query.filter_by(detail="penalty_amount").first()

#         # Ensure FeeSettings are available
#         if not (discount_value and discount_period and penalty_amount):
#             print("Fee settings missing. Skipping adjustment.")
#             return

#         discount_value = discount_value.value
#         discount_period = int(discount_period.value)  # Assuming it's stored as days
#         penalty_amount = penalty_amount.value

#         invoices = Invoice.query.all()

#         for invoice in invoices:
#             if invoice.flag:  # Already discounted or penalized, skip it
#                 continue

#             fees = invoice.fees  # Get all fees related to the invoice

#             if not fees:
#                 continue  # Skip invoices without fees

#             due_dates = [fee.due_date for fee in fees]

#             if not due_dates:
#                 continue  # Skip if there are no due dates

#             earliest_due_date = min(due_dates)  # Safely getting the minimum date

#             if today <= earliest_due_date and today >= earliest_due_date - timedelta(days=discount_period):
#                 # Apply discount only if not already applied
#                 if invoice.discount_amount == 0:
#                     invoice.discount_amount = discount_value
#                     invoice.total_amount -= discount_value
#                     invoice.flag = True  # Mark as processed
#                     print(f"Applied discount of {discount_value} to Invoice {invoice.id}")

#             elif today > earliest_due_date:
#                 # Apply penalty only if not already applied
#                 days_late = (today - earliest_due_date).days
#                 new_penalty = penalty_amount * days_late
#                 if invoice.penalty_amount == 0:
#                     invoice.penalty_amount = new_penalty
#                     invoice.total_amount += new_penalty
#                     invoice.flag = True  # Mark as processed
#                     print(f"Applied penalty of {new_penalty} to Invoice {invoice.id}")

#         db.session.commit()
#         print("Invoice adjustments applied successfully.")

from datetime import date, timedelta
from flask import current_app
from decimal import Decimal
from sqlalchemy.orm import joinedload

def check_and_update_invoices():
    """Check invoices for discount eligibility or penalty application on login."""
    with current_app.app_context():
        today = date.today()

        # Fetch fee settings
        discount_value = FeeSetting.query.filter_by(detail="discount_amount").first()
        discount_period = FeeSetting.query.filter_by(detail="discount_period").first()
        penalty_amount = FeeSetting.query.filter_by(detail="penalty_amount").first()

        # Ensure all FeeSettings are available
        if not all([discount_value, discount_period, penalty_amount]):
            print("Fee settings missing. Skipping adjustment.")
            return

        # Convert values
        discount_value = Decimal(discount_value.value)
        penalty_amount = Decimal(penalty_amount.value)
        
        discount_period = timedelta(days=int(discount_period.value))  # Convert days to timedelta

        # Fetch invoices with related fees
        invoices = Invoice.query.options(joinedload(Invoice.fees)).all()

        for invoice in invoices:

            fees = invoice.fees  # Get all fees related to the invoice
            if not fees:
                continue  # Skip invoices without fees

            due_dates = [fee.due_date for fee in fees if fee.due_date]  # Ensure valid due dates
            create_dates = [fee.create_date for fee in fees if fee.create_date]  # Ensure valid create dates

            if not due_dates or not create_dates:
                continue  # Skip invoices without valid dates

            earliest_due_date = min(due_dates)  # Get the earliest due date safely
            earliest_create_date = min(create_dates)  # Get the earliest create date safely

            print("----------------------------------------------------")
            print(f"earliest_create_date {earliest_create_date}")
            print(f"discount_period {discount_period}")
            print(f"earliest_due_date {earliest_due_date}")
            print(f"today {today}")
            
            # Apply penalty if past due date
            if today > earliest_due_date:
                days_late = (today - earliest_due_date).days
                new_penalty_amount = penalty_amount * Decimal(days_late)
                invoice.penalty_amount = new_penalty_amount
                print(f"Applied penalty of {penalty_amount} to Invoice {invoice.id}")

                
                # days_late = (today - earliest_due_date).days
                # new_penalty = penalty_amount * Decimal(days_late)
                # if invoice.penalty_amount == Decimal("0"):
                #     invoice.penalty_amount = penalty_amount
                #     invoice.total_amount += penalty_amount
                #     # invoice.flag = True  # Mark as processed
                #     print(f"Applied penalty of {penalty_amount} to Invoice {invoice.id}")
            
            # Apply discount if the earliest create date + discount period is before today
            elif earliest_create_date + discount_period > today:
                # if invoice.discount_amount == Decimal("0"):
                    invoice.discount_amount = discount_value
                    # invoice.total_amount -= discount_value
                    print(f"Applied discount of {discount_value} to Invoice {invoice.id}")
                    
        db.session.commit()
        print("Invoice adjustments applied successfully.")