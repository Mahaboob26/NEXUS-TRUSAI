# NEXUS AI: Fair & Auditable Credit Scoring

**NEXUS AI** (formerly TRUS AI) is a next-generation credit decisioning system designed to bring transparency, fairness, and governance to AI-driven lending. It bridges the gap between black-box AI models and regulatory compliance through immutable audit logging and real-time fairness monitoring.

---

## 🚩 Problem Statement
Traditional AI credit models often suffer from:
1.  **Bias & Unfairness**: Discrimination against certain demographics due to unbalanced training data.
2.  **Lack of Transparency**: "Black box" decisions that cannot be explained to regulators or applicants.
3.  **Weak Governance**: No immutable record of *why* a decision was made or which model version was used.
4.  **Poor UX**: Clunky, outdated interfaces for loan officers and risk managers.

**NEXUS AI solves this by enforcing cryptographic audit trails, real-time disparate impact monitoring, and providing a "Glassmorphic" Pro-Max UI for decision transparency.**

---

## 🏗️ Architecture

```mermaid
graph TD
    User([User / Loan Officer]) -->|Interacts| Frontend[Streamlit Frontend]
    Frontend -->|HTTPS/JSON| Backend[FastAPI Server]
    
    subgraph "Core Services"
        Backend -->|Inference| ML_Engine[Model Engine (Random Forest)]
        Backend -->|Log Decision| Audit[Audit Service]
        Backend -->|Check Fairness| Bias_Engine[Fairness Monitor]
    end
    
    subgraph "Data Layer"
        Audit -->|Cryptographic Hash| DB[(SQLite / Audit Log)]
        ML_Engine -->|Load| Artifacts[Model .pkl / Encoders]
    end
    
    Bias_Engine -.->|Alerts| Frontend
```

---

## 💻 Tech Stack

*   **Frontend**: Streamlit (Python) with Custom CSS/Glassmorphism Theme.
*   **Backend**: FastAPI (Python) for High-Performance Async API.
*   **Database**: SQLite (SQLAlchemy ORM) for relational data and audit trails.
*   **Machine Learning**: Scikit-Learn (Random Forest, Logistic Regression), Pandas, Numpy.
*   **Visualization**: Altair & Plotly for interactive dashboards.
*   **Encoders**: OneHotEncoder & StandardScaler for robust feature processing.

---

## 🤖 AI Tools Used

*   **Google Gemini (DeepMind)**: Primary Agentic AI for code generation, architectural reasoning, and task management.
*   **SquirrelScan**: Automated tool for auditing website SEO, security, and performance.
*   **Altair**: AI-optimized declarative statistical visualization library.

---

## 🧠 Prompt Strategy Summary

We employed an **Agentic Iterative Refinement** strategy:
1.  **Discovery**: "Audit the current codebase and identify logical flaws." -> Found model ignoring categorical variables.
2.  **Planning**: "Create a step-by-step implementation plan." -> Generated `implementation_plan.md`.
3.  **Execution (Step-by-Step)**:
    *   *Backend*: Refactored `audit.py` for immutable logs.
    *   *Frontend*: Applied "Glassmorphism" UI and fixed CSS collisions.
    *   *ML*: Retrained model with `ColumnTransformer` to fix logic gaps.
4.  **Verification**: Used `squirrelscan` to verify SEO/Best Practices and manual loop for UI testing.

---

## 🏁 Final Output

*   **Executive Dashboard**: Real-time view of "Approval Mix" and "Risk Profile" using interactive Donut Charts.
*   **Fairness Monitor**: Live tracking of *Disparate Impact Ratio* to ensure compliance.
*   **Live Prediction**: Sandbox environment to test loan scenarios with immediate AI explanations.
*   **Secure Auth**: Token-based authentication flow separating Frontend and Backend logic.

---

## ⚙️ Build & Reproducibility Instructions (Mandatory)

### Prerequisites
*   **Python 3.9+** installed.
*   **Git** installed.

### Setup Instructions

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/Mahaboob26/NEXUS-TRUSAI.git
    cd NEXUS-TRUSAI
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r trus-ai-mvp/requirements.txt
    ```
    *(Note: If `requirements.txt` is missing, install core libs: `pip install fastapi uvicorn streamlit pandas scikit-learn sqlalchemy altair requests`)*

3.  **Run the Application**

    **Step A: Start the Backend** (Open Terminal 1)
    ```bash
    cd trus-ai-mvp/backend
    # Windows
    ./run_backend.bat
    # Linux/Mac: uvicorn main:app --reload
    ```

    **Step B: Start the Frontend** (Open Terminal 2)
    ```bash
    cd trus-ai-mvp/frontend
    # Windows
    ./run_frontend.bat
    # Linux/Mac: streamlit run streamlit_app.py
    ```

4.  **Access the App**
    *   Frontend: [http://localhost:8501](http://localhost:8501)
    *   API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📂 Source Code Structure
*   `trus-ai-mvp/backend`: API & Database logic.
*   `trus-ai-mvp/frontend`: UI logic.
*   `indian_model_training`: ML Scripts & Jupyter Notebooks.

