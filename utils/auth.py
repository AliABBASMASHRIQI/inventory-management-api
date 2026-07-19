from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from db import cursor
from functools import wraps


def is_admin():
    current_user = get_jwt_identity()
    
    cursor.execute('''
                   SELECT role FROM USERS WHERE id = %s 
                   ''',(current_user,))
    user = cursor.fetchone()
    
    if not user:
        return False
    return user[0]== 'admin'

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):

        if not is_admin():
            return jsonify({
                "message": "Only admins can perform this action"
            }), 403

        return fn(*args, **kwargs)

    return wrapper