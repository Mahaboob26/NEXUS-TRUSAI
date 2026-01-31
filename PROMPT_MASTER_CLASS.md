# 🧠 NEXUS AI: Master Prompt Engineering Guide

This document contains a **Professional Master Prompt** designed to instruct an Advanced AI Agent to build the **NEXUS AI** (formerly TRUS AI) platform from scratch. It creates the architecture, tech stack, and design language we established.

It also includes a valid **Prompt Log** of the key iterative instructions that shaped the final product.

---

## 🚀 Part 1: The Master Build Prompt

**Copy and paste this into an advanced AI Agent (Google Gemini 2.0, Claude 3.5 Sonnet, etc.) to recreate the project:**

```markdown
### Role & Objective
You are a Principal Full-Stack AI Engineer specializing in **Responsible AI** and **Fintech**. Your task is to build **NEXUS AI**, a credit decisioning platform that prioritizes Fairness, Transparency, and Auditability.

### 🛠️ Tech Stack Constraints
*   **Backend**: Python (FastAPI) - must be async.
*   **Frontend**: Python (Streamlit) - must use a custom "Glassmorphism" CSS theme.
*   **Database**: SQLite (managed via SQLAlchemy).
*   **ML Engine**: Scikit-Learn (Random Forest) + Pandas.
*   **Audit**: Cryptographic hashing (SHA-256) for every decision.

### 🎨 Design System ("Pro Max" Style)
*   **Theme**: Dark Mode with Glassmorphism (translucent cards, blur effects).
*   **Colors**: Neon accents (Green for Approval, Red for Denial, Amber for Warning) against a deep slate background.
*   **Typography**: Clean, sans-serif (Inter/Roboto).
*   **Charts**: Use **Donut Charts** (not pie) for "Approval Mix" and "Risk Profile". Use Altair or Plotly.

### 📋 Core Functional Requirements

1.  **The Credit Model**:
    *   Train a Random Forest Classifier on the Indian Loan Dataset.
    *   **CRITICAL**: You MUST use a `ColumnTransformer` with `OneHotEncoder` for categorical variables (Gender, Education, Self_Employed). Do NOT drop these columns.
    *   Output: Approval Status (Y/N) and Approval Probability (0-100%).

2.  **The Audit Engine**:
    *   Every prediction request MUST be logged to the SQLite database.
    *   Each log entry must include: Timestamp, Inputs, Model Version, Decision, and a SHA-256 Hash of the entry used for tamper-proofing.

3.  **The Dashboard (Frontend)**:
    *   **Summary Section**: Big number metrics (Total Applications, Approval Rate, Fair Lending Score).
    *   **Visualizations**:
        *   *Approval Mix*: Donut chart (Approved vs. Denied).
        *   *Risk Profile*: Donut chart (Low/Medium/High Risk buckets).
    *   **Fairness Monitor**: Calculate "Disparate Impact Ratio" (e.g., Approval Rate of Female / Approval Rate of Male). Alert if < 0.8.
    *   **Audit Trail**: A searchable data table of the latest decisions.

### 🧩 Step-by-Step Execution Plan

1.  **Setup**: Initialize the project structure (`backend/`, `frontend/`, `models/`).
2.  **ML Training**: Write `train.py` to process the data correctly (handle categoricals!) and save `model.pkl`.
3.  **Backend API**: Create `/predict` and `/audit` endpoints. Implement the hashing logic.
4.  **Frontend Layout**: Apply `st.markdown` CSS for the glassmorphic look. Build the sidebar and main dashboard grid.
5.  **Integration**: Connect Frontend to Backend via HTTP requests (do not import backend code directly into frontend).

**Action**: Generate the project structure and the core code files (`main.py`, `app.py`, `train.py`) now.
```

---

## 🔧 Part 2: Iterative Prompt Log (What Worked)

These are the specific prompts used during development to refine the product from an MVP to a "Pro" level. Use these for fine-tuning.

### 1. Fixing the Model Logic
> "Audit the current `train.py` file. I suspect it is ignoring categorical variables like 'Gender' and 'Education' because of a ValueError. Refactor the pipeline to use `ColumnTransformer` and `OneHotEncoder` so we use ALL available features."

### 2. UI/UX "Glow Up"
> "The dashboard looks too basic. Upgrade the UI to a 'Pro Max' level using a Glassmorphism aesthetic.
> *   Inject Custom CSS for translucent cards and neon borders.
> *   Use high-contrast metric containers.
> *   Replace standard tables with styled dataframes.
> *   Make it look like a high-end Fintech terminal."

### 3. Visualizations Refinement
> "Refine the Dashboard Visuals. Replace the generic volume area chart with two specific Donut Charts:
> 1.  **Approval Mix**: Showing the ratio of Approved vs. Denied.
> 2.  **Risk Profile**: Breaking down applicants into Low, Medium, and High risk buckets."

### 4. Documentation Standard
> "Generate a README.md that strictly follows these requirements:
> *   Problem Statement (with emojis)
> *   Architecture Diagram (Mermaid)
> *   Tech Stack (Badges)
> *   AI Tools Used (Table)
> *   Prompt Strategy Summary
> *   Build Reproducibility Instructions (Mandatory)"

### 5. Deployment & Cleanup
> "Remove all temporary audit report files (`*.txt`) to clean up the repository. Then, force push the entire codebase to the remote `origin main` to ensure everything is perfectly synced."

---

*This document serves as the blueprint for the **NEXUS AI** architecture and development methodology.*
