
# MediTrack-App

A simple web application built with Python and Flask to help you track medicine expiry dates and provide alerts.

## 📜 About

This project is a "Medicine Expiry Alert Giver." It provides a web interface where users can log the medicines they have, including their expiry dates. The application will then track these dates and provide alerts for medicines that are close to expiring, helping to manage medical supplies and prevent waste.

## ✨ Features

Based on the repository files, the app likely includes the following features:

* **Add & Manage Medicines:** A user interface to add new medicines, including details like name, type, and expiry date.
* **Expiry Tracking:** A dashboard or list view to see all tracked medicines.
* **Alert System:** Visual alerts or notifications for medicines that are near or past their expiry date.
* **Persistent Storage:** Uses an **SQLite** database (`database.db`) to store the medicine list, so your data is saved.

## 🛠️ Technology Stack

* **Backend:** [**Python**](https://www.python.org/) (using the [**Flask**](https://flask.palletsprojects.com/) framework, as suggested by `app.py` and the `templates` folder).
* **Database:** [**SQLite**](https://www.sqlite.org/index.html) (as suggested by `database.db` and `init_db.py`).
* **Frontend:** **HTML**, **CSS**, and **JavaScript** (located in the `static` and `templates` folders).

## 🚀 Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

You will need to have [Python 3](https://www.python.org/downloads/) and `pip` (the Python package manager) installed on your system.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/niks1503/MediTrack-App.git](https://github.com/niks1503/MediTrack-App.git)
    cd MediTrack-App
    ```

2.  **Create and activate a virtual environment (Recommended):**
    * On macOS/Linux:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    * On Windows:
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```

3.  **Install the required dependencies:**
    *(This project does not include a `requirements.txt` file, so the primary dependency is listed below.)*
    ```bash
    pip install Flask
    ```

4.  **Initialize the database:**
    Run the `init_db.py` script to set up the `database.db` file and its tables.
    ```bash
    python init_db.py
    ```

## Usage

1.  **Run the Flask application:**
    ```bash
    python app.py
    ```

2.  **Open the application in your browser:**
    Navigate to [http://127.0.0.1:5000/](http://127.0.0.1:5000/) (this is the default address for a local Flask app).

