from flask import request,Blueprint,jsonify
from db import cursor,connection
import bcrypt
import re
from flask_jwt_extended import get_jwt_identity,create_access_token,create_refresh_token, jwt_required
from flasgger import swag_from

user_bp = Blueprint("users",__name__)

@user_bp.post('/users')
@swag_from('../docs/users/create_user.yml')
def add_user():
    try:
        data = request.get_json()
        
        
        if not data.get("name") or len(data["name"].strip()) == 0:
            return jsonify({"message": "No name given"}), 400

        if not data.get("email") or len(data["email"].strip()) == 0 or not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',data["email"]):
            return jsonify({"message": "No email given"}), 400

        phone = data.get("phone_number")
        if not phone or len(phone) != 10 or not phone.isdigit():
            return jsonify({"message": "Phone number must be 10 digits"}), 400

        
        cursor.execute("SELECT id FROM USERS WHERE email = %s", (data['email'].lower().strip(),))
        existing_email = cursor.fetchone()
        if existing_email:
            return jsonify({"message": "Email already exists"}), 400


        cursor.execute("SELECT id FROM USERS WHERE phone_number = %s", (data['phone_number'],))
        existing_phone = cursor.fetchone()
        if existing_phone:
            return jsonify({"message": "Phone number already exists"}), 400
        
        
        
        password = data['password']
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password_bytes,salt)
        password_string = password_hash.decode('utf-8')
        
        cursor.execute("INSERT INTO USERS (name,email,phone_number,password_hash) VALUES (%s,%s,%s,%s)",(data['name'].strip(),data['email'].lower().strip(),data['phone_number'],password_string))
        connection.commit()
        if cursor.rowcount>0:
            return jsonify({"message":"USER has been INserted"}),201
        else:
            return jsonify({"message":"No user has been Inserted because of Faulty data"}),400
    except Exception as e:
        connection.rollback()
        print("Error INSERTING User:",e)
        return jsonify({"message":"No user has been Inserted because of Faulty data"}),500
    
    
@user_bp.get('/users')
@swag_from('../docs/users/get_users.yml')
def get_users():
    try:
        cursor.execute("SELECT * FROM USERS")
        res = cursor.fetchall()
        if res:
            return jsonify(res),200
        else:
            return jsonify({"message":"not found any data"}),404
    except Exception as e:
        print("Search not Found because:",e)
        return jsonify({"message":"Search data was not found"}),500
    
@user_bp.get('/users/<int:user_id>')
@swag_from('../docs/users/get_user.yml')
def get_one_user(user_id):
    try:
        cursor.execute("SELECT id, name, email, phone_number FROM USERS WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        if row:
            user = {
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "phone_number": row[3]
            }
            return jsonify(user), 200
        else:
            return jsonify({"message": "User not found"}), 404

    except Exception as e:
        print("Error fetching user:", e)
        return jsonify({"message": "Database error occurred"}), 500

    
    
@user_bp.patch('/users/<int:user_id>')
@swag_from('../docs/users/update_user.yml')
def update_user(user_id):
    try:
        data = request.get_json()
        condition = []
        value = []

        # Validate and add fields
        if 'name' in data:
            if not data['name'].strip():
                return jsonify({"message": "Name cannot be empty"}), 400
            condition.append(' name = %s ')
            value.append(data['name'])

        if 'email' in data:
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', data['email']):
                return jsonify({"message": "Invalid email format"}), 400
            # Check duplicate email
            cursor.execute("SELECT id FROM USERS WHERE email = %s AND id != %s", (data['email'], user_id))
            if cursor.fetchone():
                return jsonify({"message": "Email already exists"}), 400
            condition.append(' email = %s ')
            value.append(data['email'])

        if 'phone_number' in data:
            if not data['phone_number'].isdigit() or len(data['phone_number']) != 10:
                return jsonify({"message": "Phone number must be 10 digits"}), 400
            # Check duplicate phone
            cursor.execute("SELECT id FROM USERS WHERE phone_number = %s AND id != %s", (data['phone_number'], user_id))
            if cursor.fetchone():
                return jsonify({"message": "Phone number already exists"}), 400
            condition.append(' phone_number = %s ')
            value.append(data['phone_number'])

        if not condition:
            return jsonify({"message": "Empty data sent"}), 400

        value.append(user_id)
        base_query = "UPDATE USERS SET "
        query = base_query + ", ".join(condition) + " WHERE id = %s "

        cursor.execute(query, tuple(value))
        connection.commit()

        if cursor.rowcount > 0:
            return jsonify({"message": "Data has been updated"}), 200
        else:
            return jsonify({"message": "User not found"}), 404

    except Exception as e:
        # Rollback if something goes wrong
        connection.rollback()
        print("Error updating user:", e)
        return jsonify({"message": "Database error occurred"}), 500

    
@user_bp.delete('/users/<int:user_id>')
@swag_from('../docs/users/delete_user.yml')
def delete_user(user_id):
    try:
        cursor.execute("DELETE FROM USERS WHERE id = %s", (user_id,))
        connection.commit()
        if cursor.rowcount > 0:
            return jsonify({"message": "User has been deleted"}), 200
        else:
            return jsonify({"message": "User not found or not deleted"}), 404
    except Exception as e:
        connection.rollback()
        print("Error deleting user:", e)
        return jsonify({"message": "Database error occurred"}), 500


@user_bp.get('/users/search')
@swag_from('../docs/users/search_users.yml')
def search_users():
    try:
        base_query = "SELECT id, name, email, phone_number FROM USERS "
        conditions = []
        values = []

        name = request.args.get('name')
        email = request.args.get('email')
        phone_number = request.args.get('phone_number')

        if name:
            conditions.append(" name = %s ")
            values.append(name)
        if email:
            conditions.append(" email = %s ")
            values.append(email)
        if phone_number:
            conditions.append(" phone_number = %s ")
            values.append(phone_number)

        if conditions:
            query = base_query + ' WHERE ' + ' AND '.join(conditions)
        else:
            query = base_query

        cursor.execute(query, tuple(values))
        rows = cursor.fetchall()

        if rows:
            users = [
                {"id": row[0], "name": row[1], "email": row[2], "phone_number": row[3]}
                for row in rows
            ]
            return jsonify(users), 200
        else:
            return jsonify({"message": "No users found"}), 404

    except Exception as e:
        print("Error searching users:", e)
        return jsonify({"message": "Database error occurred"}), 500


@user_bp.post('/login')
@swag_from('../docs/auth/login.yml')
def login():
    try:
        data = request.get_json()

        # Validate required fields
        if not data.get("email") or len(data["email"].strip()) == 0:
            return jsonify({"message": "Email is required"}), 400
        if not data.get("password") or len(data["password"].strip()) == 0:
            return jsonify({"message": "Password is required"}), 400

        email = data['email'].lower().strip()
        password = data['password']

        cursor.execute("SELECT id, name, email, phone_number, password_hash,role FROM USERS WHERE email = %s", (email,))
        res = cursor.fetchone()

        if res:
            password_encode = password.encode('utf-8')
            db_pass = res[4].encode('utf-8')

            if bcrypt.checkpw(password_encode, db_pass):
                access_token = create_access_token(identity=str(res[0]))
                refresh_token = create_refresh_token(identity=str(res[0]))
                return jsonify({
                    "message": "Login successful",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "name": res[1],
                    "email": res[2],
                    "phone_number": res[3],
                    "role":res[5]
                }), 200
            else:
                return jsonify({"message": "Invalid email or password"}), 401
        else:
            return jsonify({"message": "Invalid email or password"}), 401

    except Exception as e:
        print("Error during login:", e)
        return jsonify({"message": "Database error occurred"}), 500
    
    
@user_bp.post('/refresh')
@jwt_required(refresh=True)
@swag_from('../docs/auth/refresh.yml')
def refresh():
    current_user = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user)
    return jsonify({
        "access_token": new_access_token
    }), 200
    
    
    
    
    

     

    
