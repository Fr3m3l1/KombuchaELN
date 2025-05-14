from nicegui import ui
from src.database import Experiment, Batch, get_session
from src.auth import get_current_user, login_required
from src.templates import generate_experiment_html, generate_batch_dict_from_db_batch
from src.elab_api import create_and_update_experiment, initialize_api_client
from src.timepoints import get_experiment_timepoints
from elabapi_python.rest import ApiException
import datetime

# Function to delete an experiment
async def delete_experiment(experiment_id):
    session = get_session()
    try:
        experiment = session.query(Experiment).filter_by(id=experiment_id).first()
        if not experiment:
            ui.notify('Experiment not found', color='negative')
            return False

        # Delete all batches associated with this experiment
        session.query(Batch).filter_by(experiment_id=experiment_id).delete()
        
        # Delete the experiment
        session.delete(experiment)
        session.commit()

        ui.notify('Experiment deleted successfully', color='positive')
        ui.run_javascript("window.location.href = '/'")
        return True
    except Exception as e:
        session.rollback()
        ui.notify(f"Error deleting experiment: {str(e)}", color='negative')
        return False
    finally:
        session.close()

def open_experiment_delete_dialog(experiment_id, experiment_title):
    with ui.dialog() as dialog, ui.card():
        ui.label(f"Are you sure you want to delete experiment '{experiment_title}'?").classes("text-lg")
        ui.label("This will delete all batches and associated data. This action cannot be undone.").classes("text-red-500")

        async def confirm_delete():
            success = await delete_experiment(experiment_id)
            dialog.close()

        with ui.row().classes("justify-end w-full mt-4"):
            ui.button('Cancel', on_click=dialog.close).classes('mr-2')
            ui.button('Delete', color='red', on_click=confirm_delete)

        dialog.open()

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
    Sync an experiment with eLabFTW.
    If elab_id exists, update the experiment.
    Otherwise, create a new one.

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
        experiment = session.query(Experiment).filter_by(id=experiment_id).first()
        if not experiment:
            ui.notify("Experiment not found", color='negative')
            return False

        batches = session.query(Batch).filter_by(experiment_id=experiment_id).all()
        timepoints = get_experiment_timepoints(experiment_id)

        # Build a list of batch dicts with measurements from all timepoints
        batch_dicts = []
        for batch in batches:
            batch_dict = generate_batch_dict_from_db_batch(batch, timepoints=timepoints)
            batch_dicts.append(batch_dict)

        # Generate full HTML report
        html_content = generate_experiment_html(experiment.title, batch_dicts)

        # Initialize API client
        clients = initialize_api_client(current_user.elab_api_key)
        if not clients:
            ui.notify("Failed to initialize API client", color='negative')
            return False

        _, exp_client, _, _ = clients

        if experiment.elab_id:
            try:
                # Update existing experiment
                update_payload = {
                    'title': experiment.title,
                    'body': html_content,
                }
                exp_client.patch_experiment_with_http_info(
                    id=experiment.elab_id,
                    body=update_payload,
                    async_req=False
                )
                ui.notify(f"Experiment updated in eLabFTW (ID: {experiment.elab_id})", color='positive')
            except ApiException as api_error:
                if api_error.status == 403:
                    # Handle 403 Forbidden error (experiment deleted or access lost)
                    # Store experiment_id before resetting elab_id
                    experiment_id_for_dialog = experiment.id
                    
                    with ui.dialog() as dialog, ui.card():
                        ui.label("eLabFTW Access Error").classes('text-xl font-bold text-red-500')
                        ui.label("The experiment cannot be accessed in eLabFTW. It may have been deleted or your access has been revoked.").classes('my-2')
                        ui.label("Would you like to create a new experiment in eLabFTW?").classes('font-bold my-2')
                        
                        async def confirm_create_new():
                            dialog.close()
                            experiment.elab_id = None
                            # Reset the elab_id
                            session.commit()
                            # Create a fresh session and get the experiment again
                            await recreate_sync_experiment(experiment_id_for_dialog)
                        
                        async def cancel_action():
                            dialog.close()
                            ui.notify("Sync canceled", color='warning')
                        
                        with ui.row().classes('w-full justify-end'):
                            ui.button('No', on_click=cancel_action).classes('mr-2')
                            ui.button('Yes, Create New', on_click=confirm_create_new, color='primary')
                        
                        dialog.open()
                    return False
                else:
                    raise  # Re-raise other API exceptions
        else:
            # Creating new experiment - no existing elab_id
            return await create_new_elab_experiment(experiment, html_content, session)
        
        return True
    except ApiException as api_error:
        session.rollback()
        if api_error.status == 403:
            ui.notify("Access to experiment in eLabFTW denied. The experiment may have been deleted or your access revoked.", color='negative')
        else:
            ui.notify(f"API Error syncing with eLabFTW: {api_error.status} {api_error.reason}", color='negative')
        return False
    except Exception as e:
        session.rollback()
        ui.notify(f"Error syncing with eLabFTW: {str(e)}", color='negative')
        return False
    finally:
        session.close()
        
async def create_new_elab_experiment(experiment, html_content, session):
    """
    Create a new experiment in eLabFTW and update the local experiment record.
    
    Args:
        experiment: The local experiment object
        html_content: The HTML content for the eLabFTW experiment
        session: The database session
        
    Returns:
        True if creation was successful, False otherwise
    """
    current_user = get_current_user()
    # Create a new experiment
    elab_experiment = create_and_update_experiment(
        api_key=current_user.elab_api_key,
        title=experiment.title,
        body=html_content,
        tags=["KombuchaELN", "API"]
    )
    if elab_experiment:
        experiment.elab_id = elab_experiment.id
        session.commit()
        # Reload the page to show updated sync status
        ui.run_javascript("window.location.reload()")
        ui.notify(f"Experiment synced with eLabFTW (ID: {elab_experiment.id})", color='positive')
        return True
    else:
        ui.notify("Failed to sync with eLabFTW", color='negative')
        return False

async def recreate_sync_experiment(experiment_id):
    """
    Re-create an experiment in eLabFTW after access was denied to the previous one.
    Creates a fresh session and generates new content to sync.
    
    Args:
        experiment_id: The ID of the experiment to sync
        
    Returns:
        True if successful, False otherwise
    """
    # Create a new session and restart the sync process
    
    new_session = get_session()
    try:
        # Get the experiment with the fresh session
        experiment = new_session.query(Experiment).filter_by(id=experiment_id).first()
        if not experiment:
            ui.notify("Could not find experiment", color='negative')
            return False
            
        # Get batches and timepoints
        batches = new_session.query(Batch).filter_by(experiment_id=experiment_id).all()
        timepoints = get_experiment_timepoints(experiment_id)
        
        # Generate HTML content
        batch_dicts = []
        for batch in batches:
            batch_dict = generate_batch_dict_from_db_batch(batch, timepoints=timepoints)
            batch_dicts.append(batch_dict)
        
        html_content = generate_experiment_html(experiment.title, batch_dicts)
        
        # Create the experiment in eLabFTW
        result = await create_new_elab_experiment(experiment, html_content, new_session)
        return result
    except Exception as e:
        new_session.rollback()
        ui.notify(f"Error recreating experiment in eLabFTW: {str(e)}", color='negative')
        return False
    finally:
        new_session.close()

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
            ).classes('mr-4 min-w-32')
            
            sort_by = ui.select(
                ['Newest First', 'Oldest First', 'Title A-Z', 'Title Z-A'],
                value='Newest First',
                label='Sort by'
            )
        
        # Get all experiments first
        all_experiments = get_user_experiments()
        
        # Grid container that will be refreshed when filters change
        experiment_grid_container = ui.element('div').classes('w-full')
        
        def apply_filters_and_sort():
            """Apply filters and sort to the experiment list"""
            # Clear the container
            experiment_grid_container.clear()
            
            # Filter experiments
            filtered_experiments = all_experiments
            if status_filter.value != 'All':
                filtered_experiments = [exp for exp in filtered_experiments if getattr(exp, 'status', 'Planning') == status_filter.value]
            
            # Sort experiments
            if sort_by.value == 'Newest First':
                filtered_experiments.sort(key=lambda x: x.created_at, reverse=True)
            elif sort_by.value == 'Oldest First':
                filtered_experiments.sort(key=lambda x: x.created_at)
            elif sort_by.value == 'Title A-Z':
                filtered_experiments.sort(key=lambda x: x.title.lower())
            elif sort_by.value == 'Title Z-A':
                filtered_experiments.sort(key=lambda x: x.title.lower(), reverse=True)
            
            # Display filtered and sorted experiments
            with experiment_grid_container:
                if not filtered_experiments:
                    ui.label('No experiments found matching filters').classes('text-gray-500')
                else:
                    # Create a card-based layout
                    with ui.grid(columns=3).classes('w-full gap-4'):
                        for exp in filtered_experiments:
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
                                    ui.button('Delete', on_click=lambda e=exp.id, t=exp.title: open_experiment_delete_dialog(e, t), color='red')
          # Set up event handlers for filter and sort changes
        status_filter.on_value_change(lambda: apply_filters_and_sort())
        sort_by.on_value_change(lambda: apply_filters_and_sort())
        
        # Initial application of filters
        apply_filters_and_sort()
        
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
        
        # eLabFTW sync status
        with ui.row().classes('w-full mt-2'):
            if experiment.elab_id:
                ui.label(f'Synced with eLabFTW (ID: {experiment.elab_id})').classes('text-green-500')
            else:
                ui.label('Not synced with eLabFTW').classes('text-gray-500')
         
        # Experiment notes
        notes_input = ui.textarea(
            label='Experiment Notes',
            value=getattr(experiment, 'notes', ''),
            placeholder='Enter overall experiment notes or goals here...'
        ).classes('w-full mt-4')
        
        ui.separator()
        
        # Batches section
        ui.label('Batches').classes('text-xl mt-4')        # Grid layout for batch cards - changed to 1 column
        with ui.grid(columns=1).classes('w-full gap-4 mt-2'):
            for batch in batches:
                # Check if batch has any parameters set
                has_parameters = (batch.tea_type or 
                                batch.tea_concentration is not None or 
                                batch.water_amount is not None or 
                                batch.sugar_type or 
                                batch.sugar_concentration is not None or 
                                batch.inoculum_concentration is not None or 
                                batch.temperature is not None)
                
                with ui.card().classes('w-full'):
                    # Open by default if no parameters are set
                    with ui.expansion(batch.name, icon='science', value=not has_parameters).classes('w-full'):
                        # Batch header with name and status (name is now in expansion header)
                        # Full parameter listing
                        with ui.column().classes('text-sm text-gray-700 mt-2'):
                            if batch.tea_type:
                                ui.html(f'<b>Tea Type:</b> {batch.tea_type}')
                            if batch.tea_concentration is not None:
                                ui.html(f'<b>Tea Concentration:</b> {batch.tea_concentration} g/L')
                            if batch.water_amount is not None:
                                ui.html(f'<b>Water Amount:</b> {batch.water_amount} mL')
                            if batch.sugar_type:
                                ui.html(f'<b>Sugar Type:</b> {batch.sugar_type}')
                            if batch.sugar_concentration is not None:
                                ui.html(f'<b>Sugar Concentration:</b> {batch.sugar_concentration} g/L')
                            if batch.inoculum_concentration is not None:
                                ui.html(f'<b>Inoculum Concentration:</b> {batch.inoculum_concentration} %')
                            if batch.temperature is not None:
                                ui.html(f'<b>Temperature:</b> {batch.temperature} °C')
                            #if batch.status:
                            #    ui.html(f'<b>Status:</b> {batch.status}')
                        
                        # Action buttons moved here
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
