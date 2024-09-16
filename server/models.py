from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///market.db'
db = SQLAlchemy(app)

class User(db.Model):
    ROLE_BUYER = 'buyer'
    ROLE_SELLER = 'seller'

    ROLE_CHOICES = [
        (ROLE_BUYER, 'Buyer'),
        (ROLE_SELLER, 'Seller'),
    ]

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.BigInteger(), unique=True)
    address = db.Column(db.Text())
    role = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f"<User {self.username}>"

class Product(db.Model):
    product_id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float(), nullable=False)
    quantity = db.Column(db.Integer(), default=1)
    is_out_of_stock = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text())
    image_link = db.Column(db.String(500))
    category_name = db.Column(db.String(500), db.ForeignKey("category.category_id"))
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    orders = db.relationship('Order', backref='product')

class Category(db.Model):
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(80), unique=True, nullable=False)

class Review(db.Model):
    review_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'))
    buyer_name = db.Column(db.String(100))
    review_text = db.Column(db.Text)
    rating = db.Column(db.Integer)
    review_date = db.Column(db.Date)

class Order(db.Model):
    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'))
    quantity = db.Column(db.Integer)
    total_price = db.Column(db.Float)
    order_date = db.Column(db.DateTime)

class Notifications(db.Model):
    notification_id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    email = db.Column(db.String(254), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True)

if __name__ == "__main__":
    app.run(debug=True)