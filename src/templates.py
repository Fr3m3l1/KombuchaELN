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
        
        <div class="section-title">Experimental Setup</div>
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
            </tbody>
        </table>
        
        <div class="section-title">Workflow Timeline</div>
        <div class="workflow-timeline">
    """
    
    # Add workflow timeline visualization
    timepoints = ["Preparation", "Incubation Start", "Sampling", "Analysis", "Completion"]
    current_point = 0
    
    # Determine current point based on sample statuses
    if any(sample.get('status') == "Completed" for sample in samples):
        current_point = 4
    elif samples_with_results > 0:
        current_point = 3
    elif any(sample.get('status') in ["Sampling", "Analysis Pending"] for sample in samples):
        current_point = 2
    elif any(sample.get('status') == "Incubating" for sample in samples):
        current_point = 1
    elif any(sample.get('status') == "Prepared" for sample in samples):
        current_point = 0
    
    for i, point in enumerate(timepoints):
        point_class = "completed" if i < current_point else ("current" if i == current_point else "")
        connector_class = "completed" if i < current_point else ""
        
        html += f"""
            <div class="timeline-point {point_class}">
                {i+1}
                <div class="timeline-label">{point}</div>
            </div>
        """
        
        # Add connector if not the last point
        if i < len(timepoints) - 1:
            html += f'<div class="timeline-connector {connector_class}"></div>'
    
    html += """
        </div>
    </div>
    
    <div class="report-section">
        <div class="section-title">Results</div>
    """
    
    # Check if we have any measurement data to display
    has_measurements = False
    for sample in samples:
        if (sample.get('ph_value') or sample.get('micro_results') or 
            sample.get('hplc_results') or sample.get('scoby_wet_weight')):
            has_measurements = True
            break
    
    if has_measurements:
        # Display measurement data
        html += """
        <div class="section-title">pH Measurements</div>
        <div class="chart-placeholder">
            [pH measurements chart would be displayed here]
        </div>
        
        <div class="section-title">Batch Measurements</div>
        <table>
            <thead>
                <tr>
                    <th>Batch/Sample</th>
                    <th>pH Value</th>
                    <th>SCOBY Wet Weight (g)</th>
                    <th>SCOBY Dry Weight (g)</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for sample in samples:
            ph_value = sample.get('ph_value', 'N/A')
            scoby_wet = sample.get('scoby_wet_weight', 'N/A')
            scoby_dry = sample.get('scoby_dry_weight', 'N/A')
            
            html += f"""
                <tr>
                    <td>{sample.get('name', '')}</td>
                    <td>{ph_value}</td>
                    <td>{scoby_wet}</td>
                    <td>{scoby_dry}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        
        <div class="section-title">Microbiology Results</div>
        """
        
        # Display microbiology results if available
        for sample in samples:
            if sample.get('micro_results'):
                html += f"""
                <div class="timepoint-card">
                    <div class="timepoint-header">{sample.get('name', '')}</div>
                    <pre>{sample.get('micro_results', '')}</pre>
                </div>
                """
        
        html += """
        <div class="section-title">HPLC Results</div>
        <div class="chart-placeholder">
            [HPLC results chart would be displayed here]
        </div>
        """
        
        # Display HPLC results if available
        for sample in samples:
            if sample.get('hplc_results'):
                html += f"""
                <div class="timepoint-card">
                    <div class="timepoint-header">{sample.get('name', '')}</div>
                    <pre>{sample.get('hplc_results', '')}</pre>
                </div>
                """
    else:
        html += """
        <p>No measurement data is available yet. Results will be displayed here once measurements are recorded.</p>
        """
    
    html += """
    </div>
    
    <div class="report-section">
        <div class="section-title">Discussion</div>
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
