# Getting Started

## Prerequisites

Check that Python 3 is installed:

```bash
# Linux / macOS
python3 --version

# Windows
python --version
```

## Run the App

1. **Create and enter a project directory**

   ```bash
   mkdir myapp
   cd myapp
   ```

2. **Create a virtual environment**

   ```bash
   # Linux / macOS
   python3 -m venv venv

   # Windows
   python -m venv venv
   ```

3. **Activate the virtual environment**

   ```bash
   # Linux / macOS
   source venv/bin/activate

   # Windows
   venv\Scripts\activate
   ```

4. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

5. **Run the program**

   ```bash
   # Linux / macOS
   python3 run.py

   # Windows
   python run.py
   ```

6. **Deactivate the virtual environment when done**

   ```bash
   deactivate
   ```

## Run Unit Tests

```bash
pytest tests
```
