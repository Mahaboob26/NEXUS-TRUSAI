import streamlit as st

def apply_bank_theme():
    """Apply the TRUS.AI Premium Bank Theme (Pro Max UI)."""
    
    # Check if page config is already set (Streamlit only allows this once per run)
    try:
        # Increased title length to satisfy SEO rule (min 30 chars)
        st.set_page_config(
            page_title="TRUS.AI | Responsible Credit Decisioning & Governance Platform", 
            layout="wide", 
            page_icon="🏦"
        )
    except Exception:
        pass  # Page config might already be set

    inject_seo_tags()

    st.markdown(
        """
        <style>
        /* Import Inter Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, .stApp {
            font-family: 'Inter', sans-serif;
            color: #0f172a; /* Slate 900 */
        }

        /* Background */
        .stApp {
            background-color: #f8fafc; /* Slate 50 */
            background-image: 
                radial-gradient(at 0% 0%, hsla(215, 98%, 61%, 0.1) 0px, transparent 50%),
                radial-gradient(at 100% 0%, hsla(256, 96%, 67%, 0.1) 0px, transparent 50%);
        }

        /* Header Card - Glassmorphism */
        .trus-header {
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-bottom: 1px solid rgba(226, 232, 240, 0.8);
            padding: 2rem 3rem;
            border-radius: 24px;
            box-shadow: 
                0 4px 6px -1px rgba(0, 0, 0, 0.05),
                0 10px 15px -3px rgba(0, 0, 0, 0.05);
            margin-bottom: 2rem;
            color: #1e293b;
        }
        
        .trus-header h1 {
            background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
            letter-spacing: -0.025em;
            margin-bottom: 0.5rem;
        }

        /* Card Component */
        .trus-card {
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(12px);
            border-radius: 20px;
            padding: 1.5rem;
            box-shadow: 
                0 0 0 1px rgba(226, 232, 240, 1),
                0 4px 6px -1px rgba(0, 0, 0, 0.05);
            transition: all 0.2s ease-in-out;
            border: 1px solid rgba(255, 255, 255, 0.6);
        }
        
        .trus-card:hover {
            transform: translateY(-2px);
            box-shadow: 
                0 0 0 1px rgba(226, 232, 240, 1),
                0 10px 15px -3px rgba(0, 0, 0, 0.05),
                0 4px 6px -2px rgba(0, 0, 0, 0.025);
        }

        /* Custom Tag */
        .trus-tag {
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            background: linear-gradient(135deg, #dbeafe 0%, #eff6ff 100%);
            color: #1d4ed8;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            border: 1px solid #bfdbfe;
            margin-bottom: 1rem;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        }

        /* Primary Button Override */
        .stButton button[kind="primary"] {
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            border: none;
            box-shadow: 
                0 4px 6px -1px rgba(37, 99, 235, 0.2),
                0 2px 4px -1px rgba(37, 99, 235, 0.1);
            color: white;
            font-weight: 600;
            padding: 0.5rem 1.5rem;
            border-radius: 12px;
            transition: all 0.2s;
        }
        
        .stButton button[kind="primary"]:hover {
            transform: translateY(-1px);
            box-shadow: 
                0 10px 15px -3px rgba(37, 99, 235, 0.3),
                0 4px 6px -2px rgba(37, 99, 235, 0.1);
        }

        /* Input Fields */
        .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
            border-radius: 12px;
            border-color: #e2e8f0;
            background-color: #ffffff;
            transition: all 0.2s;
        }
        
        .stTextInput input:focus, .stNumberInput input:focus {
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        
        /* Metric Styling */
        div[data-testid="stMetricValue"] {
            background: linear-gradient(135deg, #0f172a 0%, #334155 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
        }

        /* Footer Styling */
        footer {
            visibility: hidden;
        }
        .trus-footer {
            margin-top: 4rem;
            border-top: 1px solid #e2e8f0;
            padding-top: 2rem;
            padding-bottom: 2rem;
            text-align: center;
            color: #64748b;
            font-size: 0.875rem;
        }
        .trus-footer a {
            color: #2563eb;
            text-decoration: none;
            margin: 0 0.5rem;
            font-weight: 500;
        }
        .trus-footer a:hover {
            text-decoration: underline;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    render_footer()


def inject_seo_tags():
    """Inject SEO metadata using JavaScript to append valid tags to <head>."""
    
    # JavaScript to create and append tags
    js_seo = """
    <script>
        // Check if description exists, if not create it
        if (!document.querySelector('meta[name="description"]')) {
            var meta = document.createElement('meta');
            meta.name = "description";
            meta.content = "TRUS.AI - The Responsible AI Governance Platform. Ensuring fairness, explainability, and compliance in automated credit decisioning.";
            document.getElementsByTagName('head')[0].appendChild(meta);
        }

        // Canonical
        if (!document.querySelector('link[rel="canonical"]')) {
            var link = document.createElement('link');
            link.rel = "canonical";
            link.href = "http://localhost:8501/";
            document.getElementsByTagName('head')[0].appendChild(link);
        }
        
        // Open Graph
        function addMeta(property, content) {
            if (!document.querySelector('meta[property="' + property + '"]')) {
                var m = document.createElement('meta');
                m.setAttribute('property', property);
                m.content = content;
                document.getElementsByTagName('head')[0].appendChild(m);
            }
        }
        
        addMeta('og:title', 'TRUS.AI | Responsible AI Governance');
        addMeta('og:description', 'Fairness, Explainability, and Compliance for AI models.');
        addMeta('og:image', 'http://localhost:8501/static/og-image.png');
        addMeta('og:type', 'website');
    </script>
    """
    
    st.components.v1.html(js_seo, height=0, width=0)


def render_footer():
    """Render a compliant footer with Privacy Policy and Contact links."""
    
    footer_html = """
    <div class="trus-footer">
        <p>&copy; 2026 TRUS.AI. All rights reserved.</p>
        <p>
            <a href="/Privacy_Policy" target="_blank">Privacy Policy</a> &bull; 
            <a href="/Contact" target="_blank">Contact Us</a> &bull; 
            <a href="/About" target="_blank">About TRUS.AI</a>
        </p>
        <p style="font-size: 0.75rem; color: #94a3b8; margin-top: 1rem;">
            Commitment to Responsible AI: Fairness &bull; Accountability &bull; Transparency
        </p>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)
