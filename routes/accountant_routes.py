# accountant_routes.py
from flask import Blueprint, abort, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Fee, Student, Invoice
from function import create_fees_for_grade, is_action_allowed, update_fee, delete_fee, view_billing, search_parent_student, create_single_fee, get_invoice_details, check_and_update_invoices
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import joinedload

accountant_blueprint = Blueprint("accountant", __name__)

""" -------------------------------------------------------------------------------------------------- """  

@accountant_blueprint.route("/billBunch", methods=["GET", "POST"])
@login_required
def billBunch():
    allowed = is_action_allowed(current_user.role, "fee_management")
    print(f"Permission check: {allowed}")
    
    if not allowed:
        return abort(403)
    
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

@accountant_blueprint.route("/billSingle", methods=["GET", "POST"])
@login_required
def billSingle():
    allowed = is_action_allowed(current_user.role, "fee_management")
    print(f"Permission check: {allowed}")
    
    if not allowed:
        return abort(403)
    
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
@accountant_blueprint.route("/search-students", methods=["GET"])
@login_required
def search_students_route():
    if current_user.role not in ["teacher", "admin", "accountant"]:
        return "Access Denied", 403

    query = request.args.get("query", "").lower()
    students = search_parent_student(query)  # No role parameter means search for students
    return jsonify(students)

""" -------------------------------------------------------------------------------------------------- """  

@accountant_blueprint.route("/viewBilling", methods=["GET"])
@login_required
def viewBilling():
    allowed = is_action_allowed(current_user.role, "fee_management")
    print(f"Permission check: {allowed}")
    
    if not allowed:
        return abort(403)
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

""" -------------------------------------------------------------------------------------------------- """

@accountant_blueprint.route("/update_fee/<int:fee_id>", methods=["POST"])
@login_required
def update_fee_route(fee_id):
    if not request.is_json:
        return jsonify({"message": "Invalid request format"}), 400

    success, message = update_fee(fee_id, request.json)
    
    if success:
        return jsonify({"message": message}), 200
    return jsonify({"message": f"Error updating fee: {message}"}), 400

""" -------------------------------------------------------------------------------------------------- """

@accountant_blueprint.route("/delete_fee/<int:fee_id>", methods=["DELETE"])
@login_required
def delete_fee_route(fee_id):
    success, message = delete_fee(fee_id)
    
    if success:
        return jsonify({"message": message}), 200
    return jsonify({"message": f"Error deleting fee: {message}"}), 400

""" -------------------------------------------------------------------------------------------------- """

@accountant_blueprint.route("/viewInvoice", methods=["GET"])
@login_required
def viewInvoice():
    check_and_update_invoices()
    allowed = is_action_allowed(current_user.role, "fee_management")
    print(f"Permission check: {allowed}")
    
    if not allowed:
        return abort(403)
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
            flash("Invalid start date format", "error")
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Fee.due_date <= end_date)
        except ValueError:
            flash("Invalid end date format", "error")

    # Get the invoices with related data and order by id
    invoices = query.options(
        joinedload(Invoice.fees).joinedload(Fee.student)
    ).order_by(Invoice.id.desc()).all()
    
    ### Calculate flag status for each invoice ###
    # for invoice in invoices:
    #     invoice.flag = False
    #     for fee in invoice.fees:
    #         if fee.due_date.date() < datetime.now().date() and fee.status == 'unpaid':
    #             invoice.flag = True
    #             break

    return render_template("viewInvoice.html", invoices=invoices)

""" -------------------------------------------------------------------------------------------------- """

# @accountant_blueprint.route("/preview_fees/<grade>", methods=["POST"])
# @login_required
# def preview_fees(grade):
#     try:
#         # Get students in the specified grade
#         students = Student.query.filter_by(grade=grade).all()
        
#         if not students:
#             return jsonify({"error": "No students found in this grade"}), 404
            
#         # Format student data for preview
#         students_data = [{
#             "name": student.name,
#             "transport": student.transport
#         } for student in students]
        
#         return jsonify({"students": students_data})
        
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

""" -------------------------------------------------------------------------------------------------- """

@accountant_blueprint.route("/fee_preview", methods=["GET"])
@login_required
def fee_preview():
    grade = request.args.get('grade')
    tuition = request.args.get('tuition', '0')
    lunch = request.args.get('lunch', '0')
    transport = request.args.get('transport', '0')
    
    tuition_float = float(tuition)
    lunch_float = float(lunch)
    transport_float = float(transport)
    
    # Get students in the specified grade
    students = Student.query.filter_by(grade=grade).all()
    
    # Calculate preview data
    preview_data = []
    for student in students:
        total = (
            (transport_float if student.transport else 0) +
            tuition_float +
            lunch_float
        )
        
        preview_data.append({
            'name': student.name,
            'grade': grade,
            'tuition': f"{tuition_float:.2f}",
            'lunch': f"{lunch_float:.2f}",
            'transport': f"{transport_float:.2f}" if student.transport else '0.00',
            'total': f"{total:.2f}"
        })
    
    return render_template('feePreview.html', 
                         preview_data=preview_data, 
                         grade=grade)
    
""" -------------------------------------------------------------------------------------------------- """

@accountant_blueprint.route("/invoice_Details/<int:invoice_id>", methods=["GET"])
@login_required
def invoice_details(invoice_id):
    invoice = get_invoice_details(invoice_id)  # Use the renamed function
    
    # if error:
    #     flash(error, "danger")
    
    return render_template('invoiceDetail.html', invoice=invoice)

""" -------------------------------------------------------------------------------------------------- """

@accountant_blueprint.route("/single_fee_preview", methods=["GET"])
@login_required
def single_fee_preview():
    student_id = request.args.get('student_id')
    details = request.args.get('details')
    price = request.args.get('price', '0')
    
    # Get student information
    student = Student.query.get(student_id)
    if not student:
        return jsonify({
            "status": "error",
            "message": "Student not found"
        }), 404
    
    price_float = float(price)
    
    return render_template('singleFeePreview.html', 
                         student=student,
                         details=details,
                         price=f"{price_float:.2f}")
    
    
@accountant_blueprint.route("/payment_tracking", methods=["GET"])
@login_required
def payment_tracking():
    check_and_update_invoices()
    allowed = is_action_allowed(current_user.role, "payment_tracking")
    print(f"Permission check: {allowed}")
    
    if not allowed:
        return abort(403)
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

@accountant_blueprint.route("/toggle_invoice_flag/<int:invoice_id>", methods=["POST"])
@login_required
def toggle_invoice_flag(invoice_id):
    try:
        invoice = Invoice.query.get_or_404(invoice_id)
        invoice.flag = not invoice.flag  # Set flag to True when clicked
        db.session.commit()
        return jsonify({"status": "success"}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

# @accountant_blueprint.route("/toggle_invoice_flag/<int:invoice_id>", methods=["POST"])
# @login_required
# def toggle_invoice_flag_route(invoice_id):
#     """
#     Route to toggle invoice flag.
#     """
#     response, status_code = toggle_invoice_flag(invoice_id)
#     return jsonify(response), status_code