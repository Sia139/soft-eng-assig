#app.py
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import *
from config import Config
from function import check_and_update_invoices

# Import role-specific routes
from routes.admin_routes import admin_blueprint
from routes.accountant_routes import accountant_blueprint
from routes.teacher_routes import teacher_blueprint
from routes.parent_routes import parent_blueprint 
  
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

app.register_blueprint(admin_blueprint, url_prefix="/admin")
app.register_blueprint(accountant_blueprint, url_prefix="/accountant")
app.register_blueprint(teacher_blueprint, url_prefix="/teacher")
app.register_blueprint(parent_blueprint, url_prefix="/parent")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
  
@app.route("/")
def index():
    return redirect(url_for("login"))

""" -------------------------------------------------------------------------------------------------- """  

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            check_and_update_invoices()  # Ensure invoices are updated upon login
            print(f"Login successful for {username} with role {user.role}")
            return redirect(url_for("initial_page"))
        flash("Invalid username or password", "error")
        
    return render_template("login.html")

""" -------------------------------------------------------------------------------------------------- """  

@app.route("/logout")
@login_required
def logout():
    logout_user()
    # flash("You have been logged out.", "success")
    return redirect(url_for("login"))

""" -------------------------------------------------------------------------------------------------- """  

@app.route("/initial page")
@login_required
def initial_page():
    
    role_dashboard_routes = {
        "admin": "admin.manageAccount",
        "accountant": "accountant.billBunch",
        "teacher": "teacher.viewStudents",
        "parent": "parent.notification",
    }

    # Retrieve the target route based on user role
    target_route = role_dashboard_routes.get(current_user.role)
    
    # Debugging: Print the target route to the console
    print(f"User role: {current_user.role}, Target route: {target_route}")
    
    if target_route:
        return redirect(url_for(target_route))

    return "Role not recognized", 404

""" -------------------------------------------------------------------------------------------------- """  

# def initialize_database():
#     """Initialize the database and create default users if needed."""
    
    
#     with app.app_context():
#         # Create tables if they don't exist
#         db.create_all()

#         # Check if users already exist
#         if not User.query.first():
#             print("No users found, creating default users...")
#             default_users = [
#                 {
#                     "username": "admin_user",
#                     "email": "admin@example.com",
#                     "password": generate_password_hash("admin123"),
#                     "role": "admin",
#                 },
#                 {
#                     "username": "accountant_user",
#                     "email": "accountant@example.com",
#                     "password": generate_password_hash("accountant123"),
#                     "role": "accountant",
#                 },
#                 {
#                     "username": "teacher_user",
#                     "email": "teacher@example.com",
#                     "password": generate_password_hash("teacher123"),
#                     "role": "teacher",
#                 },
#                 {
#                     "username": "parent_user",
#                     "email": "parent@example.com",
#                     "password": generate_password_hash("parent123"),
#                     "role": "parent",
#                 },
#             ]

#             # Create User objects and save them
#             for user_data in default_users:
#                 user = User(**user_data)
#                 db.session.add(user)

#             db.session.commit()
#             print("Default users created successfully!")
#         else:
#             print("Users already exist in the database. Skipping creation.")
            
            
#         # Add student data initialization
#         from models import Student
#         from datetime import date
        
#         if not Student.query.first():
#             print("No students found, creating default students...")
            
#             # Get the parent user's ID (assuming it was created in the earlier part)
#             parent_user = User.query.filter_by(email='parent@example.com').first()
            
#             default_students = [
#                 {
#                     "name": "John Doe",
#                     "grade": "4",
#                     "dob": date(2015, 5, 15),
#                     "transport": True,
#                     "user_id": parent_user.id
#                 },
#                 {
#                     "name": "Jane Smith",
#                     "grade": "5",
#                     "dob": date(2016, 3, 20),
#                     "transport": False,
#                     "user_id": parent_user.id
#                 }
#             ]

#             # Create Student objects and save them
#             for student_data in default_students:
#                 student = Student(**student_data)
#                 db.session.add(student)

#             db.session.commit()
#             print("Default students created successfully!")
#         else:
#             print("Students already exist in the database. Skipping creation.")


from datetime import date
from models import User, Student, Fee
# from flask_bcrypt import generate_password_hash

def initialize_database():
    """Initialize the database and create default users, students, and fees if needed."""
    
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()

        # Check if users already exist
        if not User.query.first():
            print("No users found, creating default users...")
            default_users = [
                {
                    "username": "admin_user",
                    "email": "admin@example.com",
                    "password": generate_password_hash("admin123"),
                    "role": "admin",
                },
                {
                    "username": "accountant_user",
                    "email": "accountant@example.com",
                    "password": generate_password_hash("accountant123"),
                    "role": "accountant",
                },
                {
                    "username": "teacher_user",
                    "email": "teacher@example.com",
                    "password": generate_password_hash("teacher123"),
                    "role": "teacher",
                },
                {
                    "username": "parent_user",
                    "email": "parent@example.com",
                    "password": generate_password_hash("parent123"),
                    "role": "parent",
                },
            ]

            # Create User objects and save them
            for user_data in default_users:
                user = User(**user_data)
                db.session.add(user)

            db.session.commit()
            print("Default users created successfully!")
        else:
            print("Users already exist in the database. Skipping creation.")
            
        # # Add student data initialization
        # if not Student.query.first():
        #     print("No students found, creating default students...")
            
        #     # Get the parent user's ID (assuming it was created in the earlier part)
        #     parent_user = User.query.filter_by(email='parent@example.com').first()
            
        #     default_students = [
        #         {
        #             "name": "John Doe",
        #             "grade": "4",
        #             "dob": date(2015, 5, 15),
        #             "transport": True,
        #             "user_id": parent_user.id
        #         },
        #         {
        #             "name": "Jane Smith",
        #             "grade": "5",
        #             "dob": date(2016, 3, 20),
        #             "transport": False,
        #             "user_id": parent_user.id
        #         }
        #     ]

        #     # Create Student objects and save them
        #     for student_data in default_students:
        #         student = Student(**student_data)
        #         db.session.add(student)

        #     db.session.commit()
        #     print("Default students created successfully!")

        #     # Add fee data initialization for students
        #     print("Adding default fees for students...")
        #     students = Student.query.all()

        #     # Define default fee data for students (ensure that due_date is a proper date)
        #     default_fees = [
        #         {
        #             "student_id": students[0].id,
        #             "due_date": date(2025, 2, 15),  # Use date only (no time)
        #             "amount": 100.00,
        #             "fee_type": "Tuition",
        #         },
        #         {
        #             "student_id": students[0].id,
        #             "due_date": date(2025, 3, 15),
        #             "amount": 50.00,
        #             "fee_type": "Transport",
        #         },
        #         {
        #             "student_id": students[1].id,
        #             "due_date": date(2025, 2, 15),
        #             "amount": 120.00,
        #             "fee_type": "Tuition",
        #         },
        #         {
        #             "student_id": students[1].id,
        #             "due_date": date(2025, 3, 15),
        #             "amount": 60.00,
        #             "fee_type": "Transport",
        #         }
        #     ]
            
        #     # Create Fee objects and save them
        #     for fee_data in default_fees:
        #         fee = Fee(**fee_data)
        #         db.session.add(fee)

        #     db.session.commit()
        #     print("-----------------------------------------------------------")
        #     print("Default fees created successfully!")

        # else:
        #     print("Students already exist in the database. Skipping creation.")


""" -------------------------------------------------------------------------------------------------- """  

def seed_permissions():
    with app.app_context():
        if not RolePermission.query.first():
            print('No permission initialized, setting up the permission....')
            permissions = [
                # Parent permissions
                ("parent", "make_payment", True),
                ("parent", "view_payment_history", True),
                ("parent", "notifications", True),

                # Accountant Permissions
                ("accountant", "financial_report", True),
                ("accountant", "payment_tracking", True),
                ("accountant", "fee_management", True),

                # Teacher Permissions
                ("teacher", "add_student", True),
                ("teacher", "fee_overview", True),
                ("teacher", "view_student_details", True),  # <-- Now correctly separated

                # Admin Permissions
                ("admin", "payment_tracking", True),
                ("admin", "fee_management", True),
                ("admin", "add_student", True)
            ]

            for role, function, is_allowed in permissions:
                db.session.add(RolePermission(role=role, function_name=function, is_allowed=is_allowed))

            db.session.commit()
            print("Permissions seeded successfully.")


""" -------------------------------------------------------------------------------------------------- """  

if __name__ == '__main__': 
    initialize_database()  # Initialize the database and create default users
    seed_permissions()
    app.run(debug=True)