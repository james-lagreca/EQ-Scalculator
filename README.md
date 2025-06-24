# EQ-Scalculator: Earthquake Scaling Relationship Calculator

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://eq-scalculator.streamlit.app/) <!-- TODO: Replace with your actual Streamlit app URL -->

An interactive web application for calculating, exploring, and comparing empirical earthquake fault-scaling relationships from published literature.

This tool is designed for seismologists, geologists, earthquake engineers, and students to quickly work with different scaling laws without needing to manually implement the equations.

![Application Screenshot](https://raw.githubusercontent.com/james-lagreca/EQ-Scalculator/main/screenshots/explore_relationships.png)
<!-- TODO: Upload your screenshot to a 'screenshots' folder in your repo and update this link -->

---

## ✨ Features

EQ-Scalculator provides a comprehensive suite of tools built into a user-friendly interface:

* **Single Calculation:** Quickly convert one parameter to another (e.g., Moment Magnitude `Mw` to Rupture Area `A`) using a specific published model.
* **Batch Processing:** Upload a CSV or Excel file with a list of input values and calculate the corresponding output parameter for the entire dataset in one go.
* **Monte Carlo Simulation:** Run thousands of simulations to understand the uncertainty in an output parameter. This feature allows you to weight multiple scaling models and account for aleatory variability.
* **Interactive Exploration:** Plot and visually compare different scaling relationship models on a dynamic log-log or linear scale graph. This is perfect for understanding how different models behave across a range of values.
* **Unit Conversion:** Automatically handles and converts between common units (e.g., `km` to `m`, `Nm` to `dyne.cm`).
* **Extensible Model Library:** The app is built on a modular system where new scaling relationship models can be easily added by creating a simple JSON file.

## 🚀 Live Demo

You can access the live, running application here:

**[https://eq-scalculator.streamlit.app/](https://eq-scalculator.streamlit.app/)**
<!-- TODO: Replace this with your actual Streamlit app URL -->

---

## 🛠️ Running Locally

To run this application on your own machine, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/james-lagreca/EQ-Scalculator.git](https://github.com/james-lagreca/EQ-Scalculator.git)
    cd EQ-Scalculator
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # For Windows
    python -m venv .venv
    .\.venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install the required dependencies:**
    The project uses a `requirements.txt` file to manage its dependencies.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Streamlit app:**
    ```bash
    streamlit run scaculator_app.py
    ```
    The application should now be open and running in your default web browser.

---

## 🏗️ Project Structure

The repository is organized to be clear and extensible:

EQ-Scalculator/│├── .streamlit/             # Streamlit configuration files (optional)├── _core/                  # Core calculation logic│   ├── generic_solver.py   # Main engine for solving equations│   └── helpers.py          # Unit conversion functions│├── scaling_models/         # Directory for model-defining JSON files│   └── leonard_2014/│       └── leonard_2014.json # Example model definition│├── scaculator_app.py       # The main Streamlit application file├── requirements.txt        # Python package dependencies└── README.md               # This file
### Adding New Scaling Models

One of the key designs of this app is the ability to easily add new scaling relationships. To add a new model:

1.  Create a new JSON file in the `scaling_models/` directory. You can create a new sub-directory for the author if you wish.
2.  Follow the structure of `leonard_2014.json`. Define the paper, fault types, and the specific relationship equations. The app will automatically discover and load any valid `.json` files it finds in this directory on startup.

---


