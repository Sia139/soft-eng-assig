# models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import NUMERIC

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(
        db.Enum('admin', 'accountant', 'teacher', 'parent', name='user_roles'),
        nullable=False
    )
    created_at = db.Column(db.DateTime, default=func.current_timestamp())
    flag = db.Column(db.Boolean, default=True)

    # Relationships
    students = db.relationship('Student', backref='guardian', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='user', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', cascade='all, delete-orphan')


class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    grade = db.Column(db.String(50), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    transport = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationships
    fees = db.relationship('Fee', backref='student', cascade='all, delete-orphan')
    
    @property
    def parent_name(self):
        return self.guardian.username if self.guardian else "No Guardian Assigned"

class Fee(db.Model):
    __tablename__ = 'fees'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    create_date = db.Column(db.Date, default=func.current_date())
    due_date = db.Column(db.Date, nullable=False)
    amount = db.Column(NUMERIC(10, 2), nullable=False)
    fee_type = db.Column(db.String(100), nullable=False)
    status = db.Column(db.Enum('unpaid', 'paid', name='fee_status'), default='unpaid')
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True)

    # Relationships
    invoice = db.relationship('Invoice', back_populates='fees')


class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    payment_date = db.Column(db.Date, default=func.current_timestamp()) #here maybe will have problem also
    total_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    status = db.Column(db.Enum('pending', 'paid', name='payment_status'), default='pending')


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    

class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    total_amount = db.Column(NUMERIC(10, 2), nullable=False)
    # need to add a attribute call flag
    flag = db.Column(db.Boolean, default=False)  # True if paid before the due date
    
    fees = db.relationship('Fee', back_populates='invoice', lazy='joined')

class FinancialReport(db.Model):
    __tablename__ = 'financial_reports'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fee_id = db.Column(db.Integer, db.ForeignKey('fees.id'), nullable=False)
    income = db.Column(db.Float, nullable=False)
    bad_debt = db.Column(db.Float, nullable=True)
