from flask import Flask, jsonify, request, make_response
import json, requests
from requests.auth import HTTPBasicAuth
from passlib.hash import sha256_crypt
import base64, urllib3
from phone import send_otp
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from models import db, Product, Order, User, Review, Notifications, Category, CartItem
from flask_bcrypt import Bcrypt
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from flasgger import Swagger
import jwt
from datetime import datetime, timedelta
from functools import wraps
from models import User
import secrets
from phone import send_otp
from my_tokenizer import send_token


app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///market.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
migrate = Migrate(app, db)
db.init_app(app)
swagger = Swagger(app)


# config secret key
consumer_key = "fSJKwEHnmoiV2NXAFFSMu1Ja5SOzZLTmCSnM5lWQNrkZELbG"
consumer_secret = "EPuvMFL9g7p1FxGvsLoKuOtgX8YiyRMMnH73CeJGhjG1yfncMV5VOiKGIP17muIG"

date_today = datetime.today().strftime("%Y, %m, %d")



@app.route("/")
def home():
    """
    Home endpoint.
    ---
    responses:
      200:
        description: A JSON object with server information.
    """
    data = {"Server side": "Checkers"}
    return jsonify(data), 2000


@app.route("/user_signup", methods=["POST"])
def create_user():
    """
    Create user endpoint.
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
            password:
              type: string
            email:
              type: string
            phone:
              type: string
            address:
              type: string
            image_link:
              type: string
            role:
              type: string
    responses:
      201:
        description: A JSON object with user information and OTP status.
    """
    try:
        data = request.get_json()
        if not data or not isinstance(data, dict):
            return (
                jsonify({"error": True, "message": "Invalid JSON data in request"}),
                400,
            )

        required_fields = [
            "username",
            "password",
            "email",
            "phone",
            "address",
            "image_link",
        ]
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
            image_link=data["image_link"],
            role=data["role"],
        )
        db.session.add(new_user)
        db.session.commit()

        try:
            otp_value = send_otp(data["phone"], data["username"])
        except Exception as e:
            otp_value = None

        return (
            jsonify(
                {
                    "user_id": new_user.user_id,
                    "username": new_user.username,
                    "OTP_sent": otp_value,
                }
            ),
            201,
        )

    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500


@app.route("/user_login", methods=["POST"])
def user_login():
    """
    User login endpoint.
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
            phone:
              type: string
            username:
              type: string
            password:
              type: string
    responses:
      201:
        description: A JSON object with user information and JWT token.
    """
    # Your existing route code here

    auth = request.get_json()
    if (
        not auth
        or not (auth.get("email") or auth.get("phone") or auth.get("username"))
        or not auth.get("password")
    ):
        # returns 401 if any email, phone, username, or password is missing
        return make_response(
            "Could not verify! Missing email, phone, username, or password.",
            401,
            {"WWW-Authenticate": 'Basic realm ="Login required !!"'},
        )

    email = auth.get("email")
    phone = auth.get("phone")
    username = auth.get("username")
    password = auth.get("password")

    user = None
    if email:
        user = User.query.filter_by(email=email).first()
    elif phone:
        user = User.query.filter_by(phone=phone).first()
    elif username:
        user = User.query.filter_by(username=username).first()

    if not user:
        # returns 401 if user does not exist
        return make_response(
            "Could not verify! User does not exist",
            401,
            {"WWW-Authenticate": 'Basic realm ="User does not exist !!"'},
        )

    if bcrypt.check_password_hash(user.password, password):
        # generates the JWT Token
        token = jwt.encode(
            {
                "id": user.user_id,
                "name": user.username,
                "email": user.email,
                "phone": user.phone,
            },
            "secret",
            algorithm="HS256",
        )

        return make_response(
            jsonify(
                {
                    "token": token,
                    "name": user.username,
                    "email": user.email,
                    "phone": user.phone,
                    "role": user.role,
                    "user_id": user.user_id,
                }
            ),
            201,
        )

    # returns 403 if password is wrong
    return make_response(
        "Could not verify! Wrong password",
        403,
        {"WWW-Authenticate": 'Basic realm ="Wrong Password !!"'},
    )


@app.route("/users", methods=["GET"])
def get_all_users():
    """
    Get all users endpoint.
    ---
    responses:
      200:
        description: A JSON object with list of users.
    """
    # Your existing route code here

    # querying the database
    # for all the entries in it
    users = User.query.all()
    # converting the query objects
    # to list of jsons
    output = []
    for user in users:
        # appending the user data json
        # to the response list
        output.append(
            {
                "name": user.username,
                "email": user.email,
                "id": user.user_id,
                "phone": user.phone,
                "address": user.address,
                "image_link": user.image_link,
            }
        )

    return jsonify({"users": output})


@app.route("/delete_user/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    """
    Delete user endpoint.
    ---
    parameters:
      - name: user_id
        in: path
        required: true
        description: The ID of the user to delete.
        type: integer
    responses:
      200:
        description: A JSON object with success message.
      404:
        description: A JSON object with error message if user not found.
    """
    # Your existing route code here
    
    user = User.query.filter_by(user_id=user_id).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "User deleted successfully"}), 200


def get_access_token():
    mpesa_auth_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    response = requests.get(
        mpesa_auth_url, auth=HTTPBasicAuth(consumer_key, consumer_secret)
    )
    data = response.json()
    return data["access_token"]





@app.route("/stkpush", methods=["POST"])
def stkpush():
    """
    STK push endpoint.
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            amount:
              type: integer
            phone_number:
              type: string
    responses:
      200:
        description: A JSON object with STK push response.
    """
    # Your existing route code here
    access_token = get_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    business_short_code = 174379
    pass_key = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"

    # Get amount and phone_number from the request body
    data = request.get_json()
    amount = data.get("amount", 1)  # Default to 1 if amount is not provided
    phone_number = data.get(
        "phone_number", "2547xxxxxxxx"
    )  # Default phone number if not provided

    web_name = "test"

    password = base64.b64encode(
        f"{business_short_code}{pass_key}{timestamp}".encode("utf-8")
    ).decode("utf-8")

    payload = {
        "BusinessShortCode": business_short_code,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": business_short_code,
        "PhoneNumber": phone_number,
        "CallBackURL": "https://mydomain.com/path",
        "AccountReference": web_name,
        "TransactionDesc": "Payment of X",
    }

    response = requests.post(
        "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
        headers=headers,
        json=payload,
    )

    return jsonify(response.json())


token_dict = {}


@app.route("/forgot_password", methods=["POST"])
def forgot_password():
    """
    Forgot Password Endpoint
    ---
    tags:
      - Authentication
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              description: The email of the user
              example: test@example.com
    responses:
      200:
        description: Token sent successfully
        schema:
          type: object
          properties:
            message:
              type: string
              description: Message indicating token sent successfully
              example: Token sent successfully
            token:
              type: string
              description: The generated token
              example: abcdef123456
      400:
        description: Bad request if email is missing
      404:
        description: User not found if email is not registered
      500:
        description: Internal server error
    """
    try:
        data = request.get_json()
        if not data or "email" not in data:
            return jsonify({"error": True, "message": "Email is required"}), 400

        email = data["email"]
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": True, "message": "Email not found"}), 404

        token = send_token(user.phone, user.username)
        token_dict[email] = token  # Store the token in the dictionary

        return jsonify({"message": "Token sent successfully", "token": token}), 200

    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500


@app.route("/reset_password", methods=["PATCH"])
def reset_password():
    """
    Reset Password Endpoint
    ---
    tags:
      - Authentication
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              description: The email of the user
              example: test@example.com
            token:
              type: string
              description: The reset token sent to the user
              example: abcdef123456
            new_password:
              type: string
              description: The new password to be set
              example: new_password
    responses:
      200:
        description: Password reset successfully
      400:
        description: Bad request if token, email, or new_password is missing
      404:
        description: Invalid or expired token
      500:
        description: Internal server error
    """
    try:
        data = request.get_json()
        if not data or not isinstance(data, dict):
            return (
                jsonify({"error": True, "message": "Invalid JSON data in request"}),
                400,
            )

        token = data.get("token")
        new_password = data.get("new_password")
        email = data.get("email")  # Get the email from the request data

        if not token or not new_password or not email:
            return (
                jsonify(
                    {
                        "error": True,
                        "message": "Token, email, and new_password are required",
                    }
                ),
                400,
            )

        # Verify if the token is valid
        user = User.query.filter_by(email=email).first()
        if not user or token != token_dict.get(email):
            return jsonify({"error": True, "message": "Invalid or expired token"}), 400

        # Hash the new password
        hashed_password = bcrypt.generate_password_hash(new_password).decode("utf-8")

        # Update the user's password in the database with hashed_password
        user.password = hashed_password
        db.session.commit()  # Commit the changes to the database

        # Remove the token from the dictionary
        del token_dict[email]

        return jsonify({"message": "Password reset successfully"}), 200

    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500


@app.route("/create_category", methods=["POST"])
def create_category():
    """
    Create category endpoint.
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            category_name:
              type: string
    responses:
      201:
        description: A JSON object with created category details.
      400:
        description: A JSON object with error message if category_name is missing or empty.
      500:
        description: A JSON object with error message if an error occurs.
    """
    # Your existing route code here
    try:
        data = request.get_json()
        if not data or not isinstance(data, dict):
            return (
                jsonify({"error": True, "message": "Invalid JSON data in request"}),
                400,
            )

        category_name = data.get("category_name")
        if not category_name:
            return (
                jsonify({"error": True, "message": "Missing or empty category_name"}),
                400,
            )

        new_category = Category(category_name=category_name)
        db.session.add(new_category)
        db.session.commit()

        return (
            jsonify(
                {
                    "category_id": new_category.category_id,
                    "category_name": new_category.category_name,
                }
            ),
            201,
        )

    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500


@app.route("/get_all_categories", methods=["GET"])
def get_all_categories():
    """
    Get all categories endpoint.
    ---
    responses:
      200:
        description: A JSON object with list of all categories.
      500:
        description: A JSON object with error message if an error occurs.
    """
    # Your existing route code here
    try:
        categories = Category.query.all()
        category_list = [
            {
                "category_id": category.category_id,
                "category_name": category.category_name,
            }
            for category in categories
        ]

        return jsonify({"categories": category_list}), 200

    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500


@app.route("/create_product", methods=["POST"])
def create_product():
    """
    Create product endpoint.
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            user_id:
              type: integer
            product_name:
              type: string
            price:
              type: number
            quantity:
              type: integer
            description:
              type: string
            category_name:
              type: string
            image_link:
              type: string
    responses:
      201:
        description: A JSON object with created product details.
      400:
        description: A JSON object with error message if any required field is missing or empty.
      500:
        description: A JSON object with error message if an error occurs.
    """
    # Your existing route code here

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
            (
                {
                    "user_id": new_product.user_id,
                    "product_id": new_product.product_id,
                    "product_name": new_product.product_name,
                    "image_link": new_product.image_link,
                    "category_name": new_product.category_name,
                    "quantity": new_product.quantity,
                    "price": new_product.price,
                    "description": new_product.description,
                    "message": "Product created successfully",
                }
            ),
            201,
        )

        return jsonify({"new_product": new_product_data}), 200
    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500


@app.route("/get_all_products", methods=["GET"])
def get_all_products():
    """
    Get all products endpoint.
    ---
    responses:
      200:
        description: A JSON object with list of all products.
      500:
        description: A JSON object with error message if an error occurs.
    """
    try:
        products = Product.query.all()
        product_list = []
        for product in products:
            product_list.append(
                {
                    "product_id": product.product_id,
                    "product_name": product.product_name,
                    "price": product.price,
                    "quantity": product.quantity,
                    "is_out_of_stock": product.is_out_of_stock,
                    "description": product.description,
                    "image_link": product.image_link,
                    "category_name": product.category_name,
                    "user_id": product.user_id,
                }
            )

        return jsonify({"products": product_list}), 200

    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500


@app.route("/get_product/<int:product_id>", methods=["GET"])
def get_product_by_id(product_id):
    """
    Get product by ID endpoint.
    ---
    parameters:
      - name: product_id
        in: path
        type: integer
        required: true
        description: ID of the product to retrieve.
    responses:
      200:
        description: A JSON object with product details.
      404:
        description: A JSON object with error message if product is not found.
      500:
        description: A JSON object with error message if an error occurs.
    """
    # Your existing route code here

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
            "user_id": product.user_id,
            "image_link":product.image_link,
        }

        return jsonify({"product": product_data}), 200

    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500


@app.route("/delete_product/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    """
    Delete product by ID endpoint.
    ---
    parameters:
      - name: product_id
        in: path
        type: integer
        required: true
        description: ID of the product to delete.
    responses:
      200:
        description: A JSON object with success message.
      404:
        description: A JSON object with error message if product is not found.
      500:
        description: A JSON object with error message if an error occurs.
    """
    # Your existing route code here
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
    """
    Get products by user ID endpoint.
    ---
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID of the user whose products to retrieve.
    responses:
      200:
        description: A JSON object with products details.
      404:
        description: A JSON object with error message if products are not found.
      500:
        description: A JSON object with error message if an error occurs.
    """
    # Your existing route code here
    try:
        products = Product.query.filter_by(user_id=user_id).all()

        if not products:
            return jsonify({"error": "Products not found for the given user_id"}), 404

        product_data = []
        for product in products:
            product_data.append(
                {
                    "product_id": product.product_id,
                    "product_name": product.product_name,
                    "price": product.price,
                    "quantity": product.quantity,
                    "description": product.description,
                    "category_name": product.category_name,
                    "user_id": product.user_id,
                    "image_link":product.image_link
                }
            )

        return jsonify({"products": product_data}), 200

    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500


@app.route("/orders", methods=["GET"])
def get_all_orders():
    """
    Get all orders endpoint.
    ---
    responses:
      200:
        description: A JSON object with orders details.
      500:
        description: A JSON object with error message if an error occurs.
    """
    # Your existing route code here
    try:
        orders = Order.query.all()
        orders_data = [
            {
                "user_id": order.user_id,
                "product_name": order.product_name,
                "quantity": order.quantity,
                "total_price": order.total_price,
            }
            for order in orders
        ]
        return jsonify(orders_data), 200
    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500


@app.route("/orders", methods=["POST"])
def create_orders():
    """
    Create orders endpoint.
    ---
    parameters:
      - name: body
        in: body
        required: true
        description: JSON object containing order details.
        schema:
          type: object
          properties:
            user_id:
              type: integer
              description: ID of the user placing the order.
            product_id:
              type: integer
              description: ID of the product being ordered.
            product_name:
              type: string
              description: Name of the product being ordered.
            quantity:
              type: integer
              description: Quantity of the product being ordered.
            product_price:
              type: number
              description: Price of the product being ordered.
    responses:
      201:
        description: A JSON object with order details.
      400:
        description: A JSON object with error message if request data is invalid.
      500:
        description: A JSON object with error message if an error occurs.
    """
    # Your existing route code here
    try:
        # request data in json format
        data = request.json
        if not data or not isinstance(data, dict):
            return (jsonify({"error": True, "message": "Invalid JSON format"}), 400)

        # Checking if the required fields are present and not empty
        required_fields = [
            "user_id",
            "product_id",
            "product_name",
            "quantity",
            "product_price",
        ]  # Changed total_price to product_price
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
        quantity = data.get("quantity")  ####blocker image link

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

        return (
            jsonify(
                {
                    "user_id": new_order.user_id,
                    "product_id": new_order.product_id,
                    "product_name": new_order.product_name,
                    "quantity": new_order.quantity,
                    "total_price": new_order.total_price,
                }
            ),
            201,
        )

    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500


@app.route("/orders/<int:order_id>", methods=["DELETE"])
def delete_order(order_id):
    """
    Delete order endpoint.
    ---
    parameters:
      - name: order_id
        in: path
        type: integer
        required: true
        description: ID of the order to delete.
    responses:
      204:
        description: A JSON object indicating successful deletion.
      404:
        description: A JSON object with error message if order is not found.
      500:
        description: A JSON object with error message if an error occurs.
    """
    # Your existing route code here
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
    """
    Get all reviews.
    ---
    responses:
      200:
        description: A JSON array of review objects.
    """
    # Your existing route code here
    reviews = Review.query.all()

    # Convert Review objects to dictionaries
    reviews_data = []
    for review in reviews:
        review_data = {
            "review_id": review.review_id,
            "product_id": review.product_id,
            "rating": review.rating,
            "review_text": review.review_text,
            # Add other attributes as needed
        }
        reviews_data.append(review_data)

    return jsonify(reviews_data), 200


@app.route("/reviews", methods=["POST"])
def create_review():
    """
    Create a new review.
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            product_id:
              type: integer
              description: ID of the product being reviewed.
            review_text:
              type: string
              description: The review text.
            rating:
              type: integer
              description: The rating given for the product.
    responses:
      201:
        description: A JSON object with the created review details.
    """
    # Your existing route code here
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400

        product_id = data.get("product_id")
        review_text = data.get("review_text")
        rating = data.get("rating")
        review_date = datetime.now().date()

        if not product_id or not review_text or not rating:
            return jsonify({"error": True, "message": "Missing required fields"}), 400

        new_review = Review(
            product_id=product_id,
            review_text=review_text,
            rating=rating,
            review_date=review_date,
        )

        db.session.add(new_review)
        db.session.commit()

        return (
            jsonify(
                {
                    "review_id": new_review.review_id,
                    "product_id": new_review.product_id,
                    "review_text": new_review.review_text,
                    "rating": new_review.rating,
                    "review_date": new_review.review_date.strftime("%Y-%m-%d"),
                }
            ),
            201,
        )

    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500


@app.route("/reviews/<int:review_id>", methods=["DELETE"])
def delete_review(review_id):
    """
    Delete a review by its ID.
    ---
    parameters:
      - name: review_id
        in: path
        description: ID of the review to delete
        required: true
        type: integer
    responses:
      200:
        description: Review deleted successfully
      404:
        description: Review not found
    """
    # Your existing route code here
    review = Review.query.get(review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404

    db.session.delete(review)
    db.session.commit()

    return jsonify({"message": "Review deleted successfully"}), 200


@app.route("/cartitems/<int:user_id>/<int:cart_item_id>", methods=["GET"])
def get_cart_item(user_id, cart_item_id):
    """
    Get details of a cart item.
    ---
    parameters:
      - name: user_id
        in: path
        description: ID of the user
        required: true
        type: integer
      - name: cart_item_id
        in: path
        description: ID of the cart item
        required: true
        type: integer
    responses:
      200:
        description: Details of the cart item
      404:
        description: User, cart item, or product not found
    """
    # Your existing route code here
    try:
        user = User.query.get(user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        # Retrieve the cart item based on user_id and cart_item_id
        cart_item = CartItem.query.filter_by(
            user_id=user.user_id, id=cart_item_id
        ).first()

        if not cart_item:
            return jsonify({"error": "CartItem not found or not in the cart"}), 404

        product = Product.query.get(cart_item.product_id)

        if not product:
            return jsonify({"error": "Product not found"}), 404

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
            "user_id": product.user_id,
        }

        return (
            jsonify(
                {
                    "message": "This is the response for user_id {} and cart_item_id {}".format(
                        user_id, cart_item_id
                    )
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500


@app.route("/cart", methods=["POST"])
def add_to_cart():
    """
    Add an item to the cart.
    ---
    parameters:
      - name: user_id
        in: formData
        description: ID of the user
        required: true
        type: integer
      - name: product_id
        in: formData
        description: ID of the product to add to the cart
        required: true
        type: integer
      - name: quantity
        in: formData
        description: Quantity of the product to add (default is 1)
        required: false
        type: integer
    responses:
      201:
        description: Item added to cart successfully
      400:
        description: Missing required fields
      404:
        description: Product not found
    """
    # Your existing route code here

    try:
        # Get JSON data from the request
        data = request.get_json()

        # Extract necessary fields from the JSON data
        user_id = data.get("user_id")
        product_id = data.get("product_id")
        quantity = data.get("quantity", 1)  # Default to 1 if quantity is not provided

        # Validate the presence of required fields
        if not user_id or not product_id:
            return (
                jsonify(
                    {
                        "error": True,
                        "message": "Both user_id and product_id are required.",
                    }
                ),
                400,
            )

        # Fetch product details from the database based on product_id
        product = Product.query.get(product_id)

        # Validate if the product exists
        if not product:
            return jsonify({"error": True, "message": "Product not found."}), 404

        # Check if the product is already in the user's cart
        existing_cart_item = CartItem.query.filter_by(
            user_id=user_id, product_id=product_id
        ).first()

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
                total_price=total_price,
            )
            db.session.add(new_cart_item)

        db.session.commit()

        # Return success response
        return jsonify({"message": "Item added to cart successfully."}), 201

    except Exception as e:
        # Handle any exceptions that might occur
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500


@app.route("/cartitems/<int:cart_item_id>", methods=["DELETE"])
def remove_cart_item(cart_item_id):
    """
    Remove an item from the cart by its ID.
    ---
    parameters:
      - name: cart_item_id
        in: path
        description: ID of the cart item to remove
        required: true
        type: integer
    responses:
      200:
        description: Item removed from the cart successfully
      404:
        description: Cart item not found
    """
    # Your existing route code here
    cart_item = CartItem.query.get(cart_item_id)

    if not cart_item:
        return jsonify({"error": "CartItem not found"}), 404

    # Remove the item from the cart
    db.session.delete(cart_item)
    db.session.commit()

    return jsonify({"message": "Item removed from the cart successfully"}), 200


@app.route("/cartitems/<int:user_id>", methods=["GET"])
def get_cart_items(user_id):
    """
    Get all cart items for a user by user ID.
    ---
    parameters:
      - name: user_id
        in: path
        description: ID of the user
        required: true
        type: integer
    responses:
      200:
        description: A list of cart items for the user
      404:
        description: User not found
    """
    # Your existing route code here
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    # Retrieve the items in the user's cart
    cart_items = CartItem.query.filter_by(user_id=user.user_id).all()

    # Prepare the response data
    items_data = []
    for item in cart_items:
        product = Product.query.get(item.product_id)
        items_data.append(
            {
                "id": item.id,
                "product_id": product.product_id,
                "product_name": product.product_name,
                "quantity": item.quantity,
                "price": product.price,
                "total_price": item.total_price,
                "quantity": item.quantity,
                "is_out_of_stock": product.is_out_of_stock,
                "description": product.description,
                "image_link": product.image_link,
                "category_name": product.category_name,
                "user_id": product.user_id,
                # Add other details as needed
            }
        )

    return jsonify({"cart_items": items_data}), 200


@app.route("/admin/users", methods=["GET"])
def get_users():
    """
    Get all users.
    ---
    responses:
      200:
        description: A list of users
    """
    # Your existing route code here
    users = User.query.all()
    user_data = [
        {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "address": user.address,
            "role": user.role,
            "image_link": user.image_link,
        }
        for user in users
    ]
    return jsonify(user_data), 200


@app.route("/admin/users/<int:user_id>", methods=["GET"])
def get_user_by_id(user_id):
    """
    Get user by ID.
    ---
    parameters:
      - name: user_id
        in: path
        description: ID of the user
        required: true
        type: integer
    responses:
      200:
        description: User data
      404:
        description: User not found
    """
    # Your existing route code here

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": True, "message": "User not found."}), 404
    user_data = {
        "user_id": user.user_id,
        "image_link":user.image_link,
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "address": user.address,
        "role": user.role,
    }
    return jsonify(user_data), 200


@app.route("/admin/users/del/<int:user_id>", methods=["DELETE"])
def del_user(user_id):
    """
    Delete user by ID.
    ---
    parameters:
      - name: user_id
        in: path
        description: ID of the user to delete
        required: true
        type: integer
    responses:
      200:
        description: User deleted successfully
      404:
        description: User not found
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": True, "message": "User not found."}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"User with ID {user_id} deleted successfully."}), 200


@app.route("/admin/users/block/<int:user_id>", methods=["GET", "PUT"])
def block_user(user_id):
    """
    Block or unblock a user by ID.
    ---
    parameters:
      - name: user_id
        in: path
        description: ID of the user to block/unblock
        required: true
        type: integer
    responses:
      200:
        description: User status
      404:
        description: User not found
    """
    # Your existing route code here
    if request.method == "GET":
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": True, "message": "User not found."}), 404
        return jsonify({"user_id": user_id, "status": user.role}), 200

    elif request.method == "PUT":
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": True, "message": "User not found."}), 404
        user.role = "blocked"
        db.session.commit()
        return (
            jsonify({"message": f"User with ID {user_id} blocked successfully."}),
            200,
        )


@app.route("/admin/orders", methods=["GET"])
def all_orders():
    """
    Get all orders.
    ---
    responses:
      200:
        description: List of orders
      500:
        description: An error occurred
    """
    # Your existing route code here
    try:
        orders = Order.query.all()
        orders_data = [
            {
                "order_id": order.order_id,
                "user_id": order.user_id,
                "product_name": order.product_name,
                "quantity": order.quantity,
                "total_price": order.total_price,
                "order_date": order.order_date.strftime("%Y-%m-%d %H:%M:%S"),
                # Add other attributes as needed
            }
            for order in orders
        ]

        return jsonify(orders_data), 200

    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500


@app.route("/admin/orders/<int:order_id>", methods=["GET"])
def get_order_by_id(order_id):
    """
    Get order by ID.
    ---
    parameters:
      - name: order_id
        in: path
        description: ID of the order
        required: true
        type: integer
    responses:
      200:
        description: Order details
      404:
        description: Order not found
    """
    # Your existing route code here
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": True, "message": "Order not found."}), 404
    return (
        jsonify(
            {
                "order_id": order.order_id,
                "user_id": order.user_id,
                "total_price": order.total_price,
                "order_date": order.order_date.strftime("%Y-%m-%d %H:%M:%S"),
                # Add other attributes as needed
            }
        ),
        200,
    )


@app.route("/admin/login", methods=["POST"])
def admin_login():
    """
    Admin login.
    ---
    requestBody:
      content:
        application/json:
          schema:
            type: object
            properties:
              email:
                type: string
                description: Admin email
              password:
                type: string
                description: Admin password
    responses:
      200:
        description: Admin login successful
      401:
        description: Invalid password or admin not found
      500:
        description: An error occurred
    """
    # Your existing route code here
    try:
        data = request.get_json()
        if not data:
            return (
                jsonify({"error": True, "message": "Invalid JSON data in request"}),
                400,
            )

        email = data.get("email")
        password = data.get("password")

        # Fetch the user from the database by email
        admin = User.query.filter_by(email=email, role=User.ROLE_ADMIN).first()
        if admin:
            # Check if the provided password matches the hashed password in the database
            if bcrypt.check_password_hash(admin.password, password):
                return jsonify({"message": "Admin login successful."}), 200
            else:
                return jsonify({"error": True, "message": "Invalid password."}), 401
        else:
            return jsonify({"error": True, "message": "Admin not found."}), 401

    except Exception as e:
        return jsonify({"error": True, "message": f"An error occurred: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(port=4000, debug=True)
