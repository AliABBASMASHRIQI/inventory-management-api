from flask import request, jsonify, Blueprint
from db import cursor, connection
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.auth import admin_required
from flasgger import swag_from


products_bp = Blueprint('products', __name__)

allowed_sort_fields = [
    "id",
    "name",
    "price",
    "quantity",
    "created_at",
    "updated_at"
]

allowed_order = ["asc","desc"]

@products_bp.post('/products')
@jwt_required()
@admin_required
@swag_from('../docs/products/create_product.yml')
def add_product():
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        

        if not data.get("name") or len(data["name"].strip()) == 0:
            return jsonify({"message": "No name given"}), 400
        if not data.get("price") or data["price"] < 0:
            return jsonify({"message": "Invalid price"}), 400
        if not data.get("quantity") or data["quantity"] <= 0:
            return jsonify({"message": "Quantity must be greater than 0"}), 400
        
        cursor.execute(
            "INSERT INTO PRODUCTS (name, description, price, quantity, user_id) VALUES (%s, %s, %s, %s, %s)",
            (data.get("name"), data.get("description"), data.get("price"), data.get("quantity"), current_user)
        )
        connection.commit()
        return jsonify({"message": "Product added"}), 201

    except Exception as e:
        connection.rollback()
        print("Error adding product:", e)
        return jsonify({"message": "Database error occurred"}), 500


@products_bp.get('/products')
@jwt_required()
@swag_from('../docs/products/get_products.yml')
def get_products():
    try:
        current_user = get_jwt_identity()
        page = request.args.get('page',1,type=int)
        if page < 1:
            return jsonify({
                "message": "Page must be greater than 0"
            }), 400
        per_page = 2
        offset = (page-1)*per_page
        
        sort = request.args.get('sort','id')
        order = request.args.get('order','asc').lower()  
        
        if sort not in allowed_sort_fields:
            return jsonify({"message": "Invalid sort field"}), 400

        if order not in allowed_order:
            return jsonify({"message": "Order must be asc or desc"}), 400 
        
        
        cursor.execute(f"SELECT * FROM PRODUCTS WHERE user_id = %s ORDER BY {sort} {order} LIMIT %s OFFSET %s", (current_user,per_page,offset))
        res = cursor.fetchall()
        return jsonify(res), 200
    except Exception as e:
        print("Error fetching products:", e)
        return jsonify({"message": "Database error occurred"}), 500


@products_bp.get('/products/<int:product_id>')
@jwt_required()
@swag_from('../docs/products/get_product.yml')
def get_one_product(product_id):
    try:
        current_user = get_jwt_identity()
        cursor.execute("SELECT * FROM PRODUCTS WHERE user_id = %s AND id = %s ", (current_user, product_id))
        res = cursor.fetchone()
        if res:
            return jsonify(res), 200
        else:
            return jsonify({"message": "Product not found"}), 404
    except Exception as e:
        print("Error fetching product:", e)
        return jsonify({"message": "Database error occurred"}), 500



@products_bp.patch('/products/<int:product_id>')
@jwt_required()
@admin_required
@swag_from('../docs/products/update_product.yml')
def update_product(product_id):   
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        base_query = "UPDATE PRODUCTS SET "
        condition = []
        values = []

        if data:
            if 'name' in data:
                if not data['name'].strip():
                    return jsonify({"message": "Name cannot be empty"}), 400
                condition.append("name = %s")
                values.append(data['name'])

            if 'description' in data:
                if not data['description'].strip():
                    return jsonify({"message": "Description cannot be empty"}), 400
                condition.append("description = %s")
                values.append(data['description'])

            if 'price' in data:
                try:
                    price = float(data['price'])
                    if price < 0:
                        return jsonify({"message": "Price must be non-negative"}), 400
                    condition.append("price = %s")
                    values.append(price)
                except ValueError:
                    return jsonify({"message": "Price must be a number"}), 400

            if 'quantity' in data:
                try:
                    quantity = int(data['quantity'])
                    if quantity <= 0:
                        return jsonify({"message": "Quantity must be greater than 0"}), 400
                    condition.append("quantity = %s")
                    values.append(quantity)
                except ValueError:
                    return jsonify({"message": "Quantity must be an integer"}), 400

            if not condition:
                return jsonify({"message": "No fields to update"}), 400

            query = base_query + ", ".join(condition) + " WHERE id = %s AND user_id = %s"
            values.append(product_id)
            values.append(current_user)

            cursor.execute(query, tuple(values))
            connection.commit()

            if cursor.rowcount > 0:
                return jsonify({"message": "Product updated"}), 200
            else:
                return jsonify({"message": "Product not found"}), 404
        else:
            return jsonify({"message": "No data provided"}), 400

    except Exception as e:
        connection.rollback()
        print("Error updating product:", e)
        return jsonify({"message": "Database error occurred"}), 500

@products_bp.delete('/products/<int:product_id>')
@jwt_required()
@admin_required
@swag_from('../docs/products/delete_product.yml')
def delete_product(product_id):
    try:
        current_user = get_jwt_identity()
        cursor.execute("DELETE FROM PRODUCTS WHERE user_id = %s AND id = %s", (current_user, product_id))
        connection.commit()
        if cursor.rowcount > 0:
            return jsonify({"message": "Product deleted"}), 200
        else:
            return jsonify({"message": "Product not found"}), 404
    except Exception as e:
        connection.rollback()
        print("Error deleting product:", e)
        return jsonify({"message": "Database error occurred"}), 500


@products_bp.get('/products/search')
@jwt_required()
@swag_from('../docs/products/search_products.yml')
def search_products():
    try:
        current_user = get_jwt_identity()

        name = request.args.get('name')
        min_price = request.args.get('min_price')
        max_price = request.args.get('max_price')
        quantity = request.args.get('quantity')
        created_after = request.args.get('created_after')
        created_before = request.args.get('created_before')
        updated_after = request.args.get('updated_after')
        updated_before = request.args.get('updated_before')


        page = request.args.get('page', 1, type=int)
        if page < 1:
            return jsonify({
                "message": "Page must be greater than 0"
            }), 400

        per_page = 2
        offset = (page - 1) * per_page


        sort = request.args.get('sort', 'id')
        order = request.args.get('order', 'asc').lower()

        base_query = "SELECT * FROM PRODUCTS"
        conditions = []
        values = []

        if name:
            conditions.append("name = %s")
            values.append(name)

        if current_user:
            conditions.append("user_id = %s")
            values.append(current_user)

        if quantity:
            conditions.append("quantity = %s")
            values.append(quantity)

        if min_price:
            conditions.append("price >= %s")
            values.append(min_price)

        if max_price:
            conditions.append("price <= %s")
            values.append(max_price)

        if created_after:
            conditions.append("created_at >= %s")
            values.append(created_after)

        if created_before:
            conditions.append("created_at <= %s")
            values.append(created_before)

        if updated_after:
            conditions.append("updated_at >= %s")
            values.append(updated_after)

        if updated_before:
            conditions.append("updated_at <= %s")
            values.append(updated_before)

        if sort not in allowed_sort_fields:
            return jsonify({"message": "Invalid sort field"}), 400

        if order not in allowed_order:
            return jsonify({"message": "Order must be asc or desc"}), 400


        if conditions:
            query = (
                base_query
                + " WHERE "
                + " AND ".join(conditions)
                + f" ORDER BY {sort} {order} LIMIT %s OFFSET %s"
            )
        else:
            query = (
                base_query
                + f" ORDER BY {sort} {order} LIMIT %s OFFSET %s"
            )

        values.append(per_page)
        values.append(offset)

        cursor.execute(query, tuple(values))
        res = cursor.fetchall()

        return jsonify(res), 200

    except Exception as e:
        print("Error searching products:", e)
        return jsonify({"message": "Database error occurred"}), 500
