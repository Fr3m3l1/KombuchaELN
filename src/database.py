import os
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from passlib.hash import pbkdf2_sha256

# Create the base class for our ORM models
Base = declarative_base()

# create data folder if it doesn't exist
if not os.path.exists('data'):
    os.makedirs('data')

# Define our models
class User(Base):
    __tablename__ = 'users'
    
    username = sa.Column(sa.String, primary_key=True)
    password_hash = sa.Column(sa.String, nullable=False)
    elab_api_key = sa.Column(sa.String, nullable=True)
    
    experiments = relationship("Experiment", back_populates="user", cascade="all, delete-orphan")
    
    def set_password(self, password):
        self.password_hash = pbkdf2_sha256.hash(password)
        
    def verify_password(self, password):
        return pbkdf2_sha256.verify(password, self.password_hash)

class Experiment(Base):
    __tablename__ = 'experiments'
    
    id = sa.Column(sa.Integer, primary_key=True)
    title = sa.Column(sa.String, nullable=False)
    user_id = sa.Column(sa.String, sa.ForeignKey('users.username'), nullable=False)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    elab_id = sa.Column(sa.Integer, nullable=True)
    status = sa.Column(sa.String, default="Planning", nullable=False)
    notes = sa.Column(sa.String, nullable=True)
    
    user = relationship("User", back_populates="experiments")
    batches = relationship("Batch", back_populates="experiment", cascade="all, delete-orphan")

class Batch(Base):
    __tablename__ = 'batches'
    
    id = sa.Column(sa.Integer, primary_key=True)
    experiment_id = sa.Column(sa.Integer, sa.ForeignKey('experiments.id'), nullable=False)
    name = sa.Column(sa.String, nullable=False)
    
    # Existing fields
    tea_type = sa.Column(sa.String, nullable=True)
    tea_concentration = sa.Column(sa.Float, nullable=True)
    water_amount = sa.Column(sa.Float, nullable=True)
    sugar_type = sa.Column(sa.String, nullable=True)
    sugar_concentration = sa.Column(sa.Float, nullable=True)
    inoculum_concentration = sa.Column(sa.Float, nullable=True)
    temperature = sa.Column(sa.Float, nullable=True)
    
    # New fields for workflow tracking
    status = sa.Column(sa.String, default="Setup", nullable=False)
    preparation_time = sa.Column(sa.DateTime, nullable=True)
    incubation_start_time = sa.Column(sa.DateTime, nullable=True)
    incubation_end_time = sa.Column(sa.DateTime, nullable=True)
    sample_split_time = sa.Column(sa.DateTime, nullable=True)
    micro_plating_time = sa.Column(sa.DateTime, nullable=True)
    micro_results = sa.Column(sa.String, nullable=True)
    hplc_prep_time = sa.Column(sa.DateTime, nullable=True)
    hplc_results = sa.Column(sa.String, nullable=True)
    ph_measurement_time = sa.Column(sa.DateTime, nullable=True)
    ph_value = sa.Column(sa.Float, nullable=True)
    scoby_wet_weight_time = sa.Column(sa.DateTime, nullable=True)
    scoby_wet_weight = sa.Column(sa.Float, nullable=True)
    scoby_dry_weight = sa.Column(sa.Float, nullable=True)
    temperature_logger_ids = sa.Column(sa.String, nullable=True)
    notes = sa.Column(sa.String, nullable=True)
    
    experiment = relationship("Experiment", back_populates="batches")

# Keep the Sample class for backward compatibility during migration
class Sample(Base):
    __tablename__ = 'samples'
    
    id = sa.Column(sa.Integer, primary_key=True)
    experiment_id = sa.Column(sa.Integer, sa.ForeignKey('experiments.id'), nullable=False)
    name = sa.Column(sa.String, nullable=False)
    tea_type = sa.Column(sa.String, nullable=True)
    tea_concentration = sa.Column(sa.Float, nullable=True)
    water_amount = sa.Column(sa.Float, nullable=True)
    sugar_type = sa.Column(sa.String, nullable=True)
    sugar_concentration = sa.Column(sa.Float, nullable=True)
    inoculum_concentration = sa.Column(sa.Float, nullable=True)
    temperature = sa.Column(sa.Float, nullable=True)
    
    experiment = relationship("Experiment")

# Database setup
def get_engine(db_path='data/kombucha_eln.db'):
    """Create and return a SQLAlchemy engine"""
    full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', db_path)
    return sa.create_engine(f'sqlite:///{full_path}')

def setup_database():
    """Create all tables if they don't exist"""
    engine = get_engine()
    Base.metadata.create_all(engine)
    return engine

def get_session():
    """Create and return a new session"""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()
