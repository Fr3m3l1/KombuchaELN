def generate_experiment_html(experiment_title, samples):
    """
    Generate HTML content for an experiment with samples
    
    Args:
        experiment_title: The title of the experiment
        samples: A list of sample dictionaries with parameters
        
    Returns:
        HTML string for the experiment
    """
    html = f"""
    <h1>{experiment_title}</h1>
    
    <h2>Experiment Overview</h2>
    <p>This experiment contains {len(samples)} samples with the following parameters:</p>
    
    <h2>Samples</h2>
    <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">
        <thead>
            <tr style="background-color: #f2f2f2;">
                <th>Sample Name</th>
                <th>Tea Type</th>
                <th>Tea Concentration</th>
                <th>Water Amount</th>
                <th>Sugar Type</th>
                <th>Sugar Concentration</th>
                <th>Inoculum Concentration</th>
                <th>Temperature</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for sample in samples:
        html += f"""
            <tr>
                <td>{sample.get('name', '')}</td>
                <td>{sample.get('tea_type', '')}</td>
                <td>{sample.get('tea_concentration', '')} g/L</td>
                <td>{sample.get('water_amount', '')} mL</td>
                <td>{sample.get('sugar_type', '')}</td>
                <td>{sample.get('sugar_concentration', '')} g/L</td>
                <td>{sample.get('inoculum_concentration', '')} %</td>
                <td>{sample.get('temperature', '')} °C</td>
            </tr>
        """
    
    html += """
        </tbody>
    </table>
    
    <h2>Methodology</h2>
    <p>The kombucha samples were prepared according to the parameters specified in the table above.</p>
    
    <h2>Notes</h2>
    <p>Add any additional notes or observations here.</p>
    """
    
    return html

def generate_sample_dict_from_db_sample(sample):
    """
    Convert a database Sample object to a dictionary for HTML generation
    
    Args:
        sample: A Sample object from the database
        
    Returns:
        Dictionary with sample parameters
    """
    return {
        'name': sample.name,
        'tea_type': sample.tea_type,
        'tea_concentration': sample.tea_concentration,
        'water_amount': sample.water_amount,
        'sugar_type': sample.sugar_type,
        'sugar_concentration': sample.sugar_concentration,
        'inoculum_concentration': sample.inoculum_concentration,
        'temperature': sample.temperature
    }

def generate_batch_dict_from_db_batch(batch):
    """
    Convert a database Batch object to a dictionary for HTML generation
    
    Args:
        batch: A Batch object from the database
        
    Returns:
        Dictionary with batch parameters and workflow data
    """
    batch_dict = {
        'name': batch.name,
        'tea_type': batch.tea_type,
        'tea_concentration': batch.tea_concentration,
        'water_amount': batch.water_amount,
        'sugar_type': batch.sugar_type,
        'sugar_concentration': batch.sugar_concentration,
        'inoculum_concentration': batch.inoculum_concentration,
        'temperature': batch.temperature,
        'status': batch.status
    }
    
    # Add workflow data if available
    if hasattr(batch, 'preparation_time') and batch.preparation_time:
        batch_dict['preparation_time'] = batch.preparation_time.strftime('%Y-%m-%d %H:%M')
    
    if hasattr(batch, 'incubation_start_time') and batch.incubation_start_time:
        batch_dict['incubation_start_time'] = batch.incubation_start_time.strftime('%Y-%m-%d %H:%M')
    
    if hasattr(batch, 'incubation_end_time') and batch.incubation_end_time:
        batch_dict['incubation_end_time'] = batch.incubation_end_time.strftime('%Y-%m-%d %H:%M')
    
    if hasattr(batch, 'sample_split_time') and batch.sample_split_time:
        batch_dict['sample_split_time'] = batch.sample_split_time.strftime('%Y-%m-%d %H:%M')
    
    if hasattr(batch, 'micro_plating_time') and batch.micro_plating_time:
        batch_dict['micro_plating_time'] = batch.micro_plating_time.strftime('%Y-%m-%d %H:%M')
    
    if hasattr(batch, 'micro_results') and batch.micro_results:
        batch_dict['micro_results'] = batch.micro_results
    
    if hasattr(batch, 'hplc_prep_time') and batch.hplc_prep_time:
        batch_dict['hplc_prep_time'] = batch.hplc_prep_time.strftime('%Y-%m-%d %H:%M')
    
    if hasattr(batch, 'hplc_results') and batch.hplc_results:
        batch_dict['hplc_results'] = batch.hplc_results
    
    if hasattr(batch, 'ph_measurement_time') and batch.ph_measurement_time:
        batch_dict['ph_measurement_time'] = batch.ph_measurement_time.strftime('%Y-%m-%d %H:%M')
    
    if hasattr(batch, 'ph_value') and batch.ph_value:
        batch_dict['ph_value'] = batch.ph_value
    
    if hasattr(batch, 'scoby_wet_weight_time') and batch.scoby_wet_weight_time:
        batch_dict['scoby_wet_weight_time'] = batch.scoby_wet_weight_time.strftime('%Y-%m-%d %H:%M')
    
    if hasattr(batch, 'scoby_wet_weight') and batch.scoby_wet_weight:
        batch_dict['scoby_wet_weight'] = batch.scoby_wet_weight
    
    if hasattr(batch, 'scoby_dry_weight') and batch.scoby_dry_weight:
        batch_dict['scoby_dry_weight'] = batch.scoby_dry_weight
    
    if hasattr(batch, 'temperature_logger_ids') and batch.temperature_logger_ids:
        batch_dict['temperature_logger_ids'] = batch.temperature_logger_ids
    
    if hasattr(batch, 'notes') and batch.notes:
        batch_dict['notes'] = batch.notes
    
    return batch_dict
