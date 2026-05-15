"""Professionele stijlinjectie voor de Pensioenplanner-applicatie."""

from __future__ import annotations

import streamlit as st

_CSS = """
<style>
/* =======================================================================
   Pensioenplanner — Zakelijk kleurenpalet
   Palet: #384959 (donker) | #6A89A7 (staal) | #88BDF2 (blauw) | #BDDDFC (licht)
   ======================================================================= */

/* --- Typografie & basis ---------------------------------------- */
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif !important;
}

:root {
    --navy:   #384959;
    --steel:  #6A89A7;
    --sky:    #88BDF2;
    --light:  #BDDDFC;
    --bg:     #F2F5F8;
    --white:  #FFFFFF;
    --border: #D8E4EE;
    --text:   #1A2733;
    --muted:  #6A89A7;
}

/* --- Achtergrond --------------------------------------------- */
.stApp { background-color: var(--bg) !important; }

.main .block-container {
    padding-top: 1.75rem;
    padding-right: 2.5rem;
    padding-bottom: 3rem;
    padding-left: 2.5rem;
    max-width: 1400px;
}

/* === SIDEBAR ================================================== */
section[data-testid="stSidebar"] > div:first-child {
    background-color: var(--navy) !important;
    padding-top: 1.5rem;
}

section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label {
    color: #8DADC5 !important;
}
section[data-testid="stSidebar"] strong,
section[data-testid="stSidebar"] b {
    color: #D0E3F3 !important;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(136, 189, 242, 0.12) !important;
    margin: 0.9rem 0 !important;
}
section[data-testid="stSidebar"] .stCaption p {
    color: rgba(141, 173, 197, 0.45) !important;
    font-size: 0.69rem !important;
}

/* Sidebar stap-links (voltooide stappen): zelfde layout als niet-klikbare regels */
section[data-testid="stSidebar"] a.pp-stap-link {
    display: block !important;
    text-decoration: none !important;
}
section[data-testid="stSidebar"] .pp-stap-item {
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    padding: 6px 12px !important;
    margin: 1px 0 !important;
    border-left: 2px solid transparent !important;
}
section[data-testid="stSidebar"] .pp-stap-item.pp-stap-huidig {
    border-left-color: #88BDF2 !important;
    background-color: rgba(136, 189, 242, 0.1) !important;
}
section[data-testid="stSidebar"] .pp-stap-item.pp-stap-toekomstig {
    border-left-color: transparent !important;
    background-color: transparent !important;
}
section[data-testid="stSidebar"] .pp-stap-item.pp-stap-voltooid {
    border-left-color: transparent !important;
    background-color: transparent !important;
}
section[data-testid="stSidebar"] .pp-stap-item.pp-stap-opnieuw {
    border-left-color: transparent !important;
    background-color: transparent !important;
}
section[data-testid="stSidebar"] .pp-stap-item .pp-stap-nummer {
    min-width: 1.4rem !important;
    font-variant-numeric: tabular-nums !important;
    font-size: 0.67rem !important;
    font-weight: 600 !important;
    color: rgba(136, 189, 242, 0.3) !important;
}
section[data-testid="stSidebar"] .pp-stap-item .pp-stap-label {
    font-size: 0.81rem !important;
    font-weight: 400 !important;
    line-height: 1.3 !important;
    letter-spacing: 0 !important;
    color: rgba(141, 173, 197, 0.55) !important;
}
section[data-testid="stSidebar"] .pp-stap-item.pp-stap-huidig .pp-stap-nummer {
    color: #88BDF2 !important;
    font-weight: 700 !important;
}
section[data-testid="stSidebar"] .pp-stap-item.pp-stap-huidig .pp-stap-label {
    color: #E8F2FB !important;
    font-weight: 600 !important;
}
section[data-testid="stSidebar"] .pp-stap-item.pp-stap-toekomstig .pp-stap-nummer {
    color: rgba(136, 189, 242, 0.2) !important;
}
section[data-testid="stSidebar"] .pp-stap-item.pp-stap-toekomstig .pp-stap-label {
    color: rgba(141, 173, 197, 0.28) !important;
}
section[data-testid="stSidebar"] .pp-stap-item.pp-stap-opnieuw .pp-stap-nummer {
    color: rgba(136, 189, 242, 0.25) !important;
}
section[data-testid="stSidebar"] .pp-stap-item.pp-stap-opnieuw .pp-stap-label {
    color: rgba(141, 173, 197, 0.38) !important;
}
section[data-testid="stSidebar"] a.pp-stap-link:hover .pp-stap-item {
    background-color: rgba(136, 189, 242, 0.08) !important;
    border-left-color: rgba(136, 189, 242, 0.5) !important;
}
section[data-testid="stSidebar"] a.pp-stap-link:hover .pp-stap-item .pp-stap-label {
    color: rgba(232, 242, 251, 0.86) !important;
}

/* Sidebar selectbox */
section[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
    background-color: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(136,189,242,0.15) !important;
    color: #BDDCF3 !important;
    border-radius: 5px !important;
}
section[data-testid="stSidebar"] [data-testid="stSelectbox"] svg {
    fill: rgba(136, 189, 242, 0.4) !important;
}
section[data-testid="stSidebar"] [data-testid="stSelectbox"] label {
    font-size: 0.69rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
    color: rgba(141, 173, 197, 0.55) !important;
    margin-bottom: 0.3rem !important;
}

/* Sidebar knoppen (stap-navigatie — voltooid/redo):
   strip alle Streamlit-knopchrome en maak identiek aan de HTML-nav-items */
section[data-testid="stSidebar"] .stButton {
    margin: 0 !important;
    padding: 0 !important;
}
section[data-testid="stSidebar"] .stButton > button {
    background-color: transparent !important;
    border: none !important;
    border-left: 2px solid transparent !important;
    border-radius: 0 !important;
    color: rgba(141, 173, 197, 0.55) !important;
    text-align: left !important;
    width: 100% !important;
    padding: 6px 12px !important;
    font-size: 0.81rem !important;
    font-weight: 400 !important;
    letter-spacing: 0 !important;
    box-shadow: none !important;
    transform: none !important;
    transition: border-left-color 0.12s ease, background-color 0.12s ease,
                color 0.12s ease !important;
    margin: 1px 0 !important;
    line-height: 1.3 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    gap: 8px !important;
}
section[data-testid="stSidebar"] .stButton > button > div {
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
}
section[data-testid="stSidebar"] .stButton > button [data-testid="stMarkdownContainer"] {
    width: 100% !important;
}
section[data-testid="stSidebar"] .stButton > button [data-testid="stMarkdownContainer"] p {
    width: 100% !important;
    margin: 0 !important;
    text-align: left !important;
    display: block !important;
}
section[data-testid="stSidebar"] .stButton > button p,
section[data-testid="stSidebar"] .stButton > button span,
section[data-testid="stSidebar"] .stButton > button div {
    margin: 0 !important;
    padding: 0 !important;
    text-align: left !important;
    justify-content: flex-start !important;
    font-size: 0.81rem !important;
    font-weight: 400 !important;
    line-height: 1.3 !important;
    letter-spacing: 0 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif !important;
    color: inherit !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background-color: rgba(136, 189, 242, 0.08) !important;
    border-left-color: rgba(136, 189, 242, 0.5) !important;
    color: rgba(232, 242, 251, 0.85) !important;
    transform: none !important;
    box-shadow: none !important;
}
section[data-testid="stSidebar"] .stButton > button:active,
section[data-testid="stSidebar"] .stButton > button:focus {
    background-color: rgba(136, 189, 242, 0.12) !important;
    transform: none !important;
    box-shadow: none !important;
    outline: none !important;
}

/* === HEADERS ================================================== */
.main h1 {
    color: var(--navy) !important;
    font-size: 1.4rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.015em !important;
    padding-bottom: 0.55rem !important;
    border-bottom: 2px solid var(--sky) !important;
    margin-bottom: 1.25rem !important;
    margin-top: 0 !important;
}
.main h2 {
    color: var(--navy) !important;
    font-size: 0.98rem !important;
    font-weight: 600 !important;
    margin-top: 1.5rem !important;
    margin-bottom: 0.5rem !important;
}
.main h3 {
    color: var(--steel) !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
    margin-top: 1.25rem !important;
    margin-bottom: 0.35rem !important;
}

/* === KNOPPEN (hoofdinhoud) ==================================== */
.main .stButton > button {
    background-color: var(--navy) !important;
    color: var(--white) !important;
    border: none !important;
    border-radius: 5px !important;
    padding: 0.42rem 1.1rem !important;
    font-size: 0.83rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.01em !important;
    box-shadow: 0 1px 3px rgba(56,73,89,0.15) !important;
    transition: background-color 0.12s ease, box-shadow 0.12s ease !important;
    transform: none !important;
}
.main .stButton > button:hover {
    background-color: var(--steel) !important;
    box-shadow: 0 2px 6px rgba(56,73,89,0.2) !important;
    transform: none !important;
}
.main .stButton > button:active {
    background-color: var(--navy) !important;
    box-shadow: 0 1px 2px rgba(56,73,89,0.1) !important;
    transform: none !important;
}
/* Primary button */
.main button[kind="primary"] {
    background-color: var(--steel) !important;
}
.main button[kind="primary"]:hover {
    background-color: var(--navy) !important;
}

/* === INVOERVELDEN ============================================= */
.stTextInput input,
.stTextArea textarea,
.stNumberInput input {
    background-color: var(--white) !important;
    border: 1px solid var(--border) !important;
    border-radius: 5px !important;
    color: var(--text) !important;
    font-size: 0.875rem !important;
    transition: border-color 0.12s, box-shadow 0.12s !important;
}
.stTextInput input:focus,
.stTextArea textarea:focus,
.stNumberInput input:focus {
    border-color: var(--sky) !important;
    box-shadow: 0 0 0 3px rgba(136,189,242,0.16) !important;
    outline: none !important;
}
.stSelectbox > div > div {
    background-color: var(--white) !important;
    border: 1px solid var(--border) !important;
    border-radius: 5px !important;
}
.stSelectbox > div > div:focus-within {
    border-color: var(--sky) !important;
    box-shadow: 0 0 0 3px rgba(136,189,242,0.16) !important;
}
.stDateInput input {
    background-color: var(--white) !important;
    border: 1px solid var(--border) !important;
    border-radius: 5px !important;
}

/* Veld-labels */
.stTextInput label,
.stTextArea label,
.stNumberInput label,
.stSelectbox label,
.stCheckbox label,
.stDateInput label,
.stSlider label,
.stFileUploader label {
    font-size: 0.76rem !important;
    font-weight: 500 !important;
    color: var(--steel) !important;
    letter-spacing: 0.02em !important;
}

/* File uploader */
[data-testid="stFileUploader"] > div {
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    background-color: var(--white) !important;
}

/* === METRICS ================================================== */
[data-testid="metric-container"] {
    background-color: var(--white) !important;
    border: 1px solid var(--border) !important;
    border-radius: 7px !important;
    padding: 0.85rem 1.1rem !important;
    box-shadow: 0 1px 3px rgba(56,73,89,0.05) !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.69rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
    color: var(--muted) !important;
}
[data-testid="stMetricValue"] {
    color: var(--navy) !important;
    font-size: 1.3rem !important;
    font-weight: 700 !important;
}

/* === MELDINGEN ================================================ */
.stAlert {
    border-radius: 6px !important;
    font-size: 0.84rem !important;
}

/* === DATAFRAME ================================================ */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 7px !important;
    overflow: hidden !important;
    box-shadow: 0 1px 4px rgba(56,73,89,0.05) !important;
}

/* === DIVIDER ================================================== */
hr {
    border-color: var(--border) !important;
    margin: 1.1rem 0 !important;
}

/* === CAPTION ================================================= */
.stCaption p {
    color: var(--muted) !important;
    font-size: 0.76rem !important;
}

/* === EXPANDER ================================================= */
details summary {
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    color: var(--navy) !important;
}

/* === TABS ==================================================== */
[data-testid="stTabs"] button[role="tab"] {
    color: var(--muted) !important;
    font-size: 0.84rem !important;
    font-weight: 500 !important;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: var(--navy) !important;
    border-bottom: 2px solid var(--steel) !important;
}

/* === PROGRESS BAR ============================================= */
[data-testid="stProgress"] > div > div > div > div {
    background-color: var(--sky) !important;
}

/* === VERBERG STREAMLIT CHROME ================================= */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header[data-testid="stHeader"] { visibility: hidden; height: 0; }
</style>
"""


def injecteer_stijl() -> None:
    """Injecteer het professionele kleurenpalet in de Streamlit-app."""
    st.markdown(_CSS, unsafe_allow_html=True)
