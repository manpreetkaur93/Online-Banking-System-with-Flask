from flask import Flask, flash, render_template, request, jsonify, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_required
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy,pagination
from sqlalchemy import or_,func
from faker import Faker
import random
from flask_session import Session
from flask_paginate import Pagination
from sqlalchemy.sql import func
from datetime import datetime
from sqlalchemy import asc
from sqlalchemy.orm import joinedload
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField
from wtforms.validators import DataRequired

db = SQLAlchemy()
migrate = None
app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+mysqlconnector://root:password@localhost:3306/bank_application"
app.config['SECRET_KEY'] = 'someverysecretkeyhere'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

db.init_app(app)
Session(app)
migrate = Migrate(app, db)
# login_manager = LoginManager(app)
# login_manager.login_view = 'login'
# Bootstrap(app)
class Customer(db.Model):
    __tablename__ = 'customer'
    id = db.Column(db.Integer, primary_key=True)
    namn = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)
    personnummer = db.Column(db.String(10), unique=True)
    address = db.Column(db.String(255))
    city = db.Column(db.String(255))
    accounts = db.relationship('Account', backref='customer', lazy=True)
    
    def __repr__(self):
        return f"<Customer {self.namn} - Email: {self.email}>"
    
    @property
    def total_balance(self):
        total_balance = 0
        for account in self.accounts:
            total_balance += account.calculate_balance()
        return round(total_balance, 2)

    @total_balance.setter
    def total_balance(self, value):
        pass
    
class Admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    namn = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(512), nullable=False)  # Adjusted for hashed passwords

    @classmethod
    def authenticate(cls, username, password):
        admin = cls.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            return admin
        return None

class Account(db.Model):
    __tablename__ = 'account'
    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(15), unique=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    transactions = db.relationship('Transaction', backref='account', lazy=True)
    
    def calculate_balance(self):
        balance = 0
        for transaction in self.transactions:
            balance += transaction.amount
        return balance

class Transaction(db.Model):
    __tablename__ = 'transaction'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float)
    transaction_type = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'))

# def create_tables():
#     db.create_all()

def seed_data(total: int):
    f = Faker('sv_SE')

    admin_details = [
        # Updated to use hashed passwords
        {"namn": "Stefan Holmberg", "email": "stefan.holmberg@systementor.se", "username": "Admin",
         "password": generate_password_hash("Hejsan123#")},
        {"namn": "Sebastian Mentor", "email": "stefan.holmberg@nackademin.se", "username": "Cashier",
         "password": generate_password_hash("Hejsan123#")},
        {"namn": "Manpreet", "email": "manpreet.kaur@gmail.com", "username": "Manager",
         "password": generate_password_hash("Hejsan123#")},
    ]

    for admin_detail in admin_details:
        existing_admin = Admin.query.filter(Admin.email.ilike(admin_detail["email"])).first()

        if existing_admin:
            existing_admin.namn = admin_detail["namn"]
            existing_admin.username = admin_detail["username"]
            existing_admin.password = admin_detail["password"]
        else:
            admin = Admin(**admin_detail)
            db.session.add(admin)

        db.session.commit()

    total_person = Customer.query.count()

    while total_person < total:
        namn = f.name()
        email = f.email()

        existing_customer = Customer.query.filter_by(email=email).first()
        if existing_customer:
            continue

        personnummer = f.random_number(digits=10)
        address = f.address()
        city = f.city()

        person = Customer(namn=namn, email=email, personnummer=personnummer, address=address, city=city)

        for _ in range(random.randint(1, 3)):
            account_number = f.random_number(digits=15)
            account = Account(account_number=account_number)
            person.accounts.append(account)

            initial_deposit = 5000.0
            initial_deposit_transaction = Transaction(
                amount=initial_deposit,
                transaction_type='Insättning',
                timestamp=datetime.now()
            )
            account.transactions.append(initial_deposit_transaction)

            for _ in range(random.randint(5, 20)):
                amount = round(random.uniform(-500, 500), 2)
                transaction_type = 'Insättning' if amount > 0 else 'Uttag'
                timestamp = f.date_time_this_decade()

                transaction = Transaction(
                    amount=amount,
                    transaction_type=transaction_type,
                    timestamp=timestamp
                )

                account.transactions.append(transaction)

            db.session.add(account)

        db.session.add(person)
        db.session.commit()

        total_person += 1
        
@app.route("/login")
def index():
    total_customers = Customer.query.count()
    total_accounts = Account.query.count()
    total_balance = db.session.query(func.round(func.sum(Transaction.amount), 2)).scalar() or 0

    return render_template('index.html', total_customers=total_customers, total_accounts=total_accounts, total_balance=total_balance)


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = Admin.authenticate(username, password)
        if user:
            session["user_id"] = user.id
            return redirect(url_for("index"))
        else:
            error_message = "Invalid username or password."
            return render_template("login.html", error_message=error_message)
    return render_template("login.html")

@app.route("/home")
#@login_required
def home():
    total_customers = Customer.query.count()
    total_accounts = Account.query.count()
    total_balance = db.session.query(func.round(func.sum(Transaction.amount), 2)).scalar() or 0

    return render_template('index.html', total_customers=total_customers, total_accounts=total_accounts, total_balance=total_balance)


@app.route("/customers", strict_slashes=False)
#@login_required
def customers():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    customers_paginated = Customer.query.order_by(Customer.id.asc()).paginate(page=page, per_page=per_page)
    return render_template("customers.html", customers_paginated=customers_paginated)

@app.route("/template")
def template():
    return render_template("base.html")

from sqlalchemy import or_

@app.route("/search", methods=["GET"])
#@login_required
def search():
    search_query = request.args.get("search_query", "")  # Default to empty string if not found
    sort_order = request.args.get("sort_order", "asc")  # Default to ascending if not found
    page = request.args.get('page', 1, type=int)
    per_page = 10

    if search_query:
        search_filter = (
            Customer.personnummer.like(f"%{search_query}%") |
            Customer.city.like(f"%{search_query}%") |
            Customer.namn.like(f"%{search_query}%") |
            Customer.address.like(f"%{search_query}%")
        )
    else:
        search_filter = (Customer.id > 0)  # Show all if no search query

    if sort_order == "asc":
        results = Customer.query.filter(search_filter).order_by(Customer.namn.asc()).paginate(page=page, per_page=per_page, error_out=False)
    else:
        results = Customer.query.filter(search_filter).order_by(Customer.namn.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return render_template("search_results.html", search_results=results, search_query=search_query, sort_order=sort_order)


@app.route("/customer/<int:customer_id>")
#@login_required
def view_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    return render_template("customer_profil.html", customer=customer)

@app.route('/view_account_transactions/<account_id>', methods=['GET'])
#@login_required
def view_account_transactions(account_id):
    account = Account.query.get(account_id)
    if account:
        total_balance = account.calculate_balance()
        order = request.args.get('order', 'desc')
        sort_column = Transaction.timestamp
        if order == 'asc':
            sort_column = sort_column.asc()
        else:
            sort_column = sort_column.desc()
        page = request.args.get('page', 1, type=int)
        per_page = 10
        transactions_paginated = Transaction.query.filter_by(account_id=account.id).order_by(sort_column).paginate(page=page, per_page=per_page, error_out=False)
        return render_template('account_transactions.html', account=account, transactions_paginated=transactions_paginated, order=order, total_balance=total_balance)
    return redirect(url_for('search'))

@app.route("/deposit", methods=["GET", "POST"])
#@login_required
def deposit():
    if request.method == "POST":
        account_number = request.form.get("account_number")
        deposit_amount = request.form.get("deposit_amount", type=float)

        # Check for a valid account number and positive deposit amount
        account = Account.query.filter_by(account_number=account_number).first()
        if not account:
            error_message = "Account not found. Please enter a valid account number."
            return render_template("deposit.html", error_message=error_message)

        if deposit_amount is None or deposit_amount <= 0:
            error_message = "Invalid deposit amount. Please enter a positive number."
            return render_template("deposit.html", error_message=error_message)

        # Process the deposit
        account_balance = sum(transaction.amount for transaction in account.transactions) + deposit_amount
        deposit_transaction = Transaction(
            amount=deposit_amount,
            transaction_type='Deposit',
            timestamp=datetime.now(),
            account=account
        )
        db.session.add(deposit_transaction)
        db.session.commit()

        return render_template("deposit_success.html", 
                       account=account, 
                       deposit_amount=deposit_amount, 
                       deposit_transaction=deposit_transaction, 
                       account_balance=account_balance)


    return render_template("deposit.html")


class WithdrawalForm(FlaskForm):
    account_number = StringField('Account Number', validators=[DataRequired()])
    withdrawal_amount = DecimalField('Amount (SEK)', validators=[DataRequired()])

@app.route("/withdrawal", methods=["GET", "POST"])
#@login_required
def withdrawal():
    form = WithdrawalForm()
    if form.validate_on_submit():
        account_number = form.account_number.data
        withdrawal_amount = float(form.withdrawal_amount.data)  

        account = Account.query.filter_by(account_number=account_number).first()

        if not account:
            flash("Account not found. Please try again!", 'danger')
            return render_template("withdraw.html", form=form)

        current_balance = sum(transaction.amount for transaction in account.transactions)
        if withdrawal_amount <= 0 or withdrawal_amount > current_balance:
            flash("Invalid amount or insufficient funds. Please try again!", 'danger')
            return render_template("withdraw.html", form=form)

        withdrawal_transaction = Transaction(
            amount=-withdrawal_amount,
            transaction_type='Withdraw',
            timestamp=datetime.now(),
            account=account
        )
        db.session.add(withdrawal_transaction)
        db.session.commit()

        # Store withdrawal details in session for success page
        session['withdrawal_details'] = {
            'amount': withdrawal_amount,
            'timestamp': withdrawal_transaction.timestamp.strftime('%Y-%m-%d %H:%M'),
            'new_balance': current_balance - withdrawal_amount
        }

        return redirect(url_for('withdraw_success', account_id=account.id))
    return render_template("withdraw.html", form=form)

@app.route('/withdraw_success/<int:account_id>')
#@login_required
def withdraw_success(account_id):
    account = Account.query.get_or_404(account_id)
    withdrawal_details = session.get('withdrawal_details', {})
    return render_template('withdraw_success.html', account=account, withdrawal_details=withdrawal_details)

@app.route("/transfer", methods=["GET", "POST"])
#@login_required
def transfer():
    if request.method == "POST":
        from_account_number = request.form.get("from_account_number")
        to_account_number = request.form.get("to_account_number")
        transfer_amount = float(request.form.get("transfer_amount"))

        from_account = Account.query.filter_by(account_number=from_account_number).first()
        to_account = Account.query.filter_by(account_number=to_account_number).first()

        # Check if both accounts exist
        if not from_account or not to_account:
            flash("One of the accounts is not found. Please try again!", "danger")
            return redirect(url_for('transfer'))
        
        # Validate transfer amount
        if transfer_amount <= 0:
            flash("Invalid transfer amount. Please enter a positive number.", "danger")
            return redirect(url_for('transfer'))

        # Ensure from_account has transactions before summing
        if from_account.transactions:
            from_account_balance = sum(transaction.amount for transaction in from_account.transactions)
        else:
            from_account_balance = 0.0

        # Check if the sending account has enough funds
        if transfer_amount > from_account_balance:
            flash("Not enough funds in the sender's account. Please try a lower amount!", "danger")
            return redirect(url_for('transfer'))

        # Create and add the transactions
        from_transfer_transaction = Transaction(
            amount=-transfer_amount,
            transaction_type='Transfer Out',
            timestamp=datetime.now(),
            account=from_account
        )

        to_transfer_transaction = Transaction(
            amount=transfer_amount,
            transaction_type='Transfer In',
            timestamp=datetime.now(),
            account=to_account
        )

        db.session.add(from_transfer_transaction)
        db.session.add(to_transfer_transaction)
        db.session.commit()
        new_from_account_balance = from_account_balance - transfer_amount

        return render_template("transfer_success.html", from_account=from_account, to_account=to_account, transfer_amount=transfer_amount, from_transfer_transaction=from_transfer_transaction, to_transfer_transaction=to_transfer_transaction, from_account_balance=new_from_account_balance)

    return render_template("transfer.html")

@app.route('/logout')
def logout():
    # Remove user from session
    session.pop('user_id', None)
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('login'))

if __name__ == "__main__":
    with app.app_context():
         db.create_all() 
         seed_data(500) 
    app.run(debug=True)
