"""
Global Streamlit CSS — Poppins font, cards, gradients, sidebar
"""
import streamlit as st


def inject_css():
    """Inject global CSS into Streamlit page"""
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

        /* ─── Global Font ─── */
        html, body, [class*="css"] {
            font-family: 'Poppins', sans-serif;
        }

        /* ─── Main Container ─── */
        .main .block-container {
            padding: 2rem 3rem;
            max-width: 1200px;
        }

        /* ─── Sidebar ─── */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            color: white;
        }
        [data-testid="stSidebar"] .stMarkdown h1,
        [data-testid="stSidebar"] .stMarkdown h2,
        [data-testid="stSidebar"] .stMarkdown h3,
        [data-testid="stSidebar"] .stMarkdown p,
        [data-testid="stSidebar"] .stMarkdown li,
        [data-testid="stSidebar"] .stMarkdown span {
            color: white !important;
        }
        [data-testid="stSidebar"] hr {
            border-color: rgba(255,255,255,0.2);
        }

        /* ─── Cards ─── */
        .card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 0.75rem 0;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            border: 1px solid #e8e8e8;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.12);
        }

        /* ─── Metric Cards ─── */
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            padding: 1.25rem;
            color: white;
            text-align: center;
            margin: 0.5rem 0;
        }
        .metric-card h3 {
            font-size: 2rem;
            font-weight: 700;
            margin: 0;
            color: white !important;
        }
        .metric-card p {
            font-size: 0.85rem;
            opacity: 0.9;
            margin: 0.25rem 0 0 0;
            color: white !important;
        }

        .metric-card-green {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }
        .metric-card-blue {
            background: linear-gradient(135deg, #2193b0 0%, #6dd5ed 100%);
        }
        .metric-card-orange {
            background: linear-gradient(135deg, #f2994a 0%, #f2c94c 100%);
        }
        .metric-card-red {
            background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        }
        .metric-card-purple {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }

        /* ─── Status Badges ─── */
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .status-approved, .status-active, .status-success, .status-compliant {
            background: #d4edda;
            color: #155724;
        }
        .status-pending, .status-scheduled, .status-in-progress {
            background: #fff3cd;
            color: #856404;
        }
        .status-rejected, .status-error, .status-critical, .status-overdue {
            background: #f8d7da;
            color: #721c24;
        }
        .status-open, .status-info {
            background: #cce5ff;
            color: #004085;
        }
        .status-resolved, .status-completed {
            background: #d1ecf1;
            color: #0c5460;
        }

        /* ─── Form Styling ─── */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div {
            border-radius: 8px;
            border: 1px solid #ddd;
        }
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 2px rgba(102,126,234,0.2);
        }

        /* ─── Buttons ─── */
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 8px;
            font-weight: 600;
            letter-spacing: 0.5px;
            transition: all 0.3s;
        }
        .stButton > button[kind="primary"]:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(102,126,234,0.4);
        }
        .stButton > button[kind="secondary"] {
            border-radius: 8px;
            font-weight: 500;
        }

        /* ─── Tabs ─── */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px 8px 0 0;
            padding: 0.5rem 1.5rem;
            font-weight: 500;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        /* ─── Chat Messages ─── */
        .chat-message {
            padding: 1rem;
            border-radius: 12px;
            margin: 0.5rem 0;
            max-width: 80%;
        }
        .chat-user {
            background: #e3f2fd;
            margin-left: auto;
            text-align: right;
        }
        .chat-assistant {
            background: #f5f5f5;
            margin-right: auto;
        }

        /* ─── Code Editor ─── */
        .ace_editor {
            border-radius: 8px;
            border: 1px solid #ddd;
        }

        /* ─── Tables ─── */
        .dataframe {
            border-radius: 8px;
            overflow: hidden;
        }
        .dataframe thead th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white !important;
            font-weight: 600;
        }

        /* ─── Expander ─── */
        .streamlit-expanderHeader {
            font-weight: 600;
            border-radius: 8px;
        }

        /* ─── Alert / Info boxes ─── */
        .stAlert {
            border-radius: 8px;
        }

        /* ─── Scrollbar ─── */
        ::-webkit-scrollbar {
            width: 6px;
        }
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        ::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #555;
        }

        /* ─── Section Headers ─── */
        .section-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
            font-size: 1.5rem;
            margin: 1.5rem 0 1rem 0;
        }

        /* ─── Responsive ─── */
        @media (max-width: 768px) {
            .main .block-container {
                padding: 1rem;
            }
            .metric-card h3 {
                font-size: 1.5rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)
