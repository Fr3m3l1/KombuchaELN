from nicegui import ui
from src.database import Experiment, Sample, Batch, get_session
from src.auth import get_current_user, login_required
from src.templates import generate_experiment_html, generate_sample_dict_from_db_sample, generate_batch_dict_from_db_batch
from src.elab_api import create_and_update_experiment
import datetime

async def create_experiment(title, num_batches):
    """
    Create a new experiment with the given title and number of batches
    
    Args:
        title: The title of the experiment
        num_batches: The number of batches to create
        
    Returns:
        The created experiment ID or None if creation fails
    """
    current_user = get_current_user()
    if current_user is None:
        return None
    
    session = get_session()
    try:
        # Create experiment
        experiment = Experiment(
            title=title,
            user_id=current_user.username,
            created_at=datetime.datetime.utcnow(),
            status="Planning"
        )
        
        session.add(experiment)
        session.flush()  # Get the experiment ID
        
        # Create empty batches
        for i in range(num_batches):
            batch = Batch(
                experiment_id=experiment.id,
                name=f"Batch {i+1}",
                status="Setup"
            )
            session.add(batch)
        
        session.commit()
        return experiment.id
    except Exception as e:
        session.rollback()
        ui.notify(f"Error creating experiment: {str(e)}", color='negative')
        return None
    finally:
        session.close()

def get_user_experiments():
    """
    Get all experiments for the current user
    
    Returns:
        A list of experiment objects
    """
    current_user = get_current_user()
    if current_user is None:
        return []
    
    session = get_session()
    try:
        experiments = session.query(Experiment).filter_by(user_id=current_user.username).all()
        return experiments
    finally:
        session.close()

def get_experiment(experiment_id):
    """
    Get an experiment by ID
    
    Args:
        experiment_id: The ID of the experiment
        
    Returns:
        The experiment object or None if not found
    """
    session = get_session()
    try:
        experiment = session.query(Experiment).filter_by(id=experiment_id).first()
        return experiment
    finally:
        session.close()

def get_experiment_batches(experiment_id):
    """
    Get all batches for an experiment
    
    Args:
        experiment_id: The ID of the experiment
        
    Returns:
        A list of batch objects
    """
    session = get_session()
    try:
        batches = session.query(Batch).filter_by(experiment_id=experiment_id).all()
        return batches
    finally:
        session.close()

def get_batch(batch_id):
    """
    Get a batch by ID
    
    Args:
        batch_id: The ID of the batch
        
    Returns:
        The batch object or None if not found
    """
    session = get_session()
    try:
        batch = session.query(Batch).filter_by(id=batch_id).first()
        return batch
    finally:
        session.close()

async def update_batch(batch_id, **kwargs):
    """
    Update a batch with the given parameters
    
    Args:
        batch_id: The ID of the batch
        **kwargs: The parameters to update
        
    Returns:
        True if update was successful, False otherwise
    """
    session = get_session()
    try:
        batch = session.query(Batch).filter_by(id=batch_id).first()
        if not batch:
            return False
        
        # Update batch parameters
        for key, value in kwargs.items():
            if hasattr(batch, key):
                setattr(batch, key, value)
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        ui.notify(f"Error updating batch: {str(e)}", color='negative')
        return False
    finally:
        session.close()

async def update_experiment(experiment_id, **kwargs):
    """
    Update an experiment with the given parameters
    
    Args:
        experiment_id: The ID of the experiment
        **kwargs: The parameters to update
        
    Returns:
        True if update was successful, False otherwise
    """
    session = get_session()
    try:
        experiment = session.query(Experiment).filter_by(id=experiment_id).first()
        if not experiment:
            return False
        
        # Update experiment parameters
        for key, value in kwargs.items():
            if hasattr(experiment, key):
                setattr(experiment, key, value)
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        ui.notify(f"Error updating experiment: {str(e)}", color='negative')
        return False
    finally:
        session.close()

async def log_batch_action(batch_id, action_type, timestamp=None, **values):
    """
    Log an action for a batch and update relevant fields
    
    Args:
        batch_id: The ID of the batch
        action_type: Type of action (preparation, incubation_start, etc.)
        timestamp: Optional timestamp (defaults to current time)
        **values: Additional values to update (e.g., ph_value)
        
    Returns:
        True if logging was successful, False otherwise
    """
    if timestamp is None:
        timestamp = datetime.datetime.utcnow()
    
    session = get_session()
    try:
        batch = session.query(Batch).filter_by(id=batch_id).first()
        if not batch:
            return False
        
        # Update the appropriate timestamp field based on action_type
        if hasattr(batch, f"{action_type}_time"):
            setattr(batch, f"{action_type}_time", timestamp)
        
        # Update any additional values
        for key, value in values.items():
            if hasattr(batch, key):
                setattr(batch, key, value)
        
        # Update status based on action
        status_mapping = {
            "preparation": "Prepared",
            "incubation_start": "Incubating",
            "incubation_end": "Sampling",
            "sample_split": "Analysis Pending",
            "micro_plating": "Micro Plated",
            "hplc_prep": "HPLC Prepped",
            "ph_measurement": "pH Measured",
            "scoby_wet_weight": "SCOBY Weighed",
            "scoby_dry_weight": "Completed"
        }
        
        if action_type in status_mapping:
            batch.status = status_mapping[action_type]
        
        session.commit()
        
        # Update experiment status based on batch statuses
        await update_experiment_status_from_batches(batch.experiment_id)
        
        return True
    except Exception as e:
        session.rollback()
        ui.notify(f"Error logging batch action: {str(e)}", color='negative')
        return False
    finally:
        session.close()

async def update_experiment_status_from_batches(experiment_id):
    """
    Update an experiment's status based on its batches
    
    Args:
        experiment_id: The ID of the experiment
        
    Returns:
        True if update was successful, False otherwise
    """
    session = get_session()
    try:
        experiment = session.query(Experiment).filter_by(id=experiment_id).first()
        if not experiment:
            return False
        
        batches = session.query(Batch).filter_by(experiment_id=experiment_id).all()
        
        # Determine experiment status based on batch statuses
        if not batches:
            experiment.status = "Planning"
        elif all(batch.status == "Completed" for batch in batches):
            experiment.status = "Completed"
        elif any(batch.status == "Setup" for batch in batches):
            experiment.status = "Planning"
        elif any(batch.status in ["Incubating", "Sampling"] for batch in batches):
            experiment.status = "Running"
        else:
            experiment.status = "Analysis"
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        ui.notify(f"Error updating experiment status: {str(e)}", color='negative')
        return False
    finally:
        session.close()

async def add_batch_to_experiment(experiment_id, batch_name):
    """
    Add a new batch to an experiment
    
    Args:
        experiment_id: The ID of the experiment
        batch_name: The name of the new batch
        
    Returns:
        The ID of the created batch or None if creation fails
    """
    session = get_session()
    try:
        # Create batch
        batch = Batch(
            experiment_id=experiment_id,
            name=batch_name,
            status="Setup"
        )
        
        session.add(batch)
        session.commit()
        
        return batch.id
    except Exception as e:
        session.rollback()
        ui.notify(f"Error adding batch: {str(e)}", color='negative')
        return None
    finally:
        session.close()

async def sync_experiment_with_elabftw(experiment_id):
    """
    Sync an experiment with elabFTW
    
    Args:
        experiment_id: The ID of the experiment
        
    Returns:
        True if sync was successful, False otherwise
    """
    current_user = get_current_user()
    if current_user is None or not current_user.elab_api_key:
        ui.notify("API key not set. Please set your API key first.", color='negative')
        return False
    
    session = get_session()
    try:
        # Get experiment and batches
        experiment = session.query(Experiment).filter_by(id=experiment_id).first()
        if not experiment:
            ui.notify("Experiment not found", color='negative')
            return False
        
        batches = session.query(Batch).filter_by(experiment_id=experiment_id).all()
        
        # If no batches found, try to get samples (for backward compatibility)
        if not batches:
            samples = session.query(Sample).filter_by(experiment_id=experiment_id).all()
            sample_dicts = [generate_sample_dict_from_db_sample(sample) for sample in samples]
            html_content = generate_experiment_html(experiment.title, sample_dicts)
        else:
            # Convert batches to dictionaries
            batch_dicts = [generate_batch_dict_from_db_batch(batch) for batch in batches]
            html_content = generate_experiment_html(experiment.title, batch_dicts)
        
        # Create experiment in elabFTW
        elab_experiment = create_and_update_experiment(
            api_key=current_user.elab_api_key,
            title=experiment.title,
            body=html_content,
            tags=["KombuchaELN", "API"]
        )
        
        if elab_experiment:
            # Update experiment with elabFTW ID
            experiment.elab_id = elab_experiment.id
            session.commit()
            
            ui.notify(f"Experiment synced with elabFTW (ID: {elab_experiment.id})", color='positive')
            return True
        else:
            ui.notify("Failed to sync with elabFTW", color='negative')
            return False
    except Exception as e:
        session.rollback()
        ui.notify(f"Error syncing with elabFTW: {str(e)}", color='negative')
        return False
    finally:
        session.close()

def create_experiment_list_ui():
    """Create the UI for listing experiments"""
    with ui.card().classes('w-full'):
        ui.label('My Experiments').classes('text-2xl')
        
        # Add filter/sort controls
        with ui.row().classes('w-full items-center mb-4'):
            status_filter = ui.select(
                ['All', 'Planning', 'Running', 'Analysis', 'Completed'],
                value='All',
                label='Filter by Status'
            ).classes('mr-4')
            
            sort_by = ui.select(
                ['Newest First', 'Oldest First', 'Title A-Z', 'Title Z-A'],
                value='Newest First',
                label='Sort by'
            )
        
        experiments = get_user_experiments()
        
        if not experiments:
            ui.label('No experiments found').classes('text-gray-500')
        else:
            # Create a card-based layout instead of a simple grid
            with ui.grid(columns=3).classes('w-full gap-4'):
                for exp in experiments:
                    with ui.card().classes('w-full'):
                        # Status indicator
                        status = getattr(exp, 'status', 'Planning')
                        status_colors = {
                            'Planning': 'blue',
                            'Running': 'orange',
                            'Analysis': 'purple',
                            'Completed': 'green'
                        }
                        status_color = status_colors.get(status, 'gray')
                        
                        with ui.row().classes('w-full justify-between items-center'):
                            ui.label(exp.title).classes('text-xl font-bold')
                            ui.label(status).classes(f'text-{status_color}-500 font-bold')
                        
                        ui.label(f'Created: {exp.created_at.strftime("%Y-%m-%d %H:%M")}')
                        
                        # Count batches
                        session = get_session()
                        try:
                            batch_count = session.query(Batch).filter_by(experiment_id=exp.id).count()
                            ui.label(f'{batch_count} Batches')
                        finally:
                            session.close()
                        
                        # eLabFTW status
                        if exp.elab_id:
                            ui.label(f'Synced with eLabFTW (ID: {exp.elab_id})').classes('text-green-500')
                        else:
                            ui.label('Not synced with eLabFTW').classes('text-gray-500')
                        
                        # Action buttons
                        with ui.row().classes('w-full justify-end mt-2'):
                            ui.button('View/Edit', on_click=lambda e=exp.id: ui.run_javascript(f"window.location.href = '/experiment/{e}'")).classes('mr-2')
                            ui.button('Sync', on_click=lambda e=exp.id: sync_experiment_with_elabftw(e)).classes('mr-2')
        
        ui.button('Create New Experiment', on_click=lambda: ui.run_javascript("window.location.href = '/new-experiment'")).classes('mt-4')

def create_new_experiment_ui():
    """Create the UI for creating a new experiment"""
    with ui.card().classes('w-full'):
        ui.label('Create New Experiment').classes('text-2xl')
        
        title = ui.input('Experiment Title').classes('w-full')
        num_batches = ui.number('Number of Batches', value=1, min=1, max=20).classes('w-full')
        
        async def handle_create():
            if not title.value:
                ui.notify('Please enter a title', color='negative')
                return
            
            experiment_id = await create_experiment(title.value, int(num_batches.value))
            if experiment_id:
                ui.notify('Experiment created successfully', color='positive')
                ui.run_javascript(f"window.location.href = '/experiment/{experiment_id}'")
            else:
                ui.notify('Failed to create experiment', color='negative')
        
        ui.button('Create', on_click=handle_create).classes('mt-4')
        ui.button('Cancel', on_click=lambda: ui.run_javascript("window.location.href = '/'")).classes('mt-4 ml-2')

def create_experiment_edit_ui(experiment_id):
    """
    Create the UI for editing an experiment
    
    Args:
        experiment_id: The ID of the experiment to edit
    """
    experiment = get_experiment(experiment_id)
    if not experiment:
        ui.label('Experiment not found').classes('text-xl text-red-500')
        ui.button('Back to Dashboard', on_click=lambda: ui.run_javascript("window.location.href = '/'")).classes('mt-4')
        return
    
    batches = get_experiment_batches(experiment_id)
    
    with ui.card().classes('w-full'):
        # Header with experiment title and status
        with ui.row().classes('w-full justify-between items-center'):
            with ui.column().classes('flex-grow'):
                title_input = ui.input(value=experiment.title, label='Experiment Title').classes('text-2xl w-full')
            
            status = getattr(experiment, 'status', 'Planning')
            status_colors = {
                'Planning': 'blue',
                'Running': 'orange',
                'Analysis': 'purple',
                'Completed': 'green'
            }
            status_color = status_colors.get(status, 'gray')
            ui.label(f'Status: {status}').classes(f'text-{status_color}-500 font-bold')
        
        # Experiment notes
        notes_input = ui.textarea(
            label='Experiment Notes',
            value=getattr(experiment, 'notes', ''),
            placeholder='Enter overall experiment notes or goals here...'
        ).classes('w-full mt-4')
        
        ui.separator()
        
        # Batches section
        ui.label('Batches').classes('text-xl mt-4')
        
        # Grid layout for batch cards
        with ui.grid(columns=2).classes('w-full gap-4 mt-2'):
            for batch in batches:
                with ui.card().classes('w-full'):
                    # Batch header with name and status
                    batch_status = getattr(batch, 'status', 'Setup')
                    batch_status_colors = {
                        'Setup': 'gray',
                        'Prepared': 'blue',
                        'Incubating': 'orange',
                        'Sampling': 'purple',
                        'Analysis Pending': 'indigo',
                        'Micro Plated': 'pink',
                        'HPLC Prepped': 'yellow',
                        'pH Measured': 'green',
                        'SCOBY Weighed': 'teal',
                        'Completed': 'green'
                    }
                    batch_status_color = batch_status_colors.get(batch_status, 'gray')
                    
                    with ui.row().classes('w-full justify-between items-center'):
                        ui.label(batch.name).classes('font-bold')
                        ui.label(batch_status).classes(f'text-{batch_status_color}-500 font-bold')
                    
                    # Key parameters in a compact format
                    with ui.row().classes('text-sm text-gray-600 mt-1'):
                        if batch.tea_type:
                            ui.label(f'Tea: {batch.tea_type}')
                        if batch.sugar_concentration:
                            ui.label(f'Sugar: {batch.sugar_concentration}g/L')
                        if batch.temperature:
                            ui.label(f'Temp: {batch.temperature}°C')
                    
                    # Action buttons
                    with ui.row().classes('w-full justify-end mt-2'):
                        ui.button(
                            'View Details',
                            on_click=lambda b=batch.id: ui.run_javascript(f"window.location.href = '/batch/{b}'")
                        ).classes('mr-2')
                        
                        # Only show Quick Edit if in Setup status
                        if batch_status == 'Setup':
                            ui.button(
                                'Quick Edit',
                                on_click=lambda b=batch.id: open_batch_edit_dialog(b)
                            )
        
        # Add new batch button
        async def handle_add_batch():
            batch_name = f"Batch {len(batches) + 1}"
            batch_id = await add_batch_to_experiment(experiment_id, batch_name)
            if batch_id:
                ui.notify('Batch added successfully', color='positive')
                ui.run_javascript("window.location.reload()")
            else:
                ui.notify('Failed to add batch', color='negative')
        
        ui.button('+ Add Batch', on_click=handle_add_batch).classes('mt-4')
        
        ui.separator()
        
        # Experiment actions
        with ui.row().classes('mt-4'):
            async def save_experiment():
                success = await update_experiment(
                    experiment_id,
                    title=title_input.value,
                    notes=notes_input.value
                )
                if success:
                    ui.notify('Experiment saved', color='positive')
                else:
                    ui.notify('Failed to save experiment', color='negative')
            
            ui.button('Save Experiment', on_click=save_experiment).classes('mr-2')
            ui.button('Sync with eLabFTW', on_click=lambda: sync_experiment_with_elabftw(experiment_id)).classes('mr-2')
            
            # Start experiment button (changes status from Planning to Running)
            async def start_experiment():
                success = await update_experiment(experiment_id, status='Running')
                if success:
                    ui.notify('Experiment started', color='positive')
                    # Refresh the page to show updated status
                    ui.run_javascript("window.location.reload()")
                else:
                    ui.notify('Failed to start experiment', color='negative')
            
            if status == 'Planning':
                ui.button('Start Experiment', on_click=start_experiment).classes('mr-2')
            
            ui.button('Back to Dashboard', on_click=lambda: ui.run_javascript("window.location.href = '/'")).classes('mr-2')

def open_batch_edit_dialog(batch_id):
    """
    Open a dialog to edit batch parameters
    
    Args:
        batch_id: The ID of the batch to edit
    """
    batch = get_batch(batch_id)
    if not batch:
        ui.notify('Batch not found', color='negative')
        return
    
    with ui.dialog() as dialog, ui.card():
        ui.label(f'Edit Batch: {batch.name}').classes('text-xl font-bold')
        
        name_input = ui.input('Name', value=batch.name).classes('w-full')
        tea_type_input = ui.input('Tea Type', value=batch.tea_type, placeholder='e.g. Green, Black, Herbal').classes('w-full')
        tea_conc_input = ui.number('Tea Concentration (g/L)', value=batch.tea_concentration).classes('w-full')
        water_input = ui.number('Water Amount (mL)', value=batch.water_amount).classes('w-full')
        sugar_type_input = ui.input('Sugar Type', value=batch.sugar_type, placeholder='e.g. White, Brown, Honey').classes('w-full')
        sugar_conc_input = ui.number('Sugar Concentration (g/L)', value=batch.sugar_concentration).classes('w-full')
        inoc_conc_input = ui.number('Inoculum Concentration (%)', value=batch.inoculum_concentration, min=0, max=100).classes('w-full')
        temp_input = ui.number('Temperature (°C)', value=batch.temperature).classes('w-full')
        
        async def save_batch():
            success = await update_batch(
                batch_id,
                name=name_input.value,
                tea_type=tea_type_input.value,
                tea_concentration=tea_conc_input.value,
                water_amount=water_input.value,
                sugar_type=sugar_type_input.value,
                sugar_concentration=sugar_conc_input.value,
                inoculum_concentration=inoc_conc_input.value,
                temperature=temp_input.value
            )
            if success:
                ui.notify('Batch updated successfully', color='positive')
                dialog.close()
                ui.run_javascript("window.location.reload()")
            else:
                ui.notify('Failed to update batch', color='negative')
        
        with ui.row().classes('w-full justify-end'):
            ui.button('Cancel', on_click=dialog.close).classes('mr-2')
            ui.button('Save', on_click=save_batch)
        
        dialog.open()

def create_batch_detail_ui(batch_id):
    """
    Create the UI for viewing and tracking a batch
    
    Args:
        batch_id: The ID of the batch to view
    """
    batch = get_batch(batch_id)
    if not batch:
        ui.label('Batch not found').classes('text-xl text-red-500')
        ui.button('Back to Dashboard', on_click=lambda: ui.run_javascript("window.location.href = '/'")).classes('mt-4')
        return
    
    experiment = get_experiment(batch.experiment_id)
    
    # Header section
    with ui.card().classes('w-full'):
        with ui.row().classes('w-full justify-between items-center'):
            with ui.column():
                ui.label(f'Batch: {batch.name}').classes('text-2xl')
                ui.label(f'Experiment: {experiment.title}').classes('text-lg')
                ui.button(
                    'Back to Experiment',
                    on_click=lambda: ui.run_javascript(f"window.location.href = '/experiment/{batch.experiment_id}'")
                ).classes('text-blue-500 p-0 bg-transparent')
            
            # Status badge
            status = getattr(batch, 'status', 'Setup')
            status_colors = {
                'Setup': 'gray',
                'Prepared': 'blue',
                'Incubating': 'orange',
                'Sampling': 'purple',
                'Analysis Pending': 'indigo',
                'Micro Plated': 'pink',
                'HPLC Prepped': 'yellow',
                'pH Measured': 'green',
                'SCOBY Weighed': 'teal',
                'Completed': 'green'
            }
            status_color = status_colors.get(status, 'gray')
            ui.label(status).classes(f'text-{status_color}-500 font-bold text-xl')
    
    # Key parameters display
    with ui.card().classes('w-full mt-4'):
        ui.label('Key Parameters').classes('text-xl font-bold')
        
        with ui.grid(columns=4).classes('w-full gap-4 mt-2'):
            ui.label(f'Tea Type: {batch.tea_type or "N/A"}')
            ui.label(f'Tea Concentration: {batch.tea_concentration or "N/A"} g/L')
            ui.label(f'Water Amount: {batch.water_amount or "N/A"} mL')
            ui.label(f'Sugar Type: {batch.sugar_type or "N/A"}')
            ui.label(f'Sugar Concentration: {batch.sugar_concentration or "N/A"} g/L')
            ui.label(f'Inoculum Concentration: {batch.inoculum_concentration or "N/A"} %')
            ui.label(f'Temperature: {batch.temperature or "N/A"} °C')
        
        # Only show edit button if in Setup status
        if status == 'Setup':
            ui.button('Edit Parameters', on_click=lambda: open_batch_edit_dialog(batch_id)).classes('mt-2')
    
    # Workflow progress tracker
    with ui.card().classes('w-full mt-4'):
        ui.label('Workflow Progress').classes('text-xl font-bold')
        
        stages = ['Setup', 'Preparation', 'Incubation', 'Sampling', 'Analysis', 'Completed']
        current_stage_index = 0
        
        # Determine current stage based on status
        status_to_stage = {
            'Setup': 0,
            'Prepared': 1,
            'Incubating': 2,
            'Sampling': 3,
            'Analysis Pending': 4,
            'Micro Plated': 4,
            'HPLC Prepped': 4,
            'pH Measured': 4,
            'SCOBY Weighed': 4,
            'Completed': 5
        }
        current_stage_index = status_to_stage.get(status, 0)
        
        # Create visual timeline
        with ui.row().classes('w-full items-center mt-2'):
            for i, stage in enumerate(stages):
                # Stage circle
                circle_color = 'bg-green-500' if i < current_stage_index else ('bg-blue-500' if i == current_stage_index else 'bg-gray-300')
                with ui.element('div').classes(f'rounded-full {circle_color} w-8 h-8 flex items-center justify-center text-white'):
                    ui.label(str(i+1))
                
                # Stage name
                name_color = 'text-green-500' if i < current_stage_index else ('text-blue-500' if i == current_stage_index else 'text-gray-500')
                ui.label(stage).classes(f'{name_color} text-sm')
                
                # Connector line (except after the last stage)
                if i < len(stages) - 1:
                    line_color = 'bg-green-500' if i < current_stage_index else 'bg-gray-300'
                    ui.element('div').classes(f'{line_color} h-1 flex-grow')
    
    # Create the action sections
    create_batch_action_sections(batch, batch_id, current_stage_index)

def create_batch_action_sections(batch, batch_id, current_stage_index):
    """
    Create the action sections for a batch
    
    Args:
        batch: The batch object
        batch_id: The ID of the batch
        current_stage_index: The current stage index
    """
    status = getattr(batch, 'status', 'Setup')
    
    with ui.card().classes('w-full mt-4'):
        ui.label('Actions & Logging').classes('text-xl font-bold')
        
        # Preparation section
        with ui.expansion('Preparation (Steps 1-7)', value=(current_stage_index == 0)).classes('w-full'):
            ui.label('Mark when the batch has been prepared and inoculated').classes('text-sm text-gray-600')
            
            # Show timestamp if already prepared
            if hasattr(batch, 'preparation_time') and batch.preparation_time:
                ui.label(f'Prepared on: {batch.preparation_time.strftime("%Y-%m-%d %H:%M")}').classes('text-green-500')
            else:
                async def mark_prepared():
                    success = await log_batch_action(batch_id, 'preparation')
                    if success:
                        ui.notify('Batch marked as prepared', color='positive')
                        # Refresh the page
                        ui.run_javascript("window.location.reload()")
                
                ui.button('Mark as Prepared & Inoculated', on_click=mark_prepared)
        
        # Incubation section
        with ui.expansion('Incubation (Steps 8-10)', value=(current_stage_index == 1)).classes('w-full'):
            ui.label('Record incubation start and end times').classes('text-sm text-gray-600')
            
            # Incubation start
            if hasattr(batch, 'incubation_start_time') and batch.incubation_start_time:
                ui.label(f'Incubation started: {batch.incubation_start_time.strftime("%Y-%m-%d %H:%M")}').classes('text-green-500')
                
                # Calculate target end time (11 hours later)
                target_end = batch.incubation_start_time + datetime.timedelta(hours=11)
                ui.label(f'Target end time: {target_end.strftime("%Y-%m-%d %H:%M")}').classes('text-blue-500')
            else:
                async def start_incubation():
                    success = await log_batch_action(batch_id, 'incubation_start')
                    if success:
                        ui.notify('Incubation start recorded', color='positive')
                        # Refresh the page
                        ui.run_javascript("window.location.reload()")
                
                ui.button('Start Incubation', on_click=start_incubation)
            
            # Incubation end (only show if incubation has started)
            if hasattr(batch, 'incubation_start_time') and batch.incubation_start_time:
                if hasattr(batch, 'incubation_end_time') and batch.incubation_end_time:
                    ui.label(f'Incubation ended: {batch.incubation_end_time.strftime("%Y-%m-%d %H:%M")}').classes('text-green-500')
                else:
                    async def end_incubation():
                        success = await log_batch_action(batch_id, 'incubation_end')
                        if success:
                            ui.notify('Incubation end recorded', color='positive')
                            # Refresh the page
                            ui.run_javascript("window.location.reload()")
                    
                    ui.button('End Incubation', on_click=end_incubation)
            
            # Temperature logger IDs
            ui.label('Temperature Logger IDs').classes('mt-4')
            logger_ids = ui.input(
                label='Logger IDs (Front, Middle, Back)',
                value=getattr(batch, 'temperature_logger_ids', ''),
                placeholder='e.g., T1234, T5678, T9012'
            ).classes('w-full')
            
            async def save_logger_ids():
                success = await update_batch(batch_id, temperature_logger_ids=logger_ids.value)
                if success:
                    ui.notify('Logger IDs saved', color='positive')
                else:
                    ui.notify('Failed to save logger IDs', color='negative')
            
            ui.button('Save Logger IDs', on_click=save_logger_ids).classes('mt-2')
        
        # Sampling & Splitting section
        with ui.expansion('Sampling & Splitting (Steps 11-13)', value=(current_stage_index == 2)).classes('w-full'):
            ui.label('Record when samples were split').classes('text-sm text-gray-600')
            
            if hasattr(batch, 'sample_split_time') and batch.sample_split_time:
                ui.label(f'Samples split on: {batch.sample_split_time.strftime("%Y-%m-%d %H:%M")}').classes('text-green-500')
            else:
                async def log_sample_split():
                    success = await log_batch_action(batch_id, 'sample_split')
                    if success:
                        ui.notify('Sample splitting recorded', color='positive')
                        # Refresh the page
                        ui.run_javascript("window.location.reload()")
                
                ui.button('Log Sample Splitting', on_click=log_sample_split)
        
        # Analysis - Microbiology section
        with ui.expansion('Analysis - Microbiology (Steps 14-15)', value=(current_stage_index == 3 or current_stage_index == 4)).classes('w-full'):
            ui.label('Record microbiology dilution, plating, and results').classes('text-sm text-gray-600')
            
            if hasattr(batch, 'micro_plating_time') and batch.micro_plating_time:
                ui.label(f'Micro plating done on: {batch.micro_plating_time.strftime("%Y-%m-%d %H:%M")}').classes('text-green-500')
            else:
                async def log_micro_plating():
                    success = await log_batch_action(batch_id, 'micro_plating')
                    if success:
                        ui.notify('Micro plating recorded', color='positive')
                        # Refresh the page
                        ui.run_javascript("window.location.reload()")
                
                ui.button('Log Micro Dilution & Plating', on_click=log_micro_plating)
            
            # Micro results
            ui.label('Microbiology Results').classes('mt-4')
            micro_results = ui.textarea(
                label='CFU Counts and Notes',
                value=getattr(batch, 'micro_results', ''),
                placeholder='Enter CFU counts and any observations here...'
            ).classes('w-full')
            
            async def save_micro_results():
                success = await update_batch(batch_id, micro_results=micro_results.value)
                if success:
                    ui.notify('Micro results saved', color='positive')
                else:
                    ui.notify('Failed to save micro results', color='negative')
            
            ui.button('Save Micro Results', on_click=save_micro_results).classes('mt-2')
        
        # Analysis - HPLC section
        with ui.expansion('Analysis - HPLC (Steps 16-17)', value=(current_stage_index == 4)).classes('w-full'):
            ui.label('Record HPLC sample preparation and results').classes('text-sm text-gray-600')
            
            if hasattr(batch, 'hplc_prep_time') and batch.hplc_prep_time:
                ui.label(f'HPLC prep done on: {batch.hplc_prep_time.strftime("%Y-%m-%d %H:%M")}').classes('text-green-500')
            else:
                async def log_hplc_prep():
                    success = await log_batch_action(batch_id, 'hplc_prep')
                    if success:
                        ui.notify('HPLC prep recorded', color='positive')
                        # Refresh the page
                        ui.run_javascript("window.location.reload()")
                
                ui.button('Log HPLC Sample Prep', on_click=log_hplc_prep)
            
            # HPLC results
            ui.label('HPLC Results').classes('mt-4')
            hplc_results = ui.textarea(
                label='HPLC Data and Notes',
                value=getattr(batch, 'hplc_results', ''),
                placeholder='Enter HPLC results and any observations here...'
            ).classes('w-full')
            
            async def save_hplc_results():
                success = await update_batch(batch_id, hplc_results=hplc_results.value)
                if success:
                    ui.notify('HPLC results saved', color='positive')
                else:
                    ui.notify('Failed to save HPLC results', color='negative')
            
            ui.button('Save HPLC Results', on_click=save_hplc_results).classes('mt-2')
        
        # Analysis - pH section
        with ui.expansion('Analysis - pH (Steps 18-19)', value=(current_stage_index == 4)).classes('w-full'):
            ui.label('Record pH measurement').classes('text-sm text-gray-600')
            
            if hasattr(batch, 'ph_measurement_time') and batch.ph_measurement_time:
                ui.label(f'pH measured on: {batch.ph_measurement_time.strftime("%Y-%m-%d %H:%M")}').classes('text-green-500')
                ui.label(f'pH value: {batch.ph_value or "N/A"}').classes('text-green-500')
            else:
                ph_value = ui.number('pH Value', min=0, max=14, step=0.01).classes('w-full')
                
                async def log_ph_measurement():
                    success = await log_batch_action(batch_id, 'ph_measurement', ph_value=ph_value.value)
                    if success:
                        ui.notify('pH measurement recorded', color='positive')
                        # Refresh the page
                        ui.run_javascript("window.location.reload()")
                    else:
                        ui.notify('Failed to record pH measurement', color='negative')
                
                ui.button('Log pH Measurement', on_click=log_ph_measurement).classes('mt-2')
        
        # Analysis - SCOBY section
        with ui.expansion('Analysis - SCOBY (Steps 20-22)', value=(current_stage_index == 4)).classes('w-full'):
            ui.label('Record SCOBY weight measurements').classes('text-sm text-gray-600')
            
            # Wet weight
            if hasattr(batch, 'scoby_wet_weight_time') and batch.scoby_wet_weight_time:
                ui.label(f'SCOBY wet weight measured on: {batch.scoby_wet_weight_time.strftime("%Y-%m-%d %H:%M")}').classes('text-green-500')
                ui.label(f'Wet weight: {batch.scoby_wet_weight or "N/A"} g').classes('text-green-500')
            else:
                wet_weight = ui.number('Wet Weight (g)', min=0, step=0.1).classes('w-full')
                
                async def log_wet_weight():
                    success = await log_batch_action(batch_id, 'scoby_wet_weight', scoby_wet_weight=wet_weight.value)
                    if success:
                        ui.notify('Wet weight recorded', color='positive')
                        # Refresh the page
                        ui.run_javascript("window.location.reload()")
                    else:
                        ui.notify('Failed to record wet weight', color='negative')
                
                ui.button('Log Wet Weight', on_click=log_wet_weight).classes('mt-2')
            
            # Dry weight (only show if wet weight is recorded)
            if hasattr(batch, 'scoby_wet_weight_time') and batch.scoby_wet_weight_time:
                ui.separator().classes('my-4')
                
                if hasattr(batch, 'scoby_dry_weight') and batch.scoby_dry_weight:
                    ui.label(f'Dry weight: {batch.scoby_dry_weight} g').classes('text-green-500')
                else:
                    dry_weight = ui.number('Dry Weight (g)', min=0, step=0.1).classes('w-full')
                    
                    async def log_dry_weight():
                        success = await update_batch(batch_id, scoby_dry_weight=dry_weight.value)
                        if success:
                            # Also mark as completed
                            await log_batch_action(batch_id, 'scoby_dry_weight')
                            ui.notify('Dry weight recorded', color='positive')
                            # Refresh the page
                            ui.run_javascript("window.location.reload()")
                        else:
                            ui.notify('Failed to record dry weight', color='negative')
                    
                    ui.button('Log Dry Weight', on_click=log_dry_weight).classes('mt-2')
        
        # Batch notes
        with ui.expansion('Batch Notes', value=False).classes('w-full'):
            ui.label('General observations and notes for this batch').classes('text-sm text-gray-600')
            
            notes = ui.textarea(
                label='Notes',
                value=getattr(batch, 'notes', ''),
                placeholder='Enter any general observations or notes about this batch...'
            ).classes('w-full')
            
            async def save_notes():
                success = await update_batch(batch_id, notes=notes.value)
                if success:
                    ui.notify('Notes saved', color='positive')
                else:
                    ui.notify('Failed to save notes', color='negative')
            
            ui.button('Save Notes', on_click=save_notes).classes('mt-2')
