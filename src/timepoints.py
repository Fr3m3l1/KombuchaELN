"""
Functions for managing timepoints and measurements
"""

from nicegui import ui
from src.database import Experiment, Batch, Timepoint, Measurement, get_session
import datetime
import sqlalchemy as sa

async def create_default_timepoints(experiment_id):
    """
    Create default timepoints for an experiment
    
    Args:
        experiment_id: The ID of the experiment
        
    Returns:
        True if creation was successful, False otherwise
    """
    default_timepoints = [
        {"name": "t0", "hours": 0, "order": 1, "description": "Initial measurements"},
        {"name": "t4", "hours": 4, "order": 2, "description": "4-hour measurements"},
        {"name": "t7", "hours": 7, "order": 3, "description": "7-hour measurements"},
        {"name": "t11", "hours": 11, "order": 4, "description": "Final measurements"}
    ]
    
    session = get_session()
    try:
        # Check if timepoints already exist for this experiment
        existing_timepoints = session.query(Timepoint).filter_by(experiment_id=experiment_id).all()
        if existing_timepoints:
            return True
        
        # Create default timepoints
        for tp_data in default_timepoints:
            timepoint = Timepoint(
                experiment_id=experiment_id,
                name=tp_data["name"],
                hours=tp_data["hours"],
                description=tp_data["description"],
                order=tp_data["order"]
            )
            session.add(timepoint)
        
        # Set the current timepoint to t0
        experiment = session.query(Experiment).filter_by(id=experiment_id).first()
        if experiment:
            session.flush()  # Flush to get timepoint IDs
            t0 = session.query(Timepoint).filter_by(experiment_id=experiment_id, name="t0").first()
            if t0:
                experiment.current_timepoint_id = t0.id
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        ui.notify(f"Error creating timepoints: {str(e)}", color='negative')
        return False
    finally:
        session.close()

async def create_custom_timepoint(experiment_id, name, hours, description, order=None):
    """
    Create a custom timepoint for an experiment
    
    Args:
        experiment_id: The ID of the experiment
        name: The name of the timepoint (e.g., "t0", "t4", etc.)
        hours: The hours from start (e.g., 0, 4, 7, 11)
        description: A description of the timepoint
        order: The order of the timepoint (optional, will be calculated if not provided)
        
    Returns:
        The ID of the created timepoint or None if creation fails
    """
    session = get_session()
    try:
        # Calculate order if not provided
        if order is None:
            max_order = session.query(sa.func.max(Timepoint.order)).filter_by(experiment_id=experiment_id).scalar()
            order = 1 if max_order is None else max_order + 1
        
        # Create timepoint
        timepoint = Timepoint(
            experiment_id=experiment_id,
            name=name,
            hours=hours,
            description=description,
            order=order
        )
        
        session.add(timepoint)
        session.commit()
        
        return timepoint.id
    except Exception as e:
        session.rollback()
        ui.notify(f"Error creating timepoint: {str(e)}", color='negative')
        return None
    finally:
        session.close()

def get_experiment_timepoints(experiment_id):
    """
    Get all timepoints for an experiment, ordered by their order field
    
    Args:
        experiment_id: The ID of the experiment
        
    Returns:
        A list of timepoint objects
    """
    session = get_session()
    try:
        timepoints = session.query(Timepoint).filter_by(experiment_id=experiment_id).order_by(Timepoint.order).all()
        return timepoints
    finally:
        session.close()

def get_timepoint(timepoint_id):
    """
    Get a timepoint by ID
    
    Args:
        timepoint_id: The ID of the timepoint
        
    Returns:
        The timepoint object or None if not found
    """
    session = get_session()
    try:
        timepoint = session.query(Timepoint).filter_by(id=timepoint_id).first()
        return timepoint
    finally:
        session.close()

async def set_current_timepoint(experiment_id, timepoint_id):
    """
    Set the current timepoint for an experiment
    
    Args:
        experiment_id: The ID of the experiment
        timepoint_id: The ID of the timepoint to set as current
        
    Returns:
        True if update was successful, False otherwise
    """
    session = get_session()
    try:
        experiment = session.query(Experiment).filter_by(id=experiment_id).first()
        if not experiment:
            return False
        
        experiment.current_timepoint_id = timepoint_id
        session.commit()
        
        return True
    except Exception as e:
        session.rollback()
        ui.notify(f"Error setting current timepoint: {str(e)}", color='negative')
        return False
    finally:
        session.close()

async def advance_to_next_timepoint(experiment_id):
    """
    Advance to the next timepoint in the sequence
    
    Args:
        experiment_id: The ID of the experiment
        
    Returns:
        The ID of the new current timepoint or None if there is no next timepoint
    """
    session = get_session()
    try:
        experiment = session.query(Experiment).filter_by(id=experiment_id).first()
        if not experiment or not experiment.current_timepoint_id:
            return None
        
        current_timepoint = session.query(Timepoint).filter_by(id=experiment.current_timepoint_id).first()
        if not current_timepoint:
            return None
        
        # Find the next timepoint in the sequence
        next_timepoint = session.query(Timepoint).filter_by(
            experiment_id=experiment_id
        ).filter(
            Timepoint.order > current_timepoint.order
        ).order_by(
            Timepoint.order
        ).first()
        
        if not next_timepoint:
            return None
        
        # Update the current timepoint
        experiment.current_timepoint_id = next_timepoint.id
        session.commit()
        
        return next_timepoint.id
    except Exception as e:
        session.rollback()
        ui.notify(f"Error advancing timepoint: {str(e)}", color='negative')
        return None
    finally:
        session.close()

def is_final_timepoint(timepoint_id):
    """
    Check if a timepoint is the final one for its experiment
    
    Args:
        timepoint_id: The ID of the timepoint
        
    Returns:
        True if it's the final timepoint, False otherwise
    """
    session = get_session()
    try:
        timepoint = session.query(Timepoint).filter_by(id=timepoint_id).first()
        if not timepoint:
            return False
        
        # Check if there are any timepoints with a higher order
        next_timepoint = session.query(Timepoint).filter_by(
            experiment_id=timepoint.experiment_id
        ).filter(
            Timepoint.order > timepoint.order
        ).first()
        
        return next_timepoint is None
    finally:
        session.close()

async def record_measurement(batch_id, timepoint_id, **values):
    """
    Record a measurement for a batch at a specific timepoint
    
    Args:
        batch_id: The ID of the batch
        timepoint_id: The ID of the timepoint
        **values: The measurement values to record
        
    Returns:
        True if recording was successful, False otherwise
    """
    session = get_session()
    try:
        # Check if a measurement already exists
        measurement = session.query(Measurement).filter_by(
            batch_id=batch_id,
            timepoint_id=timepoint_id
        ).first()
        
        if measurement:
            # Update existing measurement
            for key, value in values.items():
                if hasattr(measurement, key):
                    setattr(measurement, key, value)
        else:
            # Create new measurement
            measurement = Measurement(
                batch_id=batch_id,
                timepoint_id=timepoint_id,
                **values
            )
            session.add(measurement)
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        ui.notify(f"Error recording measurement: {str(e)}", color='negative')
        return False
    finally:
        session.close()

def get_batch_measurement(batch_id, timepoint_id):
    """
    Get a measurement for a batch at a specific timepoint
    
    Args:
        batch_id: The ID of the batch
        timepoint_id: The ID of the timepoint
        
    Returns:
        The measurement object or None if not found
    """
    session = get_session()
    try:
        measurement = session.query(Measurement).filter_by(
            batch_id=batch_id,
            timepoint_id=timepoint_id
        ).first()
        return measurement
    finally:
        session.close()

def get_timepoint_measurements(timepoint_id):
    """
    Get all measurements for a specific timepoint
    
    Args:
        timepoint_id: The ID of the timepoint
        
    Returns:
        A list of measurement objects
    """
    session = get_session()
    try:
        measurements = session.query(Measurement).filter_by(timepoint_id=timepoint_id).all()
        return measurements
    finally:
        session.close()

def get_batch_measurements(batch_id):
    """
    Get all measurements for a specific batch
    
    Args:
        batch_id: The ID of the batch
        
    Returns:
        A list of measurement objects
    """
    session = get_session()
    try:
        measurements = session.query(Measurement).filter_by(batch_id=batch_id).all()
        return measurements
    finally:
        session.close()

async def mark_measurement_completed(batch_id, timepoint_id, completed=True):
    """
    Mark a measurement as completed
    
    Args:
        batch_id: The ID of the batch
        timepoint_id: The ID of the timepoint
        completed: Whether the measurement is completed (default: True)
        
    Returns:
        True if update was successful, False otherwise
    """
    session = get_session()
    try:
        measurement = session.query(Measurement).filter_by(
            batch_id=batch_id,
            timepoint_id=timepoint_id
        ).first()
        
        if not measurement:
            # Create a new measurement record if it doesn't exist
            measurement = Measurement(
                batch_id=batch_id,
                timepoint_id=timepoint_id,
                completed=completed
            )
            session.add(measurement)
        else:
            measurement.completed = completed
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        ui.notify(f"Error marking measurement: {str(e)}", color='negative')
        return False
    finally:
        session.close()

def is_timepoint_completed(timepoint_id):
    """
    Check if all measurements for a timepoint are completed
    
    Args:
        timepoint_id: The ID of the timepoint
        
    Returns:
        True if all measurements are completed, False otherwise
    """
    session = get_session()
    try:
        timepoint = session.query(Timepoint).filter_by(id=timepoint_id).first()
        if not timepoint:
            return False
        
        # Get all batches for this experiment
        batches = session.query(Batch).filter_by(experiment_id=timepoint.experiment_id).all()
        if not batches:
            return False
        
        # Check if all batches have completed measurements for this timepoint
        for batch in batches:
            measurement = session.query(Measurement).filter_by(
                batch_id=batch.id,
                timepoint_id=timepoint_id
            ).first()
            
            if not measurement or not measurement.completed:
                return False
        
        return True
    finally:
        session.close()

def create_timepoint_config_ui(experiment_id):
    """
    Create the UI for configuring timepoints
    
    Args:
        experiment_id: The ID of the experiment
    """
    timepoints = get_experiment_timepoints(experiment_id)
    
    with ui.card().classes('w-full'):
        ui.label('Timepoint Configuration').classes('text-xl font-bold')
        
        # Display existing timepoints in a grid instead of a table
        if timepoints:
            with ui.grid(columns=5).classes('w-full gap-4 mt-2'):
                # Headers
                ui.label('Name').classes('font-bold')
                ui.label('Hours').classes('font-bold')
                ui.label('Description').classes('font-bold')
                ui.label('Order').classes('font-bold')
                ui.label('Actions').classes('font-bold')
                
                # Rows
                for tp in timepoints:
                    ui.label(tp.name)
                    ui.label(str(tp.hours))
                    ui.label(tp.description or '')
                    ui.label(str(tp.order))
                    ui.button('Delete', on_click=lambda t=tp.id: delete_timepoint(t), color='red')
        else:
            ui.label('No timepoints defined yet').classes('text-gray-500')
        
        # Form for adding a new timepoint
        ui.separator()
        ui.label('Add New Timepoint').classes('text-lg font-bold mt-4')
        
        name_input = ui.input('Name (e.g., t0, t4, etc.)').classes('w-full')
        hours_input = ui.number('Hours from Start', min=0, step=0.5).classes('w-full')
        description_input = ui.input('Description').classes('w-full')
        
        async def add_timepoint():
            if not name_input.value:
                ui.notify('Please enter a name', color='negative')
                return
            
            if hours_input.value is None:
                ui.notify('Please enter hours', color='negative')
                return
            
            timepoint_id = await create_custom_timepoint(
                experiment_id,
                name_input.value,
                hours_input.value,
                description_input.value
            )
            
            if timepoint_id:
                ui.notify('Timepoint added successfully', color='positive')
                ui.run_javascript("window.location.reload()")
            else:
                ui.notify('Failed to add timepoint', color='negative')
        
        ui.button('Add Timepoint', on_click=add_timepoint, color='primary').classes('mt-2')

async def delete_timepoint(timepoint_id):
    """
    Delete a timepoint
    
    Args:
        timepoint_id: The ID of the timepoint
        
    Returns:
        True if deletion was successful, False otherwise
    """
    session = get_session()
    try:
        # Check if this timepoint is currently set as current for any experiment
        experiment = session.query(Experiment).filter_by(current_timepoint_id=timepoint_id).first()
        if experiment:
            ui.notify('Cannot delete a timepoint that is currently active', color='negative')
            return False
        
        # Check if there are any measurements for this timepoint
        measurements = session.query(Measurement).filter_by(timepoint_id=timepoint_id).all()
        if measurements:
            ui.notify('Cannot delete a timepoint that has measurements', color='negative')
            return False
        
        # Delete the timepoint
        timepoint = session.query(Timepoint).filter_by(id=timepoint_id).first()
        if timepoint:
            session.delete(timepoint)
            session.commit()
            ui.notify('Timepoint deleted successfully', color='positive')
            ui.run_javascript("window.location.reload()")
            return True
        
        return False
    except Exception as e:
        session.rollback()
        ui.notify(f"Error deleting timepoint: {str(e)}", color='negative')
        return False
    finally:
        session.close()

def create_timepoint_workflow_ui(experiment_id):
    """
    Create the UI for the timepoint-based workflow
    
    Args:
        experiment_id: The ID of the experiment
    """
    experiment = get_session().query(Experiment).filter_by(id=experiment_id).first()
    if not experiment:
        ui.label('Experiment not found').classes('text-xl text-red-500')
        return
    
    # Get current timepoint
    current_timepoint = None
    if experiment.current_timepoint_id:
        current_timepoint = get_timepoint(experiment.current_timepoint_id)
    
    # Get all timepoints
    timepoints = get_experiment_timepoints(experiment_id)
    
    # Get all batches
    batches = get_session().query(Batch).filter_by(experiment_id=experiment_id).all()
    
    with ui.card().classes('w-full'):
        ui.label('Workflow Tracking').classes('text-xl font-bold')
        
        # Timepoint navigation visualization (timeline)
        with ui.row().classes('w-full items-center mt-2'):
            for i, tp in enumerate(timepoints):
                # Timepoint circle
                is_current = current_timepoint and tp.id == current_timepoint.id
                is_completed = is_timepoint_completed(tp.id)
                
                circle_color = 'bg-green-500' if is_completed else ('bg-blue-500' if is_current else 'bg-gray-300')
                with ui.element('div').classes(f'rounded-full {circle_color} w-8 h-8 flex items-center justify-center text-white'):
                    ui.label(tp.name)
                
                # Timepoint name
                name_color = 'text-green-500' if is_completed else ('text-blue-500' if is_current else 'text-gray-500')
                ui.label(f"{tp.name} ({tp.hours}h)").classes(f'{name_color} text-sm')
                
                # Connector line (except after the last timepoint)
                if i < len(timepoints) - 1:
                    line_color = 'bg-green-500' if is_completed else 'bg-gray-300'
                    ui.element('div').classes(f'{line_color} h-1 flex-grow')
        
        ui.separator()
        
        # Current timepoint section
        if current_timepoint:
            ui.label(f'Current Timepoint: {current_timepoint.name} ({current_timepoint.hours}h)').classes('text-lg font-bold mt-4')
            ui.label(current_timepoint.description).classes('text-gray-600')

            # --- Timepoint Navigation Buttons ---
            previous_tp = None
            next_tp = None
            for idx, tp in enumerate(timepoints):
                if tp.id == current_timepoint.id:
                    if idx > 0:
                        previous_tp = timepoints[idx - 1]
                    if idx < len(timepoints) - 1:
                        next_tp = timepoints[idx + 1]
                    break

            with ui.row().classes('justify-between mt-4'):
                if previous_tp:
                    async def go_to_previous(tp_id=previous_tp.id):
                        success = await set_current_timepoint(experiment_id, tp_id)
                        if success:
                            ui.notify(f'Moved to {previous_tp.name}', color='positive')
                            ui.run_javascript("window.location.reload()")
                        else:
                            ui.notify('Failed to move to previous timepoint', color='negative')
                    ui.button(f'← {previous_tp.name}', on_click=go_to_previous, color='gray')
                else:
                    ui.button('← No Previous').props('disabled')

                if next_tp:
                    async def go_to_next(tp_id=next_tp.id):
                        success = await set_current_timepoint(experiment_id, tp_id)
                        if success:
                            ui.notify(f'Moved to {next_tp.name}', color='positive')
                            ui.run_javascript("window.location.reload()")
                        else:
                            ui.notify('Failed to move to next timepoint', color='negative')
                    ui.button(f'{next_tp.name} →', on_click=go_to_next, color='gray')
                else:
                    ui.button('No Next →').props('disabled')
            # --- End Navigation Buttons ---
            
            # Measurements table
            with ui.card().classes('w-full mt-4'):
                ui.label('Batch Measurements').classes('text-lg font-bold')
                
                # Use a proper table with rows parameter
                columns = [
                    {'name': 'batch', 'label': 'Batch', 'field': 'batch'},
                    {'name': 'ph_sample', 'label': 'pH Sample', 'field': 'ph_sample'},
                    {'name': 'ph', 'label': 'pH Value', 'field': 'ph'},
                    {'name': 'micro_sample', 'label': 'Micro Sample', 'field': 'micro_sample'},
                    {'name': 'micro', 'label': 'Micro Results', 'field': 'micro'},
                    {'name': 'hplc_sample', 'label': 'HPLC Sample', 'field': 'hplc_sample'},
                    {'name': 'hplc', 'label': 'HPLC Results', 'field': 'hplc'},
                ]
                
                # Add SCOBY columns if this is the final timepoint
                if is_final_timepoint(current_timepoint.id):
                    columns.extend([
                        {'name': 'scoby_wet', 'label': 'SCOBY Wet', 'field': 'scoby_wet'},
                        {'name': 'scoby_dry', 'label': 'SCOBY Dry', 'field': 'scoby_dry'},
                    ])
                
                columns.extend([
                    {'name': 'status', 'label': 'Status', 'field': 'status'},
                    {'name': 'actions', 'label': 'Actions', 'field': 'actions'},
                ])
                
                # Prepare rows data
                rows = []
                for batch in batches:
                    measurement = get_batch_measurement(batch.id, current_timepoint.id)
                    
                    # Determine status
                    status = "Not Started"
                    if measurement:
                        status = "Completed" if measurement.completed else "In Progress"
                    
                    # Format sample collection times
                    ph_sample_status = "Not Collected"
                    if measurement and measurement.ph_sample_time:
                        ph_sample_status = measurement.ph_sample_time.strftime("%Y-%m-%d %H:%M")
                    
                    micro_sample_status = "Not Collected"
                    if measurement and measurement.micro_sample_time:
                        micro_sample_status = measurement.micro_sample_time.strftime("%Y-%m-%d %H:%M")
                    
                    hplc_sample_status = "Not Collected"
                    if measurement and measurement.hplc_sample_time:
                        hplc_sample_status = measurement.hplc_sample_time.strftime("%Y-%m-%d %H:%M")
                    
                    # Create row data
                    row = {
                        'batch': batch.name,
                        'ph_sample': ph_sample_status,
                        'ph': str(measurement.ph_value) if measurement and measurement.ph_value else "N/A",
                        'micro_sample': micro_sample_status,
                        'micro': "Recorded" if measurement and measurement.micro_results else "N/A",
                        'hplc_sample': hplc_sample_status,
                        'hplc': "Recorded" if measurement and measurement.hplc_results else "N/A",
                        'status': status,
                        'actions': 'Record Data',
                        '_batch_id': batch.id,  # Store batch_id for action button
                        '_timepoint_id': current_timepoint.id  # Store timepoint_id for action button
                    }
                    
                    # Add SCOBY data if this is the final timepoint
                    if is_final_timepoint(current_timepoint.id):
                        row['scoby_wet'] = str(measurement.scoby_wet_weight) if measurement and measurement.scoby_wet_weight else "N/A"
                        row['scoby_dry'] = str(measurement.scoby_dry_weight) if measurement and measurement.scoby_dry_weight else "N/A"
                    
                    rows.append(row)
                
                # Create the table without the actions column
                columns.pop()  # Remove the actions column
                
                table = ui.table(
                    columns=columns,
                    rows=rows,
                    row_key='batch'
                ).classes('w-full')
                
                # Add action buttons for each batch with direct test recording
                ui.label('').classes('mt-4')  # Add some spacing
                ui.label('Quick Actions:').classes('font-bold')
                
                # Calculate the number of columns based on the number of batches
                # Use a responsive grid with maximum 4 columns
                num_columns = min(4, len(batches))
                
                # Create a card for each batch with quick action buttons
                with ui.grid(columns=num_columns).classes('w-full gap-4 mt-2'):
                    for batch in batches:
                        with ui.card().classes('p-4'):
                            ui.label(batch.name).classes('font-bold text-center')
                            
                            # Get measurement for this batch
                            measurement = get_batch_measurement(batch.id, current_timepoint.id)
                            
                            # Sample collection button
                            with ui.row().classes('w-full justify-center mt-2'):
                                # Check if samples are already collected
                                all_samples_collected = (measurement and measurement.ph_sample_time and 
                                                        measurement.micro_sample_time and 
                                                        measurement.hplc_sample_time)
                                
                                if all_samples_collected:
                                    ui.label('Samples Collected').classes('text-green-500 font-bold')
                                else:
                                    async def collect_samples(b_id=batch.id, sample="ph", t_id=current_timepoint.id):
                                        now = datetime.datetime.now()
                                        
                                        # Get existing measurement to preserve other sample times
                                        existing_measurement = get_batch_measurement(b_id, t_id)
                                        
                                        # Only update the specific sample time requested
                                        match sample:
                                            case 'ph':
                                                success = await record_measurement(
                                                    b_id, 
                                                    t_id,
                                                    ph_sample_time=now
                                                )
                                            case 'micro':                                          
                                                success = await record_measurement(
                                                    b_id, 
                                                    t_id,
                                                    micro_sample_time=now
                                                )
                                            case 'hplc':
                                                success = await record_measurement(
                                                    b_id, 
                                                    t_id,
                                                    hplc_sample_time=now
                                                )
                                        if success:
                                            ui.notify('All samples recorded as collected', color='positive')
                                            ui.run_javascript("window.location.reload()")
                                        else:
                                            ui.notify('Failed to record sample collection', color='negative')
                                    
                                    # Check if individual samples are already collected
                                    ph_collected = measurement and measurement.ph_sample_time
                                    micro_collected = measurement and measurement.micro_sample_time
                                    hplc_collected = measurement and measurement.hplc_sample_time
                                    
                                    # PH Sample button
                                    if ph_collected:
                                        ui.label('PH Sample Collected').classes('text-green-500 text-center w-full')
                                    else:
                                        ui.button(
                                            'Collect PH Sample',
                                            on_click=lambda b=batch.id: collect_samples(b_id=b, sample='ph'), 
                                            color='orange'
                                        ).classes('text-white w-full')

                                    # MICRO Sample button
                                    if micro_collected:
                                        ui.label('MICRO Sample Collected').classes('text-green-500 text-center w-full')
                                    else:
                                        ui.button(
                                            'Collect MICRO Sample', 
                                            on_click=lambda b=batch.id: collect_samples(b_id=b, sample='micro'),
                                            color='yellow'
                                        ).classes('text-black w-full')

                                    # HPLC Sample button
                                    if hplc_collected:
                                        ui.label('HPLC Sample Collected').classes('text-green-500 text-center w-full')
                                    else:
                                        ui.button(
                                            'Collect HPLC Sample', 
                                            on_click=lambda b=batch.id: collect_samples(b_id=b, sample='hplc'),
                                            color='black'
                                        ).classes('text-white w-full')
                            
                            ui.separator().classes('my-2')
                            
                            # Test result buttons
                            ui.label('Record Test Results:').classes('text-center mt-2')
                            
                            with ui.grid(columns=3).classes('w-full gap-2 mt-2'):
                                # pH Button
                                async def record_ph(b_id=batch.id, t_id=current_timepoint.id):

                                    # Declare the dialog in outer scope to close it later
                                    ph_dialog = ui.dialog()

                                    with ph_dialog, ui.card():
                                        ui.label(f'Record pH for {batch.name}').classes('text-lg font-bold')
                                        
                                        # Free-text input for precise validation
                                        ph_input = ui.input('pH Value (0-14)').classes('w-full')
                                        error_label = ui.label('').classes('text-red-500 text-sm')

                                        async def save_ph():
                                            error_label.text = '' # Clear previous error
                                            try:
                                                value = float(ph_input.value)
                                                if not (0 <= value <= 14):
                                                    raise ValueError
                                            except (ValueError, TypeError):
                                                error_label.text = 'Invalid pH: please enter a value between 0 and 14.'
                                                return
                                            
                                            success = await record_measurement(b_id, t_id, ph_value=value)
                                            
                                            if success:
                                                ui.notify('pH value saved', color='positive')
                                                ph_dialog.close()
                                                ui.run_javascript("window.location.reload()")
                                            else:
                                                ui.notify('Failed to save pH value', color='negative')
                                        
                                        with ui.row().classes('w-full justify-end'):
                                            ui.button('Cancel', on_click=ph_dialog.close).classes('mr-2')
                                            ui.button('Save', on_click=save_ph, color='green').classes('bg-green-500 text-white')
                                        
                                    ph_dialog.open()
                                
                                ph_btn_color = 'bg-green-500' if measurement and measurement.ph_value else 'bg-blue-500'
                                ph_btn_text = 'pH: Recorded' if measurement and measurement.ph_value else 'Record pH'
                                ui.button(
                                    ph_btn_text, 
                                    on_click=lambda b=batch.id: record_ph(b_id=b),
                                    color='orange'
                                ).classes(f'{ph_btn_color} text-white w-full')
                                
                                # Micro Button
                                async def record_micro(b_id=batch.id, t_id=current_timepoint.id):
                                    # Open a simple dialog to enter micro results
                                    with ui.dialog() as micro_dialog, ui.card():
                                        ui.label(f'Record Microbiology for {batch.name}').classes('text-lg font-bold')
                                        micro_results = ui.textarea(
                                            'Microbiology Results',
                                            placeholder='Enter CFU counts and any observations here...'
                                        ).classes('w-full')
                                        
                                        async def save_micro():
                                            success = await record_measurement(
                                                b_id, 
                                                t_id, 
                                                micro_results=micro_results.value
                                            )
                                            if success:
                                                ui.notify('Microbiology results saved', color='positive')
                                                micro_dialog.close()
                                                ui.run_javascript("window.location.reload()")
                                            else:
                                                ui.notify('Failed to save microbiology results', color='negative')
                                        
                                        with ui.row().classes('w-full justify-end'):
                                            ui.button('Cancel', on_click=micro_dialog.close).classes('mr-2')
                                            ui.button('Save', on_click=save_micro, color='green').classes('bg-green-500 text-white')
                                        
                                        micro_dialog.open()
                                
                                micro_btn_color = 'bg-green-500' if measurement and measurement.micro_results else 'bg-blue-500'
                                micro_btn_text = 'Micro: Recorded' if measurement and measurement.micro_results else 'Record Micro'
                                ui.button(
                                    micro_btn_text, 
                                    on_click=lambda b=batch.id: record_micro(b_id=b),
                                    color='yellow'
                                ).classes(f'{micro_btn_color} text-black w-full')
                                
                                # HPLC Button
                                async def record_hplc(b_id=batch.id, t_id=current_timepoint.id):
                                    # Open a simple dialog to enter HPLC results
                                    with ui.dialog() as hplc_dialog, ui.card():
                                        ui.label(f'Record HPLC for {batch.name}').classes('text-lg font-bold')
                                        hplc_results = ui.textarea(
                                            'HPLC Results',
                                            placeholder='Enter HPLC results and any observations here...'
                                        ).classes('w-full')
                                        
                                        async def save_hplc():
                                            success = await record_measurement(
                                                b_id, 
                                                t_id, 
                                                hplc_results=hplc_results.value
                                            )
                                            if success:
                                                ui.notify('HPLC results saved', color='positive')
                                                hplc_dialog.close()
                                                ui.run_javascript("window.location.reload()")
                                            else:
                                                ui.notify('Failed to save HPLC results', color='negative')
                                        
                                        with ui.row().classes('w-full justify-end'):
                                            ui.button('Cancel', on_click=hplc_dialog.close).classes('mr-2')
                                            ui.button('Save', on_click=save_hplc, color='green').classes('bg-green-500 text-white')
                                        
                                        hplc_dialog.open()
                                
                                hplc_btn_color = 'bg-green-500' if measurement and measurement.hplc_results else 'bg-blue-500'
                                hplc_btn_text = 'HPLC: Recorded' if measurement and measurement.hplc_results else 'Record HPLC'
                                ui.button(
                                    hplc_btn_text, 
                                    on_click=lambda b=batch.id: record_hplc(b_id=b),
                                    color='black'
                                ).classes(f'{hplc_btn_color} text-white w-full')
                            
                            # SCOBY weights (only for final timepoint)
                            if is_final_timepoint(current_timepoint.id):
                                ui.separator().classes('my-2')
                                ui.label('SCOBY Weights:').classes('text-center mt-2')
                                
                                async def record_scoby(b_id=batch.id, t_id=current_timepoint.id):
                                    # Open a simple dialog to enter SCOBY weights
                                    with ui.dialog() as scoby_dialog, ui.card():
                                        ui.label(f'Record SCOBY Weights for {batch.name}').classes('text-lg font-bold')
                                        scoby_wet_weight = ui.number('Wet Weight (g)', min=0, step=0.1).classes('w-full')
                                        scoby_dry_weight = ui.number('Dry Weight (g)', min=0, step=0.1).classes('w-full')
                                        
                                        async def save_scoby():
                                            success = await record_measurement(
                                                b_id, 
                                                t_id, 
                                                scoby_wet_weight=scoby_wet_weight.value,
                                                scoby_dry_weight=scoby_dry_weight.value
                                            )
                                            if success:
                                                ui.notify('SCOBY weights saved', color='positive')
                                                scoby_dialog.close()
                                                ui.run_javascript("window.location.reload()")
                                            else:
                                                ui.notify('Failed to save SCOBY weights', color='negative')
                                        
                                        with ui.row().classes('w-full justify-end'):
                                            ui.button('Cancel', on_click=scoby_dialog.close).classes('mr-2')
                                            ui.button('Save', on_click=save_scoby).classes('bg-green-500 text-white')
                                        
                                        scoby_dialog.open()
                                
                                scoby_btn_color = 'bg-green-500' if measurement and measurement.scoby_wet_weight else 'bg-blue-500'
                                scoby_btn_text = 'SCOBY: Recorded' if measurement and measurement.scoby_wet_weight else 'Record SCOBY'
                                ui.button(
                                    scoby_btn_text, 
                                    on_click=lambda b=batch.id: record_scoby(b_id=b)
                                ).classes(f'{scoby_btn_color} text-white w-full')
                            
                            ui.separator().classes('my-2')
                            
                            # Mark as completed button
                            async def toggle_completed(b_id=batch.id, t_id=current_timepoint.id):
                                m = get_batch_measurement(b_id, t_id)
                                new_status = not (m and m.completed)
                                success = await mark_measurement_completed(b_id, t_id, completed=new_status)
                                if success:
                                    ui.notify(f'Measurement marked as {"completed" if new_status else "incomplete"}', color='positive')
                                    ui.run_javascript("window.location.reload()")
                                else:
                                    ui.notify('Failed to update completion status', color='negative')
                            
                            completed_btn_color = 'bg-green-500' if measurement and measurement.completed else 'bg-orange-500'
                            completed_btn_text = 'Completed' if measurement and measurement.completed else 'Mark as Completed'
                            ui.button(
                                completed_btn_text, 
                                on_click=lambda b=batch.id: toggle_completed(b_id=b)
                            ).classes(f'{completed_btn_color} text-white w-full mt-2')
                            
                            # Advanced options button
                            ui.button(
                                'Advanced Options', 
                                on_click=lambda b=batch.id, t=current_timepoint.id: open_measurement_dialog(b, t)
                            ).classes('bg-gray-500 text-white w-full mt-2')
            
            # Timepoint navigation buttons
            with ui.row().classes('w-full justify-between mt-4'):
                # Check if all measurements are completed
                all_completed = is_timepoint_completed(current_timepoint.id)
                
                # Only show advance button if all measurements are completed
                if all_completed:
                    # Check if this is the final timepoint
                    if is_final_timepoint(current_timepoint.id):
                        async def complete_experiment():
                            # Update experiment status to Completed
                            session = get_session()
                            try:
                                experiment = session.query(Experiment).filter_by(id=experiment_id).first()
                                if experiment:
                                    experiment.status = "Completed"
                                    session.commit()
                                    ui.notify('Experiment completed', color='positive')
                                    ui.run_javascript(f"window.location.href = '/experiment/{experiment_id}'")
                            except Exception as e:
                                session.rollback()
                                ui.notify(f"Error completing experiment: {str(e)}", color='negative')
                            finally:
                                session.close()
                        
                        ui.button('Complete Experiment',
                                  on_click=complete_experiment, color='red'
                                ).classes('text-white')
                    else:
                        async def advance_timepoint():
                            next_timepoint_id = await advance_to_next_timepoint(experiment_id)
                            if next_timepoint_id:
                                ui.notify('Advanced to next timepoint', color='positive')
                                ui.run_javascript("window.location.reload()")
                            else:
                                ui.notify('Failed to advance timepoint', color='negative')
                        
                        ui.button('Advance to Next Timepoint',
                                  on_click=advance_timepoint,
                                  color='blue'
                                ).classes('bg-blue-500 text-white')
        else:
            ui.label('No active timepoint').classes('text-lg font-bold mt-4')
            
            async def start_workflow():
                # Create default timepoints if they don't exist
                success = await create_default_timepoints(experiment_id)
                if not success:
                    ui.notify('Failed to create timepoints', color='negative')
                    return
                
                # Get the first timepoint
                session = get_session()
                try:
                    t0 = session.query(Timepoint).filter_by(experiment_id=experiment_id, name="t0").first()
                    if t0:
                        # Set as current timepoint
                        experiment = session.query(Experiment).filter_by(id=experiment_id).first()
                        if experiment:
                            experiment.current_timepoint_id = t0.id
                            experiment.status = "Running"
                            session.commit()
                            ui.notify('Workflow started', color='positive')
                            ui.run_javascript("window.location.reload()")
                    else:
                        ui.notify('Failed to find t0 timepoint', color='negative')
                except Exception as e:
                    session.rollback()
                    ui.notify(f"Error starting workflow: {str(e)}", color='negative')
                finally:
                    session.close()
            
            ui.button('Start Workflow', on_click=start_workflow).classes('bg-blue-500 text-white')

def open_measurement_dialog(batch_id, timepoint_id):
    """
    Open a dialog to record measurements for a batch at a specific timepoint
    
    Args:
        batch_id: The ID of the batch
        timepoint_id: The ID of the timepoint
    """
    batch = get_session().query(Batch).filter_by(id=batch_id).first()
    timepoint = get_timepoint(timepoint_id)
    
    if not batch or not timepoint:
        ui.notify('Batch or timepoint not found', color='negative')
        return
    
    # Get existing measurement
    measurement = get_batch_measurement(batch_id, timepoint_id)
    
    with ui.dialog() as dialog, ui.card():
        ui.label(f'Record Measurements for {batch.name} at {timepoint.name}').classes('text-xl font-bold')
        
        # Sample Collection Tracking Section
        ui.label('Sample Collection').classes('text-lg font-bold mt-4')
        ui.label('Record when samples were collected').classes('text-sm text-gray-600')
        
        # Show sample collection status
        all_samples_collected = (measurement and measurement.ph_sample_time and 
                                measurement.micro_sample_time and 
                                measurement.hplc_sample_time)
        
        if all_samples_collected:
            ui.label('All samples collected').classes('text-green-500 font-bold mt-2')
            collection_time = measurement.ph_sample_time.strftime("%Y-%m-%d %H:%M")
            ui.label(f'Collection time: {collection_time}').classes('text-green-500')
            
            async def clear_all_samples():
                success = await record_measurement(
                    batch_id, 
                    timepoint_id, 
                    ph_sample_time=None,
                    micro_sample_time=None,
                    hplc_sample_time=None
                )
                if success:
                    ui.notify('Sample collection times cleared', color='positive')
                    dialog.close()
                    ui.run_javascript("window.location.reload()")
                else:
                    ui.notify('Failed to clear sample collection times', color='negative')
            
            ui.button('Clear Collection Times', on_click=clear_all_samples).classes('mt-2 bg-red-500 text-white')
        else:
            # Show which samples are collected
            with ui.row().classes('w-full gap-2 mt-2'):
                if measurement and measurement.ph_sample_time:
                    ui.label('pH: Collected').classes('text-green-500')
                else:
                    ui.label('pH: Not collected').classes('text-gray-500')
                
                if measurement and measurement.micro_sample_time:
                    ui.label('Micro: Collected').classes('text-green-500')
                else:
                    ui.label('Micro: Not collected').classes('text-gray-500')
                
                if measurement and measurement.hplc_sample_time:
                    ui.label('HPLC: Collected').classes('text-green-500')
                else:
                    ui.label('HPLC: Not collected').classes('text-gray-500')
            
            async def collect_all_samples():
                now = datetime.datetime.now()
                # Always override all sample times with current time
                success = await record_measurement(
                    batch_id, 
                    timepoint_id, 
                    ph_sample_time=now,
                    micro_sample_time=now,
                    hplc_sample_time=now
                )
                if success:
                    ui.notify('All samples recorded as collected', color='positive')
                    dialog.close()
                    ui.run_javascript("window.location.reload()")
                else:
                    ui.notify('Failed to record sample collection', color='negative')
            
            ui.button('Collect All Samples', on_click=collect_all_samples).classes('mt-2 bg-blue-500 text-white')
        
        ui.separator().classes('my-4')
        
        # Test Results Section
        ui.label('Test Results').classes('text-lg font-bold')
        ui.label('Enter results for each test').classes('text-sm text-gray-600')
        
        with ui.tabs().classes('w-full') as tabs:
            ph_tab = ui.tab('pH')
            micro_tab = ui.tab('Microbiology')
            hplc_tab = ui.tab('HPLC')
            if is_final_timepoint(timepoint_id):
                scoby_tab = ui.tab('SCOBY')
            notes_tab = ui.tab('Notes')
        
        with ui.tab_panels(tabs, value=ph_tab).classes('w-full'):
            # pH Panel
            with ui.tab_panel(ph_tab):
                ph_value = ui.number(
                    'pH Value', 
                    value=measurement.ph_value if measurement and measurement.ph_value else None, 
                    min=0, 
                    max=14, 
                    step=0.01
                ).classes('w-full')
                
                async def save_ph():
                    success = await record_measurement(
                        batch_id, 
                        timepoint_id, 
                        ph_value=ph_value.value
                    )
                    if success:
                        ui.notify('pH value saved', color='positive')
                        dialog.close()
                        ui.run_javascript("window.location.reload()")
                    else:
                        ui.notify('Failed to save pH value', color='negative')
                
                ui.button('Save pH Result', on_click=save_ph, color='green').classes('mt-2 bg-green-500 text-white')
            
            # Microbiology Panel
            with ui.tab_panel(micro_tab):
                micro_results = ui.textarea(
                    'Microbiology Results',
                    value=measurement.micro_results if measurement and measurement.micro_results else '',
                    placeholder='Enter CFU counts and any observations here...'
                ).classes('w-full')
                
                async def save_micro():
                    success = await record_measurement(
                        batch_id, 
                        timepoint_id, 
                        micro_results=micro_results.value
                    )
                    if success:
                        ui.notify('Microbiology results saved', color='positive')
                        dialog.close()
                        ui.run_javascript("window.location.reload()")
                    else:
                        ui.notify('Failed to save microbiology results', color='negative')
                
                ui.button('Save Micro Results', on_click=save_micro, color='green').classes('mt-2 bg-green-500 text-white')
            
            # HPLC Panel
            with ui.tab_panel(hplc_tab):
                hplc_results = ui.textarea(
                    'HPLC Results',
                    value=measurement.hplc_results if measurement and measurement.hplc_results else '',
                    placeholder='Enter HPLC results and any observations here...'
                ).classes('w-full')
                
                async def save_hplc():
                    success = await record_measurement(
                        batch_id, 
                        timepoint_id, 
                        hplc_results=hplc_results.value
                    )
                    if success:
                        ui.notify('HPLC results saved', color='positive')
                        dialog.close()
                        ui.run_javascript("window.location.reload()")
                    else:
                        ui.notify('Failed to save HPLC results', color='negative')
                
                ui.button('Save HPLC Results', on_click=save_hplc, color='green').classes('mt-2 bg-green-500 text-white')
            
            # SCOBY Panel (only for final timepoint)
            if is_final_timepoint(timepoint_id):
                with ui.tab_panel(scoby_tab):
                    scoby_wet_weight = ui.number(
                        'Wet Weight (g)',
                        value=measurement.scoby_wet_weight if measurement and measurement.scoby_wet_weight else None,
                        min=0,
                        step=0.1
                    ).classes('w-full')
                    
                    scoby_dry_weight = ui.number(
                        'Dry Weight (g)',
                        value=measurement.scoby_dry_weight if measurement and measurement.scoby_dry_weight else None,
                        min=0,
                        step=0.1
                    ).classes('w-full')
                    
                    async def save_scoby():
                        success = await record_measurement(
                            batch_id, 
                            timepoint_id, 
                            scoby_wet_weight=scoby_wet_weight.value,
                            scoby_dry_weight=scoby_dry_weight.value
                        )
                        if success:
                            ui.notify('SCOBY weights saved', color='positive')
                            dialog.close()
                            ui.run_javascript("window.location.reload()")
                        else:
                            ui.notify('Failed to save SCOBY weights', color='negative')
                    
                    ui.button('Save SCOBY Weights', on_click=save_scoby).classes('mt-2 bg-green-500 text-white')
            
            # Notes Panel
            with ui.tab_panel(notes_tab):
                notes = ui.textarea(
                    'Notes',
                    value=measurement.notes if measurement and measurement.notes else '',
                    placeholder='Enter any additional notes here...'
                ).classes('w-full')
                
                async def save_notes():
                    success = await record_measurement(
                        batch_id, 
                        timepoint_id, 
                        notes=notes.value
                    )
                    if success:
                        ui.notify('Notes saved', color='positive')
                        dialog.close()
                        ui.run_javascript("window.location.reload()")
                    else:
                        ui.notify('Failed to save notes', color='negative')
                
                ui.button('Save Notes', on_click=save_notes, color='green').classes('mt-2 bg-green-500 text-white')
        
        ui.separator().classes('my-4')
        
        # Mark as completed section
        completed = ui.checkbox(
            'Mark all measurements as completed', 
            value=measurement.completed if measurement and measurement.completed else False
        )
        
        async def mark_completed():
            success = await record_measurement(
                batch_id, 
                timepoint_id, 
                completed=completed.value
            )
            if success:
                ui.notify(f'Measurement marked as {"completed" if completed.value else "incomplete"}', color='positive')
                dialog.close()
                ui.run_javascript("window.location.reload()")
            else:
                ui.notify('Failed to update completion status', color='negative')
        
        ui.button('Update Completion Status', on_click=mark_completed).classes('mt-2 bg-blue-500 text-white')
        
        with ui.row().classes('w-full justify-end mt-4'):
            ui.button('Close', on_click=dialog.close)
        
        dialog.open()
