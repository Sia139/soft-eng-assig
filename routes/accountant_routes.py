# accountant_routes.py
import calendar
from reportlab.pdfgen import canvas
from io import BytesIO
from flask import Blueprint, make_response, render_template, request, redirect, url_for, flash, jsonify
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
        return render_template('403.html')
    
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
        return render_template('403.html')
    
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
        return render_template('403.html')
    
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
        return render_template('403.html')
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
    
""" -------------------------------------------------------------------------------------------------- """
    
@accountant_blueprint.route("/payment_tracking", methods=["GET"])
@login_required
def payment_tracking():
    check_and_update_invoices()
    allowed = is_action_allowed(current_user.role, "payment_tracking")
    print(f"Permission check: {allowed}")
    
    if not allowed:
        return render_template('403.html')
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

""" -------------------------------------------------------------------------------------------------- """

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

""" -------------------------------------------------------------------------------------------------- """

@accountant_blueprint.route("/finReport", methods=["GET"])
@login_required
def finReport():
    try:
        selected_month = request.args.get('month')
        if not selected_month:
            # If no month is selected, render the template with a message
            return render_template("finReport.html", 
                                   error="Please select a month to view the report.")

        year, month = map(int, selected_month.split('-'))
        start_date = datetime(year, month, 1)
        _, last_day = calendar.monthrange(year, month)
        end_date = datetime(year, month, last_day)

        # Get fees for the selected month
        monthly_fees = Fee.query.filter(
            Fee.due_date >= start_date,
            Fee.due_date <= end_date
        ).all()

        # Calculate summary statistics
        total_income = sum(fee.amount for fee in monthly_fees if fee.status == 'paid')
        total_unpaid = sum(fee.amount for fee in monthly_fees if fee.status == 'unpaid')
        total_fees = total_income + total_unpaid

        # Fee type breakdown
        fee_type_breakdown = {}
        for fee in monthly_fees:
            fee_type_breakdown[fee.type] = fee_type_breakdown.get(fee.type, 0) + fee.amount

        # Grade-wise breakdown
        grade_breakdown = {}
        for fee in monthly_fees:
            student = Student.query.get(fee.student_id)
            grade_breakdown[student.grade] = grade_breakdown.get(student.grade, 0) + fee.amount

        # Pass data to the template
        return render_template("finReport.html", 
                               total_income=total_income,
                               total_unpaid=total_unpaid,
                               total_fees=total_fees,
                               fee_type_breakdown=fee_type_breakdown,
                               grade_breakdown=grade_breakdown,
                               selected_month=selected_month
                              )

    except Exception as e:
        print(f"Error generating report: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

@accountant_blueprint.route("/generate_report", methods=['GET'])
@login_required
def generate_report():
    try:
        selected_month = request.args.get('month')
        if not selected_month:
            return jsonify({"success": False, "error": "Month not selected"})

        year, month = map(int, selected_month.split('-'))
        start_date = datetime(year, month, 1)
        _, last_day = calendar.monthrange(year, month)
        end_date = datetime(year, month, last_day)

        monthly_fees = Fee.query.filter(
            Fee.due_date >= start_date,
            Fee.due_date <= end_date
        ).all()

        total_income = sum(float(fee.amount) for fee in monthly_fees if fee.status == 'paid')
        total_bad_debt = sum(float(fee.amount) for fee in monthly_fees if fee.status == 'unpaid')

        buffer = BytesIO()
        p = canvas.Canvas(buffer)
        
        # Define constants
        PAGE_HEIGHT = 800
        PAGE_WIDTH = 600
        MARGIN = 50
        COL_WIDTHS = [200, 100, 150]  # Widths for each column
        ROW_HEIGHT = 20
        
        def draw_table_header(y_position, headers):
            # Draw table header background
            p.setFillColorRGB(0.9, 0.9, 0.9)  # Light gray background
            p.rect(MARGIN, y_position - ROW_HEIGHT, sum(COL_WIDTHS), ROW_HEIGHT, fill=1)
            
            # Draw header text
            p.setFillColorRGB(0, 0, 0)  # Black text
            x = MARGIN
            for i, header in enumerate(headers):
                p.drawString(x + 5, y_position - 15, header)
                x += COL_WIDTHS[i]
            
            # Draw header lines
            p.line(MARGIN, y_position, MARGIN + sum(COL_WIDTHS), y_position)
            p.line(MARGIN, y_position - ROW_HEIGHT, MARGIN + sum(COL_WIDTHS), y_position - ROW_HEIGHT)
            
            return y_position - ROW_HEIGHT

        def draw_table_row(y_position, data):
            x = MARGIN
            for i, item in enumerate(data):
                p.drawString(x + 5, y_position - 15, str(item))
                x += COL_WIDTHS[i]
            
            # Draw horizontal line
            p.line(MARGIN, y_position - ROW_HEIGHT, MARGIN + sum(COL_WIDTHS), y_position - ROW_HEIGHT)
            
            return y_position - ROW_HEIGHT

        def draw_vertical_lines(start_y, end_y):
            x = MARGIN
            for width in COL_WIDTHS:
                p.line(x, start_y, x, end_y)
                x += width
            p.line(x, start_y, x, end_y)  # Last vertical line

        def add_new_page():
            p.showPage()
            p.setFont("Helvetica", 10)
            return PAGE_HEIGHT - MARGIN

        # Start first page with title
        p.setFont("Helvetica-Bold", 16)
        y_position = PAGE_HEIGHT - MARGIN
        p.drawString(MARGIN, y_position, f"Financial Report - {calendar.month_name[month]} {year}")
        
        # Add summary section
        y_position -= 40
        p.setFont("Helvetica-Bold", 12)
        p.drawString(MARGIN, y_position, "Summary")
        y_position -= 25
        p.setFont("Helvetica", 10)
        p.drawString(MARGIN, y_position, f"Total Income: ${total_income:.2f}")
        y_position -= 15
        p.drawString(MARGIN, y_position, f"Total Bad Debt: ${total_bad_debt:.2f}")
        y_position -= 15
        collection_rate = (total_income / (total_income + total_bad_debt) * 100) if (total_income + total_bad_debt) > 0 else 0
        p.drawString(MARGIN, y_position, f"Collection Rate: {collection_rate:.1f}%")
        
        # Paid Fees Table
        y_position -= 40
        p.setFont("Helvetica-Bold", 12)
        p.drawString(MARGIN, y_position, "Paid Fees")
        y_position -= 25
        
        # Draw table headers
        headers = ["Student Name", "Amount", "Payment Date"]
        table_top = y_position
        y_position = draw_table_header(y_position, headers)
        
        # Draw paid fees rows
        for fee in monthly_fees:
            if fee.status == 'paid':
                if y_position < MARGIN + ROW_HEIGHT:
                    # Draw vertical lines for current page
                    draw_vertical_lines(table_top, y_position)
                    # Start new page
                    y_position = add_new_page()
                    table_top = y_position
                    y_position = draw_table_header(y_position, headers)
                
                student = Student.query.get(fee.student_id)
                row_data = [
                    student.name,
                    f"${float(fee.amount):.2f}",
                    fee.due_date.strftime('%d/%m/%Y')
                ]
                y_position = draw_table_row(y_position, row_data)
        
        # Draw vertical lines for last page of paid fees
        draw_vertical_lines(table_top, y_position)
        
        # Unpaid Fees Table
        y_position -= 40
        if y_position < MARGIN + 100:
            y_position = add_new_page()
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(MARGIN, y_position, "Unpaid Fees")
        y_position -= 25
        
        # Draw table headers for unpaid fees
        table_top = y_position
        y_position = draw_table_header(y_position, headers)
        
        # Draw unpaid fees rows
        for fee in monthly_fees:
            if fee.status == 'unpaid':
                if y_position < MARGIN + ROW_HEIGHT:
                    draw_vertical_lines(table_top, y_position)
                    y_position = add_new_page()
                    table_top = y_position
                    y_position = draw_table_header(y_position, headers)
                
                student = Student.query.get(fee.student_id)
                row_data = [
                    student.name,
                    f"${float(fee.amount):.2f}",
                    fee.due_date.strftime('%d/%m/%Y')
                ]
                y_position = draw_table_row(y_position, row_data)
        
        # Draw vertical lines for last page of unpaid fees
        draw_vertical_lines(table_top, y_position)
        
        # Add page number and generation date
        p.setFont("Helvetica", 8)
        p.drawString(PAGE_WIDTH - 70, MARGIN - 20, f"Page {p.getPageNumber()}")
        p.drawString(MARGIN, MARGIN - 20, f"Generated on {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        p.save()
        
        buffer.seek(0)
        response = make_response(buffer.getvalue())
        response.mimetype = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=financial_report_{selected_month}.pdf'
        
        return response

    except Exception as e:
        print(f"Error generating report: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        })