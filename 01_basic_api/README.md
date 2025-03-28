# How To Run

1. Set up virtual environment:
```bash
python -m venv .venv

# On Linux or MacOS
source .venv/bin/activate

# On Windows
.venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
uvicorn main:app --reload
```