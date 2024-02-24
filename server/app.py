from flask import Flask, jsonify, request
from phone import send_otp
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from models import db, Product, Order, User, Review, Notifications, Category, CartItem
from flask_bcrypt import Bcrypt
from datetime import datetime

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///market.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
migrate = Migrate(app, db)
db.init_app(app)

@app.route("/")
def home():
    data = {"Server side": "Checkers"}
    return jsonify(data), 200

@app.route('/create_category', methods=['POST'])
def create_category():
    try:
        data = request.get_json()
        if not data or not isinstance(data, dict):
            return jsonify({"error": True, "message": "Invalid JSON data in request"}), 400

        category_name = data.get('category_name')
        if not category_name:
            return jsonify({"error": True, "message": "Missing or empty category_name"}), 400

        new_category = Category(category_name=category_name)
        db.session.add(new_category)
        db.session.commit()

        return jsonify({"category_id": new_category.category_id, "category_name": new_category.category_name}), 201

    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500
    
@app.route("/get_all_categories", methods=["GET"])
def get_all_categories():
    try:
        categories = Category.query.all()
        category_list = [{"category_id": category.category_id, "category_name": category.category_name} for category in categories]

        return jsonify({"categories": category_list}), 200

    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500
    
@app.route("/create_product", methods=["POST"])
def create_product():
    try:
        data = request.get_json()
        if not data or not isinstance(data, dict):
            return (
                jsonify({"error": True, "message": "Invalid JSON data in request"}),
                400,
            )

        required_fields = [
            "user_id",
            "product_name",
            "price",
            "quantity",
            "description",
            "category_name",
            "image_link",
            
        ]
        for field in required_fields:
            if field not in data or not data[field]:
                return (
                    jsonify({"error": True, "message": f"Missing or empty {field}"}),
                    400,
                )
        # extract json data
        user_id = data.get("user_id")


        new_product = Product(
            user_id=user_id,
            product_name=data["product_name"],
            price=data["price"],
            quantity=data["quantity"],
            description=data["description"],
            category_name=data["category_name"],
            image_link=data["image_link"],
            
            # Add other required fields here
        )
        db.session.add(new_product)
        db.session.commit()

        return (
                {
                    "user_id":new_product.user_id,
                    "product_id": new_product.product_id,
                    "product_name": new_product.product_name,
                    "image_link":new_product.image_link,
                    "category_name":new_product.category_name,
                    "quantity":new_product.quantity,
                    "price":new_product.price,
                    "description":new_product.description,
                    "message": "Product created successfully",
                }
            ),201,
            
        return jsonify({"new_product": new_product_data}), 200
    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500

@app.route("/get_all_products", methods=["GET"])
def get_all_products():
    try:
        products = Product.query.all()
        product_list = []
        for product in products:
            product_list.append({
                "product_id": product.product_id,
                "product_name": product.product_name,
                "price": product.price,
                "quantity": product.quantity,
                "is_out_of_stock": product.is_out_of_stock,
                "description": product.description,
                "image_link": product.image_link,
                "category_name": product.category_name,
                "user_id": product.user_id
            })

        return jsonify({"products": product_list}), 200

    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500
    
@app.route("/get_product/<int:product_id>", methods=["GET"])
def get_product_by_id(product_id):
    try:
        product = Product.query.get(product_id)

        if not product:
            return jsonify({"error": "Product not found"}), 404

        product_data = {
            "product_id": product.product_id,
            "product_name": product.product_name,
            "price": product.price,
            "quantity": product.quantity,
            "category_name": product.category_name,
            "user_id": product.user_id
        }

        return jsonify({"product": product_data}), 200

    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500
    
@app.route("/delete_product/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    try:
        product = Product.query.get(product_id)

        if not product:
            return jsonify({"error": "Product not found"}), 404

        db.session.delete(product)
        db.session.commit()

        return jsonify({"message": "Product deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500
@app.route("/get_product_user_id/<int:user_id>", methods=["GET"])
def get_product_by_user_id(user_id):
    try:
        products = Product.query.filter_by(user_id=user_id).all()

        if not products:
            return jsonify({"error": "Products not found for the given user_id"}), 404

        product_data = []
        for product in products:
            product_data.append({
                "product_id": product.product_id,
                "product_name": product.product_name,
                "price": product.price,
                "quantity": product.quantity,
                "category_name": product.category_name,
                "user_id": product.user_id
            })

        return jsonify({"products": product_data}), 200

    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500
@app.route("/orders", methods=["GET"])
def get_all_orders():
    try:
        orders = Order.query.all()
        orders_data = [{"user_id": order.user_id, "product_name": order.product_name, "quantity": order.quantity, "image_link": order.image_link, "total_price": order.total_price} for order in orders]
        return jsonify(orders_data), 200
    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500

@app.route("/orders", methods=["POST"])
def create_orders():
    try:
        # request data in json format
        data = request.json
        if not data or not isinstance(data, dict):
            return (
                jsonify({"error": True, "message": "Invalid JSON format"}), 400
            )

        # Checking if the required fields are present and not empty
        required_fields = ["user_id", "product_id", "product_name", "quantity", "product_price"] # Changed total_price to product_price
        for field in required_fields:
            if field not in data or not data[field]:
                return (
                    jsonify({"error": True, "message": f"Missing or empty {field}"}),
                    400,
                )

        # extract json data
        user_id = data.get("user_id")
        product_id = data.get("product_id")
        product_price = float(data.get("product_price"))  
        quantity = data.get("quantity") ####blocker image link

        # Calculate total price correctly
        total_price = product_price * quantity

        # new instance
        new_order = Order(
            user_id=user_id,
            product_id=product_id,  
            product_name=data["product_name"],
            quantity=quantity,
            total_price=total_price,
        )

        db.session.add(new_order)
        db.session.commit()

        return jsonify(
            {
                "user_id": new_order.user_id,
                "product_id": new_order.product_id,
                "product_name": new_order.product_name,
                "quantity": new_order.quantity,
                "total_price": new_order.total_price,
            }
        ), 201

    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500

@app.route("/orders/<int:order_id>", methods=["DELETE"])
def delete_order(order_id):
    try:
        order = Order.query.get(order_id)

        if not order:
            return jsonify({"error": True, "message": "Order not found"}), 404

        db.session.delete(order)
        db.session.commit()

        return jsonify({"message": "Order deleted successfully"}), 204

    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500


@app.route("/reviews", methods=["GET"])
def get_reviews():
    reviews = Review.query.all()
    return jsonify([review for review in reviews]), 200

@app.route("/reviews", methods=["POST"])
def create_review():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400

        product_id = data.get("product_id")
        product_name = data.get("product_name")
        review_text = data.get("review_text")
        rating = data.get("rating")
        review_date = datetime.now().date()

        if not product_id or not review_text or not rating:
            return jsonify({"error": True, "message": "Missing required fields"}), 400

        new_review = Review(
            product_id=product_id,
            product_name=product_name,
            review_text=review_text,
            rating=rating,
            review_date=review_date
        )

        db.session.add(new_review)
        db.session.commit()

        return jsonify(
            {
                "review_id": new_review.review_id,
                "product_id": new_review.product_id,
                "product_name":new_review.product_name,
                "review_text": new_review.review_text,
                "rating": new_review.rating,
                "review_date": new_review.review_date.strftime("%Y-%m-%d"),
            }
        ), 201

    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500

@app.route("/reviews/<int:review_id>", methods=["DELETE"])
def delete_review(review_id):
    review = Review.query.get(review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404

    db.session.delete(review)
    db.session.commit()

    return jsonify({"message": "Review deleted successfully"}), 200
@app.route('/cartitems/<int:user_id>/<int:cart_item_id>', methods=['GET'])
def get_cart_item(user_id, cart_item_id):
    try:
        user = User.query.get(user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Retrieve the cart item based on user_id and cart_item_id
        cart_item = CartItem.query.filter_by(user_id=user.user_id, id=cart_item_id).first()

        if not cart_item:
            return jsonify({'error': 'CartItem not found or not in the cart'}), 404

        product = Product.query.get(cart_item.product_id)

        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # Prepare the response data
        item_data = {
            "product_id": product.product_id,
            "product_name": product.product_name,
            "price": product.price,
            "quantity": product.quantity,
            "is_out_of_stock": product.is_out_of_stock,
            "description": product.description,
            "image_link": product.image_link,
            "category_name": product.category_name,
            "user_id": product.user_id
        }

        return jsonify({"message": "This is the response for user_id {} and cart_item_id {}".format(user_id, cart_item_id)}), 200
    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500


@app.route("/cart", methods=["POST"])
def add_to_cart():
    try:
        # Get JSON data from the request
        data = request.get_json()

        # Extract necessary fields from the JSON data
        user_id = data.get("user_id")
        product_id = data.get("product_id")
        quantity = data.get("quantity", 1)  # Default to 1 if quantity is not provided

        # Validate the presence of required fields
        if not user_id or not product_id:
            return jsonify({"error": True, "message": "Both user_id and product_id are required."}), 400

        # Fetch product details from the database based on product_id
        product = Product.query.get(product_id)

        # Validate if the product exists
        if not product:
            return jsonify({"error": True, "message": "Product not found."}), 404

        # Check if the product is already in the user's cart
        existing_cart_item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()

        if existing_cart_item:
            # Update quantity and total price if the product is already in the cart
            existing_cart_item.quantity += quantity
            existing_cart_item.total_price += product.price * quantity
        else:
            # Calculate total price
            total_price = product.price * quantity

            # Create a new CartItem object and add it to the database
            new_cart_item = CartItem(
                user_id=user_id,
                product_id=product_id,
                quantity=quantity,
                total_price=total_price
            )
            db.session.add(new_cart_item)

        db.session.commit()

        # Return success response
        return jsonify({"message": "Item added to cart successfully."}), 201

    except Exception as e:
        # Handle any exceptions that might occur
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500



@app.route('/cartitems/<int:cart_item_id>', methods=['DELETE'])
def remove_cart_item(cart_item_id):
    cart_item = CartItem.query.get(cart_item_id)

    if not cart_item:
        return jsonify({'error': 'CartItem not found'}), 404
    
    # Remove the item from the cart
    db.session.delete(cart_item)
    db.session.commit()
    
    return jsonify({'message': 'Item removed from the cart successfully'}), 200

@app.route('/cartitems/<int:user_id>', methods=['GET'])
def get_cart_items(user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Retrieve the items in the user's cart
    cart_items = CartItem.query.filter_by(user_id=user.user_id).all()
    
    # Prepare the response data
    items_data = []
    for item in cart_items:
        product = Product.query.get(item.product_id)
        items_data.append({
            "id": item.id,
            "product_id": product.product_id,
            "product_name": product.product_name,
            "quantity": item.quantity,
            "price":product.price,
            "total_price": item.total_price,
            "quantity": item.quantity,
            "is_out_of_stock": product.is_out_of_stock,
            "description": product.description,
            "image_link": product.image_link,
            "category_name": product.category_name,
            "user_id": product.user_id
            # Add other details as needed
        })
    
    return jsonify({'cart_items': items_data}), 200
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Retrieve the items in the user's cart
    cart_items = CartItem.query.filter_by(user_id=user.user_id).all()
    
    # Prepare the response data
    items_data = []
    for item in cart_items:
        product = Product.query.get(item.product_id)
        items_data.append({
            "id": item.id,
            "product_id": product.product_id,
            "product_name": product.product_name,
            "price": product.price,
            "quantity": product.quantity,
            "is_out_of_stock": product.is_out_of_stock,
            "description": product.description,
            "image_link": product.image_link,
            "category_name": product.category_name,
            "user_id": product.user_id
            # Add other details as needed
        })
    
    return jsonify({'cart_items': items_data}), 200

if __name__ == "__main__":
    app.run(port=4000, debug=True)
