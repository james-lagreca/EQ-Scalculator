EQ-Scalculator/
├── .gitignore          # Tells git which files (like .pyc or __pycache__) to ignore.
├── README.md           # Your project's main documentation page.
├── requirements.txt      # Lists Python packages needed (e.g., streamlit).
|
├── scalculator_app.py  # The main entry point for your Streamlit application.
|
├── _core/                # A package for your core, reusable logic.
│   ├── __init__.py       # Makes the _core directory a Python package.
│   ├── generic_solver.py # The mathematical engine. Solves equations.
│   └── helpers.py        # Utility functions, especially the unit converter.
|
├── scaling_models/       # Directory to hold all data from academic papers.
│   ├── __init__.py       # Makes scaling_models a Python package.
│   │
│   ├── leonard_2014/     # A dedicated folder for the Leonard (2014) paper.
│   │   ├── leonard_2014.json  # The structured data file with all coefficients and units.
│   │   └── Leonard_2014.pdf   # (Optional but good practice) Keep the source PDF here.
│   │
│   └── yang_2020/        # A dedicated folder for the Yang et al. (2020) paper.
│       ├── yang_2020.json     # The structured data file for this model.
│       └── Yang_et_al_2020.pdf # (Optional) The source PDF.
|
└── tests/                # A folder for your automated tests.
    ├── __init__.py       # Makes the tests directory a Python package.
    ├── test_helpers.py   # Tests for your unit conversion functions.
    └── test_solver.py    # Tests for your generic solver with known values.

