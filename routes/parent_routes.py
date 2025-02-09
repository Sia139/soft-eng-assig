from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models import Fee, Student, Payment, Invoice, User, db
from datetime import datetime
from sqlalchemy.sql import func, and_
from function import get_invoice_details
# from function import view_fee_details, process_payment

parent_blueprint = Blueprint("parent", __name__)

@parent_blueprint.route("/dashboard")
@login_required
def parent_dashboard():
    students = Student.query.filter_by(user_id=current_user.id).all()
    student_fees = []
    for student in students:
        fees = Fee.query.filter_by(student_id=student.id, status='unpaid').all()
        for fee in fees:
            student_fees.append({
                'student': student,
                'overdue': fee.amount,  # Assuming 'overdue' means unpaid amount
                'due_date': fee.due_date
            })
    return render_template("dashboard.html", role="Parent", student_fees=student_fees)

""" -------------------------------------------------------------------------------------------------- """  

@parent_blueprint.route("/notification")
@login_required
def notification():
    return render_template("notifications.html", role="Parent")

""" -------------------------------------------------------------------------------------------------- """  

@parent_blueprint.route("/make-payment", methods=['GET', 'POST'])
@login_required
def make_payment():
    # Get all students belonging to the current user (parent)
    students = Student.query.filter_by(user_id=current_user.id).all()
    
    if not students:
        flash('No students found under your account', 'error')
        return redirect(url_for('parent.parent_dashboard'))
    
    # Get selected student if student_id is provided
    student_id = request.args.get('student_id', type=int)
    student = None
    unpaid_fees = []
    total_overdue = 0
    
    if student_id:
        student = Student.query.filter_by(
            id=student_id, 
            user_id=current_user.id
        ).first_or_404()
        unpaid_fees = Fee.query.filter_by(student_id=student.id, status='unpaid').all()
        total_overdue = sum(fee.amount for fee in unpaid_fees)
        fee_ids = ','.join(str(fee.id) for fee in unpaid_fees)
    
    return render_template(
        "makePayment.html",
        students=students,
        student=student,
        fees=unpaid_fees,
        total_overdue=total_overdue,
        fee_ids=fee_ids if student_id else '',
        role="Parent"
    )

""" -------------------------------------------------------------------------------------------------- """  

@parent_blueprint.route("/process-payment/<int:student_id>", methods=['POST'])
@login_required
def process_payment(student_id):
    # Verify the student belongs to the current user
    student = Student.query.filter_by(
        id=student_id, 
        user_id=current_user.id
    ).first_or_404()
    
    payment_method = request.form.get('payment_method')
    fee_ids = request.form.get('fee_ids')
    
    if not payment_method:
        flash('Please select a payment method', 'error')
        return redirect(url_for('parent.make_payment', student_id=student_id))
    
    # Calculate total amount
    fees = Fee.query.filter(Fee.id.in_(fee_ids.split(','))).all()
    total_amount = sum(fee.amount for fee in fees)
    
    return render_template('paymentConfirmation.html',
                         student_id=student_id,
                         payment_method=payment_method,
                         total_amount=total_amount,
                         fee_ids=fee_ids)

""" -------------------------------------------------------------------------------------------------- """  

@parent_blueprint.route('/complete_payment/<int:student_id>', methods=['POST'])
@login_required
def complete_payment(student_id):
    # Verify the student belongs to the current user
    student = Student.query.filter_by(
        id=student_id, 
        user_id=current_user.id
    ).first_or_404()
    
    payment_method = request.form.get('payment_method')
    fee_ids = request.form.get('fee_ids')
    
    if not fee_ids:
        return jsonify({
            'status': 'error',
            'message': 'No fees selected for payment'
        }), 400
    
    try:
        # Convert fee_ids string to list of integers
        fee_id_list = [int(id) for id in fee_ids.split(',')]
        
        # Update fees to paid status
        fees = Fee.query.filter(Fee.id.in_(fee_id_list)).all()
        total_amount = sum(fee.amount for fee in fees)
        
        # Create new payment record
        payment = Payment(
            user_id=current_user.id,
            total_amount=float(total_amount),
            payment_method=payment_method,
            status='paid',
            payment_date=func.current_date()
        )
        db.session.add(payment)
        db.session.flush()
        
        # Create new invoice
        invoice = Invoice(
            total_amount=total_amount
        )
        db.session.add(invoice)
        db.session.flush()
        
        # Update fees
        for fee in fees:
            fee.status = 'paid'
            fee.invoice_id = invoice.id
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Payment completed successfully!'
        }), 200
        
    except Exception as e:
        print(f"Error processing payment: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while processing payment'
        }), 500

""" -------------------------------------------------------------------------------------------------- """  

@parent_blueprint.route("/payment-history")
@login_required
def payment_history():
    # Get only the specific user's paid payments first
    payments = Payment.query.filter_by(
                user_id=current_user.id,
                status='paid'
            ).order_by(Payment.id.asc()).all()
    
    payment_history = []
    
    # Get all students under the current parent
    students = Student.query.filter_by(user_id=current_user.id).all()
    student_ids = [student.id for student in students]
    
    # Get all paid fees for these students
    invoices = Invoice.query\
        .join(Fee, Fee.invoice_id == Invoice.id)\
        .filter(
            Fee.student_id.in_(student_ids),
            Fee.status == 'paid'
        )\
        .order_by(Invoice.id.asc())\
        .all()
    
    # Match payments with invoices by index
    for i, payment in enumerate(payments):
        if i < len(invoices):
            payment_history.append((payment, invoices[i], None, None))
    
    return render_template(
        "paymentHistory.html",
        payments=payment_history,
        role="Parent"
    )
    
""" -------------------------------------------------------------------------------------------------- """  


@parent_blueprint.route("/invoice_Details/<int:invoice_id>", methods=["GET"])
@login_required
def invoice_details(invoice_id):

    invoice = get_invoice_details(invoice_id)

    return render_template('invoiceDetail.html', invoice=invoice)