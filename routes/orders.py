from flask import request,Blueprint,jsonify
from db import connection,cursor
from flask_jwt_extended import jwt_required,get_jwt_identity
from flasgger import swag_from

orders_bp = Blueprint('orders',__name__)

@orders_bp.post('/orders')
@jwt_required()
@swag_from('../docs/orders/create_order.yml')
def create_order():
    try:
        current_user = get_jwt_identity()
        cursor.execute("INSERT INTO ORDERS (user_id) Values (%s)",(current_user,))
        connection.commit()
        if cursor.rowcount>0:
            return jsonify({"message":f"Order created successfully for order_id - {cursor.lastrowid}."}),201
        else:
            return jsonify({"message":"Error creating order"    }),400
    except Exception as e:
        connection.rollback()
        print(f"Error:{e}")
        return jsonify({"message":"Error creating order"}),500
    
@orders_bp.get('/orders')
@jwt_required()
@swag_from('../docs/orders/get_orders.yml')
def get_all_orders():
    try:
        current_user = get_jwt_identity()
        cursor.execute("SELECT * FROM ORDERS WHERE user_id = %s",(current_user,))
        res = cursor.fetchall()
        return jsonify(res),200

    except Exception as e:
        print(f"Error:{e}")
        return jsonify({"message":"Error in Displaying all orders"}),500
    
@orders_bp.get('/orders/<int:id>')
@jwt_required()
@swag_from('../docs/orders/get_order.yml')
def get_one_order(id):
    try:
        current_user = get_jwt_identity()
        query = """
        SELECT 
            O.id AS order_id,
            O.status,
            O.created_at,
            U.name AS user_name,
            P.name AS product_name,
            oi.quantity AS quantity,
            oi.price_at_purchase AS price_at_purchase
        FROM order_items oi
        INNER JOIN Orders O ON oi.order_id = O.id
        INNER JOIN Products P ON oi.product_id = P.id
        INNER JOIN Users U ON O.user_id = U.id
        WHERE O.user_id = %s AND O.id = %s
        """
        cursor.execute(query, (current_user, id))
        result = cursor.fetchall()   

        # Result Indexes
        # 0 -> order_id
        # 1 -> status
        # 2 -> created_at
        # 3 -> user_name
        # 4 -> product_name
        # 5 -> quantity
        # 6 -> price_at_purchase


        if result:
            order_data = {
                "order_id": result[0][0],
                "status": result[0][1],
                "created_at": result[0][2],
                "customer": result[0][3],
                "items": [],
                "total": 0
            }
            for res in result:
                    item_total = res[5] * res[6]

                    order_data["items"].append({
                        "product_name": res[4],
                        "quantity": res[5],
                        "price": res[6],
                        "item_total": item_total
                    })

                    order_data["total"] += item_total

            return jsonify(order_data), 200
        else:
            return jsonify({"message": "Order not found"}), 404
    except Exception as e:
        print({"Error": e})
        return jsonify({"message": "DATABASE ERROR OCCURED"}), 500
    
@orders_bp.patch('/orders/<int:id>')
@jwt_required()
@swag_from('../docs/orders/update_order.yml')
def update_order(id):
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        status = data.get("status")

        if not status:
            return jsonify({
                "message": "Status is required"
            }), 400

        status = status.strip().lower()

        if status not in ("pending", "completed", "cancelled"):
            return jsonify({
                "message": "Only pending, completed or cancelled are allowed"
            }), 400
        
        cursor.execute("Update ORDERS SET status = %s WHERE id = %s AND user_id = %s",(status.strip().lower(),id,current_user))
        connection.commit()
        if cursor.rowcount>0:
            return jsonify({
                    "message": "Order Updated"
                }), 200
        else:
            return jsonify({"Message":"Error in Updating Order"}),400
    except Exception as e:
        connection.rollback()
        print({"Error":e})
        return jsonify({"Message":"Error in Updating Order"}),500
    
    
@orders_bp.delete('/orders/<int:id>')
@jwt_required()
@swag_from('../docs/orders/delete_order.yml')
def delete_order(id):
    try:
        current_user = get_jwt_identity()
        cursor.execute("DELETE FROM ORDERS WHERE user_id = %s AND id = %s", (current_user, id))
        connection.commit()
        if cursor.rowcount > 0:
            return jsonify({"message": "Order deleted"}), 200
        else:
            return jsonify({"message": "Order not found"}), 404
    except Exception as e:
        connection.rollback()
        print("Error deleting product:", e)
        return jsonify({"message": "Database error occurred"}), 500


@orders_bp.post('/orders/<int:order_id>/items')
@jwt_required()
@swag_from('../docs/orders/add_order_item.yml')
def add_order_item(order_id):
    try:
        data = request.get_json()
        product_id = data.get("product_id")
        quantity = data.get("quantity")

        if product_id is None:
            return jsonify({"message": "Please provide a product_id"}), 400

        if quantity is None:
            return jsonify({"message": "Please provide quantity"}), 400

        if quantity <= 0:
            return jsonify({"message": "Quantity must be greater than 0"}), 400
        current_user = get_jwt_identity()


        cursor.execute(
            "SELECT id FROM ORDERS WHERE id = %s AND user_id = %s",
            (order_id, current_user)
        )
        order = cursor.fetchone()

        if not order:
            return jsonify({"message": "Order not found or you do not own this order"}), 404


        cursor.execute(
            """
            SELECT id, price, quantity
            FROM PRODUCTS
            WHERE id = %s
            """,
            (product_id,)
        )

        product = cursor.fetchone()

        if not product:
            return jsonify({"message": "Product not found"}), 404

        product_price = product[1]
        stock = product[2]

        if stock < quantity:
            return jsonify({"message": "Not enough stock available"}), 400

        cursor.execute(
            """
            INSERT INTO ORDER_ITEMS
            (order_id, product_id, quantity, price_at_purchase)
            VALUES (%s, %s, %s, %s)
            """,
            (order_id, product_id, quantity, product_price)
        )

        cursor.execute(
            """
            UPDATE PRODUCTS
            SET quantity = quantity - %s
            WHERE id = %s
            """,
            (quantity, product_id)
        )

        connection.commit()

        return jsonify({
            "message": "Product added to order successfully"
        }), 201

    except Exception as e:
        connection.rollback()
        print("Error:", e)
        return jsonify({
            "message": "Database error occurred"
        }), 500