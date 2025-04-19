"""
Migration script to transition from samples to batches
"""

import sys
import os
import datetime

# Add the parent directory to the path so we can import the src package
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from src.database import get_session, get_engine, Base, Experiment, Sample, Batch
import sqlalchemy as sa

def migrate_samples_to_batches():
    """
    Migrate data from the samples table to the batches table
    """
    print("Starting migration from samples to batches...")
    
    # Create the batches table if it doesn't exist
    engine = get_engine()
    if not sa.inspect(engine).has_table('batches'):
        Base.metadata.tables['batches'].create(engine)
        print("Created batches table")
    
    # Add new columns to experiments table if they don't exist
    inspector = sa.inspect(engine)
    experiment_columns = [col['name'] for col in inspector.get_columns('experiments')]
    
    with engine.begin() as conn:
        if 'status' not in experiment_columns:
            conn.execute(sa.text("ALTER TABLE experiments ADD COLUMN status VARCHAR DEFAULT 'Planning' NOT NULL"))
            print("Added status column to experiments table")
        
        if 'notes' not in experiment_columns:
            conn.execute(sa.text("ALTER TABLE experiments ADD COLUMN notes VARCHAR"))
            print("Added notes column to experiments table")
    
    # Get all samples and copy to batches
    session = get_session()
    try:
        samples = session.query(Sample).all()
        print(f"Found {len(samples)} samples to migrate")
        
        for sample in samples:
            # Check if a batch with this sample ID already exists
            existing_batch = session.query(Batch).filter_by(id=sample.id).first()
            if existing_batch:
                print(f"Batch with ID {sample.id} already exists, skipping")
                continue
            
            # Create a new batch with the same data
            batch = Batch(
                id=sample.id,
                experiment_id=sample.experiment_id,
                name=sample.name,
                tea_type=sample.tea_type,
                tea_concentration=sample.tea_concentration,
                water_amount=sample.water_amount,
                sugar_type=sample.sugar_type,
                sugar_concentration=sample.sugar_concentration,
                inoculum_concentration=sample.inoculum_concentration,
                temperature=sample.temperature,
                status="Setup"  # Default status for migrated samples
            )
            
            session.add(batch)
        
        # Update experiment relationships
        experiments = session.query(Experiment).all()
        print(f"Updating {len(experiments)} experiments")
        
        for experiment in experiments:
            # Set default status if not already set
            if not hasattr(experiment, 'status') or not experiment.status:
                experiment.status = "Planning"
        
        session.commit()
        print("Migration completed successfully")
    except Exception as e:
        session.rollback()
        print(f"Error during migration: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    migrate_samples_to_batches()
