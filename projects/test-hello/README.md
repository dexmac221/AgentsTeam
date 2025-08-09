# Clone the repository
git clone https://github.com/yourusername/hello-world-cli.git
cd hello-world-cli

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt

# Install the package in editable mode
pip install -e .