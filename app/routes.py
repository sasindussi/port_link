import os
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from app import db
from app.models import User, Job

main_bp = Blueprint('main', __name__)

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

# Client Post Job Route
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
        flash('Job posted successfully!', 'success')
        return redirect(url_for('main.jobs_page'))
        
    return render_template('post_job.html')

@main_bp.route('/apply-job/<int:job_id>', methods=['POST'])
def apply_job(job_id):
    if 'user_id' not in session:
        flash('Please log in as a driver to apply.', 'danger')
        return redirect(url_for('main.login_page'))
        
    user = User.query.get_or_404(session['user_id'])
    if user.role != 'driver':
        flash('Only registered drivers can apply for transport jobs!', 'danger')
        return redirect(url_for('main.jobs_page'))
        
    job = Job.query.get_or_404(job_id)
    job.driver_id = user.id
    job.status = f'Accepted by Driver: {user.name}'
    db.session.commit()
    flash('Successfully applied and accepted the transport job!', 'success')
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

# Admin Delete User
@main_bp.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('main.admin_login'))
        
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Cannot delete admin account!', 'danger')
        return redirect(url_for('main.admin_dashboard'))
        
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