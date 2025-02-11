from flask import Blueprint, render_template, request,  redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, User, Student, Fee, Invoice, RolePermission, FeeSetting
from function import create_fees_for_grade, create_single_fee, view_billing, search_parent_student, create_student, search_parent_student, check_and_update_invoices, is_action_allowed
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
    # route to teacher_blueprint
    return render_template("addStudent.html")

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
    #route to accountant_blueprint
    return render_template("billSingle.html")


"""--------------------------------------------------------------------------------------------------"""

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

"""--------------------------------------------------------------------------------------------------"""

@admin_blueprint.route("/viewInvoice", methods=["GET"])
@login_required
def viewInvoice():
    check_and_update_invoices()
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

"""--------------------------------------------------------------------------------------------------"""

@admin_blueprint.route("/payment_tracking", methods=["GET"])
@login_required
def payment_tracking():
    check_and_update_invoices()
    # Get query parameters
    student_name = request.args.get("name")  # Fixed parameter for student name search
    grade = request.args.get("grade")
    status = request.args.get("status")  # Paid/Unpaid filter


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

    # Retrieve and sort invoices
    invoices = query.options(
        joinedload(Invoice.fees).joinedload(Fee.student)
    ).order_by(Invoice.id.desc()).all()

    return render_template(
        "paymentTracking.html",
        invoices=invoices,
        filter_status=status,
        filter_grade=grade,
        search_name=student_name
    )

"""--------------------------------------------------------------------------------------------------"""

@admin_blueprint.route('/rolePermission', methods=['GET', 'POST'])
@login_required
def role_permission():
    roles = ["accountant", "parent", "teacher"]
    
    if request.method == 'POST':
        data = request.get_json()
        role = data.get("role")
        updated_permissions = data.get("permissions")

        if not role or not updated_permissions:
            return jsonify({"success": False, "message": "Invalid request data"}), 400

        # Update database
        for function_name, is_allowed in updated_permissions.items():
            permission = RolePermission.query.filter_by(role=role, function_name=function_name).first()
            if permission:
                permission.is_allowed = is_allowed
            else:
                new_permission = RolePermission(role=role, function_name=function_name, is_allowed=is_allowed)
                db.session.add(new_permission)

        db.session.commit()
        return jsonify({"success": True})

    # Fetch role (default to accountant)
    selected_role = request.args.get("role", "accountant")
    
    # Fetch permissions for the selected role
    permissions = RolePermission.query.filter_by(role=selected_role).all()
    
    return render_template("rolePermission.html", roles=roles, selected_role=selected_role, permissions=permissions)

"""--------------------------------------------------------------------------------------------------"""

@admin_blueprint.route('/fee_structure', methods=['GET', 'POST'])
@login_required
def fee_structure():
    if current_user.role != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized access."}), 403

    # Fetch all settings and convert them into a dictionary
    settings = FeeSetting.query.all()
    fee_dict = {setting.detail: setting.value for setting in settings}

    # Ensure required settings exist
    required_settings = ['penalty_amount', 'discount_period', 'discount_amount']
    for setting in required_settings:
        if setting not in fee_dict:
            new_setting = FeeSetting(detail=setting, value=0)  # Default value 0.0
            db.session.add(new_setting)
            fee_dict[setting] = 0  # Add to dictionary as well

    db.session.commit()  # Commit new settings if needed

    if request.method == 'POST':
        try:
            if 'penalty' in request.form:
                fee_dict['penalty_amount'] = float(request.form['penalty'])
            if 'period' in request.form:
                fee_dict['discount_period'] = int(request.form['period'])
            if 'discount' in request.form:
                fee_dict['discount_amount'] = float(request.form['discount'])

            # Update the database values
            for setting in settings:
                setting.value = fee_dict.get(setting.detail, setting.value)

            db.session.commit()
            return jsonify({"status": "success", "message": "Fee structure updated successfully!"})

        except ValueError:
            return jsonify({"status": "error", "message": "Invalid input! Please enter numeric values."}), 400

    return render_template("feeStructure.html", fee_dict=fee_dict)

"""--------------------------------------------------------------------------------------------------"""

@admin_blueprint.route('/sys_config', methods=['GET', 'POST'])
@login_required
def sys_config():
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data received'}), 400  # Handle missing data
            
            action = data.get('action')
            if not action:
                return jsonify({'error': 'No action specified'}), 400  # Handle missing action
            
            print(f"Received action: {action}")  # Debugging output in console

            # if not is_action_allowed(current_user.role, "update_permissions"):
            #     return jsonify({'error': 'Unauthorized'}), 403

            if action == 'pause':
                permission = RolePermission.query.get(1)
                if permission:
                    permission.is_allowed = False
            elif action == 'play':
                RolePermission.query.update({RolePermission.is_allowed: True})
            elif action == 'stop':
                RolePermission.query.filter(RolePermission.role != 'admin').update({RolePermission.is_allowed: False})
            else:
                return jsonify({'error': 'Invalid action'}), 400  # Handle unexpected actions

            db.session.commit()
            return jsonify({'message': f'Action "{action}" executed successfully'})

        except Exception as e:
            print(f"Error: {e}")  # Log error in Flask console
            return jsonify({'error': 'Server error'}), 500  # Handle unexpected server errors

    return render_template("sysConfig.html")
