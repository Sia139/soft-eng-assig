from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models import Fee, Notification, Student, Payment, Invoice, User, db
from datetime import datetime
from sqlalchemy.sql import func, and_
from function import get_invoice_details, is_action_allowed
# from function import view_fee_details, process_payment

parent_blueprint = Blueprint("parent", __name__)

@parent_blueprint.route("/notification")
@login_required
def notification():
    allowed = is_action_allowed(current_user.role, "notifications")
    print(f"Permission check: {allowed}")
    
    if not allowed:
        return render_template('403.html')
    
    notifications = Notification.query.filter_by(user_id=current_user.id).all()
    return render_template("notifications.html", notifications=notifications)

""" -------------------------------------------------------------------------------------------------- """  

# @parent_blueprint.route("/make-payment", methods=['GET', 'POST'])
# @login_required
# def make_payment():
#     allowed = is_action_allowed(current_user.role, "make_payment")
#     print(f"Permission check: {allowed}")
    
#     if not allowed:
#         return abort(403)
#     # Get all students belonging to the current user (parent)
#     students = Student.query.filter_by(user_id=current_user.id).all()
    
#     if not students:
#         flash('No students found under your account', 'error')
#         return redirect(url_for('parent.parent_dashboard'))
    
#     # Get selected student if student_id is provided
#     student_id = request.args.get('student_id', type=int)
#     student = None
#     unpaid_fees = []
#     total_overdue = 0
    
#     if student_id:
#         student = Student.query.filter_by(
#             id=student_id, 
#             user_id=current_user.id
#         ).first_or_404()
#         unpaid_fees = Fee.query.filter_by(student_id=student.id, status='unpaid').all()
#         total_overdue = sum(fee.amount for fee in unpaid_fees)
#         fee_ids = ','.join(str(fee.id) for fee in unpaid_fees)
    
#     return render_template(
#         "makePayment.html",
#         students=students,
#         student=student,
#         fees=unpaid_fees,
#         total_overdue=total_overdue,
#         fee_ids=fee_ids if student_id else '',
#         role="Parent"
#     )

@parent_blueprint.route("/make-payment", methods=['GET', 'POST'])
@login_required
def make_payment():
    allowed = is_action_allowed(current_user.role, "make_payment")
    print(f"Permission check: {allowed}")
    
    if not allowed:
        return render_template('403.html')

    # Get all students belonging to the current user (parent)
    students = Student.query.filter_by(user_id=current_user.id).all()

    if not students:
        flash('No students found under your account', 'error')
        return redirect(url_for('parent.parent_dashboard'))

    # Get selected student if student_id is provided
    student_id = request.args.get('student_id', type=int)
    student = None
    unpaid_fees = []
    total_amount = 0
    total_discount = 0
    total_penalty = 0
    fee_ids = ''

    if student_id:
        student = Student.query.filter_by(id=student_id, user_id=current_user.id).first_or_404()
        unpaid_fees = Fee.query.filter_by(student_id=student.id, status='unpaid').all()

        if unpaid_fees:
            # Get all related invoices
            invoice_ids = {fee.invoice_id for fee in unpaid_fees if fee.invoice_id}
            invoices = Invoice.query.filter(Invoice.id.in_(invoice_ids)).all()

            total_amount = sum(fee.amount for fee in unpaid_fees)
            total_discount = sum(invoice.discount_amount for invoice in invoices if invoice.discount_amount)
            total_penalty = sum(invoice.penalty_amount for invoice in invoices if invoice.penalty_amount)

            fee_ids = ','.join(str(fee.id) for fee in unpaid_fees)

    return render_template(
        "makePayment.html",
        students=students,
        student=student,
        fees=unpaid_fees,
        total_amount=total_amount,
        total_discount=total_discount,
        total_penalty=total_penalty,
        total_overdue=total_amount + total_penalty - total_discount,
        fee_ids=fee_ids,
        role="Parent"
    )


""" -------------------------------------------------------------------------------------------------- """  

# @parent_blueprint.route("/process-payment/<int:student_id>", methods=['POST'])
# @login_required
# def process_payment(student_id):
#     # Verify the student belongs to the current user
#     student = Student.query.filter_by(
#         id=student_id, 
#         user_id=current_user.id
#     ).first_or_404()
    
#     payment_method = request.form.get('payment_method')
#     fee_ids = request.form.get('fee_ids')
    
#     if not payment_method:
#         flash('Please select a payment method', 'error')
#         return redirect(url_for('parent.make_payment', student_id=student_id))
    
#     # Calculate total amount
#     fees = Fee.query.filter(Fee.id.in_(fee_ids.split(','))).all()
   

#     total_overdue = sum(fee.amount for fee in fees) 
    
#     return render_template('paymentConfirmation.html',
#                          student_id=student_id,
#                          payment_method=payment_method,
#                          total_overdue=total_overdue,
#                          fee_ids=fee_ids)

@parent_blueprint.route("/process-payment/<int:student_id>", methods=['POST'])
@login_required
def process_payment(student_id):
    # Verify the student belongs to the current user
    student = Student.query.filter_by(id=student_id, user_id=current_user.id).first_or_404()
    
    payment_method = request.form.get('payment_method')
    fee_ids = request.form.get('fee_ids')

    if not payment_method:
        flash('Please select a payment method', 'error')
        return redirect(url_for('parent.make_payment', student_id=student_id))

    if not fee_ids:
        flash('No fees selected for payment', 'error')
        return redirect(url_for('parent.make_payment', student_id=student_id))

    # Fetch fees
    fees = Fee.query.filter(Fee.id.in_(fee_ids.split(','))).all()

    if not fees:
        flash('Selected fees not found', 'error')
        return redirect(url_for('parent.make_payment', student_id=student_id))

    # Get related invoices
    invoice_ids = {fee.invoice_id for fee in fees if fee.invoice_id}
    invoices = Invoice.query.filter(Invoice.id.in_(invoice_ids)).all()

    # Calculate total amounts
    total_amount = sum(fee.amount for fee in fees)
    total_discount = sum(invoice.discount_amount for invoice in invoices if invoice.discount_amount)
    total_penalty = sum(invoice.penalty_amount for invoice in invoices if invoice.penalty_amount)
    
    total_overdue = total_amount + total_penalty - total_discount

    return render_template(
        'paymentConfirmation.html',
        student_id=student_id,
        payment_method=payment_method,
        total_overdue=total_overdue,
        fee_ids=fee_ids
    )


""" -------------------------------------------------------------------------------------------------- """  

# @parent_blueprint.route('/complete_payment/<int:student_id>', methods=['POST'])
# @login_required
# def complete_payment(student_id):
#     # Verify the student belongs to the current user
#     student = Student.query.filter_by(
#         id=student_id, 
#         user_id=current_user.id
#     ).first_or_404()
    
#     payment_method = request.form.get('payment_method')
#     fee_ids = request.form.get('fee_ids')
    
#     if not fee_ids:
#         return jsonify({
#             'status': 'error',
#             'message': 'No fees selected for payment'
#         }), 400
    
#     try:
#         # Convert fee_ids string to list of integers
#         fee_id_list = [int(id) for id in fee_ids.split(',')]
        
#         # Update fees to paid status
#         fees = Fee.query.filter(Fee.id.in_(fee_id_list)).all()
#         total_amount = sum(fee.amount for fee in fees)
        
#         # Create new payment record
#         payment = Payment(
#             user_id=current_user.id,
#             total_amount=float(total_amount),
#             payment_method=payment_method,
#             status='paid',
#             payment_date=func.current_date()
#         )
#         db.session.add(payment)
#         db.session.flush()
        
#         # Create new invoice
#         invoice = Invoice(
#             total_amount=total_amount
#         )
#         db.session.add(invoice)
#         db.session.flush()
        
#         # Update fees
#         for fee in fees:
#             fee.status = 'paid'
#             fee.invoice_id = invoice.id
        
#         db.session.commit()
        
#         return jsonify({
#             'status': 'success',
#             'message': 'Payment completed successfully!'
#         }), 200
        
#     except Exception as e:
#         print(f"Error processing payment: {str(e)}")
#         db.session.rollback()
#         return jsonify({
#             'status': 'error',
#             'message': 'An error occurred while processing payment'
#         }), 500

@parent_blueprint.route('/complete_payment/<int:student_id>', methods=['POST'])
@login_required
def complete_payment(student_id):
    # Verify the student belongs to the current user
    student = Student.query.filter_by(id=student_id, user_id=current_user.id).first_or_404()

    payment_method = request.form.get('payment_method')
    fee_ids = request.form.get('fee_ids')

    if not fee_ids:
        return jsonify({'status': 'error', 'message': 'No fees selected for payment'}), 400

    try:
        # Convert fee_ids string to list of integers
        fee_id_list = [int(id) for id in fee_ids.split(',')]

        # Retrieve fees
        fees = Fee.query.filter(Fee.id.in_(fee_id_list)).all()
        if not fees:
            return jsonify({'status': 'error', 'message': 'Selected fees not found'}), 400

        # Get related invoices
        invoice_ids = {fee.invoice_id for fee in fees if fee.invoice_id}
        invoices = Invoice.query.filter(Invoice.id.in_(invoice_ids)).all()

        # Calculate amounts
        total_amount = sum(fee.amount for fee in fees)
        total_discount = sum(invoice.discount_amount for invoice in invoices if invoice.discount_amount)
        total_penalty = sum(invoice.penalty_amount for invoice in invoices if invoice.penalty_amount)

        total_overdue = total_amount + total_penalty - total_discount

        # Create new payment record
        payment = Payment(
            user_id=current_user.id,
            total_amount=float(total_overdue),
            payment_method=payment_method,
            status='paid',
            payment_date=func.current_date()
        )
        db.session.add(payment)
        db.session.flush()

        # Update fees to paid status
        for fee in fees:
            fee.status = 'paid'

        # Mark associated invoices as paid if all their fees are paid
        for invoice in invoices:
            all_fees_paid = all(fee.status == 'paid' for fee in Fee.query.filter_by(invoice_id=invoice.id).all())
            if all_fees_paid:
                invoice.status = 'paid'  # Ensure invoice status is updated

        db.session.commit()

        return jsonify({'status': 'success', 'message': 'Payment completed successfully!'}), 200

    except Exception as e:
        print(f"Error processing payment: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'An error occurred while processing payment'}), 500

""" -------------------------------------------------------------------------------------------------- """  

# @parent_blueprint.route("/payment-history")
# @login_required
# def payment_history():
#     allowed = is_action_allowed(current_user.role, "view_payment_history")
#     print(f"Permission check: {allowed}")
    
#     if not allowed:
#         return abort(403)
#     # Get only the specific user's paid payments first
#     payments = Payment.query.filter_by(
#                 user_id=current_user.id,
#                 status='paid'
#             ).order_by(Payment.id.asc()).all()
    
#     payment_history = []
    
#     # Get all students under the current parent
#     students = Student.query.filter_by(user_id=current_user.id).all()
#     student_ids = [student.id for student in students]
    
#     # Get all paid fees for these students
#     invoices = Invoice.query\
#         .join(Fee, Fee.invoice_id == Invoice.id)\
#         .filter(
#             Fee.student_id.in_(student_ids),
#             Fee.status == 'paid'
#         )\
#         .order_by(Invoice.id.asc())\
#         .all()
    
#     # Match payments with invoices by index
#     for i, payment in enumerate(payments):
#         if i < len(invoices):
#             payment_history.append((payment, invoices[i], None, None))
    
#     return render_template(
#         "paymentHistory.html",
#         payments=payment_history,
#         role="Parent"
#     )

# @parent_blueprint.route("/payment-history")
# @login_required
# def payment_history():
#     allowed = is_action_allowed(current_user.role, "view_payment_history")
#     print(f"Permission check: {allowed}")
    
#     if not allowed:
#         return abort(403)
    
#     # Get all students under the current parent
#     students = Student.query.filter_by(user_id=current_user.id).all()
#     student_ids = [student.id for student in students]
    
#     # Get only the specific user's paid payments
#     payments = Payment.query.filter_by(
#         user_id=current_user.id,
#         status='paid'
#     ).order_by(Payment.id.asc()).all()

#     # Get all invoices related to these students
#     invoices = Invoice.query.join(Fee, Fee.invoice_id == Invoice.id).filter(
#         Fee.student_id.in_(student_ids),
#         Fee.status == 'paid'
#     ).order_by(Invoice.id.asc()).all()

#     # Fetch fees and students for each invoice
#     payment_history = []
#     for invoice in invoices:
#         related_fees = Fee.query.filter_by(invoice_id=invoice.id).all()
#         for fee in related_fees:
#             student = Student.query.get(fee.student_id)
#             matching_payment = next((p for p in payments if p.total_amount == invoice.total_amount), None)
#             if matching_payment:
#                 payment_history.append((matching_payment, invoice, fee, student))

#     return render_template(
#         "paymentHistory.html",
#         payments=payment_history,
#         role="Parent"
#     )

@parent_blueprint.route("/payment-history")
@login_required
def payment_history():
    allowed = is_action_allowed(current_user.role, "view_payment_history")
    print(f"Permission check: {allowed}")
    
    if not allowed:
        return render_template('403.html')
    
    # Get the user's paid payments
    payments = Payment.query.filter_by(
        user_id=current_user.id,
        status='paid'
    ).order_by(Payment.id.asc()).all()
    
    # Use a dictionary to map payments to their invoices (avoid duplicates)
    payment_history_dict = {}

    for payment in payments:
        invoice = Invoice.query.join(Fee).filter(
            Fee.invoice_id == Invoice.id,
            Fee.status == 'paid'
        ).order_by(Invoice.id.asc()).first()  # Get the first invoice

        if invoice and payment.id not in payment_history_dict:
            payment_history_dict[payment.id] = (payment, invoice, None, None)  # Avoid multiple mappings

    payment_history = list(payment_history_dict.values())  # Convert dictionary to list for template rendering

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

""" -------------------------------------------------------------------------------------------------- """  

@parent_blueprint.route("/receipt/<int:receipt>", methods=["GET"])
@login_required
def receipt(receipt):
    payment = Payment.query.filter_by(id=receipt).first()
    return render_template("receipt.html", payment = payment)

""" -------------------------------------------------------------------------------------------------- """

@parent_blueprint.route("/delete-notification/<int:notification_id>", methods=['POST'])
@login_required
def delete_notification(notification_id):
    print(f"Delete request received for notification ID: {notification_id}")  # Debugging

    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first()
    
    if not notification:
        print("Notification not found!")  # Debugging
        return jsonify({'status': 'error', 'message': 'Notification not found'}), 404

    db.session.delete(notification)
    db.session.commit()

    print(f"Notification {notification_id} deleted successfully")  # Debugging
    return jsonify({'status': 'success', 'message': 'Notification deleted successfully'}), 200

