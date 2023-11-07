from datetime import datetime
from flask import render_template, url_for, flash, redirect, request, abort
from tracking import app, db, bcrypt
from tracking.forms import RegistrationForm, LoginForm, UpdateAccountForm, TransactionForm, BudgetForm
from tracking.models import User, Transactions, Budget
from flask_login import login_user, current_user, logout_user, login_required

@app.route("/")
@app.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
    remaining_budget = get_remaining_budget()
    budget_dates = Budget.query.all()
    #transactions = Transactions.query.all()
    #return render_template('home.html', transactions=transactions)
    budget_entries = Budget.query.order_by(Budget.added_date.desc()).limit(5).all()
    transactions = Transactions.query.order_by(Transactions.transaction_date.desc()).paginate(page=page, per_page=5)
    return render_template('home.html', transactions=transactions, remaining_budget=remaining_budget, 
                           budget_dates=budget_dates, budget_entries=budget_entries, title = "Home")


def get_remaining_budget():
    totalBudget = Budget.query.with_entities(db.func.sum(Budget.amount_added)).scalar() or 0.0
    totalTransactions = Transactions.query.with_entities(db.func.sum(Transactions.amount)).scalar() or 0.0

    remainingBudget = totalBudget - totalTransactions
    return remainingBudget


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/acccount", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template('account.html', title='Account', form=form)


@app.route("/new_entry", methods=['GET', 'POST'])
@login_required
def new_entry():
    form = TransactionForm()
    if form.validate_on_submit():
        transaction_date_str = request.form.get('transaction_date')
        transaction_date = datetime.strptime(transaction_date_str, '%Y-%m-%d')
        transaction = Transactions(
            username = current_user.username,
            amount=form.amount.data,
            description=form.description.data,
            category=form.category.data,
            card_name=form.card_name.data,
            transaction_date=transaction_date
        )
        db.session.add(transaction)
        db.session.commit()
        flash('Your transaction has been added!', 'success')
        return redirect(url_for('home'))
    return render_template('new_entry.html', form=form, legend='New Transaction')


@app.route('/transaction/<int:id>')
def transaction(id):
    transaction = Transactions.query.get_or_404(id)
    return render_template('transaction.html', title= 'Specific transaction', transaction=transaction)


@app.route("/transactions/<int:id>/delete", methods=['POST'])
@login_required
def delete_transaction(id):
    transaction = Transactions.query.get_or_404(id)
    if transaction.user != current_user:
        abort(403)
    db.session.delete(transaction)
    db.session.commit()
    flash('Your transaction has been removed!', 'success')
    return redirect(url_for('home'))


@app.route("/transactions/<int:id>/update", methods=['GET', 'POST'])
@login_required
def update_transaction(id):
    transaction = Transactions.query.get_or_404(id)
    if transaction.username != current_user.username:
        abort(403)

    form = TransactionForm()
    if form.validate_on_submit():
        transaction_date_str = request.form.get('transaction_date')
        transaction_date = datetime.strptime(transaction_date_str, '%Y-%m-%d')
        transaction.amount = form.amount.data
        transaction.description = form.description.data
        transaction.category = form.category.data
        transaction.card_name = form.card_name.data
        transaction.transaction_date = transaction_date

        db.session.commit()
        flash('Your transaction has been updated!', 'success')
        return redirect(url_for('transaction', id=id))

    elif request.method == 'GET':
        form.amount.data = transaction.amount
        form.description.data = transaction.description
        form.category.data = transaction.category
        form.card_name.data = transaction.card_name
        form.transaction_date.data = transaction.transaction_date

    return render_template('new_entry.html', title='Update Transaction', form=form, legend='Update Transaction')



@app.route("/submit_budget", methods=['GET', 'POST'])
@login_required
def submit_budget():
    form = BudgetForm()
    if form.validate_on_submit():
        added_date_str = request.form.get('added_date')
        added_date = datetime.strptime(added_date_str, '%Y-%m-%d')
        budget = Budget(
            amount_added=form.amount_added.data,
            added_date=added_date
        )
        db.session.add(budget)
        db.session.commit()
        flash('Your budget has been updated!', 'success')
        return redirect(url_for('home'))
    return render_template('submit_budget.html', form=form, legend='Add Budget')


@app.route('/budget/<int:id>')
def budget(id):
    budget = Budget.query.get_or_404(id)
    return render_template('budget.html', title= 'Specific budget', budget=budget)


@app.route("/budget/<int:id>/delete", methods=['POST'])
@login_required
def delete_budget(id):
    budget = Budget.query.get_or_404(id)
    db.session.delete(budget)
    db.session.commit()
    flash('Budget has been updated!(Deleted entry)', 'success')
    return redirect(url_for('home'))


@app.route("/budget/<int:id>/update", methods=['GET', 'POST'])
@login_required
def update_budget(id):
    budget = Budget.query.get_or_404(id)
    form = BudgetForm()
    if form.validate_on_submit():
        budget_date_str = request.form.get('added_date')
        budget_date = datetime.strptime(budget_date_str, '%Y-%m-%d')
        budget.amount_added = form.amount_added.data
        budget.added_date = form.added_date.data

        db.session.commit()
        flash('Budget has been updated!(Edited entry)', 'success')
        return redirect(url_for('budget', id=id))

    elif request.method == 'GET':
        form.amount_added.data = budget.amount_added
        form.added_date.data = budget.added_date

    return render_template('submit_budget.html', title='Update budget entry', form=form, legend='Update budget entry')


@app.route("/user/<string:username>")
def user_transactions(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    transaction = Transactions.query.filter_by(user=user)\
        .order_by(Transactions.transaction_date.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_transactions.html', transaction=transaction, user=user)
