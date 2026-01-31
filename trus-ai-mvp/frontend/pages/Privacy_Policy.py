from theme import apply_bank_theme
import streamlit as st

def main():
    apply_bank_theme()
    
    st.markdown("""
    <div class="trus-header">
        <h1>Privacy Policy</h1>
        <p>Your data privacy is our priority.</p>
    </div>
    
    <div class="trus-card">
        <h3>1. Data Collection</h3>
        <p>We collect only the data necessary to provide our credit decisioning services, including income, employment details, and credit history.</p>
        
        <h3>2. Data Usage</h3>
        <p>Your data is used solely for the purpose of evaluating creditworthiness and improving our fairness models. We do not sell your data to third parties.</p>
        
        <h3>3. Data Security</h3>
        <p>We implement industry-standard security measures to protect your personal information.</p>
        
        <h3>4. Contact Us</h3>
        <p>If you have any questions about this policy, please contact us at privacy@trus.ai.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
