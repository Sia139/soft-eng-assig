Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\venv\Scripts\activate

<!-- viewBilling.html -->
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>View Billing</title>
    <link rel="icon" type="image/x-icon" href="{{ url_for('static', filename='images/icon.png') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='viewBilling.css') }}">
</head>

<body>
    <!-- Sidebar -->
    <div id="mySidebar" class="sidebar">
        <div class="logo-section">
            <img src="{{ url_for('static', filename='images/kids.jpeg') }}">
        </div>
        <nav class="menu">
            <div class="dropdown">
                <button class="dropdown-btn">Fee</button>
                <div class="dropdown-content">
                    <a href="{{ url_for('accountant.viewBilling') }}">View & edit bill</a>
                    <a href="#">Update bill</a>
                    <a href="{{ url_for('accountant.billBunch') }}">Create bill bunch</a>
                    <a href="#">Create bill single</a>
                    <a href="#">Update bill</a>
                </div>
            </div>
            <div class="dropdown">
                <button class="dropdown-btn">Create bill</button>
                <div class="dropdown-content">
                    <a href="#">By grade</a>
                    <a href="#">By individual</a>
                </div>
            </div>
            <div class="dropdown">
                <button class="dropdown-btn">Financial</button>
                <div class="dropdown-content">
                    <a href="#">Financial report</a>
                    <a href="#">Payment tracking</a>
                </div>
        </nav>
        <div class="logout-section">
            <a href="/logout">&#x2190;</a>
        </div>
    </div>

    <button class="collapse-button">&#9776;</button>

    <!-- Main Content -->
    <div class="main-content">
        <header class="header">
            <div class="time">08:27am</div>
            <div class="admin-section">
                <span>Accountant</span>
            </div>
        </header>

        <section class="content">
            <div class="header-container">
                <h1>View & Edit Billing</h1>

                <form method="GET" action="{{ url_for('accountant.viewBilling') }}">
                    <div class="search-bar">
                    <input type="text" name="student_name" placeholder="Search by name" value="{{ request.args.get('student_name', '') }}">

                    <select id="grade" name="grade" onchange="this.form.submit();">
                        <option value="">Select Grade</option>
                        <option value="4" {% if request.args.get('grade') == "4" %}selected{% endif %}>Grade 4</option>
                        <option value="5" {% if request.args.get('grade') == "5" %}selected{% endif %}>Grade 5</option>
                        <option value="6" {% if request.args.get('grade') == "6" %}selected{% endif %}>Grade 6</option>
                    </select>

                    <select name="status" onchange="this.form.submit();">
                        <option value="">All Status</option>
                        <option value="unpaid" {% if request.args.get('status') == 'unpaid' %}selected{% endif %}>Unpaid</option>
                        <option value="paid" {% if request.args.get('status') == 'paid' %}selected{% endif %}>Paid</option>
                    </select>

                    <button>&#x27A4;</button>
                    </div>
                </form>
            </div>

            <table id="myTable2">
                <thead>
                    <tr>
                        <th onclick="sortTable(0)">#Id <span class="sort"></span></th>
                        <th onclick="sortTable(1)">Name <span class="sort"></span></th>
                        <th onclick="sortTable(2)">Details <span class="sort"></span></th>
                        <th onclick="sortTable(3)">Amount <span class="sort"></span></th>
                        <th onclick="sortTable(4)">Due Date <span class="sort"></span></th>
                        <th onclick="sortTable(5)">Status <span class="sort"></span></th>
                        <th>Edit</th>
                    </tr>
                </thead>
                <tbody>
                    {% if fees %}
                        {% for fee in fees %}
                            <tr>
                                <td>
                                    <a href="#"><span class="invoice">{{ fee.id }}</span></a>
                                </td>
                                <td>
                                    <span class="name">{{ fee.student.name }}</span>
                                </td>
                                <td>
                                    <input type="text" class="details" data-id="{{ fee.id }}" value="{{ fee.fee_type }}">
                                </td>
                                <td>
                                    <input type="number" class="amount" data-id="{{ fee.id }}" value="{{ fee.amount }}">
                                </td>
                                <td>
                                    <input type="date" class="dueDate" data-id="{{ fee.id }}" value="{{ fee.due_date }}">
                                </td>
                                <td>
                                    <select class="status" data-id="{{ fee.id }}">
                                        <option value="unpaid" {% if fee.status == 'unpaid' %}selected{% endif %}>Unpaid</option>
                                        <option value="paid" {% if fee.status == 'paid' %}selected{% endif %}>Paid</option>
                                    </select>
                                </td>
                                <td class="edit">
                                    <button class="update-btn" data-id="{{ fee.id }}">Save</button>
                                    <button class="delete-btn" data-id="{{ fee.id }}">Delete</button>
                                </td>
                            </tr>
                        {% endfor %}
                    {% else %}
                        <tr>
                            <td colspan="7">No fee records found.</td>
                        </tr>
                    {% endif %}
                </tbody>
            </table>
        </section>
    </div>
    <script src="{{ url_for('static', filename='viewBilling.js') }}"></script>
    <script>
        document.querySelectorAll('.update-btn').forEach(button => {
            button.addEventListener('click', function() {
                const feeId = this.getAttribute('data-id');
                const row = this.closest('tr');
                const feeType = row.querySelector('.details').value;
                const amount = row.querySelector('.amount').value;
                const dueDate = row.querySelector('.dueDate').value;
                const status = row.querySelector('.status').value;

                fetch(`/update_fee/${feeId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        fee_type: feeType,
                        amount: amount,
                        due_date: dueDate,
                        status: status
                    })
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                })
                .catch(error => {
                    console.error('Error:', error);
                });
            });
        });
    </script>
</body>

</html>

# accountant_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Fee, Student
from function import create_fees_for_grade, update_fee, delete_fee  

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
    # Fetch query parameters for filtering (if any)
    student_name = request.args.get("student_name")
    grade = request.args.get("grade")
    status = request.args.get("status")

    # Start with a base query
    fees_query = Fee.query.join(Student)  # Join with Student to filter by student attributes

    # Apply filters if provided
    if student_name and student_name.strip():
        fees_query = fees_query.filter(Student.name.ilike(f"%{student_name.strip()}%"))
    if grade and grade.strip():
        fees_query = fees_query.filter(Student.grade == grade.strip())
    if status and status.strip():
        fees_query = fees_query.filter(Fee.status == status.strip())


    # Fetch the filtered fees
    fees = fees_query.all()
    print("Fees fetched:", fees)  # Debug print

    # Render the template with the fees
    return render_template("viewBilling.html", fees=fees)

@accountant_blueprint.route("/update_fee/<int:fee_id>", methods=["POST"])
@login_required
def update_fee_route(fee_id):
    data = request.json
    return update_fee(fee_id, data)

@accountant_blueprint.route("/delete_fee/<int:fee_id>", methods=["DELETE"])
@login_required
def delete_fee_route(fee_id):
    return delete_fee(fee_id)


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

""" -------------------------------------------------------------------------------------------------- """

def update_fee(fee_id, data):
    fee = Fee.query.get(fee_id)

    if not fee:
        return jsonify({"message": "Fee record not found"}), 404

    fee.fee_type = data["fee_type"]
    fee.amount = Decimal(data["amount"])
    fee.status = data["status"]

    db.session.commit()
    return jsonify({"message": "Fee updated successfully"})

def delete_fee(fee_id):
    fee = Fee.query.get(fee_id)

    if not fee:
        return jsonify({"message": "Fee record not found"}), 404

    db.session.delete(fee)
    db.session.commit()
    return jsonify({"message": "Fee deleted successfully"})


at the viewBilling make the user can edit the fee details. after user click the save button it will update the changed data to database 