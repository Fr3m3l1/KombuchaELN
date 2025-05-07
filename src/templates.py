from src.timepoints import get_batch_measurement

def generate_batch_dict_from_db_batch(batch, timepoints=None):
    batch_dict = {
        'name': batch.name,
        'tea_type': batch.tea_type,
        'tea_concentration': batch.tea_concentration,
        'water_amount': batch.water_amount,
        'sugar_type': batch.sugar_type,
        'sugar_concentration': batch.sugar_concentration,
        'inoculum_concentration': batch.inoculum_concentration,
        'temperature': batch.temperature,
        'status': batch.status,
        'measurements': []
    }

    if timepoints:
        for tp in timepoints:
            m = get_batch_measurement(batch.id, tp.id)
            if m:
                measurement_data = {
                    'timepoint': tp.name,
                    'ph_value': m.ph_value,
                    'ph_sample_time': m.ph_sample_time,
                    'micro_results': m.micro_results,
                    'micro_sample_time': m.micro_sample_time,
                    'hplc_results': m.hplc_results,
                    'hplc_sample_time': m.hplc_sample_time,
                    'scoby_wet_weight': m.scoby_wet_weight,
                    'scoby_dry_weight': m.scoby_dry_weight,
                    'notes': m.notes,
                    'completed': m.completed
                }
                batch_dict['measurements'].append(measurement_data)

    return batch_dict


def generate_experiment_html(experiment_title, samples):
    """
    Generate HTML content for an experiment with samples
    
    Args:
        experiment_title: The title of the experiment
        samples: A list of sample dictionaries with parameters
        
    Returns:
        HTML string for the experiment
    """
    
    # Count how many samples have results
    samples_with_results = 0
    for sample in samples:
        if sample.get('ph_value') or sample.get('micro_results') or sample.get('hplc_results'):
            samples_with_results += 1
    
    
    # Start building the HTML with CSS styling
    html = f"""
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 20px;
        }}
        .report-header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #ddd;
        }}
        .report-title {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .report-meta {{
            font-size: 14px;
            color: #666;
        }}
        .report-section {{
            margin-bottom: 30px;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
            padding-bottom: 5px;
            border-bottom: 1px solid #eee;
        }}
        .status-badge {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .status-planning {{
            background-color: #e3f2fd;
            color: #0d47a1;
        }}
        .status-running {{
            background-color: #fff8e1;
            color: #ff6f00;
        }}
        .status-analysis {{
            background-color: #f3e5f5;
            color: #6a1b9a;
        }}
        .status-completed {{
            background-color: #e8f5e9;
            color: #1b5e20;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        th, td {{
            padding: 10px;
            border: 1px solid #ddd;
            text-align: left;
        }}
        th {{
            background-color: #f5f5f5;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        .parameter-name {{
            font-weight: bold;
            width: 30%;
        }}
        .chart-placeholder {{
            background-color: #f5f5f5;
            border: 1px dashed #ccc;
            padding: 20px;
            text-align: center;
            margin-bottom: 20px;
        }}
        .timepoint-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .timepoint-card {{
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            background-color: #fff;
        }}
        .timepoint-header {{
            font-weight: bold;
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 1px solid #eee;
        }}
        .measurement-item {{
            margin-bottom: 5px;
        }}
        .notes-section {{
            background-color: #fffde7;
            padding: 15px;
            border-left: 4px solid #ffd600;
            margin-bottom: 20px;
        }}
        .workflow-timeline {{
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }}
        .timeline-point {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background-color: #ddd;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            color: white;
            position: relative;
        }}
        .timeline-point.completed {{
            background-color: #4caf50;
        }}
        .timeline-point.current {{
            background-color: #2196f3;
        }}
        .timeline-connector {{
            height: 3px;
            flex-grow: 1;
            background-color: #ddd;
        }}
        .timeline-connector.completed {{
            background-color: #4caf50;
        }}
        .timeline-label {{
            position: absolute;
            top: 25px;
            left: 50%;
            transform: translateX(-50%);
            white-space: nowrap;
            font-size: 12px;
        }}
    </style>
    
    <div class="report-section">
        <div class="section-title">Abstract</div>
        <p>
            This report documents a kombucha fermentation experiment involving {len(samples)} different batches/samples.
            The experiment investigates the effects of various parameters on kombucha fermentation, including tea type,
            sugar concentration, and fermentation temperature.
        </p>
    </div>
    
    <div class="report-section">
        <div class="section-title">Introduction</div>
        <p>
            Kombucha is a fermented tea beverage produced by a symbiotic culture of bacteria and yeast (SCOBY).
            This experiment aims to investigate how different parameters affect the fermentation process and the
            final product characteristics. The parameters under investigation include tea type, tea concentration,
            sugar type, sugar concentration, inoculum concentration, and fermentation temperature.
        </p>
    </div>
    
    <div class="report-section">
        <div class="section-title">Materials and Methods</div>
        <p>
            The experiment was conducted using {len(samples)} different batches with varying parameters.
            Each batch was prepared according to the parameters specified in the table below and monitored
            throughout the fermentation process. Measurements were taken at specific timepoints to track
            changes in pH, microbial composition, and metabolite production.
        </p>
        
        <p>
        <div class="section-title">Experimental Setup</div>
        <p>

        <table>
            <thead>
                <tr>
                    <th>Batch/Sample</th>
                    <th>Tea Type</th>
                    <th>Tea Concentration</th>
                    <th>Water Amount</th>
                    <th>Sugar Type</th>
                    <th>Sugar Concentration</th>
                    <th>Inoculum Concentration</th>
                    <th>Temperature</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for sample in samples:
        status = sample.get('status', 'Setup')
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
                <td>{status}</td>
            </tr>
        """

    html += """
        </div>
    </div>
    
    <div class="report-section">
    <p>
        <div class="section-title">Results</div>
    <p>
    """
    
    # Check if we have any measurement data in any sample at any timepoint
    has_measurements = any(
        m.get('ph_value') or m.get('micro_results') or m.get('hplc_results') or m.get('scoby_wet_weight')
        for sample in samples
        for m in sample.get('measurements', [])
    )

    if has_measurements:
        html += """
        <table>
            <thead>
                <tr>
                    <th>Batch</th>
                    <th>Timepoint</th>
                    <th>pH</th>
                    <th>pH Sample Time</th>
                    <th>Microbiology</th>
                    <th>Micro Sample Time</th>
                    <th>HPLC</th>
                    <th>HPLC Sample Time</th>
                    <th>SCOBY Wet (g)</th>
                    <th>SCOBY Dry (g)</th>
                    <th>Notes</th>
                </tr>
            </thead>
            <tbody>
        """
        for sample in samples:
            for m in sample.get('measurements', []):
                html += f"""
                <tr>
                    <td>{sample.get('name')}</td>
                    <td>{m.get('timepoint')}</td>
                    <td>{m.get('ph_value') or 'N/A'}</td>
                    <td>{m.get('ph_sample_time').strftime('%Y-%m-%d %H:%M') if m.get('ph_sample_time') else 'N/A'}</td>
                    <td>{(m.get('micro_results')[:30] + '...') if m.get('micro_results') else 'N/A'}</td>
                    <td>{m.get('micro_sample_time').strftime('%Y-%m-%d %H:%M') if m.get('micro_sample_time') else 'N/A'}</td>
                    <td>{(m.get('hplc_results')[:30] + '...') if m.get('hplc_results') else 'N/A'}</td>
                    <td>{m.get('hplc_sample_time').strftime('%Y-%m-%d %H:%M') if m.get('hplc_sample_time') else 'N/A'}</td>
                    <td>{m.get('scoby_wet_weight') or 'N/A'}</td>
                    <td>{m.get('scoby_dry_weight') or 'N/A'}</td>
                    <td>{m.get('notes') or '—'}</td>
                </tr>
                """
        html += """
            </tbody>
        </table>
        """
    else:
        html += """
        <p>No measurement data is available yet. Results will be displayed here once measurements are recorded.</p>
        """
    
    html += """
    </div>
    
    <div class="report-section">
    <p>
        <div class="section-title">Discussion</div>
    </p>
        <p>
            This section should contain an interpretation of the results, comparing the different batches
            and discussing how the various parameters affected the fermentation process and final product.
            Key observations and trends should be highlighted here.
        </p>
    </div>
    
    <div class="report-section">
        <div class="section-title">Conclusion</div>
        <p>
            Summarize the main findings of the experiment and their implications. Discuss whether the
            experiment achieved its objectives and what insights were gained about kombucha fermentation.
            Suggest potential applications of these findings and directions for future research.
        </p>
    </div>
    """
    
    # Add notes section if any batch has notes
    has_notes = any(sample.get('notes') for sample in samples)
    if has_notes:
        html += """
        <div class="report-section">
            <div class="section-title">Notes and Observations</div>
            <div class="notes-section">
        """
        
        for sample in samples:
            if sample.get('notes'):
                html += f"""
                <p><strong>{sample.get('name', '')}:</strong> {sample.get('notes', '')}</p>
                """
        
        html += """
            </div>
        </div>
        """
    else:
        html += """
        <div class="report-section">
            <div class="section-title">Notes and Observations</div>
            <div class="notes-section">
                <p>No specific notes or observations have been recorded for this experiment.</p>
            </div>
        </div>
        """
    
    return html

# This function is kept for backward compatibility but is no longer used
# as the application now uses Batch objects instead of Sample objects
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

def generate_batch_dict_from_db_batch(batch, timepoints=None):
    """
    Convert a Batch object to a dictionary including measurement data for all timepoints.
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
        'status': batch.status,
        'measurements': []
    }

    if timepoints:
        for tp in timepoints:
            m = get_batch_measurement(batch.id, tp.id)
            if m:
                measurement_data = {
                    'timepoint': tp.name,
                    'ph_value': m.ph_value,
                    'ph_sample_time': m.ph_sample_time,
                    'micro_results': m.micro_results,
                    'micro_sample_time': m.micro_sample_time,
                    'hplc_results': m.hplc_results,
                    'hplc_sample_time': m.hplc_sample_time,
                    'scoby_wet_weight': m.scoby_wet_weight,
                    'scoby_dry_weight': m.scoby_dry_weight,
                    'notes': m.notes,
                    'completed': m.completed
                }
                batch_dict['measurements'].append(measurement_data)

    return batch_dict