import requests
import streamlit as st
import pandas as pd
import altair as alt
from theme import apply_bank_theme
from auth import is_logged_in, logout

BACKEND_URL = "http://localhost:8000"

def get_summary():
    try:
        resp = requests.get(f"{BACKEND_URL}/dashboard/summary", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Failed to fetch dashboard data: {e}")
        return {}

def main():
    if not is_logged_in():
        st.warning("Please login first.")
        st.page_link("pages/Login.py", label="Go to Login")
        st.stop()
        
    apply_bank_theme()
    
    # Header
    st.markdown("""
    <div class="trus-header">
        <div class="trus-tag">Analytics Hub</div>
        <h1>Executive Dashboard</h1>
        <p>Real-time monitoring of credit model performance, fairness, and operational volume.</p>
    </div>
    """, unsafe_allow_html=True)
    
    data = get_summary()
    if not data:
        st.info("No data available yet. Run some predictions in the Sandbox!")
        return

    # 1. KPI Cards
    total = data.get("total", 0)
    approvals = data.get("approvals", 0)
    denials = data.get("denials", 0)
    
    approval_rate = (approvals / total * 100) if total > 0 else 0
    denial_rate = (denials / total * 100) if total > 0 else 0
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="trus-card">', unsafe_allow_html=True)
        st.metric("Total Applications", f"{total}", delta=f"{total} all-time")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with c2:
        st.markdown('<div class="trus-card">', unsafe_allow_html=True)
        st.metric("Approval Rate", f"{approval_rate:.1f}%", delta="Target > 60%")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with c3:
        st.markdown('<div class="trus-card">', unsafe_allow_html=True)
        st.metric("Rejection Rate", f"{denial_rate:.1f}%", delta_color="inverse", delta="Target < 40%")
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.markdown("---")
    
    # 2. Charts & Trends
    col_chart, col_recent = st.columns([2, 1])
    
    with col_chart:
        st.markdown("### 📊 Portfolio Composition")
        
        pc1, pc2 = st.columns(2)
        
        with pc1:
            st.caption("Approval Mix")
            outcome_df = pd.DataFrame([
                {"Category": "Approved", "Count": approvals},
                {"Category": "Denied", "Count": denials}
            ])
            
            base = alt.Chart(outcome_df).encode(theta=alt.Theta("Count", stack=True))
            pie = base.mark_arc(innerRadius=45).encode(
                color=alt.Color("Category", scale=alt.Scale(domain=['Approved', 'Denied'], range=['#10b981', '#ef4444'])),
                order=alt.Order("Count", sort="descending"),
                tooltip=["Category", "Count"]
            )
            text = base.mark_text(radius=1.3).encode(
                text=alt.Text("Count"),
                order=alt.Order("Count", sort="descending")
            )
            st.altair_chart(pie + text, use_container_width=True)

        with pc2:
            st.caption("Risk Profile")
            risk_raw = data.get("risk_distribution", [])
            if risk_raw:
                risk_df = pd.DataFrame(risk_raw)
                base_risk = alt.Chart(risk_df).encode(theta=alt.Theta("count", stack=True))
                pie_risk = base_risk.mark_arc(innerRadius=45).encode(
                    color=alt.Color("category", legend=None),
                    order=alt.Order("count", sort="descending"),
                    tooltip=["category", "count"]
                )
                st.altair_chart(pie_risk, use_container_width=True)
            else:
                st.info("No risk data.")


    # 3. Recent Activity Table
    with col_recent:
        st.markdown("### 🕒 Recent Decisions")
        recent = data.get("recent", [])
        if recent:
            # Create a clean dataframe for display
            df_recent = pd.DataFrame(recent)
            df_display = df_recent[["decision", "probability", "timestamp"]].copy()
            
            # Format
            df_display["decision"] = df_display["decision"].apply(
                lambda x: "✅ Approved" if x == "approved" else "❌ Denied"
            )
            df_display["probability"] = df_display["probability"].apply(lambda x: f"{x:.2f}")
            df_display["timestamp"] = pd.to_datetime(df_display["timestamp"]).dt.strftime('%H:%M')
            
            st.dataframe(
                df_display, 
                hide_index=True,
                column_config={
                    "decision": "Outcome",
                    "probability": "Score",
                    "timestamp": "Time"
                },
                use_container_width=True
            )
        else:
            st.caption("No recent activity.")

    st.markdown("---")

    # 4. AI Fairness Monitor
    st.markdown("### ⚖️ AI Fairness Monitor")
    
    try:
        fair_resp = requests.get(f"{BACKEND_URL}/dashboard/fairness", timeout=5)
        if fair_resp.status_code == 200:
            fair_data = fair_resp.json()
            if fair_data.get("available"):
                f1, f2, f3 = st.columns(3)
                
                # Extract metrics (assuming simplified Demo structure)
                # In a real app we'd parse the full 'by_group' dictionary
                groups = fair_data.get("by_group", {})
                
                with f1:
                    st.markdown("**Selection Rates**")
                    if groups:
                        st.bar_chart(groups)
                    else:
                        st.caption("Insufficient data")
                        
                with f2:
                    # Calculate simple disparities
                    rates = list(groups.values())
                    if rates and max(rates) > 0:
                        disparate_impact = min(rates) / max(rates)
                        st.metric("Disparate Impact Ratio", f"{disparate_impact:.2f}", delta="Target > 0.8")
                        
                        if disparate_impact < 0.8:
                            st.warning("⚠️ Potential bias detected")
                        else:
                            st.success("✅ Limits verified")
                            
                with f3:
                    st.markdown("**Compliance Status**")
                    st.info("Algorithmic auditing active. Model `indian_v1` running.")
                    
            else:
                st.info("Fairness metrics require more data points to converge.")
    except Exception:
        st.warning("Could not contact fairness engine.")

if __name__ == "__main__":
    main()
