from nicegui import ui
from src.database import Experiment, Batch, get_session
from src.auth import get_current_user, login_required
from src.templates import generate_experiment_html, generate_batch_dict_from_db_batch
from src.elab_api import create_and_update_experiment
import datetime

# New function to duplicate a batch
async def duplicate_batch(batch_id):
    session = get_session()
    try:
        original = session.query(Batch).filter_by(id=batch_id).first()
        if not original:
            ui.notify('Original batch not found', color='negative')
            return

        new_batch = Batch(
            experiment_id=original.experiment_id,
            name=f'{original.name} (Copy)',
            status='Setup',
            tea_type=original.tea_type,
            tea_concentration=original.tea_concentration,
            water_amount=original.water_amount,
            sugar_type=original.sugar_type,
            sugar_concentration=original.sugar_concentration,
            inoculum_concentration=original.inoculum_concentration,
            temperature=original.temperature,
        )

        session.add(new_batch)
        session.commit()

        ui.notify('Batch duplicated successfully', color='positive')
        ui.run_javascript("window.location.reload()")
    except Exception as e:
        session.rollback()
        ui.notify(f"Error duplicating batch: {str(e)}", color='negative')
    finally:
        session.close()

# Function to delete a batch
async def delete_batch(batch_id):
    session = get_session()
    try:
        batch = session.query(Batch).filter_by(id=batch_id).first()
        if not batch:
            ui.notify('Batch not found', color='negative')
            return

        session.delete(batch)
        session.commit()

        ui.notify('Batch deleted successfully', color='positive')
        ui.run_javascript("window.location.reload()")
    except Exception as e:
        session.rollback()
        ui.notify(f"Error deleting batch: {str(e)}", color='negative')
    finally:
        session.close()

def open_delete_dialog(batch_id, batch_name):
    with ui.dialog() as dialog, ui.card():
        ui.label(f"Are you sure you want to delete {batch_name}?").classes("text-lg")

        async def confirm_delete():
            await delete_batch(batch_id)
            dialog.close()

        with ui.row().classes("justify-end w-full"):
            ui.button('Cancel', on_click=dialog.close).classes('mr-2')
            ui.button('Delete', color='red', on_click=confirm_delete)

        dialog.open()

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
        
        # Handle case where no batches are found
        if not batches:
            ui.notify("No batches found for this experiment. Please add at least one batch.", color='warning')
            # Create an empty list of batch dictionaries
            batch_dicts = []
            html_content = generate_experiment_html(experiment.title, batch_dicts)
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
                            ui.button('Sync', on_click=lambda e=exp.id: sync_experiment_with_elabftw(e), color='indigo').classes('mr-2')
        
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
        
        ui.button('Create', on_click=handle_create, color='green').classes('mt-4')
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

    with ui.grid(columns=2).classes('w-full gap-4 mt-2'):
        for batch in batches:
            with ui.card().classes('w-full'):
                with ui.row().classes('w-full justify-between items-center'):
                    ui.label(batch.name).classes('font-bold')

                with ui.row().classes('text-sm text-gray-600 mt-1'):
                    if batch.tea_type:
                        ui.label(f'Tea: {batch.tea_type}')
                    if batch.sugar_concentration:
                        ui.label(f'Sugar: {batch.sugar_concentration}g/L')
                    if batch.temperature:
                        ui.label(f'Temp: {batch.temperature}°C')

                with ui.row().classes('w-full justify-end mt-2'):
                    ui.button(
                        'View Details',
                        on_click=lambda b=batch.id: ui.run_javascript(f"window.location.href = '/batch/{b}'")
                    ).classes('mr-2')
                    ui.button(
                        'Quick Edit',
                        on_click=lambda b=batch.id: open_batch_edit_dialog(b)
                    ).classes('mr-2')
                    ui.button(
                        'Duplicate',
                        on_click=lambda b=batch.id: duplicate_batch(b)
                    ).classes('mr-2')
                    ui.button(
                        'Delete',
                        on_click=lambda b_id=batch.id, b_name=batch.name: open_delete_dialog(b_id, b_name),
                        color='red'
    )

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
                    with ui.row().classes('w-full justify-between items-center'):
                        ui.label(batch.name).classes('font-bold')
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

            ui.button('Save Experiment', on_click=save_experiment, color='green').classes('mr-2')
            ui.button('Sync with eLabFTW', on_click=lambda: sync_experiment_with_elabftw(experiment_id), color='indigo').classes('mr-2')

            # Workflow buttons
            ui.button(
                'Workflow Tracking',
                on_click=lambda: ui.run_javascript(f"window.location.href = '/experiment/{experiment_id}/workflow'"),
                color='purple'
            ).classes('mr-2')

            ui.button(
                'Configure Timepoints',
                on_click=lambda: ui.run_javascript(f"window.location.href = '/experiment/{experiment_id}/timepoints'"),
                color='pink'
            ).classes('mr-2')

            ui.button('Back to Dashboard', on_click=lambda: ui.run_javascript("window.location.href = '/'"), color='gray').classes('mr-2')
       
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
            ui.button('Save', on_click=save_batch, color='green')
        
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
                ).classes('mt-4')
    
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
        
        ui.button('Edit Parameters', on_click=lambda: open_batch_edit_dialog(batch_id)).classes('mt-2')
