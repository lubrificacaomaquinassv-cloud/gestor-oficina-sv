import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from st_supabase_connection import SupabaseConnection
from datetime import datetime, date, timedelta

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Gestor Oficina — Santa Vergínia",
    layout="wide",
    page_icon="🔧",
)

# CSS industrial verde escuro
st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background:#0a1409; }
  [data-testid="stSidebar"]          { background:#111c10; border-right:1px solid #1e2e1c; }
  [data-testid="stHeader"]           { background:#0a1409; }
  h1,h2,h3,h4                        { color:#e8edd0; font-family:'Barlow Condensed',sans-serif; letter-spacing:2px; }
  .metric-card {
    background:#111c10; border:1px solid #1e2e1c; border-radius:10px;
    padding:16px 20px; position:relative; overflow:hidden;
  }
  .metric-card::before {
    content:''; position:absolute; top:0; left:0; right:0; height:3px;
  }
  .card-green::before  { background:#4a9e3f; }
  .card-yellow::before { background:#d4a017; }
  .card-red::before    { background:#c0392b; }
  .card-blue::before   { background:#2980b9; }
  .metric-label { font-size:10px; color:#8aab80; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:4px; }
  .metric-value { font-size:32px; font-weight:700; color:#e8edd0; line-height:1; font-family:'Barlow Condensed',sans-serif; }
  .metric-sub   { font-size:11px; color:#4a6644; margin-top:3px; }
  .section-title {
    font-family:'Barlow Condensed',sans-serif; font-size:13px; font-weight:700;
    letter-spacing:2px; text-transform:uppercase; color:#8aab80;
    border-left:4px solid #4a9e3f; padding-left:10px; margin:20px 0 10px;
  }
  .stTabs [data-baseweb="tab-list"] { background:#111c10; border-bottom:2px solid #1e2e1c; gap:0; }
  .stTabs [data-baseweb="tab"] {
    color:#4a6644; font-family:'Barlow Condensed',sans-serif;
    font-size:12px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase;
    padding:10px 20px; border-bottom:3px solid transparent;
  }
  .stTabs [aria-selected="true"] { color:#6fcf60 !important; border-bottom:3px solid #4a9e3f !important; }
  div[data-testid="metric-container"] {
    background:#111c10; border:1px solid #1e2e1c; border-radius:10px; padding:14px;
  }
  div[data-testid="metric-container"] label { color:#8aab80 !important; font-size:11px !important; }
  div[data-testid="metric-container"] [data-testid="stMetricValue"] { color:#e8edd0 !important; }
</style>
""", unsafe_allow_html=True)

PLOTLY_DARK = dict(
    paper_bgcolor='#111c10',
    plot_bgcolor='#0d180c',
    font=dict(color='#8aab80', family='Barlow Condensed'),
    xaxis=dict(gridcolor='#1e2e1c', zerolinecolor='#1e2e1c'),
    yaxis=dict(gridcolor='#1e2e1c', zerolinecolor='#1e2e1c'),
    margin=dict(l=10, r=10, t=30, b=10),
)

# ─────────────────────────────────────────────
# CONEXÃO
# ─────────────────────────────────────────────
conn = st.connection("supabase", type=SupabaseConnection, ttl=300)

# ─────────────────────────────────────────────
# CARGA DE DADOS
# ─────────────────────────────────────────────
@st.cache_data(ttl=180, show_spinner="Atualizando horímetros...")
def carregar_lubrificacao(_conn):
    resp = _conn.query("*", table="vw_proxima_troca_v4").execute()
    df = pd.DataFrame(resp.data)
    if df.empty:
        return df
    df["horas_restantes"]  = pd.to_numeric(df["horas_restantes"],  errors="coerce")
    df["h_atual"]          = pd.to_numeric(df["h_atual"],           errors="coerce")
    df["h_proxima_troca"]  = pd.to_numeric(df["h_proxima_troca"],   errors="coerce")
    df["h_na_troca"]       = pd.to_numeric(df["h_na_troca"],        errors="coerce")
    df["data_ultima_troca"] = pd.to_datetime(df["data_ultima_troca"], errors="coerce")
    df["data_ultimo_apontamento"] = pd.to_datetime(df["data_ultimo_apontamento"], errors="coerce")
    return df

@st.cache_data(ttl=180, show_spinner="Carregando abastecimentos...")
def carregar_abastecimento(_conn):
    resp = _conn.query("*", table="vw_abastecimento_consolidado").execute()
    df = pd.DataFrame(resp.data)
    if df.empty:
        return df
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["liters"]     = pd.to_numeric(df["liters"],      errors="coerce")
    df["hourmeter"]  = pd.to_numeric(df["hourmeter"],   errors="coerce")
    return df

@st.cache_data(ttl=180, show_spinner="Carregando apontamentos...")
def carregar_apontamentos(_conn):
    resp = _conn.query("*", table="apontamento_campo").execute()
    df = pd.DataFrame(resp.data)
    if df.empty:
        return df
    df["data"]             = pd.to_datetime(df["data"],    errors="coerce")
    df["h_final"]          = pd.to_numeric(df["h_final"],  errors="coerce")
    df["horas_trabalhadas"]= pd.to_numeric(df["horas_trabalhadas"], errors="coerce")
    return df

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
col_logo, col_title, col_sync = st.columns([1, 8, 2])
with col_logo:
    st.markdown("""
    <div style='background:#1a2e18;border:1px solid #1e2e1c;border-radius:8px;
    width:52px;height:52px;display:flex;align-items:center;justify-content:center;
    font-family:Barlow Condensed,sans-serif;font-weight:800;font-size:18px;color:#6fcf60;'>SV</div>
    """, unsafe_allow_html=True)
with col_title:
    st.markdown("""
    <div style='font-family:Barlow Condensed,sans-serif;font-weight:800;font-size:22px;
    letter-spacing:2px;color:#e8edd0;'>GESTOR DA OFICINA — SANTA VERGÍNIA</div>
    <div style='font-size:11px;color:#8aab80;letter-spacing:1px;'>
    Lubrificação · Horímetros · Abastecimento Comboio · Tempo Real</div>
    """, unsafe_allow_html=True)
with col_sync:
    if st.button("🔄 Atualizar", key="btn_refresh"):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"Atualizado: {datetime.now().strftime('%d/%m %H:%M')}")

st.divider()

# ─────────────────────────────────────────────
# CARREGAR
# ─────────────────────────────────────────────
df_lub   = carregar_lubrificacao(conn)
df_abast = carregar_abastecimento(conn)
df_apont = carregar_apontamentos(conn)

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🔧 Troca de Óleo",
    "⏱ Horímetros",
    "⛽ Abastecimento Comboio",
    "📊 Análise Geral",
])

# ══════════════════════════════════════════════
# TAB 1 — TROCA DE ÓLEO
# ══════════════════════════════════════════════
with tab1:

    if df_lub.empty:
        st.warning("Nenhum dado de lubrificação encontrado.")
    else:
        # KPIs
        ok   = df_lub[df_lub["status_troca"] == "OK"].shape[0]
        prox = df_lub[df_lub["status_troca"] == "PROXIMO"].shape[0]
        atr  = df_lub[df_lub["status_troca"] == "EM ATRASO"].shape[0]
        total= len(df_lub)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("✅ Status OK",       ok,    help="Equipamentos dentro do prazo")
        c2.metric("⚠️ Próximo ≤ 100h",  prox,  help="Troca prevista em breve")
        c3.metric("🔴 Em Atraso",        atr,   help="Horímetro ultrapassou o prazo")
        c4.metric("📋 Total Monitorado", total)

        st.markdown('<div class="section-title">Horas Restantes por Equipamento</div>', unsafe_allow_html=True)

        # Gráfico de barras horizontais com cores por status
        color_map = {"OK": "#4a9e3f", "PROXIMO": "#d4a017", "EM ATRASO": "#c0392b"}
        df_chart = df_lub.sort_values("horas_restantes", ascending=True).copy()
        df_chart["cor"] = df_chart["status_troca"].map(color_map)

        fig_bar = go.Figure()
        for status, cor in color_map.items():
            dfg = df_chart[df_chart["status_troca"] == status]
            if dfg.empty:
                continue
            fig_bar.add_trace(go.Bar(
                y=dfg["vehicle"],
                x=dfg["horas_restantes"],
                name=status,
                orientation="h",
                marker_color=cor,
                text=dfg["horas_restantes"].apply(lambda v: f"{v:.0f}h" if pd.notna(v) else "—"),
                textposition="outside",
                textfont=dict(color="#e8edd0", size=11),
                hovertemplate="<b>%{y}</b><br>Restante: %{x:.0f}h<extra></extra>",
            ))

        fig_bar.update_layout(
            **PLOTLY_DARK,
            height=max(400, len(df_lub) * 28),
            barmode="relative",
            legend=dict(orientation="h", y=1.05, x=0, font=dict(color="#e8edd0")),
            xaxis_title="Horas restantes para troca",
            yaxis=dict(gridcolor="#1e2e1c", tickfont=dict(color="#e8edd0", size=11)),
            xaxis=dict(gridcolor="#1e2e1c", zeroline=True, zerolinecolor="#c0392b", zerolinewidth=2),
        )
        fig_bar.add_vline(x=0,   line_color="#c0392b", line_width=2, line_dash="dash")
        fig_bar.add_vline(x=100, line_color="#d4a017", line_width=1, line_dash="dot",
                          annotation_text="Alerta 100h", annotation_font_color="#d4a017",
                          annotation_position="top right")

        st.plotly_chart(fig_bar, use_container_width=True, key="chart_lub_barras")

        # ── Gauges individuais para equipamentos críticos ──
        criticos = df_lub[df_lub["status_troca"].isin(["EM ATRASO", "PROXIMO"])].head(8)
        if not criticos.empty:
            st.markdown('<div class="section-title">Gauge — Equipamentos Críticos</div>', unsafe_allow_html=True)

            n = len(criticos)
            cols_per_row = 4
            rows = (n + cols_per_row - 1) // cols_per_row

            for row in range(rows):
                cols = st.columns(cols_per_row)
                for i in range(cols_per_row):
                    idx = row * cols_per_row + i
                    if idx >= n:
                        break
                    rec = criticos.iloc[idx]
                    h_rest = rec["horas_restantes"] if pd.notna(rec["horas_restantes"]) else 0
                    h_prox = rec["h_proxima_troca"] if pd.notna(rec["h_proxima_troca"]) else 1000
                    h_atual= rec["h_atual"]         if pd.notna(rec["h_atual"])          else 0
                    intervalo = h_prox - rec["h_na_troca"] if pd.notna(rec["h_na_troca"]) else 250

                    # % de vida consumida
                    pct_consumido = min(100, max(0, ((h_atual - rec["h_na_troca"]) / max(intervalo, 1)) * 100))
                    cor_gauge = "#c0392b" if rec["status_troca"] == "EM ATRASO" else "#d4a017"

                    fig_g = go.Figure(go.Indicator(
                        mode="gauge+number+delta",
                        value=h_atual,
                        delta={"reference": h_prox, "valueformat": ".0f",
                               "increasing": {"color": "#c0392b"},
                               "decreasing": {"color": "#4a9e3f"}},
                        number={"suffix": "h", "font": {"color": "#e8edd0", "size": 20}},
                        title={"text": f"<b>{rec['vehicle']}</b><br><span style='font-size:10px;color:#8aab80'>"
                                       f"Troca em {h_prox:.0f}h · Restam {h_rest:.0f}h</span>",
                               "font": {"color": "#e8edd0", "size": 13}},
                        gauge={
                            "axis": {"range": [rec["h_na_troca"], h_prox + abs(min(0, h_rest))],
                                     "tickcolor": "#4a6644"},
                            "bar":  {"color": cor_gauge, "thickness": 0.25},
                            "bgcolor": "#0d180c",
                            "bordercolor": "#1e2e1c",
                            "steps": [
                                {"range": [rec["h_na_troca"], h_prox - 100], "color": "#1a3318"},
                                {"range": [h_prox - 100, h_prox],            "color": "#2a2200"},
                                {"range": [h_prox, h_prox + 200],            "color": "#2a1010"},
                            ],
                            "threshold": {
                                "line": {"color": "#c0392b", "width": 3},
                                "thickness": 0.8,
                                "value": h_prox,
                            },
                        },
                    ))
                    fig_g.update_layout(
                        paper_bgcolor="#111c10",
                        plot_bgcolor="#111c10",
                        height=220,
                        margin=dict(l=10, r=10, t=60, b=10),
                    )
                    with cols[i]:
                        st.plotly_chart(fig_g, use_container_width=True,
                                        key=f"gauge_{rec['vehicle']}_{idx}")

        # ── Tabela detalhada ──
        st.markdown('<div class="section-title">Tabela Completa — Ordenada por Urgência</div>', unsafe_allow_html=True)

        def badge(status):
            colors = {
                "OK":        ("🟢", "#1a3318", "#6fcf60"),
                "PROXIMO":   ("🟡", "#2a2200", "#d4a017"),
                "EM ATRASO": ("🔴", "#2a1010", "#e74c3c"),
            }
            e, bg, fg = colors.get(status, ("⚪", "#111", "#fff"))
            return f"{e} {status}"

        df_tbl = df_lub[[
            "vehicle", "h_na_troca", "h_proxima_troca",
            "h_atual", "horas_restantes", "data_ultimo_apontamento", "status_troca"
        ]].copy()
        df_tbl.columns = ["Frota", "H.Troca", "Próxima(h)", "H.Atual", "Restante(h)", "Último Apoint.", "Status"]
        df_tbl["Status"] = df_tbl["Status"].apply(badge)
        df_tbl["Último Apoint."] = pd.to_datetime(df_tbl["Último Apoint."]).dt.strftime("%d/%m/%Y")
        df_tbl["Restante(h)"] = df_tbl["Restante(h)"].apply(
            lambda v: f"{v:+.0f}h" if pd.notna(v) else "—"
        )

        st.dataframe(
            df_tbl,
            use_container_width=True,
            height=400,
            key="tabela_lub",
            hide_index=True,
        )

# ══════════════════════════════════════════════
# TAB 2 — HORÍMETROS
# ══════════════════════════════════════════════
with tab2:

    if df_apont.empty:
        st.warning("Sem apontamentos de campo disponíveis.")
    else:
        st.markdown('<div class="section-title">Evolução do Horímetro por Frota</div>', unsafe_allow_html=True)

        # Filtro de frota
        frotas = sorted(df_apont["frota"].dropna().unique().tolist())
        sel_frotas = st.multiselect(
            "Selecione frotas:",
            options=frotas,
            default=frotas[:6],
            key="sel_frotas_horimetro",
        )

        if sel_frotas:
            df_h = df_apont[df_apont["frota"].isin(sel_frotas)].copy()
            df_h = df_h.sort_values("data")

            # Line chart horímetro ao longo do tempo
            fig_line = px.line(
                df_h,
                x="data",
                y="h_final",
                color="frota",
                markers=True,
                labels={"data": "Data", "h_final": "Horímetro (h)", "frota": "Frota"},
                title="Evolução do Horímetro",
                color_discrete_sequence=px.colors.qualitative.Safe,
            )
            fig_line.update_layout(**PLOTLY_DARK, height=400)
            fig_line.update_traces(line=dict(width=2), marker=dict(size=5))
            st.plotly_chart(fig_line, use_container_width=True, key="chart_horimetro_linha")

            # Horas trabalhadas — heatmap frota × dia
            st.markdown('<div class="section-title">Heatmap — Horas Trabalhadas por Frota × Dia</div>',
                        unsafe_allow_html=True)

            df_heat = df_h.copy()
            df_heat["dia"] = df_heat["data"].dt.strftime("%d/%m")
            pivot = df_heat.pivot_table(
                index="frota", columns="dia",
                values="horas_trabalhadas", aggfunc="sum"
            ).fillna(0)

            fig_heat = px.imshow(
                pivot,
                color_continuous_scale=["#0a1409", "#1a3318", "#2d6a27", "#4a9e3f", "#6fcf60"],
                aspect="auto",
                labels=dict(x="Dia", y="Frota", color="Horas"),
            )
            fig_heat.update_layout(**PLOTLY_DARK, height=max(300, len(sel_frotas) * 35))
            fig_heat.update_coloraxes(colorbar_tickfont=dict(color="#8aab80"))
            st.plotly_chart(fig_heat, use_container_width=True, key="chart_heatmap")

        # Tabela último horímetro por frota
        st.markdown('<div class="section-title">Último Horímetro Registrado por Frota</div>',
                    unsafe_allow_html=True)

        df_ult = (
            df_apont.sort_values("data")
            .groupby("frota", as_index=False)
            .agg(
                ultimo_horimetro=("h_final", "max"),
                ultima_data=("data", "max"),
                total_horas=("horas_trabalhadas", "sum"),
            )
            .sort_values("ultimo_horimetro", ascending=False)
        )
        df_ult["ultima_data"] = df_ult["ultima_data"].dt.strftime("%d/%m/%Y")
        df_ult.columns = ["Frota", "Horímetro Atual (h)", "Último Registro", "Total Horas Acumuladas"]

        st.dataframe(df_ult, use_container_width=True, hide_index=True, key="tabela_horimetros")

# ══════════════════════════════════════════════
# TAB 3 — ABASTECIMENTO COMBOIO
# ══════════════════════════════════════════════
with tab3:

    if df_abast.empty:
        st.warning("Sem dados de abastecimento.")
    else:
        # KPIs
        total_l = df_abast["liters"].sum()
        total_ev = len(df_abast)
        frotas_ab = df_abast["vehicle"].nunique()
        hoje = pd.Timestamp(date.today())
        litros_hoje = df_abast[df_abast["created_at"].dt.date == date.today()]["liters"].sum()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("⛽ Total Abastecido",   f"{total_l:,.0f} L")
        c2.metric("📋 Eventos",            total_ev)
        c3.metric("🚜 Frotas Abastecidas", frotas_ab)
        c4.metric("📅 Litros Hoje",        f"{litros_hoje:,.0f} L")

        # Filtro período
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            dt_ini = st.date_input("De:", value=date.today() - timedelta(days=30), key="abast_ini")
        with col_f2:
            dt_fim = st.date_input("Até:", value=date.today(), key="abast_fim")

        mask = (
            (df_abast["created_at"].dt.date >= dt_ini) &
            (df_abast["created_at"].dt.date <= dt_fim)
        )
        df_f = df_abast[mask].copy()

        if df_f.empty:
            st.info("Sem dados no período selecionado.")
        else:
            col_g1, col_g2 = st.columns(2)

            with col_g1:
                st.markdown('<div class="section-title">Volume por Frota (L)</div>',
                            unsafe_allow_html=True)
                df_por_frota = (
                    df_f.groupby("vehicle", as_index=False)["liters"]
                    .sum().sort_values("liters", ascending=True)
                )
                fig_frota = go.Figure(go.Bar(
                    y=df_por_frota["vehicle"],
                    x=df_por_frota["liters"],
                    orientation="h",
                    marker=dict(
                        color=df_por_frota["liters"],
                        colorscale=[[0, "#1a3318"], [0.5, "#2d6a27"], [1, "#6fcf60"]],
                        showscale=False,
                    ),
                    text=df_por_frota["liters"].apply(lambda v: f"{v:,.0f}L"),
                    textposition="outside",
                    textfont=dict(color="#e8edd0", size=11),
                ))
                fig_frota.update_layout(**PLOTLY_DARK, height=max(300, len(df_por_frota) * 26))
                st.plotly_chart(fig_frota, use_container_width=True, key="chart_abast_frota")

            with col_g2:
                st.markdown('<div class="section-title">Volume Diário (L)</div>',
                            unsafe_allow_html=True)
                df_diario = (
                    df_f.groupby(df_f["created_at"].dt.date, as_index=False)["liters"]
                    .sum()
                )
                df_diario.columns = ["data", "litros"]
                fig_diario = px.area(
                    df_diario,
                    x="data", y="litros",
                    labels={"data": "Data", "litros": "Litros"},
                    color_discrete_sequence=["#4a9e3f"],
                )
                fig_diario.update_traces(
                    fill="tozeroy",
                    line=dict(color="#6fcf60", width=2),
                    fillcolor="rgba(74,158,63,0.25)",
                )
                fig_diario.update_layout(**PLOTLY_DARK, height=300)
                st.plotly_chart(fig_diario, use_container_width=True, key="chart_abast_diario")

            # Tabela detalhada
            st.markdown('<div class="section-title">Detalhe dos Abastecimentos</div>',
                        unsafe_allow_html=True)
            df_show = df_f[["created_at", "vehicle", "operator", "work_front",
                             "fuel_type", "liters", "hourmeter"]].copy()
            df_show["created_at"] = df_show["created_at"].dt.strftime("%d/%m/%Y %H:%M")
            df_show.columns = ["Data/Hora", "Frota", "Operador", "Frente", "Combustível", "Litros (L)", "Horímetro"]
            st.dataframe(df_show, use_container_width=True, height=350,
                         hide_index=True, key="tabela_abast")

# ══════════════════════════════════════════════
# TAB 4 — ANÁLISE GERAL
# ══════════════════════════════════════════════
with tab4:

    st.markdown('<div class="section-title">Distribuição de Status — Lubrificação</div>',
                unsafe_allow_html=True)

    if not df_lub.empty:
        col_p1, col_p2 = st.columns(2)

        with col_p1:
            # Donut status
            status_count = df_lub["status_troca"].value_counts().reset_index()
            status_count.columns = ["status", "count"]
            color_seq = {"OK": "#4a9e3f", "PROXIMO": "#d4a017", "EM ATRASO": "#c0392b"}
            fig_donut = px.pie(
                status_count,
                names="status",
                values="count",
                hole=0.6,
                color="status",
                color_discrete_map=color_seq,
            )
            fig_donut.update_traces(
                textfont=dict(color="#e8edd0"),
                hovertemplate="<b>%{label}</b><br>%{value} equipamentos<extra></extra>",
            )
            fig_donut.update_layout(
                **PLOTLY_DARK,
                height=320,
                legend=dict(font=dict(color="#e8edd0")),
                annotations=[dict(
                    text=f"<b>{len(df_lub)}</b><br>frotas",
                    x=0.5, y=0.5, font=dict(size=16, color="#e8edd0"),
                    showarrow=False,
                )],
            )
            st.plotly_chart(fig_donut, use_container_width=True, key="chart_donut_status")

        with col_p2:
            # Scatter horímetro atual vs próxima troca
            fig_sc = px.scatter(
                df_lub.dropna(subset=["h_atual", "h_proxima_troca"]),
                x="h_atual",
                y="h_proxima_troca",
                color="status_troca",
                text="vehicle",
                size_max=12,
                color_discrete_map=color_seq,
                labels={"h_atual": "Horímetro Atual (h)", "h_proxima_troca": "Próxima Troca (h)"},
                title="Horímetro Atual × Próxima Troca",
            )
            fig_sc.update_traces(textposition="top center", textfont=dict(size=9, color="#e8edd0"))
            fig_sc.add_shape(
                type="line",
                x0=df_lub["h_atual"].min(), y0=df_lub["h_atual"].min(),
                x1=df_lub["h_atual"].max(), y1=df_lub["h_atual"].max(),
                line=dict(color="#c0392b", dash="dash", width=1),
            )
            fig_sc.update_layout(**PLOTLY_DARK, height=320,
                                  legend=dict(font=dict(color="#e8edd0")))
            st.plotly_chart(fig_sc, use_container_width=True, key="chart_scatter_lub")

    # Timeline de trocas
    if not df_lub.empty:
        st.markdown('<div class="section-title">Timeline — Última Troca de Óleo</div>',
                    unsafe_allow_html=True)

        df_tl = df_lub.dropna(subset=["data_ultima_troca"]).copy()
        df_tl["data_fim"] = df_tl["data_ultima_troca"] + pd.Timedelta(days=7)

        color_seq_tl = {"OK": "#4a9e3f", "PROXIMO": "#d4a017", "EM ATRASO": "#c0392b"}
        fig_gantt = px.timeline(
            df_tl.sort_values("data_ultima_troca"),
            x_start="data_ultima_troca",
            x_end="data_fim",
            y="vehicle",
            color="status_troca",
            color_discrete_map=color_seq_tl,
            labels={"vehicle": "Frota", "data_ultima_troca": "Data Troca"},
        )
        fig_gantt.update_layout(**PLOTLY_DARK, height=max(300, len(df_tl) * 22),
                                 legend=dict(font=dict(color="#e8edd0")))
        fig_gantt.update_yaxes(tickfont=dict(color="#e8edd0", size=10))
        st.plotly_chart(fig_gantt, use_container_width=True, key="chart_gantt")

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.divider()
st.markdown(
    "<div style='text-align:center;font-size:11px;color:#4a6644;'>"
    "Santa Vergínia Agropecuária e Florestal · Controladoria · Gestor Oficina</div>",
    unsafe_allow_html=True,
)
