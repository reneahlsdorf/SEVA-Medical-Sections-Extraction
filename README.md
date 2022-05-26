SEVA Medical Sections Extraction
==============================

The repository for the SEVA PhysionNet publication "Semi-supervised Extraction, Validation and model-based Analysis of Medical Sections in MIMIC-III Patient Notes"

Repo Organization
------------

    ├── LICENSE
    ├── data               <- The main data directory. Please store all data files from the PhysioNet project here to make the other scripts work.
    │
    ├── notebooks          <- Jupyter notebooks for loading the SVC models and generating sections from MIMIC
    │
    ├── src                <- The Python module for the sectioning code. Imported by the other notebooks and scripts.
    │
    │
    ├── requirements.txt   <- The requirements file for the notebooks and scripts. Jupyter should already be present on your system and is thus not included here. Generated with `pip freeze > requirements.txt`
    │
    ├── setup.py           <- Makes sectioning module pip installable (pip install -e .) so src can be imported
    └── src                <- Source code for use in this project.
        ├── __init__.py    <- Makes src a Python module
        │
        ├── data           <- Helper to load and process the trigger file etc.
        │
        ├── db             <- Helpers to interface Google BigQuery MIMIC tables
        │
        ├── models         <- Helpers to utilize the pre-trained SVC sectioning models
        │
        └── sectioning     <- Core module which contains all the sectioning logic
    

--------

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
