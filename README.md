# Kombucha ELN

A NiceGUI interface for elabFTW designed specifically for managing kombucha experiments.

## Features

- User authentication system
- API key management for elabFTW integration
- Create and manage kombucha experiments
- Define multiple samples per experiment with detailed parameters
- Track key parameters for each sample:
  - Tea type and concentration
  - Water amount
  - Sugar type and concentration
  - Inoculum concentration
  - Temperature
- Generate formatted HTML content
- Sync experiments with elabFTW

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/KombuchaELN.git
cd KombuchaELN
```

2. Install the required dependencies:

```bash
pip install nicegui python-dotenv sqlalchemy passlib elabapi_python
```

3. Set up your elabFTW API key in the `.env` file:

```
elabftw_key=your-api-key-here
```

## Usage

1. Run the application:

```bash
python run.py
```

2. Open your browser and navigate to:

```
http://localhost:8080
```

3. Register a new user account and log in.

4. Add your elabFTW API key in the API Key management section.

5. Create new experiments, define samples, and sync with elabFTW.

## Project Structure

- `run.py`: Main entry point for the application
- `src/`: Source code directory
  - `main.py`: NiceGUI application setup and routes
  - `auth.py`: User authentication and API key management
  - `database.py`: Database models and setup
  - `elab_api.py`: Integration with elabFTW API
  - `experiments.py`: Experiment and sample management
  - `templates.py`: HTML template generation

## License

MIT
