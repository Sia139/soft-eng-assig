from flask import Blueprint, render_template, request,  redirect, url_for, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, User, Student, Fee, Invoice
from function import create_fees_for_grade, create_single_fee, view_billing, search_parent_student, create_student, search_parent_student
# from function import create_user, create_student, process_billing, search_parent_student, calculate_outstanding_balance
from sqlalchemy.orm import joinedload
from datetime import datetime

admin_blueprint = Blueprint("admin", __name__)

""" -------------------------------------------------------------------------------------------------- """  

@admin_blueprint.route("/createUser", methods=["GET", "POST"])
@login_required
def createUser():
    if current_user.role != "admin":
        return "Access Denied", 403
    
    if request.method == "POST":
        from function import create_user
        result = create_user()
        return jsonify(result)
    
    return render_template("addAccount.html")

""" -------------------------------------------------------------------------------------------------- """  

@admin_blueprint.route("/manageAccount", methods=["GET", "POST"])
@login_required
def manageAccount():
    from datetime import datetime
    users = User.query.all()
    now = datetime.now()
    # Get search parameter with empty string as default
    search = request.args.get('search', '')
    role = request.args.get('role', '')
    return render_template("manageAccount.html", users=users, now=now, search=search, role=role)

""" -------------------------------------------------------------------------------------------------- """  

@admin_blueprint.route("/update_user_role", methods=["GET", "POST"])
@login_required
def update_user_role():
        
    data = request.get_json()
    user_id = data.get('user_id')
    new_role = data.get('new_role')
    
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Don't allow updating the last admin
        if user.role == 'admin' and User.query.filter_by(role='admin').count() <= 1:
            return jsonify({
                'success': False, 
                'message': 'Cannot make change of the last admin user'
            }), 400
            
        # Don't allow self role update
        if user.id == current_user.id:
            return jsonify({
                'success': False, 
                'message': 'Cannot update your own role'
            }), 400
            
        user.role = new_role
        db.session.commit()
        return jsonify({'success': True}), 200
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

""" -------------------------------------------------------------------------------------------------- """  

@admin_blueprint.route("/delete_user", methods=['POST'])
@login_required
def delete_user():
    if current_user.role != "admin":
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    try:
        data = request.get_json()
        if not data or 'user_id' not in data:
            return jsonify({'success': False, 'message': 'No user ID provided'}), 400
            
        user_id = data.get('user_id')
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
            
        # Don't allow deleting the last admin
        if user.role == 'admin' and User.query.filter_by(role='admin').count() <= 1:
            return jsonify({
                'success': False, 
                'message': 'Cannot delete the last admin user'
            }), 400
            
        # Don't allow self-deletion
        if user.id == current_user.id:
            return jsonify({
                'success': False, 
                'message': 'Cannot delete your own account'
            }), 400
            
        # Delete associated students if it's a parent
        if user.role == 'parent':
            Student.query.filter_by(user_id=user.id).delete()
            
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting user: {str(e)}'
        }), 500

"""--------------------------------------------------------------------------------------------------"""

#add student
@admin_blueprint.route("/addStudent", methods=["GET", "POST"])
@login_required
def addStudent():
    if current_user.role != "admin":
        return "Access Denied", 403

    if request.method == "POST":
        create_student()
            
    # Get parents for the dropdown search in the form
    parents = search_parents_route()
    return render_template("addStudent.html")

#cause of (AJAX)
@admin_blueprint.route("/searchParents", methods=["GET"])
@login_required
def search_parents_route():
    if current_user.role not in ["teacher", "admin"]:
        return "Access Denied", 403

    query = request.args.get("query", "").lower()
    parents = search_parent_student(query, role="parent")
    return jsonify(parents)

""" -------------------------------------------------------------------------------------------------- """  

@admin_blueprint.route("/viewStudents")
@login_required
def viewStudents():
    if current_user.role != "admin":
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

@admin_blueprint.route("/billBunch", methods=["GET", "POST"])
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
            return jsonify({
                "status": "error",
                "message": "All fields are required."
            }), 400

        # Call function without author (it uses current_user)
        success, message = create_fees_for_grade(grade, fee_details, due_date)

        if success:
            return jsonify({
                "status": "success",
                "message": "Fees created successfully!"
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": f"Error: {message}"
            }), 400

    return render_template("billBunch.html")

""" -------------------------------------------------------------------------------------------------- """  

@admin_blueprint.route("/billSingle", methods=["GET", "POST"])
@login_required
def billSingle():
    if request.method == "POST":
        student_id = request.form.get("student_id")
        fee_type = request.form.get("details")
        amount = request.form.get("price")
        due_date = request.form.get("due_date")
        
        if not all([student_id, fee_type, amount, due_date]):
            return jsonify({"status": "error", "message": "All fields are required"}), 400
            
        try:
            # Create a single fee with invoice
            success, message = create_single_fee(student_id, fee_type, amount, due_date)
            
            if success:
                return jsonify({"status": "success", "message": message}), 200
            return jsonify({"status": "error", "message": message}), 400
            
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
            
    return render_template("billSingle.html")

#cause of (AJAX)
@admin_blueprint.route("/search-students", methods=["GET"])
@login_required
def search_students_route():
    if current_user.role not in ["teacher", "admin", "accountant"]:
        return "Access Denied", 403

    query = request.args.get("query", "").lower()
    students = search_parent_student(query)  # No role parameter means search for students
    return jsonify(students)

@admin_blueprint.route("/viewBilling", methods=["GET"])
@login_required
def viewBilling():
    # Get query parameters
    student_name = request.args.get("student_name")
    grade = request.args.get("grade")
    status = request.args.get("status")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    # Use the generic view_billing function
    fees, error = view_billing(student_name, grade, status, start_date, end_date)
    
    if error:
        fees = []
        return jsonify({"error": error}), 400

    return render_template("viewBilling.html", fees=fees)

@admin_blueprint.route("/viewInvoice", methods=["GET"])
@login_required
def viewInvoice():
    # Get query parameters
    student_name = request.args.get("student_name")
    grade = request.args.get("grade")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    # Build the query
    query = Invoice.query.join(Fee).join(Student)

    if student_name:
        query = query.filter(Student.name.ilike(f"%{student_name}%"))
    if grade:
        query = query.filter(Student.grade == grade)
    
    # Add date filtering based on Fee's due_date
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Fee.due_date >= start_date)
        except ValueError:
            return jsonify("Invalid start date format", "error"), 400
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Fee.due_date <= end_date)
        except ValueError:
            return jsonify("Invalid end date format", "error"), 400

    # Get the invoices with related data and order by id
    invoices = query.options(
        joinedload(Invoice.fees).joinedload(Fee.student)
    ).order_by(Invoice.id.desc()).all()
    
    # Calculate flag status for each invoice
    # for invoice in invoices:
    #     invoice.flag = False
    #     for fee in invoice.fees:
    #         if fee.due_date.date() < datetime.now().date() and fee.status == 'unpaid':
    #             invoice.flag = True
    #             break

    return render_template("viewInvoice.html", invoices=invoices)
