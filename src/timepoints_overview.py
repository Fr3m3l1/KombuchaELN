"""
Functions for displaying the timepoint measurements overview
"""

from nicegui import ui
from src.database import Experiment, Batch, Timepoint, Measurement, get_session
from src.timepoints import get_experiment_timepoints, get_batch_measurement, record_measurement, mark_measurement_completed, is_final_timepoint
import datetime

def get_experiment_measurements_matrix(experiment_id):
    """
    Get all measurements for an experiment organized as a matrix of timepoints and batches
    
    Args:
        experiment_id: The ID of the experiment
        
    Returns:
        A dictionary with timepoints as keys and dictionary of batch measurements as values
    """
    session = get_session()
    try:
        # Get timepoints for this experiment
        timepoints = get_experiment_timepoints(experiment_id)
        
        # Get batches for this experiment
        batches = session.query(Batch).filter_by(experiment_id=experiment_id).all()
        
        # Create measurements matrix
        measurements_matrix = {}
        
        for timepoint in timepoints:
            measurements_matrix[timepoint.id] = {
                'timepoint': timepoint,
                'batches': {}
            }
            
            for batch in batches:
                # Get measurement for this batch at this timepoint
                measurement = session.query(Measurement).filter_by(
                    batch_id=batch.id,
                    timepoint_id=timepoint.id
                ).first()
                
                measurements_matrix[timepoint.id]['batches'][batch.id] = {
                    'batch': batch,
                    'measurement': measurement
                }
        
        return measurements_matrix, timepoints, batches
    finally:
        session.close()

def create_measurements_overview_ui(experiment_id):
    """
    Create the UI for the measurements overview
    
    Args:
        experiment_id: The ID of the experiment
    """
    # Get experiment info
    session = get_session()
    experiment = session.query(Experiment).filter_by(id=experiment_id).first()
    session.close()
    
    if not experiment:
        ui.label('Experiment not found').classes('text-xl text-red-500')
        return
    
    # Get measurement data matrix
    measurements_matrix, timepoints, batches = get_experiment_measurements_matrix(experiment_id)
    
    with ui.card().classes('w-full'):
        # Title and header
        ui.label(f'Measurements Overview: {experiment.title}').classes('text-xl font-bold')
        
        ui.label('This overview allows you to see all measurements across all timepoints and batches').classes('text-gray-600 mt-2')
          # Measurement table section
        ui.label('pH Values').classes('text-lg font-bold mt-4')
        
        # Create a table for pH values
        with ui.element('div').classes('w-full overflow-x-auto mt-2'):
            # Create a grid layout for a table-like structure
            with ui.grid(columns=len(timepoints) + 1).classes('w-full'):
                # Header row
                ui.label('Batch/Timepoint').classes('font-bold')
                for timepoint in timepoints:
                    ui.label(f"{timepoint.name} ({timepoint.hours}h)").classes('font-bold')
                
                # Data rows
                for batch in batches:
                    ui.label(batch.name).classes('font-bold')
                    
                    for timepoint in timepoints:
                        measurement = get_batch_measurement(batch.id, timepoint.id)
                        ph_value = measurement.ph_value if measurement and measurement.ph_value is not None else None
                        
                        # Create an editable cell
                        b_id = batch.id  # Capture batch_id for lambda
                        t_id = timepoint.id  # Capture timepoint_id for lambda
                        
                        with ui.card().classes('p-2 m-1'):
                            async def update_ph(e, b=b_id, t=t_id):
                                try:
                                    value = float(e.value) if e.value else None
                                    if value is not None and not (0 <= value <= 14):
                                        ui.notify('pH must be between 0 and 14', color='negative')
                                        e.value = ""
                                        return
                                        
                                    success = await record_measurement(
                                        b, 
                                        t, 
                                        ph_value=value
                                    )
                                    
                                    if success:
                                        ui.notify('pH updated', color='positive')
                                    else:
                                        ui.notify('Failed to update pH', color='negative')
                                except (ValueError, TypeError):
                                    ui.notify('Invalid pH value', color='negative')
                                    e.value = ""
                            
                            # Use a number input with high precision
                            ui.number(value=ph_value, 
                                    on_change=lambda e, b=b_id, t=t_id: update_ph(e, b, t),
                                    min=0, max=14, step=0.01
                            ).props('dense outlined').style('width: 100px')        # Microbiology Results section
        ui.label('Microbiology Results').classes('text-lg font-bold mt-6')
        
        # Create a grid for microbiology results
        with ui.element('div').classes('w-full overflow-x-auto mt-2'):
            with ui.grid(columns=len(timepoints) + 1).classes('w-full'):
                # Header row
                ui.label('Batch/Timepoint').classes('font-bold')
                for timepoint in timepoints:
                    ui.label(f"{timepoint.name} ({timepoint.hours}h)").classes('font-bold')
                
                # Data rows
                for batch in batches:
                    ui.label(batch.name).classes('font-bold')
                    
                    for timepoint in timepoints:
                        measurement = get_batch_measurement(batch.id, timepoint.id)
                        micro_results = measurement.micro_results if measurement and measurement.micro_results else ""
                        has_results = bool(micro_results)
                        
                        # Create cell with button
                        b_id = batch.id  # Capture batch_id for lambda
                        t_id = timepoint.id  # Capture timepoint_id for lambda
                        
                        with ui.card().classes('p-2 m-1'):
                            # Create a button to open a dialog for editing micro results
                            async def open_micro_dialog(b_id, t_id):
                                # Get current values
                                m = get_batch_measurement(b_id, t_id)
                                current_results = m.micro_results if m and m.micro_results else ""
                                
                                session = get_session()
                                batch_obj = session.query(Batch).filter_by(id=b_id).first()
                                tp_obj = session.query(Timepoint).filter_by(id=t_id).first()
                                batch_name = batch_obj.name if batch_obj else "Unknown"
                                tp_name = tp_obj.name if tp_obj else "Unknown"
                                session.close()
                                
                                with ui.dialog() as dialog, ui.card():
                                    ui.label(f'Edit Micro Results - {batch_name} at {tp_name}').classes('text-lg font-bold')
                                    
                                    results_input = ui.textarea('Microbiology Results', 
                                                                value=current_results,
                                                                placeholder='Enter CFU counts and any observations here...'
                                                            ).classes('w-full')
                                    
                                    async def save_micro():
                                        success = await record_measurement(
                                            b_id, 
                                            t_id, 
                                            micro_results=results_input.value
                                        )
                                        
                                        if success:
                                            ui.notify('Micro results updated', color='positive')
                                            dialog.close()
                                            ui.run_javascript("window.location.reload()")
                                        else:
                                            ui.notify('Failed to update micro results', color='negative')
                                    
                                    with ui.row().classes('w-full justify-end gap-2'):
                                        ui.button('Cancel', on_click=dialog.close)
                                        ui.button('Save', on_click=save_micro, color='green')
                                    
                                dialog.open()
                            
                            btn_color = 'green' if has_results else 'blue'
                            btn_label = 'View/Edit' if has_results else 'Add Results'
                            ui.button(btn_label, 
                                    on_click=lambda _, b=b_id, t=t_id: open_micro_dialog(b, t), 
                                    color=btn_color).props('dense')
          # HPLC Results section
        ui.label('HPLC Results').classes('text-lg font-bold mt-6')
        
        # Create a grid for HPLC results
        with ui.element('div').classes('w-full overflow-x-auto mt-2'):
            with ui.grid(columns=len(timepoints) + 1).classes('w-full'):
                # Header row
                ui.label('Batch/Timepoint').classes('font-bold')
                for timepoint in timepoints:
                    ui.label(f"{timepoint.name} ({timepoint.hours}h)").classes('font-bold')
                
                # Data rows
                for batch in batches:
                    ui.label(batch.name).classes('font-bold')
                    
                    for timepoint in timepoints:
                        measurement = get_batch_measurement(batch.id, timepoint.id)
                        hplc_results = measurement.hplc_results if measurement and measurement.hplc_results else ""
                        has_results = bool(hplc_results)
                        
                        # Create cell with button
                        b_id = batch.id  # Capture batch_id for lambda
                        t_id = timepoint.id  # Capture timepoint_id for lambda
                        
                        with ui.card().classes('p-2 m-1'):
                            # Create a button to open a dialog for editing HPLC results
                            async def open_hplc_dialog(b_id, t_id):
                                # Get current values
                                m = get_batch_measurement(b_id, t_id)
                                current_results = m.hplc_results if m and m.hplc_results else ""
                                
                                session = get_session()
                                batch_obj = session.query(Batch).filter_by(id=b_id).first()
                                tp_obj = session.query(Timepoint).filter_by(id=t_id).first()
                                batch_name = batch_obj.name if batch_obj else "Unknown"
                                tp_name = tp_obj.name if tp_obj else "Unknown"
                                session.close()
                                
                                with ui.dialog() as dialog, ui.card():
                                    ui.label(f'Edit HPLC Results - {batch_name} at {tp_name}').classes('text-lg font-bold')
                                    
                                    results_input = ui.textarea('HPLC Results', 
                                                                value=current_results,
                                                                placeholder='Enter HPLC results and any observations here...'
                                                            ).classes('w-full')
                                    
                                    async def save_hplc():
                                        success = await record_measurement(
                                            b_id, 
                                            t_id, 
                                            hplc_results=results_input.value
                                        )
                                        
                                        if success:
                                            ui.notify('HPLC results updated', color='positive')
                                            dialog.close()
                                            ui.run_javascript("window.location.reload()")
                                        else:
                                            ui.notify('Failed to update HPLC results', color='negative')
                                    
                                    with ui.row().classes('w-full justify-end gap-2'):
                                        ui.button('Cancel', on_click=dialog.close)
                                        ui.button('Save', on_click=save_hplc, color='green')
                                    
                                dialog.open()
                            
                            btn_color = 'green' if has_results else 'blue'
                            btn_label = 'View/Edit' if has_results else 'Add Results'
                            ui.button(btn_label, 
                                    on_click=lambda _, b=b_id, t=t_id: open_hplc_dialog(b, t), 
                                    color=btn_color).props('dense')
          # Completion Status section
        ui.label('Completion Status').classes('text-lg font-bold mt-6')
        
        # Create a grid for completion status
        with ui.element('div').classes('w-full overflow-x-auto mt-2'):
            with ui.grid(columns=len(timepoints) + 1).classes('w-full'):
                # Header row
                ui.label('Batch/Timepoint').classes('font-bold')
                for timepoint in timepoints:
                    ui.label(f"{timepoint.name} ({timepoint.hours}h)").classes('font-bold')
                
                # Data rows
                for batch in batches:
                    ui.label(batch.name).classes('font-bold')
                    
                    for timepoint in timepoints:
                        measurement = get_batch_measurement(batch.id, timepoint.id)
                        completed = measurement and measurement.completed
                        
                        # Create a cell with completion toggle
                        b_id = batch.id  # Capture batch_id for lambda
                        t_id = timepoint.id  # Capture timepoint_id for lambda
                        
                        with ui.card().classes('p-2 m-1 flex justify-center'):
                            async def toggle_completed(e, b, t):
                                success = await mark_measurement_completed(b, t, completed=e.value)
                                if success:
                                    ui.notify(f'Status updated to {"completed" if e.value else "incomplete"}', color='positive')
                                else:
                                    ui.notify('Failed to update status', color='negative')
                                    e.value = not e.value  # Revert change on failure
                            
                            # Use a switch to toggle completion
                            ui.switch('', 
                                    value=completed, 
                                    on_change=lambda e, b=b_id, t=t_id: toggle_completed(e, b, t)
                                   ).classes('ml-4')
        
        # SCOBY Weights section (only shown for final timepoints)
        # Check if any timepoint is a final timepoint
        has_final_timepoint = any(is_final_timepoint(tp.id) for tp in timepoints)
        
        if has_final_timepoint:
            ui.label('SCOBY Weights').classes('text-lg font-bold mt-6')
            
            # Create a grid for SCOBY weights
            with ui.element('div').classes('w-full overflow-x-auto mt-2'):
                with ui.grid(columns=len(timepoints) + 1).classes('w-full'):
                    # Header row
                    ui.label('Batch/Timepoint').classes('font-bold')
                    for timepoint in timepoints:
                        is_final = is_final_timepoint(timepoint.id)
                        label_text = f"{timepoint.name} ({timepoint.hours}h)"
                        if is_final:
                            label_text += " (Final)"
                        ui.label(label_text).classes('font-bold')
                    
                    # Data rows
                    for batch in batches:
                        ui.label(batch.name).classes('font-bold')
                        
                        for timepoint in timepoints:
                            measurement = get_batch_measurement(batch.id, timepoint.id)
                            is_final = is_final_timepoint(timepoint.id)
                            
                            # Capture batch_id and timepoint_id for lambda functions
                            b_id = batch.id
                            t_id = timepoint.id
                            
                            with ui.card().classes('p-2 m-1'):
                                if is_final:
                                    # Get current SCOBY weight values
                                    wet_weight = measurement.scoby_wet_weight if measurement and measurement.scoby_wet_weight is not None else None
                                    dry_weight = measurement.scoby_dry_weight if measurement and measurement.scoby_dry_weight is not None else None
                                    
                                    # Function to open a dialog for editing SCOBY weights
                                    async def open_scoby_dialog(b_id, t_id):
                                        # Get current values
                                        m = get_batch_measurement(b_id, t_id)
                                        current_wet = m.scoby_wet_weight if m and m.scoby_wet_weight is not None else None
                                        current_dry = m.scoby_dry_weight if m and m.scoby_dry_weight is not None else None
                                        
                                        session = get_session()
                                        batch_obj = session.query(Batch).filter_by(id=b_id).first()
                                        tp_obj = session.query(Timepoint).filter_by(id=t_id).first()
                                        batch_name = batch_obj.name if batch_obj else "Unknown"
                                        tp_name = tp_obj.name if tp_obj else "Unknown"
                                        session.close()
                                        
                                        with ui.dialog() as dialog, ui.card():
                                            ui.label(f'Edit SCOBY Weights - {batch_name} at {tp_name}').classes('text-lg font-bold')
                                            
                                            wet_input = ui.number('Wet Weight (g)', 
                                                                value=current_wet,
                                                                min=0, step=0.1
                                                            ).classes('w-full')
                                            
                                            dry_input = ui.number('Dry Weight (g)', 
                                                                value=current_dry,
                                                                min=0, step=0.1
                                                            ).classes('w-full')
                                            
                                            async def save_scoby():
                                                success = await record_measurement(
                                                    b_id, 
                                                    t_id, 
                                                    scoby_wet_weight=wet_input.value,
                                                    scoby_dry_weight=dry_input.value
                                                )
                                                
                                                if success:
                                                    ui.notify('SCOBY weights updated', color='positive')
                                                    dialog.close()
                                                    ui.run_javascript("window.location.reload()")
                                                else:
                                                    ui.notify('Failed to update SCOBY weights', color='negative')
                                            
                                            with ui.row().classes('w-full justify-end gap-2'):
                                                ui.button('Cancel', on_click=dialog.close)
                                                ui.button('Save', on_click=save_scoby, color='green')
                                            
                                        dialog.open()
                                    
                                    # Display SCOBY weights if available, otherwise show a button to add them
                                    if wet_weight is not None or dry_weight is not None:
                                        with ui.element('div').classes('flex flex-col items-center'):
                                            if wet_weight is not None:
                                                ui.label(f'Wet: {wet_weight}g').classes('text-sm')
                                            if dry_weight is not None:
                                                ui.label(f'Dry: {dry_weight}g').classes('text-sm')
                                            ui.button('Edit', 
                                                    on_click=lambda _, b=b_id, t=t_id: open_scoby_dialog(b, t),
                                                    color='green').props('dense size="sm"')
                                    else:
                                        ui.button('Add Weights', 
                                                on_click=lambda _, b=b_id, t=t_id: open_scoby_dialog(b, t),
                                                color='blue').props('dense')
                                else:
                                    # Display N/A for non-final timepoints
                                    ui.label('N/A').classes('text-center text-gray-500')
        
        # Navigation buttons
        with ui.row().classes('w-full justify-between mt-8'):
            ui.button('Back to Experiment', on_click=lambda: ui.run_javascript(f"window.location.href = '/experiment/{experiment_id}'"),
                      color='blue').classes('mr-2')
            ui.button('Go to Workflow', on_click=lambda: ui.run_javascript(f"window.location.href = '/experiment/{experiment_id}/workflow'"), 
                      color='purple')
