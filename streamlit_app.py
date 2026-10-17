import base64
import os

import pandas as pd
import requests
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError


st.set_page_config(
    page_title="Gateway CIP | Monitor",
    page_icon="CIP",
    layout="wide",
)

DEFAULT_API_BASE_URL = "http://34.226.194.178:8010"
try:
    API_BASE_URL = st.secrets["API_BASE_URL"]
except (KeyError, StreamlitSecretNotFoundError):
    API_BASE_URL = os.getenv("API_BASE_URL", DEFAULT_API_BASE_URL)
API_BASE_URL = API_BASE_URL.rstrip("/")
DEVICE_FIELDS = [
    ("Bomba de drenado", "estado_bomba_drenado", "pump"),
    ("Bomba dosificadora", "estado_bomba_dosificadora", "pump"),
    ("Resistencia", "estado_resistencia", "heater"),
    ("Motor de agitacion", "motor_agitacion", "motor"),
]
CYCLE_STEPS = ["PRE-ENJUAGUE", "ENJABONADO", "ENJUAGUE"]

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap');
    :root {
      --ink: #182d2a;
      --muted: #73817a;
      --paper: #f3f5f0;
      --line: #dfe6de;
      --green: #286b52;
      --green-dark: #183f35;
      --lime: #d5ed78;
      --amber: #d9822b;
      --off: #9aa59e;
    }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .stApp { background: var(--paper); color: var(--ink); }
    .block-container { max-width: 1440px; padding-top: 2rem; padding-bottom: 3rem; }
    h1, h2, h3 { color: var(--ink); }
    h1 { font-family: 'Barlow Condensed', sans-serif !important; font-size: 2.7rem !important; letter-spacing: 0 !important; }
    [data-testid="stSidebar"] { background: #e9eee7; }
    .masthead { display:flex; justify-content:space-between; align-items:center; margin-bottom:1.25rem; }
    .brand { display:flex; gap:.75rem; align-items:center; }
    .brand-mark { background:var(--green-dark); color:var(--lime); font:700 1.15rem 'Barlow Condensed',sans-serif; padding:.45rem .65rem; border-radius:4px; letter-spacing:0; }
    .brand-name { font:600 1rem 'DM Sans',sans-serif; letter-spacing:0; }
    .live-pill { display:flex; align-items:center; gap:.45rem; color:var(--green); font-size:.78rem; font-weight:700; text-transform:uppercase; }
    .live-dot { width:.5rem; height:.5rem; border-radius:50%; background:#45a878; box-shadow:0 0 0 4px #45a87822; }
    .live-pill.waiting { color:#9a661e; }
    .live-pill.waiting .live-dot { background:#d79a36; box-shadow:0 0 0 4px #d79a3622; }
    .live-pill.down { color:#a14b45; }
    .live-pill.down .live-dot { background:#c35d55; box-shadow:0 0 0 4px #c35d5522; }
    [data-testid="stSlider"] [role="slider"] { background:#286b52 !important; border-color:#286b52 !important; }
    [data-testid="stSlider"] [data-baseweb="slider"] > div > div { background:#286b52 !important; }
    .cycle-hero { position:relative; overflow:hidden; display:grid; grid-template-columns:1.15fr 1fr .7fr; gap:1.4rem; align-items:center; background:var(--green-dark); color:#f8fbf6; padding:1.5rem 1.8rem; border-radius:8px; margin:.6rem 0 1.1rem; }
    .cycle-hero:after { content:''; position:absolute; width:270px; height:270px; right:23%; top:-205px; border:1px solid #ffffff15; border-radius:50%; box-shadow:0 0 0 28px #ffffff08,0 0 0 58px #ffffff06; pointer-events:none; }
    .eyebrow { color:#b9d6c7; font-size:.69rem; font-weight:700; text-transform:uppercase; letter-spacing:.08em; }
    .cycle-name { color:#fff; font:600 2.1rem 'Barlow Condensed',sans-serif; margin:.15rem 0 0; }
    .cycle-steps { display:flex; align-items:center; gap:.35rem; }
    .cycle-step { flex:1; display:flex; align-items:center; gap:.45rem; color:#a6b8af; font-size:.68rem; font-weight:700; white-space:nowrap; }
    .cycle-step.active { color:var(--lime); }
    .step-number { width:1.55rem; height:1.55rem; border:1px solid #789286; border-radius:50%; display:grid; place-items:center; flex:none; }
    .active .step-number { background:var(--lime); border-color:var(--lime); color:var(--green-dark); }
    .cycle-divider { height:1px; flex:0 1 24px; background:#70877c; }
    .hero-temp { text-align:right; border-left:1px solid #ffffff2b; padding-left:1.3rem; }
    .hero-temp strong { display:block; color:#fff; font:600 2.5rem 'Barlow Condensed',sans-serif; line-height:1; }
    .hero-temp span { color:#b9d6c7; font-size:.72rem; text-transform:uppercase; }
    .section-label { margin:1.5rem 0 .75rem; display:flex; justify-content:space-between; align-items:baseline; }
    .section-label h3 { font:600 1.35rem 'Barlow Condensed',sans-serif; margin:0; }
    .section-label span { color:var(--muted); font-size:.75rem; }
    .info-card { min-height:142px; background:#fff; border:1px solid var(--line); border-radius:7px; padding:1rem 1.1rem; }
    .info-label { color:var(--muted); font-size:.75rem; font-weight:600; }
    .info-value { color:var(--ink); font:600 1.7rem 'Barlow Condensed',sans-serif; margin-top:.75rem; }
    .tank-row { display:flex; align-items:center; gap:.85rem; margin-top:.6rem; }
    .tank { width:30px; height:62px; border:2px solid #93a39a; border-radius:5px 5px 8px 8px; padding:3px; display:flex; align-items:flex-end; background:#f6f8f5; }
    .tank-fill { width:100%; background:#68a98a; border-radius:2px 2px 5px 5px; }
    .tank-fill.low { background:#d99a4c; }
    .tank-fill.empty { background:#d99a4c; }
    .tank-fill.full { background:#68a98a; }
    .tank-copy strong { display:block; font:600 1.35rem 'Barlow Condensed',sans-serif; }
    .tank-copy small { color:var(--muted); font-size:.68rem; }
    .device-card { height:177px; padding:1rem; background:#fff; border:1px solid var(--line); border-radius:7px; display:flex; flex-direction:column; justify-content:space-between; }
    .device-top { display:flex; align-items:flex-start; justify-content:space-between; gap:.4rem; }
    .device-name { color:var(--muted); font-size:.72rem; font-weight:600; line-height:1.3; max-width:100px; }
    .device-state { padding:.22rem .48rem; border-radius:3px; font-size:.64rem; font-weight:700; letter-spacing:.04em; }
    .device-state.on { background:#e3f3e9; color:#28764d; }
    .device-state.off { background:#edf0ed; color:#77847c; }
    .device-art { display:flex; align-items:center; justify-content:center; height:94px; }
    .device-art img { width:108px; height:90px; }
    .device-foot { color:var(--muted); font-size:.67rem; }
    .history-panel { background:#fff; border:1px solid var(--line); border-radius:7px; padding:1rem 1.15rem; }
    [data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:6px; }
    @media(max-width:900px) {
      .cycle-hero { grid-template-columns:1fr; gap:1rem; }
      .hero-temp { text-align:left; border-left:0; border-top:1px solid #ffffff2b; padding:1rem 0 0; }
      .cycle-steps { flex-wrap:wrap; }
      .cycle-step { white-space:normal; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Panel")
    refresh_seconds = st.slider("Actualizar cada (segundos)", 2, 60, 5)
    history_limit = st.select_slider(
        "Lecturas en el historial",
        options=[10, 25, 50, 100, 250, 500],
        value=100,
    )


def render_icon(device: str, active: bool) -> str:
    color = "#286b52" if active else "#aab4ad"
    detail = "#d5ed78" if active else "#dce2dd"
    if device == "motor":
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 140 100">
        <g fill="none" stroke="{color}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
          <rect x="24" y="22" width="73" height="55" rx="14" fill="#f4f7f2"/>
          <path d="M97 39h13v21H97M37 78v7m48-7v7M15 85h102"/>
          <circle cx="61" cy="49" r="17" fill="{detail}"/>
          <path d="M61 33c-2 9 3 12 0 16m14 0c-9-2-12 3-16 0m1 16c2-9-3-12 0-16m-14 0c9 2 12-3 16 0"/>
          <path d="M43 22l-5-7m36 7 5-7"/>
        </g></svg>"""
    elif device == "heater":
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 140 100">
        <g fill="none" stroke="{color}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 72h13l8-43 13 43 14-43 13 43 14-43 13 43h11" fill="none"/>
          <path d="M25 82h91M42 24V15m27 9V12m28 12V15"/>
          <circle cx="69" cy="85" r="4" fill="{detail}" stroke="{color}"/>
        </g></svg>"""
    else:
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 140 100">
        <g fill="none" stroke="{color}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
          <path d="M25 76h78V50H78V34H48v16H25z" fill="#f4f7f2"/>
          <path d="M48 34V22h30v12M58 22v-7h10v7M25 61H14v-9h11m89 24V48h9v28z"/>
          <circle cx="63" cy="59" r="13" fill="{detail}"/>
          <path d="M63 47c-1 6 3 8 0 12m12 0c-6-1-8 3-12 0m0 12c1-6-3-8 0-12m-12 0c6 1 8-3 12 0"/>
          <path d="M35 76v8m54-8v8M19 84h100"/>
        </g></svg>"""
    return base64.b64encode(svg.encode("utf-8")).decode("ascii")


def render_device_card(label: str, field: str, icon: str, latest: dict) -> str:
    raw_state = latest.get(field)
    state = str(raw_state).strip().upper() if raw_state is not None else "SIN DATO"
    active = state == "ON"
    known = state in {"ON", "OFF"}
    encoded_icon = render_icon(icon, active)
    state_class = "on" if active else "off" if known else "unknown"
    state_label = "ENCENDIDO" if active else "APAGADO" if known else "SIN DATO"
    subtext = "En funcionamiento" if active else "En espera" if known else "Esperando lectura del PLC"
    return f"""<div class="device-card">
      <div class="device-top">
        <span class="device-name">{label}</span>
            <span class="device-state {state_class}">{state_label}</span>
      </div>
      <div class="device-art"><img alt="Ilustracion de {label}" src="data:image/svg+xml;base64,{encoded_icon}"></div>
      <div class="device-foot">{subtext}</div>
    </div>"""


def render_cycle(cycle: str, temperature: float | None) -> None:
    current = cycle.strip().upper()
    try:
        active_index = CYCLE_STEPS.index(current)
    except ValueError:
        active_index = -1
    steps = []
    for index, label in enumerate(CYCLE_STEPS):
        state_class = "cycle-step active" if index == active_index else "cycle-step"
        number = "✓" if index < active_index else str(index + 1)
        steps.append(
            f'<div class="{state_class}"><span class="step-number">{number}</span>'
            f"<span>{label}</span></div>"
        )
        if index < len(CYCLE_STEPS) - 1:
            steps.append('<div class="cycle-divider"></div>')
    cycle_label = current if active_index >= 0 else "ESPERANDO LECTURA"
    temperature_label = f"{temperature:.1f} °C" if temperature is not None else "--.- °C"
    st.markdown(
        f"""<section class="cycle-hero">
          <div><div class="eyebrow">Ciclo en curso</div><div class="cycle-name">{cycle_label}</div></div>
          <div class="cycle-steps">{''.join(steps)}</div>
          <div class="hero-temp"><strong>{temperature_label}</strong><span>Temperatura de proceso</span></div>
        </section>""",
        unsafe_allow_html=True,
    )


@st.fragment(run_every=f"{refresh_seconds}s")
def mostrar_monitor() -> None:
    latest = None
    api_reachable = False
    try:
        latest_response = requests.get(f"{API_BASE_URL}/api/dato", timeout=8)
        api_reachable = True
        if latest_response.status_code == 404:
            latest = None
        else:
            latest_response.raise_for_status()
            latest = latest_response.json()
    except requests.RequestException as error:
        st.error(f"No se pudo consultar la ultima lectura: {error}")

    status_text = (
        "LECTURA EN VIVO" if latest else "API EN LINEA · ESPERANDO PLC"
        if api_reachable else "API SIN CONEXION"
    )
    status_class = "live-pill" if latest else "live-pill waiting" if api_reachable else "live-pill down"
    st.markdown(
        '<div class="masthead"><div class="brand"><span class="brand-mark">CIP</span>'
        '<span class="brand-name">CONTROL DE PROCESO</span></div>'
        f'<span class="{status_class}"><i class="live-dot"></i>{status_text}</span></div>',
        unsafe_allow_html=True,
    )
    display = latest or {
        "ciclo": "ESPERANDO PLC",
        "temperatura": None,
        "nivel_cabina": "SIN DATO",
        "nivel_t_residual": "SIN DATO",
        "estado_bomba_drenado": None,
        "estado_bomba_dosificadora": None,
        "estado_resistencia": None,
        "motor_agitacion": None,
    }
    render_cycle(
        display["ciclo"],
        float(display["temperatura"]) if display["temperatura"] is not None else None,
    )
    st.markdown(
        '<div class="section-label"><h3>Condiciones del sistema</h3>'
        '<span>Lectura actual del proceso</span></div>',
        unsafe_allow_html=True,
    )

    def render_level(label: str, value: str) -> str:
        level = value.strip().upper()
        level = {
            "TRUE": "VACIO",
            "1": "VACIO",
            "FALSE": "LLENO",
            "0": "LLENO",
        }.get(level, level)
        fill = {"BAJO": 24, "MEDIO": 58, "ALTO": 88, "LLENO": 100}.get(level, 0)
        fill_class = "empty" if level == "VACIO" else "full" if level == "LLENO" else "low" if level == "BAJO" else ""
        return f"""<div class="info-card"><div class="info-label">{label}</div>
          <div class="tank-row"><div class="tank"><div class="tank-fill {fill_class}" style="height:{fill}%"></div></div>
          <div class="tank-copy"><strong>{level}</strong><small>Nivel detectado</small></div></div></div>"""

    condition_columns = st.columns([1.1, 1.1, 2.4])
    temperature_value = display["temperatura"]
    temperature_text = f"{float(temperature_value):.1f} °C" if temperature_value is not None else "--.- °C"
    condition_columns[0].markdown(
        f'<div class="info-card"><div class="info-label">Temperatura actual</div>'
        f'<div class="info-value">{temperature_text}</div></div>',
        unsafe_allow_html=True,
    )
    condition_columns[1].markdown(
        render_level("Nivel de cabina", display["nivel_cabina"]),
        unsafe_allow_html=True,
    )
    condition_columns[2].markdown(
        render_level("Nivel de tanque residual", display["nivel_t_residual"]),
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-label"><h3>Equipos</h3>'
        '<span>Verde: activo · Gris: apagado o sin lectura</span></div>',
        unsafe_allow_html=True,
    )
    device_columns = st.columns(len(DEVICE_FIELDS))
    for column, (label, field, icon) in zip(device_columns, DEVICE_FIELDS):
        column.markdown(
            render_device_card(label, field, icon, display),
            unsafe_allow_html=True,
        )
    if latest is not None:
        st.caption(f"Actualizado {latest['fecha_hora']} UTC · Registro #{latest['id']}")

    st.markdown(
        '<div class="section-label"><h3>Tendencia de temperatura</h3>'
        '<span>Historico reciente</span></div>',
        unsafe_allow_html=True,
    )
    try:
        history_response = requests.get(
            f"{API_BASE_URL}/api/datos",
            params={"limit": history_limit, "offset": 0},
            timeout=8,
        )
        history_response.raise_for_status()
        history = history_response.json()
        records = history.get("registros", [])
    except (requests.RequestException, ValueError) as error:
        st.error(f"No se pudo consultar el historial: {error}")
        return

    if not records:
        st.info("El historial aparecera aqui cuando el PLC envie sus primeras lecturas.")
        return

    frame = pd.DataFrame(records)
    frame["fecha_hora"] = pd.to_datetime(frame["fecha_hora"], utc=True)
    chronological = frame.sort_values("fecha_hora")
    st.markdown('<div class="history-panel">', unsafe_allow_html=True)
    st.line_chart(chronological, x="fecha_hora", y="temperatura", x_label="Hora (UTC)", y_label="°C")

    visible_columns = [
        "id",
        "fecha_hora",
        "temperatura",
        "ciclo",
        "nivel_cabina",
        "nivel_t_residual",
        "estado_bomba_drenado",
        "estado_bomba_dosificadora",
        "estado_resistencia",
        "motor_agitacion",
    ]
    display_frame = frame[visible_columns].copy()
    display_frame["fecha_hora"] = display_frame["fecha_hora"].dt.strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )
    with st.expander(f"Ver lecturas detalladas · {history.get('total', 0)} registros"):
        st.dataframe(display_frame, hide_index=True, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


mostrar_monitor()
