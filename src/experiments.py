from nicegui import ui
from src.database import Experiment, Sample, get_session
from src.auth import get_current_user, login_required
from src.templates import generate_experiment_html, generate_sample_dict_from_db_sample
from src.elab_api import create_and_update_experiment
import datetime

async def create_experiment(title, num_samples):
    """
    Create a new experiment with the given title and number of samples
    
    Args:
        title: The title of the experiment
        num_samples: The number of samples to create
        
    Returns:
        The created experiment object or None if creation fails
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
            created_at=datetime.datetime.utcnow()
        )
        
        session.add(experiment)
        session.flush()  # Get the experiment ID
        
        # Create empty samples
        for i in range(num_samples):
            sample = Sample(
                experiment_id=experiment.id,
                name=f"Sample {i+1}"
            )
            session.add(sample)
        
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

def get_experiment_samples(experiment_id):
    """
    Get all samples for an experiment
    
    Args:
        experiment_id: The ID of the experiment
        
    Returns:
        A list of sample objects
    """
    session = get_session()
    try:
        samples = session.query(Sample).filter_by(experiment_id=experiment_id).all()
        return samples
    finally:
        session.close()

async def update_sample(sample_id, **kwargs):
    """
    Update a sample with the given parameters
    
    Args:
        sample_id: The ID of the sample
        **kwargs: The parameters to update
        
    Returns:
        True if update was successful, False otherwise
    """
    session = get_session()
    try:
        sample = session.query(Sample).filter_by(id=sample_id).first()
        if not sample:
            return False
        
        # Update sample parameters
        for key, value in kwargs.items():
            if hasattr(sample, key):
                setattr(sample, key, value)
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        ui.notify(f"Error updating sample: {str(e)}", color='negative')
        return False
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
        # Get experiment and samples
        experiment = session.query(Experiment).filter_by(id=experiment_id).first()
        if not experiment:
            ui.notify("Experiment not found", color='negative')
            return False
        
        samples = session.query(Sample).filter_by(experiment_id=experiment_id).all()
        
        # Convert samples to dictionaries
        sample_dicts = [generate_sample_dict_from_db_sample(sample) for sample in samples]
        
        # Generate HTML content
        html_content = generate_experiment_html(experiment.title, sample_dicts)
        
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
        
        experiments = get_user_experiments()
        
        if not experiments:
            ui.label('No experiments found').classes('text-gray-500')
        else:
            # Create a simple grid layout for the table
            with ui.grid(columns=4).classes('w-full'):
                # Table headers
                ui.label('Title').classes('font-bold')
                ui.label('Created').classes('font-bold')
                ui.label('elabFTW ID').classes('font-bold')
                ui.label('Actions').classes('font-bold')
                
                # Table rows
                for exp in experiments:
                    ui.label(exp.title)
                    ui.label(exp.created_at.strftime('%Y-%m-%d %H:%M'))
                    ui.label(str(exp.elab_id) if exp.elab_id else 'Not synced')
                    
                    # Action buttons in the last column
                    with ui.element('div'):
                        ui.button('Edit', on_click=lambda e=exp.id: ui.run_javascript(f"window.location.href = '/experiment/{e}'")).classes('mr-2')
        
        ui.button('Create New Experiment', on_click=lambda: ui.run_javascript("window.location.href = '/new-experiment'")).classes('mt-4')

def create_new_experiment_ui():
    """Create the UI for creating a new experiment"""
    with ui.card().classes('w-full'):
        ui.label('Create New Experiment').classes('text-2xl')
        
        title = ui.input('Experiment Title').classes('w-full')
        num_samples = ui.number('Number of Samples', value=1, min=1, max=20).classes('w-full')
        
        async def handle_create():
            if not title.value:
                ui.notify('Please enter a title', color='negative')
                return
            
            experiment_id = await create_experiment(title.value, int(num_samples.value))
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
    
    samples = get_experiment_samples(experiment_id)
    
    with ui.card().classes('w-full'):
        ui.label(f'Edit Experiment: {experiment.title}').classes('text-2xl')
        
        # Experiment details
        with ui.row().classes('w-full'):
            ui.label('Title:').classes('font-bold')
            title_input = ui.input(value=experiment.title).classes('w-full')
        
        ui.separator()
        
        # Samples
        ui.label('Samples').classes('text-xl mt-4')
        
        for sample in samples:
            with ui.card().classes('w-full mb-4'):
                ui.label(f'Sample: {sample.name}').classes('font-bold')
                
                with ui.grid(columns=2).classes('w-full gap-4'):
                    # Sample name
                    name_input = ui.input('Name', value=sample.name).classes('w-full')
                    
                    # Tea type
                    tea_type_input = ui.input(
                        'Tea Type',
                        placeholder='e.g. Green, Black, Herbal',
                        value=sample.tea_type
                    ).classes('w-full')
                    
                    # Tea concentration
                    tea_conc_input = ui.number('Tea Concentration (g/L)', value=sample.tea_concentration).classes('w-full')
                    
                    # Water amount
                    water_input = ui.number('Water Amount (mL)', value=sample.water_amount).classes('w-full')
                    
                    # Sugar type
                    sugar_type_input = ui.input(
                        'Sugar Type',
                        placeholder='e.g. White, Brown, Honey',
                        value=sample.sugar_type
                    ).classes('w-full')
                    
                    # Sugar concentration
                    sugar_conc_input = ui.number('Sugar Concentration (g/L)', value=sample.sugar_concentration).classes('w-full')
                    
                    # Inoculum concentration
                    inoc_conc_input = ui.number('Inoculum Concentration (%)', value=sample.inoculum_concentration).classes('w-full')
                    
                    # Temperature
                    temp_input = ui.number('Temperature (°C)', value=sample.temperature).classes('w-full')
                
                async def save_sample(s_id, name_i, tea_type_i, tea_conc_i, water_i, sugar_type_i, sugar_conc_i, inoc_conc_i, temp_i):
                    success = await update_sample(
                        s_id,
                        name=name_i.value,
                        tea_type=tea_type_i.value,
                        tea_concentration=tea_conc_i.value,
                        water_amount=water_i.value,
                        sugar_type=sugar_type_i.value,
                        sugar_concentration=sugar_conc_i.value,
                        inoculum_concentration=inoc_conc_i.value,
                        temperature=temp_i.value
                    )
                    if success:
                        ui.notify('Sample updated successfully', color='positive')
                    else:
                        ui.notify('Failed to update sample', color='negative')
                
                ui.button(
                    'Save Sample', 
                    on_click=lambda s=sample.id, n=name_input, tt=tea_type_input, tc=tea_conc_input, 
                                    w=water_input, st=sugar_type_input, sc=sugar_conc_input, 
                                    ic=inoc_conc_input, t=temp_input: save_sample(s, n, tt, tc, w, st, sc, ic, t)
                ).classes('mt-2')
        
        ui.separator()
        
        # Actions
        with ui.row().classes('mt-4'):
            ui.button('Save Experiment', on_click=lambda: ui.notify('Experiment saved', color='positive')).classes('mr-2')
            ui.button('Sync with elabFTW', on_click=lambda: sync_experiment_with_elabftw(experiment_id)).classes('mr-2')
            ui.button('Back to Dashboard', on_click=lambda: ui.run_javascript("window.location.href = '/'")).classes('mr-2')
