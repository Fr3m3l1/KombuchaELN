import os
import elabapi_python
from elabapi_python.rest import ApiException
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Default API host
DEFAULT_HOST = "https://elabftw.lsfm.zhaw.ch/api/v2"

#"https://elabftw.michaelscheidegger.ch/api/v2"

def initialize_api_client(api_key=None):
    """
    Initialize and return an elabFTW API client
    
    Args:
        api_key: The API key to use for authentication. If None, will try to use the one from .env
        
    Returns:
        A tuple of (api_client, exp_client, items_client, info_client) or None if initialization fails
    """
    if api_key is None:
        # Try to get API key from environment
        api_key = os.getenv('elabftw_key')
        
    if not api_key:
        logger.error("No API key provided and none found in environment")
        return None
    
    try:
        # Initialize configuration
        configuration = elabapi_python.Configuration()
        configuration.host = DEFAULT_HOST
        
        # Create API client
        api_client = elabapi_python.ApiClient(configuration)
        
        # Set API key in Authorization header
        api_client.set_default_header(header_name='Authorization', header_value=api_key)
        
        # Create API objects
        info_client = elabapi_python.InfoApi(api_client)
        exp_client = elabapi_python.ExperimentsApi(api_client)
        items_client = elabapi_python.ItemsApi(api_client)
        
        # Test connection
        info_client.get_info()
        
        logger.info("ElabFTW API Client initialized successfully")
        return api_client, exp_client, items_client, info_client
    
    except ApiException as e:
        logger.error(f"API Error: {e.status} {e.reason}")
        if e.body:
            logger.error(f"Error details: {e.body}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return None

def create_and_update_experiment(api_key, title, body, category_id=None, status_id=1, tags=None, content_type=1):
    """
    Creates a new experiment in elabFTW
    
    Args:
        api_key: The API key to use for authentication
        title: The title of the experiment
        body: The HTML body content of the experiment
        category_id: The category ID (default: 1)
        status_id: The status ID (default: 1)
        tags: A list of tags (default: None)
        content_type: Content type (1=HTML, 2=Markdown) (default: 1)
        
    Returns:
        The created experiment object or None if creation fails
    """
    if tags is None:
        tags = []
    
    # Initialize API client
    clients = initialize_api_client(api_key)
    if not clients:
        return None
    
    _, exp_client, _, _ = clients
    
    try:
        logger.info(f"Creating experiment: {title}")
        
        # Create minimal experiment first
        minimal_experiment = elabapi_python.Experiment(
            title=title,
            category=category_id,
            status=status_id,
            tags=tags,
            content_type=content_type
        )
        
        # Post the experiment
        response_post, status_post, headers_post = exp_client.post_experiment_with_http_info(
            body=minimal_experiment, async_req=False
        )
        
        # Extract experiment ID from Location header
        location = headers_post.get('Location')
        if not location:
            logger.error("Failed to get Location header from response")
            return None
        
        exp_id = int(location.split('/').pop())
        logger.info(f"Created experiment with ID: {exp_id}")
        
        # Update the experiment with the body content
        update_payload = {'body': body}
        exp_client.patch_experiment_with_http_info(
            id=exp_id,
            body=update_payload,
            async_req=False
        )
        
        # Fetch and return the final experiment
        final_experiment = exp_client.get_experiment(exp_id)
        logger.info(f"Successfully updated experiment {exp_id}")
        return final_experiment
    
    except ApiException as e:
        logger.error(f"API Error: {e.status} {e.reason}")
        if e.body:
            logger.error(f"Error details: {e.body}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return None

def test_api_connection(api_key):
    """
    Test the API connection with the given key
    
    Args:
        api_key: The API key to test
        
    Returns:
        True if connection is successful, False otherwise
    """
    try:
        clients = initialize_api_client(api_key)
        if clients:
            return True
        return False
    except Exception:
        return False
