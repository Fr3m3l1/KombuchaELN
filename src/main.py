from nicegui import ui, app
from src.database import setup_database
from src.auth import create_login_ui, create_register_ui, create_api_key_ui, login_required, get_current_user, logout
from src.experiments import create_experiment_list_ui, create_new_experiment_ui, create_experiment_edit_ui

# Set up the database
engine = setup_database()

# Set up the app
app.title = 'Kombucha ELN'

# Define routes
@ui.page('/')
@login_required
def index():
    with ui.column().classes('w-full max-w-6xl mx-auto p-4'):
        with ui.row().classes('w-full justify-between items-center'):
            ui.label('Kombucha ELN').classes('text-3xl')
            
            with ui.row():
                ui.button('API Key', on_click=lambda: ui.run_javascript("window.location.href = '/api-key'")).classes('mr-2')
                
                def handle_logout():
                    # Clear user from session
                    if 'username' in app.storage.user:
                        del app.storage.user['username']
                    # Navigate to login page
                    logout()
                
                ui.button('Logout', on_click=handle_logout)
        
        ui.separator()
        
        create_experiment_list_ui()

@ui.page('/login')
def login_page():
    with ui.column().classes('w-full max-w-6xl mx-auto p-4'):
        ui.label('Kombucha ELN').classes('text-3xl text-center mb-8')
        create_login_ui()

@ui.page('/register')
def register_page():
    with ui.column().classes('w-full max-w-6xl mx-auto p-4'):
        ui.label('Kombucha ELN').classes('text-3xl text-center mb-8')
        create_register_ui()

@ui.page('/api-key')
@login_required
def api_key_page():
    with ui.column().classes('w-full max-w-6xl mx-auto p-4'):
        with ui.row().classes('w-full justify-between items-center'):
            ui.label('Kombucha ELN').classes('text-3xl')
            ui.button('Back to Dashboard', on_click=lambda: ui.run_javascript("window.location.href = '/'")).classes('mr-2')
        
        ui.separator()
        
        create_api_key_ui()

@ui.page('/new-experiment')
@login_required
def new_experiment_page():
    with ui.column().classes('w-full max-w-6xl mx-auto p-4'):
        with ui.row().classes('w-full justify-between items-center'):
            ui.label('Kombucha ELN').classes('text-3xl')
            ui.button('Back to Dashboard', on_click=lambda: ui.run_javascript("window.location.href = '/'")).classes('mr-2')
        
        ui.separator()
        
        create_new_experiment_ui()

@ui.page('/experiment/{experiment_id}')
@login_required
def experiment_page(experiment_id: int):
    with ui.column().classes('w-full max-w-6xl mx-auto p-4'):
        with ui.row().classes('w-full justify-between items-center'):
            ui.label('Kombucha ELN').classes('text-3xl')
            ui.button('Back to Dashboard', on_click=lambda: ui.run_javascript("window.location.href = '/'")).classes('mr-2')
        
        ui.separator()
        
        create_experiment_edit_ui(experiment_id)

# Add custom CSS
@ui.page('/styles.css')
def styles():
    return """
    body {
        font-family: 'Arial', sans-serif;
        background-color: #f5f5f5;
    }
    
    .nicegui-card {
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-radius: 8px;
    }
    
    .nicegui-button {
        border-radius: 4px;
    }
    """

# Add custom head content
ui.add_head_html("""
<link rel="stylesheet" href="/styles.css">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
""")

# Redirect to login if not authenticated
@app.middleware('http')
async def auth_middleware(request, call_next):
    if request.url.path not in ['/login', '/register', '/styles.css'] and not request.url.path.startswith('/_nicegui'):
        if get_current_user() is None:
            # Use a different approach for redirection
            from starlette.responses import RedirectResponse
            return RedirectResponse(url='/login')
    return await call_next(request)
