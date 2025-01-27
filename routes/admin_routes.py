from flask import Blueprint, render_template, request,  redirect, url_for, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, User, Student, Fee, Payment
# from function import create_user, create_student, process_billing, search_parent_student, calculate_outstanding_balance
from sqlalchemy.orm import joinedload

admin_blueprint = Blueprint("admin", __name__)

""" -------------------------------------------------------------------------------------------------- """  

@admin_blueprint.route("/create-user", methods=["GET", "POST"])
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

@admin_blueprint.route("/manage-account", methods=["GET", "POST"])
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
        if user:
            user.role = new_role
            db.session.commit()
            return jsonify({'success': True}), 200
        return jsonify({'success': False, 'message': 'User not found'}), 404
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

""" -------------------------------------------------------------------------------------------------- """  