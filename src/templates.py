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
