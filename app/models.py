from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'client', 'driver', 'admin'
    phone = db.Column(db.String(20), nullable=True)
    
    # Driver 1km charge rate
    rate_per_km = db.Column(db.Float, nullable=True, default=0.0)

    # Original Documents
    nic_document = db.Column(db.String(255), nullable=True)
    business_reg = db.Column(db.String(255), nullable=True)
    driving_license = db.Column(db.String(255), nullable=True)
    vehicle_license = db.Column(db.String(255), nullable=True)
    vehicle_photo = db.Column(db.String(255), nullable=True)
    police_report = db.Column(db.String(255), nullable=True)
    
    is_approved = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)

    # Pending Fields for Profile Update Requests
    pending_name = db.Column(db.String(100), nullable=True)
    pending_phone = db.Column(db.String(20), nullable=True)
    pending_nic = db.Column(db.String(255), nullable=True)
    pending_bus_reg = db.Column(db.String(255), nullable=True)
    pending_driving_license = db.Column(db.String(255), nullable=True)
    pending_vehicle_license = db.Column(db.String(255), nullable=True)
    pending_vehicle_photo = db.Column(db.String(255), nullable=True)
    pending_police_report = db.Column(db.String(255), nullable=True)
    has_pending_update = db.Column(db.Boolean, default=False)


class Job(db.Model):
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    container_size = db.Column(db.String(50), nullable=False)
    pickup_location = db.Column(db.String(255), nullable=False)
    dropoff_location = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='Pending') # Pending, Accepted, Completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    client = db.relationship('User', foreign_keys=[client_id], backref=db.backref('posted_jobs', lazy=True))
    driver = db.relationship('User', foreign_keys=[driver_id], backref=db.backref('accepted_jobs', lazy=True))


class JobApplication(db.Model):
    __tablename__ = 'job_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(50), default='Pending') # Pending, Selected, Rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    job = db.relationship('Job', backref=db.backref('applications', lazy=True, cascade='all, delete-orphan'))
    driver = db.relationship('User', backref=db.backref('job_bids', lazy=True))