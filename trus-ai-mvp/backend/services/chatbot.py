from pathlib import Path
from typing import List, Dict, Optional

import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent.parent

# Project layout:
#   TRUS_AI/
#     indian_model_training/
#       data/indian_loan_dataset.csv
#     trus-ai-mvp/
#       backend/services/chatbot.py (this file)
DATA_PATH = (
    BASE_DIR.parent.parent / "indian_model_training" / "data" / "indian_loan_dataset.csv"
)

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_embedder: SentenceTransformer | None = None
_index: faiss.IndexFlatIP | None = None
_documents: List[str] = []
_dataset: Optional[pd.DataFrame] = None


def _load_corpus() -> List[str]:
    return [
        "To improve loan approval chances, maintain a strong history of on-time repayments.",
        "Reducing existing debts and credit utilization lowers perceived risk.",
        "Providing collateral or a co-signer can help borderline applications.",
        "Stable employment and consistent income increase creditworthiness.",
        "Avoid applying for multiple loans or credit lines in a short period.",
        "If your application is denied, ask for specific reasons and address them before reapplying.",
        "Building savings and an emergency fund shows financial resilience.",
    ]


def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(_MODEL_NAME)
    return _embedder


def _build_index():
    global _index, _documents
    if _index is not None:
        return

    _documents = _load_corpus()
    embedder = _get_embedder()
    embeddings = embedder.encode(_documents, convert_to_numpy=True, normalize_embeddings=True)
    dim = embeddings.shape[1]
    _index = faiss.IndexFlatIP(dim)
    _index.add(embeddings.astype("float32"))


def _load_dataset() -> Optional[pd.DataFrame]:
    """Load Indian loan dataset once for data-driven Q&A.

    Returns None if the file is missing or unreadable so that the
    chatbot can gracefully fall back to generic guidance.
    """

    global _dataset
    if _dataset is not None:
        return _dataset

    try:
        df = pd.read_csv(DATA_PATH)
    except Exception:
        _dataset = None
        return None

    # Basic cleaning: keep only rows with numeric loan/balance
    for col in ["LoanAmount", "bank_balance"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "Approved" in df.columns:
        # Focus on approved loans when deriving typical ranges
        df = df[df["Approved"] == 1].copy()

    _dataset = df.dropna(subset=["LoanAmount", "bank_balance"], how="any")
    return _dataset


_BANK_KEYWORDS = [
    "loan",
    "credit",
    "emi",
    "interest",
    "bank",
    "savings",
    "fixed deposit",
    "fd",
    "rd",
    "account",
    "cibil",
    "statement",
    "repayment",
    "overdue",
    "default",
    "moratorium",
]


def _is_banking_query(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in _BANK_KEYWORDS)


def _retrieve(query: str, top_k: int = 3) -> List[str]:
    _build_index()
    embedder = _get_embedder()
    query_emb = embedder.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    scores, indices = _index.search(query_emb.astype("float32"), top_k)
    results: List[str] = []
    for idx in indices[0]:
        if 0 <= idx < len(_documents):
            results.append(_documents[idx])
    return results


def _extract_loan_amount(question: str) -> Optional[float]:
    """Extract a loan amount in rupees from the question, if present.

    Very simple heuristic: pick the first integer with at least 5 digits
    (e.g. 800000) and treat it as the requested amount.
    """

    import re

    numbers = re.findall(r"\d+", question.replace(",", ""))
    for n in numbers:
        try:
            value = float(n)
        except ValueError:
            continue
        if value >= 50000:  # ignore tiny numbers that are not ticket sizes
            return value
    return None


def _answer_from_dataset(question: str) -> Optional[str]:
    """Try to answer application-specific questions using the dataset.

    Handles questions about:
      - required / typical *bank balance*
      - *income* or salary levels
      - *EMI to income* ratios
      - *credit history* / *CIBIL* bands
      - *behavioural* scores (mobile_usage_score, transaction_stability_score)
      - *credit utilisation* (credit_utilization)

    Returns None if it cannot confidently answer from data.
    """

    q = question.lower()

    df = _load_dataset()
    if df is None or df.empty:
        return None

    loan_amount = _extract_loan_amount(question)

    # Filter loans around the requested amount if available, so that
    # numbers feel specific to the user scenario.
    df_filtered = df
    if loan_amount is not None and "LoanAmount" in df.columns:
        lower = loan_amount * 0.7
        upper = loan_amount * 1.3
        subset = df[(df["LoanAmount"] >= lower) & (df["LoanAmount"] <= upper)]
        if not subset.empty:
            df_filtered = subset

    if df_filtered.empty:
        return None

    def fmt_rupees(v: float) -> str:
        return f"₹{v:,.0f}"

    # 1) Average bank balance questions
    if "bank balance" in q or "average balance" in q:
        if "bank_balance" not in df_filtered.columns:
            return None
        balances = df_filtered["bank_balance"].astype(float).dropna()
        if balances.empty:
            return None
        q50 = balances.quantile(0.5)
        q25 = balances.quantile(0.25)
        q75 = balances.quantile(0.75)

        if loan_amount is None:
            intro = "For this kind of loan profile, you should aim to maintain an average bank balance"
        else:
            intro = (
                "For a loan amount roughly around "
                f"{fmt_rupees(loan_amount)}, you should aim to maintain an average bank balance"
            )

        return (
            f"{intro} of about {fmt_rupees(q50)}. In many approved cases, balances between "
            f"approximately {fmt_rupees(q25)} and {fmt_rupees(q75)} have been sufficient. "
            "Keeping a higher and more stable balance will generally strengthen your profile, "
            "but final approval still depends on income, EMI, credit history and other factors."
        )

    # 2) Income / salary questions
    if "income" in q or "salary" in q:
        # Use total_income if available, else ApplicantIncome + CoapplicantIncome
        if "total_income" in df_filtered.columns:
            incomes = df_filtered["total_income"].astype(float).dropna()
        elif {"ApplicantIncome", "CoapplicantIncome"}.issubset(df_filtered.columns):
            incomes = (
                df_filtered["ApplicantIncome"].astype(float)
                + df_filtered["CoapplicantIncome"].astype(float)
            ).dropna()
        else:
            incomes = pd.Series(dtype="float64")

        if incomes.empty:
            return None

        q50 = incomes.quantile(0.5)
        q25 = incomes.quantile(0.25)
        q75 = incomes.quantile(0.75)

        if loan_amount is None:
            intro = "For this type of loan, you should target a combined monthly income"
        else:
            intro = (
                "For a loan amount roughly around "
                f"{fmt_rupees(loan_amount)}, you should target a combined monthly income"
            )

        return (
            f"{intro} of around {fmt_rupees(q50)}. In practice, many accepted customers "
            f"have incomes in the range of roughly {fmt_rupees(q25)} to {fmt_rupees(q75)}. "
            "Higher and more stable income improves approval odds, especially when EMI "
            "stays well below 40% of income."
        )

    # 3) EMI to income ratio questions
    if "emi" in q and ("ratio" in q or "income" in q):
        if "income_to_emi_ratio" not in df_filtered.columns:
            return None
        ratios = df_filtered["income_to_emi_ratio"].astype(float).replace([np.inf, -np.inf], np.nan).dropna()
        if ratios.empty:
            return None

        q50 = ratios.quantile(0.5)
        q25 = ratios.quantile(0.25)
        q75 = ratios.quantile(0.75)

        return (
            "For healthy profiles, you should aim for an income-to-EMI ratio of around "
            f"{q50:0.1f}, with many good cases falling between about {q25:0.1f} and "
            f"{q75:0.1f}. This roughly corresponds to EMIs staying comfortably below "
            "35–40% of take-home income in most situations."
        )

    # 4) Credit history / CIBIL questions
    if "credit history" in q or "cibil" in q or "score" in q:
        parts: List[str] = []

        if "Credit_History" in df_filtered.columns:
            good_share = (
                (df_filtered["Credit_History"] == 1).sum() / max(len(df_filtered), 1)
            )
            parts.append(
                f"A strong credit history is important. In many accepted cases, roughly {good_share*100:0.0f}% "
                "had a clean track record with no major defaults."
            )

        if "cibil_proxy_score" in df_filtered.columns:
            scores = df_filtered["cibil_proxy_score"].astype(float).dropna()
            if not scores.empty:
                q50 = scores.quantile(0.5)
                q25 = scores.quantile(0.25)
                q75 = scores.quantile(0.75)
                parts.append(
                    "As a broad guide, a proxy credit score around "
                    f"{q50:0.0f}, with many good cases between {q25:0.0f} and {q75:0.0f}, "
                    "is considered healthier for approval."
                )

        if not parts:
            return None

        parts.append(
            "Maintaining on-time payments, low overdue amounts and avoiding cheque bounces "
            "are key to keeping scores in a healthy band."
        )
        return " ".join(parts)

    # 5) Behavioural / digital footprint questions
    if "mobile" in q or "digital" in q or "behaviour" in q or "behavior" in q:
        cols = []
        if "mobile_usage_score" in df_filtered.columns:
            cols.append("mobile_usage_score")
        if "transaction_stability_score" in df_filtered.columns:
            cols.append("transaction_stability_score")

        if not cols:
            return None

        lines: List[str] = []
        for c in cols:
            vals = df_filtered[c].astype(float).dropna()
            if vals.empty:
                continue
            q50 = vals.quantile(0.5)
            q25 = vals.quantile(0.25)
            q75 = vals.quantile(0.75)
            lines.append(
                f"You should aim for {c} around {q50:0.0f}, with a comfortable zone roughly "
                f"between {q25:0.0f} and {q75:0.0f}."
            )

        if not lines:
            return None

        lines.append(
            "Consistent usage of the same primary SIM and regular salary/business credits "
            "into one main account tend to support stronger behavioural scores."
        )
        return " ".join(lines)

    # 6) Credit utilisation questions
    if "utilisation" in q or "utilization" in q or "usage" in q:
        if "credit_utilization" not in df_filtered.columns:
            return None
        vals = df_filtered["credit_utilization"].astype(float).replace([np.inf, -np.inf], np.nan).dropna()
        if vals.empty:
            return None

        q50 = vals.quantile(0.5)
        q25 = vals.quantile(0.25)
        q75 = vals.quantile(0.75)

        return (
            "As a guideline, you should try to keep overall credit utilisation around "
            f"{q50:0.1f}x of your reference balances, with a safer zone roughly between "
            f"{q25:0.1f}x and {q75:0.1f}x. Lower utilisation (for example keeping card and "
            "loan limits only partly used) usually signals lower risk."
        )

    # If none of the specialised handlers matched, fall back to generic logic.
    return None


def answer_question(question: str, context: Dict | None = None) -> str:
    """Answer only banking-related questions; refuse everything else.

    For banking/loan/credit topics we use retrieved guidance and, if
    available, the last model decision context. For off-topic questions we
    return a polite refusal.
    """

    if not _is_banking_query(question):
        return (
            "I am designed only to help with banking and loan-related queries, "
            "such as EMIs, credit history, loan approval factors and risk. "
            "I cannot answer questions outside of banking."
        )

    # First, try to answer directly from the loan dataset for
    # application-specific queries (e.g. required bank balance).
    dataset_answer = _answer_from_dataset(question)
    if dataset_answer is not None:
        return dataset_answer

    snippets = _retrieve(question, top_k=3)
    base = (
        "Here are some practical steps you can take regarding your loan application, "
        "based on general credit risk practices:"
    )
    bullet_points = "\n".join([f"- {s}" for s in snippets])

    context_note = ""
    if context:
        decision = context.get("decision")
        explanation = (context.get("explanation") or {}).copy()
        top_neg = explanation.get("top_negative") or []
        if decision and top_neg:
            main_factor = top_neg[0]
            fname = main_factor.get("feature")
            context_note = (
                "\n\nFrom your last automated decision, the most important factor that reduced your "
                f"approval score was '{fname}'. Focus on improving that specific aspect "
                "(for example by lowering related dues, improving repayment discipline, or strengthening income stability)."
            )

    follow_up = (
        "\n\nThese are general recommendations and not legal or financial advice. "
        "Please review them with your bank or a qualified advisor before taking decisions."
    )

    return f"{base}\n{bullet_points}{context_note}{follow_up}"

