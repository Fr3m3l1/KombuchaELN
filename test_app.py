"""
Test script for Kombucha ELN application
"""

import os
import sys
import asyncio
from passlib.hash import pbkdf2_sha256
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path so we can import the src package
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.database import User, Experiment, Sample, Base, get_engine, get_session

async def test_database():
    """Test database functionality"""
    print("Testing database functionality...")
    
    # Set up database
    engine = get_engine()
    Base.metadata.create_all(engine)
    
    # Create session
    session = get_session()
    
    try:
        # Create test user
        username = "testuser"
        password = "testpassword"
        
        # Check if user already exists
        existing_user = session.query(User).filter_by(username=username).first()
        if existing_user:
            print(f"User '{username}' already exists")
        else:
            # Create new user
            user = User(username=username)
            user.set_password(password)
            session.add(user)
            session.commit()
            print(f"Created user '{username}'")
        
        # Verify user can authenticate
        user = session.query(User).filter_by(username=username).first()
        if user and pbkdf2_sha256.verify(password, user.password_hash):
            print(f"User '{username}' authenticated successfully")
        else:
            print(f"Failed to authenticate user '{username}'")
        
        # Create test experiment
        experiment = Experiment(
            title="Test Kombucha Experiment",
            user_id=username
        )
        session.add(experiment)
        session.flush()  # Get the experiment ID
        
        # Create test samples
        for i in range(3):
            sample = Sample(
                experiment_id=experiment.id,
                name=f"Sample {i+1}",
                tea_type="Green Tea",
                tea_concentration=5.0,
                water_amount=500.0,
                sugar_type="White Sugar",
                sugar_concentration=70.0,
                inoculum_concentration=10.0,
                temperature=25.0
            )
            session.add(sample)
        
        session.commit()
        print(f"Created experiment '{experiment.title}' with 3 samples")
        
        # Verify experiment and samples were created
        experiments = session.query(Experiment).filter_by(user_id=username).all()
        print(f"Found {len(experiments)} experiments for user '{username}'")
        
        for exp in experiments:
            samples = session.query(Sample).filter_by(experiment_id=exp.id).all()
            print(f"Experiment '{exp.title}' has {len(samples)} samples")
            
            for sample in samples:
                print(f"  - Sample '{sample.name}': {sample.tea_type}, {sample.tea_concentration} g/L")
        
        print("Database test completed successfully")
        
    except Exception as e:
        session.rollback()
        print(f"Error: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(test_database())
