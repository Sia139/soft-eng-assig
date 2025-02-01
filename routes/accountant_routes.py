# accountant_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Fee, Student, Invoice
from function import create_fees_for_grade, update_fee, delete_fee, view_billing
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import joinedload

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
    # Get query parameters
    student_name = request.args.get("student_name")
    grade = request.args.get("grade")
    status = request.args.get("status")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    # Use the generic view_billing function
    fees, error = view_billing(student_name, grade, status, start_date, end_date)
    
    if error:
        flash(error, "error")
        fees = []

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

@accountant_blueprint.route("/delete_fee/<int:fee_id>", methods=["DELETE"])
@login_required
def delete_fee_route(fee_id):
    success, message = delete_fee(fee_id)
    
    if success:
        return jsonify({"message": message}), 200
    return jsonify({"message": f"Error deleting fee: {message}"}), 400

@accountant_blueprint.route("/viewInvoice", methods=["GET"])
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
    
    # Calculate flag status for each invoice
    for invoice in invoices:
        invoice.flag = False
        for fee in invoice.fees:
            if fee.due_date.date() < datetime.now().date() and fee.status == 'unpaid':
                invoice.flag = True
                break

    return render_template("viewInvoice.html", invoices=invoices)

@accountant_blueprint.route("/download_invoice/<int:invoice_id>")
@login_required
def download_invoice(invoice_id):
    # Implement invoice download functionality
    # This could generate a PDF or Excel file of the invoice
    pass

@accountant_blueprint.route("/preview_fees/<grade>", methods=["POST"])
@login_required
def preview_fees(grade):
    try:
        # Get students in the specified grade
        students = Student.query.filter_by(grade=grade).all()
        
        if not students:
            return jsonify({"error": "No students found in this grade"}), 404
            
        # Format student data for preview
        students_data = [{
            "name": student.name,
            "transport": student.transport
        } for student in students]
        
        return jsonify({"students": students_data})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@accountant_blueprint.route("/fee_preview", methods=["GET"])
@login_required
def fee_preview():
    grade = request.args.get('grade')
    tuition = request.args.get('tuition', '0')
    lunch = request.args.get('lunch', '0')
    transport = request.args.get('transport', '0')
    
    # Get students in the specified grade
    students = Student.query.filter_by(grade=grade).all()
    
    # Calculate preview data
    preview_data = []
    for student in students:
        total = (
            float(transport) if student.transport else 0 +
            float(tuition) +
            float(lunch)
        )
        
        preview_data.append({
            'name': student.name,
            'grade': grade,
            'tuition': tuition,
            'lunch': lunch,
            'transport': transport if student.transport else '0.00',
            'total': f"{total:.2f}"
        })
    
    return render_template('feePreview.html', 
                         preview_data=preview_data, 
                         grade=grade)