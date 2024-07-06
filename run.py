from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import datetime
import hashlib
from sqlalchemy import func

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Liquidmind.AI!@#$%^&*'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/liquidmind'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class MSME(db.Model):
    __tablename__ = 'msme'
    msme_id = db.Column(db.String(30), primary_key=True)
    msme_business_name = db.Column(db.String(50))
    phone_number = db.Column(db.Integer)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(128))  # Adjusted length for bcrypt hash
    erp_system = db.Column(db.String(10))
    erp_id = db.Column(db.String(30))
    industry = db.Column(db.String(30))

class Vendor(db.Model):
    __tablename__ = 'vendor'
    vendor_id = db.Column(db.String(30), primary_key=True)
    msme_id = db.Column(db.String(30), db.ForeignKey('msme.msme_id'))
    vendor_business_name = db.Column(db.String(30))
    phone_number = db.Column(db.Integer)
    email = db.Column(db.String(50))
    pg = db.Column(db.String(30))
    pg_link = db.Column(db.String(50))
    industry = db.Column(db.String(30))
    gstin = db.Column(db.Integer)

class Invoice(db.Model):
    __tablename__ = 'invoices'
    invoice_id = db.Column(db.String(30), primary_key=True)
    msme_id = db.Column(db.String(30), db.ForeignKey('msme.msme_id'))
    vendor_business_name = db.Column(db.String(30))
    vendor_id = db.Column(db.String(30), db.ForeignKey('vendor.vendor_id'))
    invoice_date = db.Column(db.Date)
    due_date = db.Column(db.Date)
    subtotal = db.Column(db.Numeric(12, 2))
    tax = db.Column(db.Numeric(12, 2))
    advance = db.Column(db.Numeric(12, 2))
    discount = db.Column(db.Numeric(12, 2))
    total_amount = db.Column(db.Numeric(12, 2))
    status = db.Column(db.String(20))

class PayNow(db.Model):
    __tablename__ = 'paynow'
    transaction_id = db.Column(db.String(30), primary_key=True)
    invoice_id = db.Column(db.String(30), db.ForeignKey('invoices.invoice_id'))
    total_amount_paid = db.Column(db.Numeric(12, 2))
    discount_type = db.Column(db.String(20))
    discount_amount = db.Column(db.Numeric(12, 2))
    overdue_fee_type = db.Column(db.String(20))
    overdue_fee = db.Column(db.Numeric(12, 2))
    timestamp = db.Column(db.DateTime)

class Installment(db.Model):
    __tablename__ = 'installments'
    installment_id = db.Column(db.String(20), primary_key=True)
    invoice_id = db.Column(db.String(30), db.ForeignKey('invoices.invoice_id'))
    selected_date = db.Column(db.Date)
    amount = db.Column(db.Numeric(12, 3))
    discount_type = db.Column(db.String(20))
    discount_amount = db.Column(db.Numeric(12, 2))
    overdue_fee_type = db.Column(db.String(20))
    overdue_fee = db.Column(db.Numeric(12, 2))
    transaction_id = db.Column(db.String(30), db.ForeignKey('paynow.transaction_id'))
    status = db.Column(db.String(30))

def generate_msme_id(email):
    now = datetime.datetime.now()
    datetime_str = now.strftime('%Y%m%d%H%M%S%f')
    unique_str = email + datetime_str
    user_id = hashlib.sha256(unique_str.encode()).hexdigest()
    return user_id

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    erp = request.form['erp']
    erp_id = request.form['erp_id']
    phone_number = request.form['phone_number']
    business_name = request.form['business_name']
    industry = request.form['industry']

    # Check if passwords match
    if password != confirm_password:
        flash('Passwords do not match!')
        return redirect(url_for('index'))

    # Check if email already exists
    existing_msme = MSME.query.filter_by(email=email).first()
    if existing_msme:
        flash('Email already exists!')
        return redirect(url_for('index'))

    # Hash the password using bcrypt
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    print(f"DEBUG: Hashed password: {hashed_password}")

    # Generate MSME ID
    msme_id = generate_msme_id(email)

    # Create new MSME instance
    new_msme = MSME(
        msme_id=msme_id,
        msme_business_name=business_name,
        phone_number=phone_number,
        email=email,
        password=hashed_password,
        erp_system=erp,
        erp_id=erp_id,
        industry=industry
    )

    # Add to database
    db.session.add(new_msme)
    db.session.commit()

    flash('Registration successful!')
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    # Find MSME by email
    msme = MSME.query.filter_by(email=email).first()
    print(f"DEBUG: Retrieved MSME: {msme}")

    if not msme:
        flash('Login Unsuccessful. Please check email and password.')
        return redirect(url_for('index'))

    # Check password hash
    password_match = bcrypt.check_password_hash(msme.password, password)
    print(f"DEBUG: Password hash from DB: {msme.password}")
    print(f"DEBUG: Password entered: {password}")
    print(f"DEBUG: Password match: {password_match}")

    if not password_match:
        flash('Login Unsuccessful. Please check email and password.')
        return redirect(url_for('index'))

    # Set session or token for the user
    session['user_id'] = msme.msme_id

    flash('Login successful!')
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in first.')
        return redirect(url_for('index'))

    # Fetch user details
    msme = MSME.query.filter_by(msme_id=user_id).first()

    # Fetch invoice and payment data
    total_invoices = db.session.query(func.count(Invoice.invoice_id)).filter_by(msme_id=user_id).scalar()
    total_paid = db.session.query(func.sum(Invoice.total_amount)).filter_by(msme_id=user_id, status='Paid').scalar() or 0
    due = db.session.query(func.sum(Invoice.total_amount)).filter_by(msme_id=user_id, status='Due').scalar() or 0
    overdue = db.session.query(func.sum(Invoice.total_amount)).filter_by(msme_id=user_id, status='Overdue').scalar() or 0
    discount = db.session.query(func.sum(PayNow.discount_amount)).join(Invoice).filter(Invoice.msme_id == user_id).scalar() or 0
    late_fees_paid = db.session.query(func.sum(PayNow.overdue_fee)).join(Invoice).filter(Invoice.msme_id == user_id).scalar() or 0

    invoices_due_today = db.session.query(func.count(Invoice.invoice_id)).filter_by(msme_id=user_id, due_date=datetime.date.today()).scalar()
    amount_due_today = db.session.query(func.sum(Invoice.total_amount)).filter_by(msme_id=user_id, due_date=datetime.date.today()).scalar() or 0
    total_vendors = Vendor.query.filter_by(msme_id=user_id).count()
    average_days_to_pay = db.session.query(func.avg(func.datediff(PayNow.timestamp, Invoice.due_date))).join(Invoice).filter(Invoice.msme_id == user_id).scalar() or 0

    # Fetch next 7 payments due
    next_payments_due = db.session.query(Invoice.vendor_business_name, Invoice.due_date, Invoice.total_amount)\
                                  .filter(Invoice.msme_id == user_id, Invoice.status == 'Due')\
                                  .order_by(Invoice.due_date.asc())\
                                  .limit(7).all()

    return render_template('dashboard.html', user=msme, total_invoices=total_invoices, total_paid=total_paid, due=due, overdue=overdue, 
                           discount=discount, late_fees_paid=late_fees_paid, invoices_due_today=invoices_due_today, amount_due_today=amount_due_today, 
                           total_vendors=total_vendors, average_days_to_pay=average_days_to_pay, next_payments_due=next_payments_due)

@app.route('/vendors', methods=['GET', 'POST'])
def vendors():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in first.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        vendor_business_name = request.form['vendor_business_name']
        vendor_id = request.form['vendor_id']
        phone_number = request.form['phone_number']
        email = request.form['email']
        pg = request.form['pg']
        pg_link = request.form['pg_link']
        industry = request.form['industry']
        gstin = request.form['gstin']

        new_vendor = Vendor(
            vendor_id=vendor_id,
            msme_id=user_id,
            vendor_business_name=vendor_business_name,
            phone_number=phone_number,
            email=email,
            pg=pg,
            pg_link=pg_link,
            industry=industry,
            gstin=gstin
        )

        db.session.add(new_vendor)
        db.session.commit()
        flash('Vendor registered successfully!')

    # Fetch all vendors for this MSME
    vendors = Vendor.query.filter_by(msme_id=user_id).all()

    return render_template('vendors.html', user=MSME.query.filter_by(msme_id=user_id).first(), vendors=vendors)

@app.route('/edit_vendor/<vendor_id>', methods=['GET', 'POST'])
def edit_vendor(vendor_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in first.')
        return redirect(url_for('index'))

    vendor = Vendor.query.get(vendor_id)

    if request.method == 'POST':
        vendor.vendor_business_name = request.form['vendor_business_name']
        vendor.phone_number = request.form['phone_number']
        vendor.email = request.form['email']
        vendor.pg = request.form['pg']
        vendor.pg_link = request.form['pg_link']
        vendor.industry = request.form['industry']
        vendor.gstin = request.form['gstin']

        db.session.commit()
        flash('Vendor details updated successfully!')
        return redirect(url_for('vendors'))

    return render_template('edit_vendor.html', user=MSME.query.filter_by(msme_id=user_id).first(), vendor=vendor)

@app.route('/delete_vendor/<vendor_id>', methods=['POST'])
def delete_vendor(vendor_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in first.')
        return redirect(url_for('index'))

    vendor = Vendor.query.get(vendor_id)
    db.session.delete(vendor)
    db.session.commit()
    flash('Vendor deleted successfully!')

    return redirect(url_for('vendors'))

@app.route('/calendar')
def calendar():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in first.')
        return redirect(url_for('index'))

    return render_template('calendar.html', user=MSME.query.filter_by(msme_id=user_id).first())

@app.route('/profile')
def profile():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in first.')
        return redirect(url_for('index'))

    msme = MSME.query.filter_by(msme_id=user_id).first()
    return render_template('profile.html', user=msme)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/google_login')
def google_login():
    # Implement Google OAuth login
    pass

if __name__ == '__main__':
    app.run(debug=True)
