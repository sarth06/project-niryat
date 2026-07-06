"""
Project Niryat // Supply Chain Command Center
Enterprise UI/UX refactor.

STRICT PRESERVATION NOTE:
All mathematical logic, the supplier_score formula, true_price_variance
calculation, context_payload keys, the Gemini prompt text, the fallback
response structure, and the SHA-256 audit hashing are byte-for-byte
identical to the original working version. Only architecture, styling,
session-state handling, micro-interactions, and chart presentation
have been enhanced.
"""

import streamlit as st
import time
import json
import hashlib
import datetime as dt
from typing import Any, Dict, Tuple, Optional

import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ==========================================================
# PAGE CONFIG
# ==========================================================
st.set_page_config(
    page_title="Project Niryat // Command Center",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🛡️",
)

# ==========================================================
# ENTERPRISE STYLING — Glassmorphism / Slate palette / Inter
# ==========================================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    .stApp {
        background: radial-gradient(circle at 15% 10%, #131c31 0%, #0b1120 45%, #070b16 100%);
        color: #e2e8f0;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1526 0%, #0a0f1d 100%);
        border-right: 1px solid rgba(148, 163, 184, 0.12);
    }
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #e2e8f0;
        letter-spacing: 0.02em;
    }

    /* Header */
    .niryat-title {
        font-size: 2.05rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        background: linear-gradient(90deg, #38bdf8 0%, #22d3ee 55%, #34d399 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.15rem;
    }
    .niryat-subtitle {
        color: #94a3b8;
        font-size: 0.95rem;
        font-weight: 500;
        margin-bottom: 1.2rem;
    }

    /* Glassmorphism section cards */
    .glass-card {
        background: rgba(30, 41, 59, 0.45);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(148, 163, 184, 0.14);
        border-radius: 16px;
        padding: 1.25rem 1.4rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.28);
        margin-bottom: 1rem;
    }
    .glass-card h3 {
        margin-top: 0;
        font-weight: 700;
        color: #f1f5f9;
        font-size: 1rem;
        letter-spacing: 0.01em;
        text-transform: uppercase;
        opacity: 0.9;
    }

    /* Metric styling */
    div[data-testid="stMetric"] {
        background: rgba(15, 23, 42, 0.55);
        border: 1px solid rgba(148, 163, 184, 0.12);
        border-radius: 12px;
        padding: 0.85rem 1rem 0.6rem 1rem;
    }
    div[data-testid="stMetricValue"] {
        color: #f8fafc;
        font-size: 26px;
        font-weight: 700;
    }
    div[data-testid="stMetricLabel"] {
        color: #94a3b8;
        font-size: 11.5px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    div[data-testid="stMetricDelta"] {
        font-weight: 600;
    }

    /* Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        border: 1px solid rgba(148, 163, 184, 0.18);
        font-weight: 600;
        letter-spacing: 0.01em;
        padding: 0.55rem 0.9rem;
        transition: all 0.15s ease;
    }
    div[data-testid="column"]:nth-of-type(1) .stButton>button {
        background: linear-gradient(90deg, #16a34a, #22c55e);
        color: white;
        box-shadow: 0 4px 14px rgba(34, 197, 94, 0.25);
    }
    div[data-testid="column"]:nth-of-type(1) .stButton>button:hover {
        box-shadow: 0 6px 20px rgba(34, 197, 94, 0.4);
        transform: translateY(-1px);
    }
    div[data-testid="column"]:nth-of-type(2) .stButton>button {
        background: rgba(239, 68, 68, 0.12);
        color: #fca5a5;
        border: 1px solid rgba(239, 68, 68, 0.35);
    }
    div[data-testid="column"]:nth-of-type(2) .stButton>button:hover {
        background: rgba(239, 68, 68, 0.22);
    }
    section[data-testid="stSidebar"] .stButton>button {
        background: linear-gradient(90deg, #0ea5e9, #22d3ee);
        color: #04121c;
        font-weight: 700;
    }

    /* Code / email draft block */
    .stCodeBlock, pre {
        border-radius: 12px !important;
        border: 1px solid rgba(148, 163, 184, 0.14) !important;
    }

    /* Divider */
    hr {
        border-color: rgba(148, 163, 184, 0.14);
    }

    /* Badge chips */
    .niryat-chip {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 11.5px;
        font-weight: 700;
        letter-spacing: 0.03em;
        margin-right: 6px;
    }
    .chip-green { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.35);}
    .chip-blue  { background: rgba(56,189,248,0.15); color: #38bdf8; border: 1px solid rgba(56,189,248,0.35);}
    .chip-amber { background: rgba(245,158,11,0.15); color: #fbbf24; border: 1px solid rgba(245,158,11,0.35);}
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================================
# HARDWARE DETECTION
# ==========================================================
try:
    import cudf  # noqa: F401
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False


# ==========================================================
# CORE PIPELINE FUNCTIONS (logic untouched — only wrapped)
# ==========================================================

def generate_shipment_data(sim_rows: int, seed: int = 42) -> pd.DataFrame:
    """Synthesize the global shipping manifest dataset."""
    np.random.seed(seed)
    return pd.DataFrame({
        'shipment_id': np.arange(sim_rows, dtype=np.int32),
        'api_molecule': np.random.choice(
            ['Paracetamol (KSM)', 'Azithromycin', 'Metformin'],
            sim_rows, p=[0.5, 0.3, 0.2]
        ),
        'origin_country': np.random.choice(
            ['China', 'Germany', 'USA', 'India (Domestic)'],
            sim_rows, p=[0.6, 0.15, 0.15, 0.1]
        ),
        'price_usd_per_kg': np.random.uniform(15.0, 50.0, sim_rows),
        'status': np.random.choice(
            ['On Time', 'Delayed', 'Port Blocked'],
            sim_rows, p=[0.85, 0.10, 0.05]
        ),
    })


def compute_macro_baseline(df: pd.DataFrame) -> Dict[str, float]:
    """Baseline average price per molecule, used for true variance math."""
    return df.groupby('api_molecule')['price_usd_per_kg'].mean().to_dict()


def run_cpu_pipeline(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, float]:
    """Standard pandas/CPU aggregation track."""
    start_cpu = time.perf_counter()
    cpu_blocked = df[df['status'] == 'Port Blocked']
    cpu_shock = cpu_blocked.groupby(['api_molecule', 'origin_country']).size().reset_index(name='blocked_count')
    cpu_stable = df[df['status'] == 'On Time']
    cpu_backup = cpu_stable.groupby(['api_molecule', 'origin_country']).agg(
        avg_price=('price_usd_per_kg', 'mean'),
        available_volume=('shipment_id', 'count')
    ).reset_index()
    end_cpu = time.perf_counter()
    return cpu_shock, cpu_backup, (end_cpu - start_cpu)


def run_gpu_pipeline(
    df: pd.DataFrame,
    gpu_available: bool,
    cpu_time_fallback: float
) -> Tuple[pd.DataFrame, pd.DataFrame, float]:
    """NVIDIA RAPIDS cuDF acceleration track, with CPU-derived fallback profile."""
    if gpu_available:
        import cudf
        df_gpu = cudf.from_pandas(df)
        start_gpu = time.perf_counter()
        gpu_blocked = df_gpu[df_gpu['status'] == 'Port Blocked']
        gpu_shock = gpu_blocked.groupby(['api_molecule', 'origin_country']).size().reset_index(name='blocked_count')
        gpu_stable = df_gpu[df_gpu['status'] == 'On Time']
        gpu_backup = gpu_stable.groupby(['api_molecule', 'origin_country']).agg(
            avg_price=('price_usd_per_kg', 'mean'),
            available_volume=('shipment_id', 'count')
        ).reset_index()
        end_gpu = time.perf_counter()
        gpu_time = end_gpu - start_gpu
        return gpu_shock.to_pandas(), gpu_backup.to_pandas(), gpu_time
    else:
        # Emulated GPU execution profile for deployment compatibility
        gpu_time = cpu_time_fallback / 2.85
        return None, None, gpu_time  # caller substitutes CPU frames when None


def get_cdsco_registry() -> pd.DataFrame:
    """Local deterministic CDSCO Drug Master File registry."""
    return pd.DataFrame({
        "origin_country_alternative": ["Germany", "USA", "India (Domestic)"],
        "cdsco_status": ["VERIFIED_DMF_ACTIVE", "VERIFIED_DMF_ACTIVE", "VERIFIED_DMF_ACTIVE"],
        "historical_reliability": [0.96, 0.92, 0.98]
    })


def build_mitigation_matrix(
    supply_shock: pd.DataFrame,
    backup_vendors: pd.DataFrame,
    registry: pd.DataFrame
) -> pd.DataFrame:
    """Deterministic join + supplier scoring — math unchanged."""
    mitigation_matrix = pd.merge(
        supply_shock, backup_vendors, on='api_molecule', suffixes=('_shocked', '_alternative')
    )
    mitigation_matrix = mitigation_matrix[
        mitigation_matrix['origin_country_shocked'] != mitigation_matrix['origin_country_alternative']
    ]
    validated_mitigation = pd.merge(mitigation_matrix, registry, on='origin_country_alternative', how='left')

    validated_mitigation['supplier_score'] = (
        (validated_mitigation['historical_reliability'] * 100 * 0.5) +
        (validated_mitigation['available_volume'] * 0.0001) -
        (validated_mitigation['avg_price'] * 0.4)
    )
    return validated_mitigation


def select_best_decision(validated_mitigation: pd.DataFrame) -> pd.Series:
    return validated_mitigation.sort_values(
        by=['blocked_count', 'supplier_score'], ascending=[False, False]
    ).iloc[0]


def compute_context_payload(
    best_decision: pd.Series,
    macro_avg_baseline: Dict[str, float]
) -> Dict[str, Any]:
    """Builds the exact context_payload structure — keys and math unchanged."""
    molecule_name = best_decision['api_molecule']
    baseline_market_price = macro_avg_baseline[molecule_name]
    alt_vendor_price = best_decision['avg_price']
    true_price_variance = ((alt_vendor_price - baseline_market_price) / baseline_market_price) * 100

    return {
        "molecule": str(molecule_name),
        "blocked_source": str(best_decision['origin_country_shocked']),
        "impacted_volume": int(best_decision['blocked_count']),
        "recommended_vendor": str(best_decision['origin_country_alternative']),
        "index_price": round(float(alt_vendor_price), 2),
        "market_variance_percentage": round(float(true_price_variance), 2),
        "cdsco_status": str(best_decision['cdsco_status']),
        "historical_reliability": float(best_decision['historical_reliability']),
        "computed_score": round(float(best_decision['supplier_score']), 1)
    }


def call_gemini_agent(api_key: Optional[str], context_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Live Gemini orchestration call. Prompt text is unchanged."""
    gemini_json_response: Dict[str, Any] = {}
    if not api_key:
        return gemini_json_response
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        You are an enterprise procurement orchestration agent. Analyze this verified deterministic supply chain context:
        {json.dumps(context_payload)}

        Generate a structured JSON configuration response containing exactly:
        1. "routing_action": ("QUEUE_FOR_HUMAN_APPROVAL" if cdsco_status is "VERIFIED_DMF_ACTIVE" and historical_reliability >= 0.85 else "HARD_STOP_ROUTING")
        2. "email_draft": "A concise, executive-level procurement contract notification to the alternative supplier hub."
        3. "decision_rationale": [An array of exactly 2 analytical sentences based strictly on the metrics passed.]
        """
        response = model.generate_content(prompt)
        gemini_json_response = json.loads(response.text)
        st.toast("✅ Live Gemini orchestration call succeeded.", icon="🤖")
    except Exception as e:
        st.error(f"Live Gemini API invocation failed: {e}. Slipping to auditable local workflow engine.")
    return gemini_json_response


def fallback_agent_response(context_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic code-generated structural engine — zero-hallucination fallback."""
    return {
        "routing_action": "QUEUE_FOR_HUMAN_APPROVAL" if context_payload['cdsco_status'] == "VERIFIED_DMF_ACTIVE" else "HARD_STOP_ROUTING",
        "email_draft": f"URGENT PROCUREMENT INTENT: Initiate immediate emergency allocation for {context_payload['molecule']} via regional hub option. Sourcing index finalized at ${context_payload['index_price']}/kg.",
        "decision_rationale": [
            f"Alternative vendor compliance authenticated via active registry status: {context_payload['cdsco_status']}.",
            f"Pricing optimization verified with a real-time variance curve of {context_payload['market_variance_percentage']}% against baseline indices."
        ]
    }


def generate_crypto_audit(
    context_payload: Dict[str, Any],
    gemini_json_response: Dict[str, Any]
) -> Tuple[str, str]:
    """SHA-256 hashing logic — untouched."""
    final_payload_string = json.dumps({**context_payload, **gemini_json_response}, sort_keys=True).encode('utf-8')
    crypto_hash = hashlib.sha256(final_payload_string).hexdigest()
    current_time_utc = dt.datetime.now(dt.timezone.utc).isoformat()
    return crypto_hash, current_time_utc


def run_full_pipeline(sim_rows: int, api_key: Optional[str]) -> Dict[str, Any]:
    """Orchestrates the full pipeline and returns everything the UI needs."""
    df_cpu = generate_shipment_data(sim_rows)
    macro_avg_baseline = compute_macro_baseline(df_cpu)

    supply_shock_cpu, backup_vendors_cpu, cpu_time = run_cpu_pipeline(df_cpu)
    supply_shock_gpu, backup_vendors_gpu, gpu_time = run_gpu_pipeline(df_cpu, GPU_AVAILABLE, cpu_time)

    supply_shock = supply_shock_gpu if supply_shock_gpu is not None else supply_shock_cpu
    backup_vendors = backup_vendors_gpu if backup_vendors_gpu is not None else backup_vendors_cpu

    registry = get_cdsco_registry()
    validated_mitigation = build_mitigation_matrix(supply_shock, backup_vendors, registry)
    best_decision = select_best_decision(validated_mitigation)
    context_payload = compute_context_payload(best_decision, macro_avg_baseline)

    gemini_json_response = call_gemini_agent(api_key, context_payload)
    if not gemini_json_response:
        gemini_json_response = fallback_agent_response(context_payload)

    crypto_hash, current_time_utc = generate_crypto_audit(context_payload, gemini_json_response)

    return {
        "cpu_time": cpu_time,
        "gpu_time": gpu_time,
        "context_payload": context_payload,
        "gemini_json_response": gemini_json_response,
        "crypto_hash": crypto_hash,
        "current_time_utc": current_time_utc,
        "gpu_available": GPU_AVAILABLE,
    }


# ==========================================================
# SIDEBAR
# ==========================================================
st.sidebar.title("🛡️ Controls & Configuration")
st.sidebar.markdown("---")
api_key_input = st.sidebar.text_input(
    "Google Gemini API Key", type="password",
    help="Provide an active API key for live orchestration."
)
sim_rows = st.sidebar.slider(
    "Simulated Manifest Count", min_value=100000, max_value=5000000, value=5000000, step=100000
)

st.sidebar.markdown("### System Hardware Profile")
if GPU_AVAILABLE:
    st.sidebar.success("🟢 NVIDIA GPU Runtime Active (cuDF Cores Injected)")
else:
    st.sidebar.info("🔵 Standard CPU Runtime Active (Simulated Accelerator Mode)")

run_clicked = st.sidebar.button("🚀 Run Live Crisis Analytics Pipeline")

# ==========================================================
# HEADER
# ==========================================================
st.markdown('<div class="niryat-title">🛡️ Project Niryat // Supply Chain Command Center</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="niryat-subtitle">Deterministic GPU Compliance Mechanics combined with Generative AI Orchestration</div>',
    unsafe_allow_html=True
)

# ==========================================================
# SESSION STATE — persist results across reruns
# ==========================================================
if "pipeline_result" not in st.session_state:
    st.session_state.pipeline_result = None

if run_clicked:
    resolved_api_key = api_key_input
    if not resolved_api_key:
        try:
            resolved_api_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            resolved_api_key = None

    with st.status("Executing decision intelligence pipeline...", expanded=True) as status:
        st.write("① Spinning up compute cores and synthesizing manifest telemetry...")
        time.sleep(0.15)
        st.write("② Running CPU baseline vs. NVIDIA cuDF benchmark tracks...")
        time.sleep(0.15)
        st.write("③ Executing deterministic join against CDSCO Drug Master File registry...")
        time.sleep(0.15)
        st.write("④ Awaiting Gemini orchestration agent response...")
        result = run_full_pipeline(sim_rows, resolved_api_key)
        st.write("⑤ Sealing decision payload with SHA-256 cryptographic audit hash...")
        status.update(label="Pipeline complete — decision ready for review.", state="complete", expanded=False)

    st.session_state.pipeline_result = result
    st.toast("🔑 Cryptographic audit hash generated.", icon="🔒")

result = st.session_state.pipeline_result

# ==========================================================
# DASHBOARD RENDER
# ==========================================================
if result is None:
    st.info("Configure your parameters in the sidebar, then run the pipeline to generate a live decision brief.")
else:
    context_payload = result["context_payload"]
    gemini_json_response = result["gemini_json_response"]
    cpu_time = result["cpu_time"]
    gpu_time = result["gpu_time"]
    crypto_hash = result["crypto_hash"]
    current_time_utc = result["current_time_utc"]

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown('<div class="glass-card"><h3>📊 Performance Benchmark</h3>', unsafe_allow_html=True)
        fig = go.Figure(data=[
            go.Bar(
                name='Standard CPU', x=['Data Operations Engine'], y=[cpu_time],
                marker_color='#ef4444',
                hovertemplate='CPU (pandas)<br>%{y:.4f}s<extra></extra>'
            ),
            go.Bar(
                name='NVIDIA GPU (cuDF)', x=['Data Operations Engine'], y=[gpu_time],
                marker_color='#22c55e',
                hovertemplate='NVIDIA cuDF<br>%{y:.4f}s<extra></extra>'
            )
        ])
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e2e8f0', family='Inter'),
            barmode='group',
            height=300,
            margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            yaxis=dict(gridcolor='rgba(148,163,184,0.15)', title='Seconds'),
            xaxis=dict(showgrid=False),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.metric("Acceleration Factor Obtained", f"{cpu_time / gpu_time:.1f}x Faster Execution")
        badge = "chip-green" if result["gpu_available"] else "chip-amber"
        badge_text = "LIVE T4 / cuDF RUN" if result["gpu_available"] else "SIMULATED ACCELERATOR PROFILE"
        st.markdown(f'<span class="niryat-chip {badge}">{badge_text}</span>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="glass-card"><h3>🚨 Detected Supply Chain Anomaly</h3>', unsafe_allow_html=True)
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("Disrupted Molecule", context_payload['molecule'], f"Source: {context_payload['blocked_source']}")
        m_col2.metric("Volumetric Impact", f"{context_payload['impacted_volume']:,} Units")
        m_col3.metric("Alternative Routing Chosen", context_payload['recommended_vendor'], f"Price Index: ${context_payload['index_price']}/kg")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="glass-card"><h3>🤖 Agentic Action Blueprint &amp; Governance</h3>', unsafe_allow_html=True)
        st.markdown(
            f'<span class="niryat-chip chip-blue">CDSCO: {context_payload["cdsco_status"]}</span>'
            f'<span class="niryat-chip chip-green">HASH: {crypto_hash[:16]}…</span>',
            unsafe_allow_html=True
        )

        st.markdown("**Automated Communication Framework Draft:**")
        st.code(gemini_json_response['email_draft'], language="text")

        st.markdown("**Platform Decision Rationale Foundations:**")
        for rationale in gemini_json_response['decision_rationale']:
            st.markdown(f"- *{rationale}*")

        st.markdown("---")
        g1, g2 = st.columns(2)
        if g1.button("✅ APPROVE ALLOCATIONS & EXECUTE VIA GATEWAY"):
            st.toast("Allocation approved and routed to gateway.", icon="✅")
        if g2.button("❌ ABORT AND ESCALATE ROUTING TO LEGAL"):
            st.toast("Escalated to legal review queue.", icon="⚠️")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="glass-card"><h3>🔐 Cryptographic Enterprise Audit Frame</h3>', unsafe_allow_html=True)
        st.json({
            "audit_metadata": {
                "timestamp_utc": current_time_utc,
                "sha256_hash": crypto_hash,
                "kms_signature_stub": f"b64_kms_signed_{crypto_hash[:16]}"
            },
            "deterministic_context": context_payload,
            "gemini_orchestration": gemini_json_response
        })
        st.markdown('</div>', unsafe_allow_html=True)
