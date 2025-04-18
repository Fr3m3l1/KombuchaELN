from nicegui import ui, app
from src.database import User, get_session
import functools

def get_current_user():
    """Get the current user from the session"""
    try:
        # Use dictionary-style access with a try/except block
        try:
            username = app.storage.user['username']
            if not username:
                return None
        except (KeyError, TypeError):
            return None
        
        session = get_session()
        try:
            return session.query(User).filter_by(username=username).first()
        finally:
            session.close()
    except (AttributeError, RuntimeError):
        # Handle case when app.storage.user is not available
        return None

def login_required(func):
    """Decorator to ensure user is logged in before accessing a page"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if get_current_user() is None:
            # Use JavaScript to navigate
            ui.run_javascript(f"window.location.href = '/login'")
            return
        return func(*args, **kwargs)
    return wrapper

async def login(username, password):
    """Authenticate a user and store in the session"""
    session = get_session()
    try:
        user = session.query(User).filter_by(username=username).first()
        
        if user and user.verify_password(password):
            # Return the username to be stored in session by the caller
            return True, username
        return False, None
    finally:
        session.close()

def logout():
    """Log out the current user"""
    # Use JavaScript to navigate
    ui.run_javascript(f"window.location.href = '/login'")

async def register(username, password):
    """Register a new user"""
    session = get_session()
    try:
        # Check if user already exists
        existing_user = session.query(User).filter_by(username=username).first()
        if existing_user:
            return False, "Username already exists"
        
        # Create new user
        user = User(username=username)
        user.set_password(password)
        
        session.add(user)
        session.commit()
        return True, "User registered successfully"
    except Exception as e:
        session.rollback()
        return False, f"Error: {str(e)}"
    finally:
        session.close()

async def update_api_key(api_key):
    """Update the API key for the current user"""
    current_user = get_current_user()
    
    if current_user is None:
        return False, "Not logged in"
    
    session = get_session()
    try:
        user = session.query(User).filter_by(username=current_user.username).first()
        if not user:
            return False, "User not found"
        
        user.elab_api_key = api_key
        session.commit()
        
        return True, "API key updated successfully"
    except Exception as e:
        session.rollback()
        return False, f"Error: {str(e)}"
    finally:
        session.close()

def get_current_user_api_key():
    """Get the API key for the current user"""
    current_user = get_current_user()
    if current_user is None:
        return None
    return current_user.elab_api_key

def create_login_ui():
    """Create the login UI components"""
    with ui.card().classes('w-96 mx-auto'):
        ui.label('Login').classes('text-2xl text-center')
        username = ui.input('Username').classes('w-full')
        password = ui.input('Password', password=True).classes('w-full')
        
        # Add status label to show login status
        status_label = ui.label('').classes('text-center text-red-500')
        
        async def handle_login():
            # Clear previous status
            status_label.text = ''
            
            # Validate inputs
            if not username.value:
                status_label.text = 'Username is required'
                return
                
            if not password.value:
                status_label.text = 'Password is required'
                return
            
            try:
                success, user_name = await login(username.value, password.value)
                if success:
                    # Store username in session
                    app.storage.user['username'] = user_name
                    ui.notify('Login successful', color='positive')
                    # Use JavaScript to navigate
                    ui.run_javascript(f"window.location.href = '/'")
                else:
                    status_label.text = 'Invalid username or password'
            except Exception as e:
                status_label.text = f"Error: {str(e)}"
        
        # Create a form element without the prevent_default parameter
        with ui.element('form'):
            ui.button('Login', on_click=handle_login).classes('w-full')
        
        ui.separator()
        
        ui.label('New User?').classes('text-center')
        
        def go_to_register():
            # Use JavaScript to navigate
            ui.run_javascript(f"window.location.href = '/register'")
        
        ui.button('Register', on_click=go_to_register).classes('w-full')

def create_register_ui():
    """Create the registration UI components"""
    with ui.card().classes('w-96 mx-auto'):
        ui.label('Register').classes('text-2xl text-center')
        username = ui.input('Username').classes('w-full')
        password = ui.input('Password', password=True).classes('w-full')
        confirm_password = ui.input('Confirm Password', password=True).classes('w-full')
        
        # Add status label to show registration status
        status_label = ui.label('').classes('text-center text-red-500')
        
        async def handle_register():
            # Clear previous status
            status_label.text = ''
            
            # Validate inputs
            if not username.value:
                status_label.text = 'Username is required'
                return
                
            if not password.value:
                status_label.text = 'Password is required'
                return
                
            if password.value != confirm_password.value:
                status_label.text = 'Passwords do not match'
                return
            
            try:
                success, message = await register(username.value, password.value)
                if success:
                    ui.notify(message, color='positive')
                    # Use JavaScript to navigate
                    ui.run_javascript(f"window.location.href = '/login'")
                else:
                    status_label.text = message
            except Exception as e:
                status_label.text = f"Error: {str(e)}"
        
        # Create a form element without the prevent_default parameter
        with ui.element('form'):
            ui.button('Register', on_click=handle_register).classes('w-full')
        
        ui.separator()
        
        def go_to_login():
            # Use JavaScript to navigate
            ui.run_javascript(f"window.location.href = '/login'")
        
        ui.button('Back to Login', on_click=go_to_login).classes('w-full')

def create_api_key_ui():
    """Create the API key management UI components"""
    with ui.card().classes('w-96 mx-auto'):
        ui.label('API Key Management').classes('text-2xl text-center')
        
        current_key = get_current_user_api_key() or ''
        api_key = ui.input('elabFTW API Key', value=current_key).classes('w-full')
        
        # Add status label to show update status
        status_label = ui.label('').classes('text-center text-red-500')
        
        async def handle_update():
            # Clear previous status
            status_label.text = ''
            
            try:
                success, message = await update_api_key(api_key.value)
                if success:
                    ui.notify(message, color='positive')
                else:
                    status_label.text = message
            except Exception as e:
                status_label.text = f"Error: {str(e)}"
        
        ui.button('Save API Key', on_click=handle_update).classes('w-full')
        
        ui.separator()
        
        def go_to_dashboard():
            # Use JavaScript to navigate
            ui.run_javascript(f"window.location.href = '/'")
        
        ui.button('Back to Dashboard', on_click=go_to_dashboard).classes('w-full')
