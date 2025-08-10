# raskladka/models.py
from flask_login import UserMixin
from datetime import datetime
from raskladka import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    meal_plans = db.relationship("MealPlan", backref="user", lazy=True)


class MealPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    days = db.relationship("Day", backref="meal_plan", lazy=True, cascade="all, delete-orphan")


class Day(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meal_plan_id = db.Column(db.Integer, db.ForeignKey("meal_plan.id"), nullable=False)
    day_number = db.Column(db.Integer, nullable=False)
    meals = db.relationship("Meal", backref="day", lazy=True, cascade="all, delete-orphan")


class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day_id = db.Column(db.Integer, db.ForeignKey("day.id"), nullable=False)
    meal_type = db.Column(db.String(50), nullable=False)
    products = db.relationship("Product", backref="meal", lazy=True, cascade="all, delete-orphan")


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meal_id = db.Column(db.Integer, db.ForeignKey("meal.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    weight = db.Column(db.Integer, nullable=False)
