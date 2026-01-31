# NEXUS AI: Fair & Auditable Credit Scoring

**NEXUS AI** is an advanced credit decisioning system designed to bring transparency, fairness, and governance to AI-driven lending. It combines a robust Random Forest credit model with an immutable audit log and a real-time governance dashboard.

## 🚀 Key Features

*   **🛡️ Governance-First Architecture**: Every model decision is cryptographically hashed and chained to ensure audit integrity.
*   **⚖️ Algorithmic Fairness**: Built-in fairness monitors track Disparate Impact and demographic parity in real-time.
*   **🧠 Explainable AI**: Utilizes SHAP values to explain *why* a loan was approved or denied.
*   **📊 Executive Dashboard**: "Pro Max" glassmorphic UI visualizing portfolio risk, approval rates, and compliance alerts.
*   **🇮🇳 Indian Context**: Trained on Indian loan datasets, optimized for local demographics.

## 🛠️ Tech Stack

*   **Frontend**: Streamlit (with Custom CSS/Glassmorphism)
*   **Backend**: FastAPI (Python)
*   **Database**: SQLite (SQLAlchemy)
*   **ML**: Scikit-Learn (Random Forest, Logistic Regression)
*   **Visualization**: Altair & Plotly

## ⚡ Quick Start

### Prerequisites
*   Python 3.9+
*   Node.js (for optional tools)

### Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/yourusername/nexus-ai.git
    cd nexus-ai
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Application**
    
    *Terminal 1 (Backend):*
    ```bash
    cd backend
    ./run_backend.bat
    ```
    
    *Terminal 2 (Frontend):*
    ```bash
    cd frontend
    ./run_frontend.bat
    ```

4.  **Access the Dashboard**
    Open your browser at `http://localhost:8501`.

## 📂 Project Structure

*   `backend/`: FastAPI application, database models, and service logic.
*   `frontend/`: Streamlit application pages and UI themes.
*   `indian_model_training/`: ML training scripts and dataset exploration.
*   `audit_report.txt`: Automated audit findings using SquirrelScan.

---
*Built for the Future of Responsible AI.*
