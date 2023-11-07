from tracking import db, login_manager, app
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable = False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    transactions = db.relationship('Transactions', backref='user', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}, {self.user_id}')"


class Transactions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), db.ForeignKey('user.username'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255))
    category = db.Column(db.String(100))
    card_name = db.Column(db.String(100))
    transaction_date = db.Column(db.DateTime, nullable = False)


class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount_added = db.Column(db.Float, nullable=False)
    added_date = db.Column(db.DateTime, nullable = False)

