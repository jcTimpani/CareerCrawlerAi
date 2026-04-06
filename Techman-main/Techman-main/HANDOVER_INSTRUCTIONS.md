# Tech Company Web Crawler & Job Tracker - Handover Instructions

This document provides step-by-step instructions for installing and running the project on a new machine.

## 📋 Prerequisites

Before starting, ensure the following are installed on the system:

1.  **Python 3.11+**: [Download Python](https://www.python.org/downloads/)
    *   *Important*: Check "Add Python to PATH" during installation.
2.  **MySQL Server 8.0+**: [Download MySQL Installer](https://dev.mysql.com/downloads/installer/)
    *   Install "Server only" or "Developer Default".
    *   Remember the **root password** you set during installation.
3.  **Google Chrome**: Required for the web crawler (Selenium).
4.  **PowerShell**: Standard on Windows 10/11.

---

## 🚀 Quick Start (Automated)

The project includes an automation script to handle setup and startup.

1.  **Unzip the Project**: Extract the project folder to any location (e.g., `Documents\TechJobCrawler`).
2.  **Run the Script**:
    *   Right-click `start_project.ps1`.
    *   Select **Run with PowerShell**.

    **What the script does:**
    *   Creates a virtual environment (`venv`).
    *   Installs all required Python libraries.
    *   Downloads necessary NLP models.
    *   Starts the Backend API server.
    *   Opens the Frontend in your browser.

    > **Note**: If the backend fails to start, it's likely due to database connection errors. See "Database Setup" below.

---

## 🗄️ Database Setup (Required)

The application uses MySQL by default. You must configure it before the app can work fully.

1.  **Create the Database**:
    Open MySQL Workbench (or Command Line) and run:
    ```sql
    CREATE DATABASE tech_jobs_db;
    ```
    *(Optional: You can import the initial schema from `database/schema.sql` if tables are not auto-created)*

2.  **Configure Connection**:
    Open `config.yaml` in any text editor and update the `database` section:
    ```yaml
    database:
      type: "mysql"
      host: "localhost"
      port: 3306
      username: "root"        # Your MySQL username
      password: "YOUR_PASSWORD" # Your MySQL root password
      name: "tech_jobs_db"
    ```

---

## ⚙️ Other Configuration

### API Keys
To enable AI features (Interview Practice, Skill Gap Analysis), add your API keys in `config.yaml`:

```yaml
api_keys:
  openai: "sk-..."      # Optional: For advanced AI features
  gemini: "AIza..."     # Required: For Interview AI
```

---

## 🔧 Manual Setup (If Script Fails)

If `start_project.ps1` doesn't work, follow these manual steps:

1.  **Open Command Prompt / PowerShell** in the project folder.

2.  **Create Virtual Environment**:
    ```powershell
    python -m venv venv
    ```

3.  **Activate Environment**:
    ```powershell
    .\venv\Scripts\activate
    ```

4.  **Install Dependencies**:
    ```powershell
    pip install -r requirements.txt
    ```

5.  **Download NLP Model**:
    ```powershell
    python -m spacy download en_core_web_sm
    ```

6.  **Run Backend**:
    ```powershell
    cd backend
    python main.py
    ```

7.  **Open Frontend**:
    Double-click `frontend\index.html` or open it in your browser.

















    steps to run projects: 

    note if mysql server stopped then run these commands: 

    1) command : sudo kill -TERM 49275 35811

    2) command : 
ps aux | egrep "mysqld_safe|/Applications/XAMPP/xamppfiles/sbin/mysqld" | grep -v grep
sudo lsof -i :3306


    3) then stop all and start all in xampp.

    4) command : source venv/bin/activate

    5) command : cd backend

    6) command : python3 main.py

    7) then too see frontend open index.html which is in frontend folder 
        /Users/rahulsingh/Desktop/Capstone1/7/frontend/index.html
