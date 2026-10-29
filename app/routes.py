from flask import current_app as app, request, jsonify, render_template
from app import db
from .models import User, Job

# ==================== WEB PAGE ROUTES ====================

# Render Home / Landing Page
@app.route('/')
def home():
    return render_template('index.html')

# Render Register Page
@app.route('/register')
def register_page():
    return render_template('register.html')

# Render Available Jobs Page (Public View)
@app.route('/jobs')
def jobs_page():
    return render_template('jobs.html')

# Render Login Page
@app.route('/login')
def login_page():
    return render_template('login.html')

# Render Contact Us Page
@app.route('/contact')
def contact_page():
    return render_template('contact.html')


# ==================== API ENDPOINTS ====================

# User Registration API
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({"error": "Email already exists!"}), 400
        
    new_user = User(
        name=data.get('name'),
        email=data.get('email'),
        password=data.get('password'),
        role=data.get('role'),
        phone=data.get('phone')
    )
    
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered successfully!"}), 201

# User Login API
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    
    if user and user.password == data.get('password'):
        return jsonify({
            "message": "Login successful!",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role
            }
        }), 200
    
    return jsonify({"error": "Invalid email or password!"}), 401

# Create Container Transport Job (Client) API
@app.route('/api/jobs', methods=['POST'])
def create_job():
    data = request.get_json()
    
    new_job = Job(
        client_id=data.get('client_id'),
        container_size=data.get('container_size'),
        pickup_location=data.get('pickup_location'),
        dropoff_location=data.get('dropoff_location')
    )
    
    db.session.add(new_job)
    db.session.commit()
    return jsonify({"message": "Job posted successfully!"}), 201

# Get All Available Jobs (For Drivers / Guests) API
@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    jobs = Job.query.all()
    job_list = []
    for job in jobs:
        job_list.append({
            "id": job.id,
            "client_id": job.client_id,
            "driver_id": job.driver_id,
            "container_size": job.container_size,
            "pickup_location": job.pickup_location,
            "dropoff_location": job.dropoff_location,
            "status": job.status
        })
    return jsonify(job_list), 200

# Driver Accept Job API
@app.route('/api/jobs/<int:job_id>/accept', methods=['PUT'])
def accept_job(job_id):
    data = request.get_json()
    driver_id = data.get('driver_id')
    
    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found!"}), 404
        
    if job.status != 'Pending':
        return jsonify({"error": "Job is already accepted or completed!"}), 400
        
    job.driver_id = driver_id
    job.status = 'Accepted'
    db.session.commit()
    
    return jsonify({"message": "Job accepted successfully!", "job_id": job.id, "status": job.status}), 200