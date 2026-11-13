import os
import random
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from flask_mail import Message
from app import db, mail
from app.models import User, Job, JobApplication, Review

main_bp = Blueprint('main', __name__)

# Temporary OTP storage
otp_storage = {}

# Helper function to save uploaded files
def save_file(file_storage):
    from flask import current_app
    if file_storage and file_storage.filename != '':
        filename = secure_filename(file_storage.filename)
        upload_folder = os.path.join(current_app.root_path, 'static/uploads')
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        file_storage.save(file_path)
        return filename
    return None

@main_bp.route('/')
def home():
    return render_template('index.html')

@main_bp.route('/contact')
def contact_page():
    return render_template('contact.html')

# Register Page & Form Submission
@main_bp.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        name = request.form.get('fullname') or request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        phone = request.form.get('phone')
        
        # Driver 1km rate capture (if role is driver)
        rate_per_km_val = 0.0
        if role == 'driver':
            rate_input = request.form.get('rate_per_km')
            if rate_input:
                rate_per_km_val = float(rate_input)
                
        if User.query.filter_by(email=email).first():
            flash('Email already exists!', 'danger')
            return redirect(url_for('main.register_page'))
            
        nic_doc = save_file(request.files.get('nic_client') or request.files.get('nic_driver'))
        bus_reg = save_file(request.files.get('business_reg'))
        drv_lic = save_file(request.files.get('driving_license'))
        veh_lic = save_file(request.files.get('vehicle_license'))
        veh_pho = save_file(request.files.get('vehicle_photo'))
        pol_rep = save_file(request.files.get('police_report'))
        
        new_user = User(
            name=name,
            email=email,
            password=password,
            role=role,
            phone=phone,
            rate_per_km=rate_per_km_val,
            nic_document=nic_doc,
            business_reg=bus_reg,
            driving_license=drv_lic,
            vehicle_license=veh_lic,
            vehicle_photo=veh_pho,
            police_report=pol_rep,
            is_approved=False,
            is_admin=False
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Awaiting admin approval.', 'success')
        return redirect(url_for('main.login_page'))
    return render_template('register.html')

# Login Route
@main_bp.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('No account found with this email! Please register first.', 'danger')
            return redirect(url_for('main.login_page'))
            
        if user.password != password:
            flash('Incorrect password! Please try again.', 'danger')
            return redirect(url_for('main.login_page'))
            
        session['user_id'] = user.id
        session['name'] = user.name
        session['is_admin'] = user.is_admin
        session['role'] = user.role
        flash('Login successful!', 'success')
        
        if user.is_admin:
            return redirect(url_for('main.admin_dashboard'))
        else:
            return redirect(url_for('main.home'))
            
    return render_template('login.html')

# Forgot Password Route (Sends OTP via SMTP)
@main_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('No account found with this email address.', 'danger')
            return redirect(url_for('main.forgot_password'))
            
        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))
        otp_storage[email] = otp
        
        # Send OTP via SMTP (Gmail)
        try:
            msg = Message(
                subject="Port Link - Password Reset OTP",
                recipients=[email],
                body=f"Hello {user.name},\n\nYour OTP for password reset is: {otp}\n\nThis OTP is valid for 10 minutes. Do not share it with anyone."
            )
            mail.send(msg)
            flash('6-digit OTP has been sent to your email address. Please check your inbox.', 'success')
            return redirect(url_for('main.verify_otp', email=email))
        except Exception as e:
            print("Mail Error:", e)
            flash('Failed to send OTP email. Please check your email configuration.', 'danger')
            
    return render_template('forgot_password.html')

# Verify OTP Route
@main_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    email = request.args.get('email')
    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        if otp_storage.get(email) == entered_otp:
            flash('OTP verified successfully! Now you can reset your password.', 'success')
            return redirect(url_for('main.reset_password', email=email))
        else:
            flash('Invalid or expired OTP. Please try again.', 'danger')
            
    return render_template('verify_otp.html', email=email)

# Reset Password Route
@main_bp.route('/reset-password/<email>', methods=['GET', 'POST'])
def reset_password(email):
    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('main.reset_password', email=email))
            
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = new_password
            db.session.commit()
            
            if email in otp_storage:
                del otp_storage[email]
                
            flash('Password reset successful! Please log in with your new password.', 'success')
            return redirect(url_for('main.login_page'))
            
    return render_template('reset_password.html', email=email)

# Admin Login Route
@main_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.password == password and user.is_admin:
            session['user_id'] = user.id
            session['name'] = user.name
            session['is_admin'] = True
            session['role'] = user.role
            flash('Admin Login successful!', 'success')
            return redirect(url_for('main.admin_dashboard'))
        else:
            flash('Invalid Admin Credentials or Unauthorized Access!', 'danger')
            return redirect(url_for('main.admin_login'))
            
    return render_template('admin_login.html')

# Logout Route
@main_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('main.home'))

# User Profile View & Update Request
@main_bp.route('/profile', methods=['GET', 'POST'])
def user_profile():
    if 'user_id' not in session:
        flash('Please log in first.', 'danger')
        return redirect(url_for('main.login_page'))
        
    user = User.query.get_or_404(session['user_id'])
    if request.method == 'POST':
        user.pending_name = request.form.get('fullname')
        user.pending_phone = request.form.get('phone')
        
        if user.role == 'driver':
            rate = request.form.get('rate_per_km')
            if rate:
                user.rate_per_km = float(rate)
                
        nic_doc = save_file(request.files.get('nic_doc'))
        bus_reg = save_file(request.files.get('business_reg'))
        drv_lic = save_file(request.files.get('driving_license'))
        veh_lic = save_file(request.files.get('vehicle_license'))
        veh_pho = save_file(request.files.get('vehicle_photo'))
        pol_rep = save_file(request.files.get('police_report'))
        
        if nic_doc: user.pending_nic = nic_doc
        if bus_reg: user.pending_bus_reg = bus_reg
        if drv_lic: user.pending_driving_license = drv_lic
        if veh_lic: user.pending_vehicle_license = veh_lic
        if veh_pho: user.pending_vehicle_photo = veh_pho
        if pol_rep: user.pending_police_report = pol_rep
        
        user.has_pending_update = True
        db.session.commit()
        flash('Profile update request submitted successfully! Awaiting admin approval.', 'success')
        return redirect(url_for('main.user_profile'))
        
    return render_template('profile.html', user=user)

# View All Jobs Page
@main_bp.route('/jobs')
def jobs_page():
    jobs = Job.query.all()
    return render_template('jobs.html', jobs=jobs)

# Client Post Job Route (With email notification to all approved drivers)
@main_bp.route('/post-job', methods=['GET', 'POST'])
def post_job():
    if 'user_id' not in session:
        flash('Please log in first to post a job.', 'danger')
        return redirect(url_for('main.login_page'))
        
    user = User.query.get_or_404(session['user_id'])
    if user.role != 'client':
        flash('Only clients can post jobs!', 'danger')
        return redirect(url_for('main.jobs_page'))
        
    if request.method == 'POST':
        new_job = Job(
            container_size=request.form.get('container_size'),
            pickup_location=request.form.get('pickup_location'),
            dropoff_location=request.form.get('dropoff_location'),
            description=request.form.get('description'),
            client_id=user.id,
            status='Pending'
        )
        db.session.add(new_job)
        db.session.commit()
        
        # Send email notification to all approved drivers
        try:
            drivers = User.query.filter_by(role='driver', is_approved=True).all()
            driver_emails = [d.email for d in drivers if d.email]
            
            if driver_emails:
                from flask import current_app
                msg = Message(
                    subject="Port Link - New Transport Job Posted!",
                    recipients=[current_app.config.get('MAIL_USERNAME')],
                    bcc=driver_emails,
                    body=f"Hello Driver,\n\nA new transport job has been posted by {user.name}!\n\nPickup: {new_job.pickup_location}\nDropoff: {new_job.dropoff_location}\nContainer Size: {new_job.container_size}\n\nPlease log in to the Port Link platform to view details and apply.\n\nBest Regards,\nPort Link Team"
                )
                mail.send(msg)
        except Exception as e:
            print("Job Notification Email Error:", e)

        flash('Job posted successfully and notifications sent to drivers!', 'success')
        return redirect(url_for('main.jobs_page'))
        
    return render_template('post_job.html')

# Driver Apply for Job (With email notification to the job owner / client)
@main_bp.route('/apply-job/<int:job_id>', methods=['POST'])
def apply_job(job_id):
    if 'user_id' not in session:
        flash('Please log in as a driver to apply.', 'danger')
        return redirect(url_for('main.login_page'))
        
    driver = User.query.get_or_404(session['user_id'])
    if driver.role != 'driver':
        flash('Only registered drivers can apply for transport jobs!', 'danger')
        return redirect(url_for('main.jobs_page'))
        
    job = Job.query.get_or_404(job_id)
    
    existing_app = JobApplication.query.filter_by(job_id=job.id, driver_id=driver.id).first()
    if existing_app:
        flash('You have already applied for this job!', 'warning')
        return redirect(url_for('main.jobs_page'))
        
    new_application = JobApplication(
        job_id=job.id,
        driver_id=driver.id,
        status='Pending'
    )
    db.session.add(new_application)
    db.session.commit()
    
    # Send email notification to the client
    try:
        client = User.query.get(job.client_id)
        if client and client.email:
            msg = Message(
                subject="Port Link - New Driver Request for your Job!",
                recipients=[client.email],
                body=f"Hello {client.name},\n\nDriver {driver.name} has requested/applied for your transport job ({job.pickup_location} to {job.dropoff_location}).\n\nPlease log in to your Port Link dashboard to view the driver's details and approve the selection.\n\nBest Regards,\nPort Link Team"
            )
            mail.send(msg)
    except Exception as e:
        print("Driver Request Email Error:", e)

    flash('Successfully applied for the transport job and notified the client!', 'success')
    return redirect(url_for('main.jobs_page'))

# Client Rate Driver Route
@main_bp.route('/job/<int:job_id>/rate-driver', methods=['POST'])
def rate_driver(job_id):
    if 'user_id' not in session:
        flash('Please log in first.', 'danger')
        return redirect(url_for('main.login_page'))
        
    job = Job.query.get_or_404(job_id)
    if job.client_id != session['user_id']:
        flash('Unauthorized action!', 'danger')
        return redirect(url_for('main.jobs_page'))
        
    if not job.driver_id:
        flash('No driver assigned to this job yet!', 'warning')
        return redirect(url_for('main.jobs_page'))
        
    rating = request.form.get('rating')
    comment = request.form.get('comment')
    
    existing_review = Review.query.filter_by(job_id=job.id, client_id=session['user_id']).first()
    if existing_review:
        existing_review.rating = int(rating)
        existing_review.comment = comment
        flash('Review updated successfully!', 'success')
    else:
        new_review = Review(
            job_id=job.id,
            client_id=session['user_id'],
            driver_id=job.driver_id,
            rating=int(rating),
            comment=comment
        )
        db.session.add(new_review)
        flash('Driver rated and reviewed successfully!', 'success')
        
    db.session.commit()
    return redirect(url_for('main.jobs_page'))

# Client Delete Job Route
@main_bp.route('/job/delete/<int:job_id>', methods=['POST'])
def delete_job(job_id):
    if 'user_id' not in session:
        flash('Please log in first.', 'danger')
        return redirect(url_for('main.login_page'))
        
    job = Job.query.get_or_404(job_id)
    if job.client_id != session['user_id']:
        flash('Unauthorized action! You can only delete your own job posts.', 'danger')
        return redirect(url_for('main.jobs_page'))
        
    db.session.delete(job)
    db.session.commit()
    flash('Job post deleted successfully!', 'success')
    return redirect(url_for('main.jobs_page'))

# Client Selects a Driver from Applicants
@main_bp.route('/job/<int:job_id>/select-driver/<int:driver_id>', methods=['POST'])
def select_driver(job_id, driver_id):
    if 'user_id' not in session:
        flash('Please log in first.', 'danger')
        return redirect(url_for('main.login_page'))
        
    job = Job.query.get_or_404(job_id)
    if job.client_id != session['user_id']:
        flash('Unauthorized action!', 'danger')
        return redirect(url_for('main.jobs_page'))
        
    job.driver_id = driver_id
    job.status = 'Assigned'
    
    app = JobApplication.query.filter_by(job_id=job_id, driver_id=driver_id).first()
    if app:
        app.status = 'Selected'
        
    db.session.commit()
    flash('Driver selected successfully for your transport job!', 'success')
    return redirect(url_for('main.jobs_page'))

# Admin Dashboard
@main_bp.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Unauthorized access! Please log in as admin.', 'danger')
        return redirect(url_for('main.admin_login'))
        
    users = User.query.all()
    jobs = Job.query.all()
    return render_template('admin_dashboard.html', users=users, jobs=jobs)

# Admin Approve User
@main_bp.route('/admin/approve/<int:user_id>', methods=['POST'])
def approve_user(user_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('main.admin_login'))
        
    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()
    flash(f'User {user.name} approved successfully!', 'success')
    return redirect(url_for('main.admin_dashboard'))

# Admin Approve Profile Update
@main_bp.route('/admin/approve_update/<int:user_id>', methods=['POST'])
def approve_profile_update(user_id):
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('main.admin_login'))
        
    user = User.query.get_or_404(user_id)
    if user.has_pending_update:
        if user.pending_name: user.name = user.pending_name
        if user.pending_phone: user.phone = user.pending_phone
        if user.pending_nic: user.nic_document = user.pending_nic
        if user.pending_bus_reg: user.business_reg = user.pending_bus_reg
        if user.pending_driving_license: user.driving_license = user.pending_driving_license
        if user.pending_vehicle_license: user.vehicle_license = user.pending_vehicle_license
        if user.pending_vehicle_photo: user.vehicle_photo = user.pending_vehicle_photo
        if user.pending_police_report: user.police_report = user.pending_police_report
        
        user.pending_name = None
        user.pending_phone = None
        user.pending_nic = None
        user.pending_bus_reg = None
        user.pending_driving_license = None
        user.pending_vehicle_license = None
        user.pending_vehicle_photo = None
        user.pending_police_report = None
        user.has_pending_update = False
        db.session.commit()
        
    flash(f'Profile update for {user.name} approved successfully!', 'success')
    return redirect(url_for('main.admin_dashboard'))

# Admin Delete User (With cascade/safety checks for driver applications)
@main_bp.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('main.admin_login'))
        
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Cannot delete admin account!', 'danger')
        return redirect(url_for('main.admin_dashboard'))
        
    # Safety check: Delete driver's job applications first if user is a driver
    if user.role == 'driver':
        JobApplication.query.filter_by(driver_id=user.id).delete()
        
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.name} has been removed successfully.', 'success')
    return redirect(url_for('main.admin_dashboard'))

# Admin Profile Update Route
@main_bp.route('/admin/update_profile', methods=['POST'])
def update_admin_profile():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('main.admin_login'))
        
    admin_user = User.query.get_or_404(session['user_id'])
    new_name = request.form.get('admin_name')
    new_password = request.form.get('admin_password')
    
    if new_name:
        admin_user.name = new_name
        session['name'] = new_name
    if new_password:
        admin_user.password = new_password
        
    db.session.commit()
    flash('Admin profile updated successfully!', 'success')
    return redirect(url_for('main.admin_dashboard'))