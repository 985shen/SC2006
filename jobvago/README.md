# Installing python virtual env on a mac and run program
---
1. check if python3 is installed: `python3 --version`
2. create a directory: mkdir folder, cd folder
3. create the virtual env: `python3 -m venv venv`
4. activate the virtual env: `source venv/bin/activate`
5. install required modules: `pip install -r requirements.txt`
6. run main program: `python3 run.py`
7. deactivate the virtual env: `deactivate`


# Installing python virtual env on a windows and run program
---
1. check if python3 is installed: `python -version`
2. create a directory: mkdir folder, cd folder
3. create the virtual env: `python -m venv venv`
4. activate the virtual env: `venv\Scripts\activate`
5. install required modules: `pip install -r requirements.txt`
6. run main program: `python run.py`
7. deactivate the virtual env: `deactivate`

# Run Unit Tests
---
1. `pytest tests`