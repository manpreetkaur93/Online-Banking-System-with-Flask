# from random import random
# from faker import Faker
# from flask_sqlalchemy import SQLAlchemy
# from datetime import datetime
# from werkzeug.security import generate_password_hash, check_password_hash
# from flask_login import UserMixin

# db = SQLAlchemy()

# class Customer(db.Model):
#     __tablename__ = 'customer'
#     id = db.Column(db.Integer, primary_key=True)
#     namn = db.Column(db.String(255))
#     email = db.Column(db.String(255), unique=True)
#     personnummer = db.Column(db.String(10), unique=True)
#     address = db.Column(db.String(255))
#     city = db.Column(db.String(255))
#     accounts = db.relationship('Account', backref='customer', lazy=True)
    
#     def __repr__(self):
#         return f"<Customer {self.namn} - Email: {self.email}>"
    
#     @property
#     def total_balance(self):
#         total_balance = 0
#         for account in self.accounts:
#             total_balance += account.calculate_balance()
#         return round(total_balance, 2)

#     @total_balance.setter
#     def total_balance(self, value):
#         pass
    
# class Admin(db.Model, UserMixin):
#     id = db.Column(db.Integer, primary_key=True)
#     namn = db.Column(db.String(100), nullable=False)
#     email = db.Column(db.String(120), unique=True, nullable=False)
#     username = db.Column(db.String(50), nullable=False)
#     password = db.Column(db.String(128), nullable=False)  # Adjusted for hashed passwords

#     @classmethod
#     def authenticate(cls, username, password):
#         admin = cls.query.filter_by(username=username).first()
#         if admin and check_password_hash(admin.password, password):
#             return admin
#         return None

# class Account(db.Model):
#     __tablename__ = 'account'
#     id = db.Column(db.Integer, primary_key=True)
#     account_number = db.Column(db.String(15), unique=True)
#     customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
#     transactions = db.relationship('Transaction', backref='account', lazy=True)
    
#     def calculate_balance(self):
#         balance = 0
#         for transaction in self.transactions:
#             balance += transaction.amount
#         return balance

# class Transaction(db.Model):
#     __tablename__ = 'transaction'
#     id = db.Column(db.Integer, primary_key=True)
#     amount = db.Column(db.Float)
#     transaction_type = db.Column(db.String(255))
#     timestamp = db.Column(db.DateTime)
#     account_id = db.Column(db.Integer, db.ForeignKey('account.id'))

# def create_tables():
#     db.create_all()

# def seed_data(total: int):
#     f = Faker('sv_SE')

#     admin_details = [
#         # Updated to use hashed passwords
#         {"namn": "Stefan Holmberg", "email": "stefan.holmberg@systementor.se", "username": "Admin",
#          "password": generate_password_hash("Hejsan123#")},
#         {"namn": "Sebastian Mentor", "email": "stefan.holmberg@nackademin.se", "username": "Cashier",
#          "password": generate_password_hash("Hejsan123#")},
#         {"namn": "Manpreet", "email": "manpreet.kaur@gmail.com", "username": "Manager",
#          "password": generate_password_hash("Hejsan123#")},
#     ]

#     for admin_detail in admin_details:
#         existing_admin = Admin.query.filter(Admin.email.ilike(admin_detail["email"])).first()

#         if existing_admin:
#             existing_admin.namn = admin_detail["namn"]
#             existing_admin.username = admin_detail["username"]
#             existing_admin.password = admin_detail["password"]
#         else:
#             admin = Admin(**admin_detail)
#             db.session.add(admin)

#         db.session.commit()

#     total_person = Customer.query.count()

#     while total_person < total:
#         namn = f.name()
#         email = f.email()

#         existing_customer = Customer.query.filter_by(email=email).first()
#         if existing_customer:
#             continue

#         personnummer = f.random_number(digits=10)
#         address = f.address()
#         city = f.city()

#         person = Customer(namn=namn, email=email, personnummer=personnummer, address=address, city=city)

#         for _ in range(random.randint(1, 3)):
#             account_number = f.random_number(digits=15)
#             account = Account(account_number=account_number)
#             person.accounts.append(account)

#             initial_deposit = 5000.0
#             initial_deposit_transaction = Transaction(
#                 amount=initial_deposit,
#                 transaction_type='Insättning',
#                 timestamp=datetime.now()
#             )
#             account.transactions.append(initial_deposit_transaction)

#             for _ in range(random.randint(5, 20)):
#                 amount = round(random.uniform(-500, 500), 2)
#                 transaction_type = 'Insättning' if amount > 0 else 'Uttag'
#                 timestamp = f.date_time_this_decade()

#                 transaction = Transaction(
#                     amount=amount,
#                     transaction_type=transaction_type,
#                     timestamp=timestamp
#                 )

#                 account.transactions.append(transaction)

#             db.session.add(account)

#         db.session.add(person)
#         db.session.commit()

#         total_person += 1
#         seed_data(500)

# After defining all the models and functions, call the following externally, not within seed_data itself:
#create_tables()
