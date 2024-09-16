from faker import Faker
from random import randint
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from models import db, Buyer, Farmer, Product, Review, Notifications, Order
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Configure app
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///market.db')  # Default to sqlite:///market.db if DATABASE_URI is not set
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with the Flask app
db.init_app(app)

fake = Faker()

if __name__ == '__main__':
    print("Seeded database with example data")

254710224989
