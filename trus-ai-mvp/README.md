# TRUS.AI MVP

Transparent Responsible Unified System for Ethical AI in Banking.

This MVP demonstrates:

- Loan approval / denial via an ML model (German Credit dataset)
- SHAP-based, plain-English explanations
- Dynamic consent over input fields
- Simple RAG-style chatbot advisor (local embeddings + FAISS)
- Banker/regulator dashboard with approvals/denials and model pause control
- Immutable audit trail stored in SQLite with hash chaining

## 1. Project Structure

```text
trus-ai-mvp/
  backend/
    main.py
    model/
      train_model.py
      model.pkl
      explainer.pkl
    services/
      explain.py
      remediation.py
      consent.py
      chatbot.py
      audit.py
      fairness.py
    data/
      credit_data.csv
    db.sqlite
    requirements.txt

  frontend/
    streamlit_app.py
    pages/
      Consent.py
      Dashboard.py
      Chatbot.py
    components/
      charts.py
```

## 2. Setup

From the `backend/` folder:

```bash
pip install -r requirements.txt
```

This installs FastAPI, Streamlit, scikit-learn, SHAP, Fairlearn, FAISS, sentence-transformers, etc.

> Note: the sentence-transformers model (`all-MiniLM-L6-v2`) will be downloaded on first use.

## 3. Train the Model

From `backend/`:

```bash
python -m model.train_model
```

This will:

- Download the German Credit dataset from OpenML (if not already cached)
- Save it as `data/credit_data.csv`
- Train a logistic regression pipeline
- Save `model/model.pkl` and `model/explainer.pkl`

## 4. Run the FastAPI Backend

From `backend/`:

```bash
uvicorn main:app --reload --port 8000
```

The backend exposes:

- `GET /health`
- `POST /predict`
- `POST /chat`
- `GET /dashboard/summary`
- `POST /model/pause`
- `POST /model/resume`

The first prediction will also initialize `db.sqlite` and store an audit record.

## 5. Run the Streamlit Frontend

In a separate terminal, from the `frontend/` folder:

```bash
streamlit run streamlit_app.py
```

By default Streamlit runs on `http://localhost:8501` and connects to the backend at `http://localhost:8000`.

### Pages

- **Home** (`streamlit_app.py`):
  - Simple loan application simulator
  - Shows decision, probability, SHAP-based explanation, and remediation suggestions

- **Consent** (`pages/Consent.py`):
  - Toggle which input fields the model is allowed to use
  - Shows baseline vs consent-modified decisions and probability delta

- **Dashboard** (`pages/Dashboard.py`):
  - Approval vs denial pie chart
  - Total counts
  - Buttons to pause/resume the model (calls backend endpoints)

- **Chatbot** (`pages/Chatbot.py`):
  - Simple advisor chatbot using local RAG over remediation guidance

## 6. Notes

- All components run locally; no paid cloud services are used.
- The audit log is hash-chained via SHA-256 in `audit.py`.
- For reproducibility you can clear `db.sqlite` and rerun predictions.
