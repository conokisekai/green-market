from flask import Flask, jsonify, request
from phone import send_otp
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from models import db, Product, Order, User, Review, Notifications, Category
from flask_bcrypt import Bcrypt

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

@app.route("/user_signup", methods=["POST"])
def create_user():
    try:
        data = request.get_json()
        if not data or not isinstance(data, dict):
            return (
                jsonify({"error": True, "message": "Invalid JSON data in request"}),
                400,
            )

        required_fields = ["username", "password", "email", "phone", "address"]
        for field in required_fields:
            if field not in data or not data[field]:
                return (
                    jsonify({"error": True, "message": f"Missing or empty {field}"}),
                    400,
                )

        hashed_password = bcrypt.generate_password_hash(data["password"]).decode(
            "utf-8"
        )
        new_user = User(
            username=data["username"],
            password=hashed_password,
            email=data["email"],
            phone=data["phone"],
            address=data["address"],
             role=data["role"],
        )
        db.session.add(new_user)
        db.session.commit()

        # Send OTP only once after adding the user
        send_otp(data["phone"], data["username"])

        return (
            jsonify(
                {
                    "id": new_user.user_id,
                    "name": new_user.username,
                    "OTP sent": True,
                }
            ),
            201,
        )

    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500

@app.route("/user_login", methods=["POST"])
def user_login():
    try:
        data = request.get_json()
        if not data or not any(key in data for key in ["username", "phone", "email"]) or "password" not in data:
            return jsonify({"error": True, "message": "Invalid request data"}), 400

        username = data.get("username")
        phone = data.get("phone")
        email = data.get("email")
        password = data["password"]

        # Fetch the user based on provided username, phone, or email
        user = User.query.filter(
            (User.username == username) |
            (User.phone == phone) |
            (User.email == email)
        ).first()

        if not user or not bcrypt.check_password_hash(user.password, password):
            return jsonify({"error": True, "message": "Invalid username, phone, email, or password"}), 401

        return jsonify({
            "message": "Login successful",
            "user_type": "user",
            "username": user.username
        }), 200

    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500

@app.route("/del_user_login/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "User deleted successfully"}), 200

@app.route("/update_user/<int:user_id>", methods=["PATCH"])
def patch_user(user_id):
    try:
        data = request.json
        new_username = data.get("username")
        new_password = data.get("password")

        user = User.query.get(user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        if new_username:
            user.username = new_username

        if new_password:
            user.password = new_password

        db.session.commit()

        return jsonify({"message": "User information updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": "An error occurred"}), 500
    
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
    
@app.route('/get_category/<int:category_id>', methods=['GET'])
def get_category_by_id(category_id):
    try:
        category = Category.query.get(category_id)

        if not category:
            return jsonify({"error": "Category not found"}), 404

        category_data = {
            "category_id": category.category_id,
            "category_name": category.category_name
        }

        return jsonify({"category": category_data}), 200

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

        new_product = Product(
            product_name=data["product_name"],
            price=data["price"],
            quantity=data["quantity"],
            description=data["description"],
            category_name=data["category_name"],  
            image_link=data["image_link"],  
        )
        db.session.add(new_product)
        db.session.commit()

        return (
            jsonify(
                {
                    "product_id": new_product.product_id,
                    "product_name": new_product.product_name,
                    "message": "Product created successfully",
                }
            ),
            201,
        )

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
            "is_out_of_stock": product.is_out_of_stock,
            "description": product.description,
            "image_link": product.image_link,
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
    
@app.route("/update_product/<int:product_id>", methods=["PATCH"])
def update_product(product_id):
    try:
        product = Product.query.get(product_id)

        if not product:
            return jsonify({"error": "Product not found"}), 404

        data = request.json
        fields_to_update = ["product_name", "price", "quantity", "description", "category_name", "image_link"]

        for field in fields_to_update:
            new_value = data.get(field)
            if new_value is not None:
                setattr(product, field, new_value)

        db.session.commit()

        return jsonify({"message": "Product information updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500

    
if __name__ == "__main__":
    app.run(port=4000, debug=True)
