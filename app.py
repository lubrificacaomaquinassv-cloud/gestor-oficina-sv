import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime, timedelta

st.set_page_config(page_title="Gestor Oficina — Santa Vergínia", layout="wide", page_icon="🔧")

st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:#0a1409;}
[data-testid="stSidebar"]{background:#111c10;border-right:1px solid #1e2e1c;}
[data-testid="stHeader"]{background:#0a1409;}
h1,h2,h3{color:#e8edd0;font-family:'Barlow Condensed',sans-serif;letter-spacing:2px;}
.sec{font-family:'Barlow Condensed',sans-serif;font-size:12px;font-weight:700;
  letter-spacing:2px;text-transform:uppercase;color:#8aab80;
  border-left:4px solid #4a9e3f;padding-left:10px;margin:18px 0 10px;}
.stTabs [data-baseweb="tab-list"]{background:#111c10;border-bottom:2px solid #1e2e1c;gap:0;}
.stTabs [data-baseweb="tab"]{color:#4a6644;font-family:'Barlow Condensed',sans-serif;
  font-size:12px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;
  padding:10px 20px;border-bottom:3px solid transparent;}
.stTabs [aria-selected="true"]{color:#6fcf60!important;border-bottom:3px solid #4a9e3f!important;}
div[data-testid="metric-container"]{background:#111c10;border:1px solid #1e2e1c;border-radius:10px;padding:14px;}
div[data-testid="metric-container"] label{color:#8aab80!important;font-size:11px!important;}
div[data-testid="metric-container"] [data-testid="stMetricValue"]{color:#e8edd0!important;}
</style>
""", unsafe_allow_html=True)

PDARK = dict(paper_bgcolor='#111c10', plot_bgcolor='#0d180c',
             font=dict(color='#8aab80', family='Barlow Condensed'),
             margin=dict(l=10, r=10, t=30, b=10))

# ── CONEXÃO ──────────────────────────────────────────────────
from st_supabase_connection import SupabaseConnection
conn = st.connection("supabase", type=SupabaseConnection, ttl=300)

def sb(table):
    try:
        r = conn.client.table(table).select("*").execute()
    except Exception:
        r = conn.query("*", table=table).execute()
    return pd.DataFrame(r.data)

# ── CARGA ─────────────────────────────────────────────────────
@st.cache_data(ttl=120, show_spinner=False)
def load_os(_c):
    df = sb("ordem_servico")
    if df.empty: return df
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True).dt.tz_convert("America/Campo_Grande")
    df["data"] = df["created_at"].dt.date
    df["tempo_min"] = pd.to_numeric(df["tempo_min"], errors="coerce").fillna(0)
    return df

@st.cache_data(ttl=120, show_spinner=False)
def load_bor(_c):
    df = sb("os_borracharia")
    if df.empty: return df
    df["criado_em"] = pd.to_datetime(df["criado_em"], errors="coerce")
    df["data"] = df["criado_em"].dt.date
    df["tempo_minutos"] = pd.to_numeric(df["tempo_minutos"], errors="coerce").fillna(0)
    return df

@st.cache_data(ttl=120, show_spinner=False)
def load_lub(_c):
    df = sb("vw_proxima_troca_v4")
    if df.empty: return df
    for col in ["horas_restantes","h_atual","h_proxima_troca","h_na_troca"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["data_ultima_troca"] = pd.to_datetime(df["data_ultima_troca"], errors="coerce")
    df["data_ultimo_apontamento"] = pd.to_datetime(df["data_ultimo_apontamento"], errors="coerce")
    return df

@st.cache_data(ttl=120, show_spinner=False)
def load_abast(_c):
    df = sb("vw_abastecimento_consolidado")
    if df.empty: return df
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True).dt.tz_convert("America/Campo_Grande")
    df["data"] = df["created_at"].dt.date
    df["liters"] = pd.to_numeric(df["liters"], errors="coerce").fillna(0)
    return df

@st.cache_data(ttl=120, show_spinner=False)
def load_transf(_c):
    df = sb("combustivel_transferencia")
    if df.empty: return df
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df["quantidade_l"] = pd.to_numeric(df["quantidade_l"], errors="coerce").fillna(0)
    return df

def fmt(n, dec=0):
    if pd.isna(n): return "—"
    return f"{n:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ── HEADER ────────────────────────────────────────────────────
c1, c2, c3 = st.columns([1, 8, 2])
with c1:
    st.markdown("<div style='background:#1a2e18;border:1px solid #1e2e1c;border-radius:8px;"
                "width:52px;height:52px;display:flex;align-items:center;justify-content:center;"
                "font-family:Barlow Condensed,sans-serif;font-weight:800;font-size:18px;"
                "color:#6fcf60;margin-top:4px'>SV</div>", unsafe_allow_html=True)
with c2:
    st.markdown("<div style='font-family:Barlow Condensed,sans-serif;font-weight:800;font-size:22px;"
                "letter-spacing:2px;color:#e8edd0;'>GESTOR DA OFICINA — SANTA VERGÍNIA</div>"
                "<div style='font-size:11px;color:#8aab80;letter-spacing:1px;'>"
                "OS · Lubrificação · Borracharia · Comboio · Tempo Real</div>",
                unsafe_allow_html=True)
with c3:
    if st.button("🔄 Atualizar", key="refresh"):
        st.cache_data.clear(); st.rerun()
    st.caption(datetime.now().strftime("%d/%m/%Y %H:%M"))

st.divider()

df_os    = load_os(conn)
df_bor   = load_bor(conn)
df_lub   = load_lub(conn)
df_abast = load_abast(conn)
df_transf= load_transf(conn)

hoje = date.today()
mes_ini = hoje.replace(day=1)

tab1, tab2, tab3 = st.tabs(["🔧 Ordens de Serviço", "🛢 Lubrificação & Borracharia", "⛽ Comboio"])

# ══════════════════════════════════════════════════════════════
# TAB 1 — OS
# ══════════════════════════════════════════════════════════════
with tab1:
    if df_os.empty:
        st.warning("Sem dados de OS.")
    else:
        os_hoje = df_os[df_os["data"] == hoje]
        os_mes  = df_os[df_os["data"] >= mes_ini]
        os_aberto = df_os[df_os["status"].str.upper().str.contains("ABERTO|EM ANDAMENTO", na=False)]

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("🔧 OS Hoje",         len(os_hoje))
        c2.metric("📋 OS no Mês",        len(os_mes))
        c3.metric("🔴 Em Aberto",        len(os_aberto))
        c4.metric("✅ Finalizadas Mês",  len(os_mes[os_mes["status"].str.upper().str.contains("FINAL", na=False)]))

        # ── 5 OS do dia ──
        st.markdown('<div class="sec">OS registradas hoje</div>', unsafe_allow_html=True)
        if os_hoje.empty:
            st.info("Nenhuma OS registrada hoje.")
        else:
            cols_show = [c for c in ["numero_os","id_frota","sistema","tipo_manutencao","status","mecanico","descricao"] if c in os_hoje.columns]
            df_show = os_hoje.sort_values("created_at", ascending=False).head(5)[cols_show].copy()
            df_show.columns = [c.replace("_"," ").title() for c in cols_show]

            def color_status(val):
                v = str(val).upper()
                if "FINAL" in v: return "color:#6fcf60"
                if "ABERTO" in v or "ANDAMENTO" in v: return "color:#e74c3c"
                return "color:#d4a017"

            st.dataframe(df_show, use_container_width=True, hide_index=True,
                         height=min(250, 55 + len(df_show)*38), key="tbl_os_hoje")

        # ── OS em aberto ──
        if not os_aberto.empty:
            st.markdown('<div class="sec">OS em aberto</div>', unsafe_allow_html=True)
            cols_ab = [c for c in ["numero_os","id_frota","sistema","tipo_manutencao","mecanico","created_at"] if c in os_aberto.columns]
            df_ab = os_aberto.sort_values("created_at").head(10)[cols_ab].copy()
            if "created_at" in df_ab.columns:
                df_ab["created_at"] = df_ab["created_at"].dt.strftime("%d/%m %H:%M")
            df_ab.columns = [c.replace("_"," ").title() for c in cols_ab]
            st.dataframe(df_ab, use_container_width=True, hide_index=True,
                         height=min(300, 55 + len(df_ab)*38), key="tbl_os_aberto")

        # ── Rankings ──
        col_r1, col_r2 = st.columns(2)

        with col_r1:
            st.markdown('<div class="sec">Ocorrências mais solicitadas</div>', unsafe_allow_html=True)
            if "sistema" in os_mes.columns:
                rank_sis = os_mes.groupby("sistema").size().reset_index(name="qtd").sort_values("qtd", ascending=True).tail(8)
                fig1 = go.Figure(go.Bar(
                    y=rank_sis["sistema"], x=rank_sis["qtd"], orientation="h",
                    marker_color="#2980b9",
                    text=rank_sis["qtd"], textposition="outside",
                    textfont=dict(color="#e8edd0", size=12),
                ))
                fig1.update_layout(**PDARK, height=280,
                                   xaxis_gridcolor="#1e2e1c",
                                   yaxis_gridcolor="#1e2e1c",
                                   yaxis_tickfont=dict(color="#e8edd0", size=11))
                st.plotly_chart(fig1, use_container_width=True, key="chart_rank_sis")

        with col_r2:
            st.markdown('<div class="sec">Equipamentos com mais OS</div>', unsafe_allow_html=True)
            if "id_frota" in os_mes.columns:
                rank_frota = os_mes.groupby("id_frota").size().reset_index(name="qtd").sort_values("qtd", ascending=True).tail(8)
                fig2 = go.Figure(go.Bar(
                    y=rank_frota["id_frota"], x=rank_frota["qtd"], orientation="h",
                    marker_color="#c0392b",
                    text=rank_frota["qtd"], textposition="outside",
                    textfont=dict(color="#e8edd0", size=12),
                ))
                fig2.update_layout(**PDARK, height=280,
                                   xaxis_gridcolor="#1e2e1c",
                                   yaxis_gridcolor="#1e2e1c",
                                   yaxis_tickfont=dict(color="#e8edd0", size=11))
                st.plotly_chart(fig2, use_container_width=True, key="chart_rank_frota")

        # ── Tipo manutenção ──
        st.markdown('<div class="sec">Corretiva × Preventiva no mês</div>', unsafe_allow_html=True)
        if "tipo_manutencao" in os_mes.columns:
            tipo_cnt = os_mes["tipo_manutencao"].value_counts().reset_index()
            tipo_cnt.columns = ["tipo","qtd"]
            colors = {"CORRETIVA":"#c0392b","PREVENTIVA":"#4a9e3f"}
            fig3 = go.Figure(go.Bar(
                x=tipo_cnt["tipo"], y=tipo_cnt["qtd"],
                marker_color=[colors.get(str(t).upper(), "#2980b9") for t in tipo_cnt["tipo"]],
                text=tipo_cnt["qtd"], textposition="outside",
                textfont=dict(color="#e8edd0", size=13),
            ))
            fig3.update_layout(**PDARK, height=220,
                               xaxis_gridcolor="#1e2e1c",
                               yaxis_gridcolor="#1e2e1c",
                               xaxis_tickfont=dict(color="#e8edd0", size=12))
            st.plotly_chart(fig3, use_container_width=True, key="chart_tipo_manut")

# ══════════════════════════════════════════════════════════════
# TAB 2 — LUBRIFICAÇÃO & BORRACHARIA
# ══════════════════════════════════════════════════════════════
with tab2:
    col_l, col_b = st.columns(2)

    # ── BORRACHARIA ──
    with col_b:
        st.markdown('<div class="sec">Borracharia — OS recentes</div>', unsafe_allow_html=True)
        if df_bor.empty:
            st.info("Sem registros de borracharia.")
        else:
            bor_kpi1, bor_kpi2 = st.columns(2)
            bor_kpi1.metric("OS Borracharia Mês", len(df_bor[df_bor["data"] >= mes_ini]))
            bor_kpi2.metric("Hoje", len(df_bor[df_bor["data"] == hoje]))

            cols_bor = [c for c in ["numero_os","id_frota","tipo_manutencao","borracheiro","status","descricao","criado_em"] if c in df_bor.columns]
            df_bor_show = df_bor.sort_values("criado_em", ascending=False).head(5)[cols_bor].copy()
            if "criado_em" in df_bor_show.columns:
                df_bor_show["criado_em"] = pd.to_datetime(df_bor_show["criado_em"]).dt.strftime("%d/%m %H:%M")
            df_bor_show.columns = [c.replace("_"," ").title() for c in cols_bor]
            st.dataframe(df_bor_show, use_container_width=True, hide_index=True,
                         height=min(280, 55+len(df_bor_show)*38), key="tbl_bor")

            # Ranking tipo borracharia
            if "tipo_manutencao" in df_bor.columns:
                st.markdown('<div class="sec">Tipos mais frequentes</div>', unsafe_allow_html=True)
                rank_b = df_bor["tipo_manutencao"].value_counts().reset_index()
                rank_b.columns = ["tipo","qtd"]
                fig_b = go.Figure(go.Bar(
                    x=rank_b["tipo"], y=rank_b["qtd"],
                    marker_color="#d4a017",
                    text=rank_b["qtd"], textposition="outside",
                    textfont=dict(color="#e8edd0", size=12),
                ))
                fig_b.update_layout(**PDARK, height=200,
                                    xaxis_gridcolor="#1e2e1c",
                                    yaxis_gridcolor="#1e2e1c",
                                    xaxis_tickfont=dict(color="#e8edd0", size=11))
                st.plotly_chart(fig_b, use_container_width=True, key="chart_bor_tipo")

    # ── LUBRIFICAÇÃO ──
    with col_l:
        st.markdown('<div class="sec">Lubrificação — horímetros</div>', unsafe_allow_html=True)
        if df_lub.empty:
            st.info("Sem dados de lubrificação.")
        else:
            ok   = (df_lub["status_troca"] == "OK").sum()
            prox = (df_lub["status_troca"] == "PROXIMO").sum()
            atr  = (df_lub["status_troca"] == "EM ATRASO").sum()
            l1,l2,l3 = st.columns(3)
            l1.metric("✅ OK",       ok)
            l2.metric("⚠️ Próximo",  prox)
            l3.metric("🔴 Atrasado", atr)

            # Velocímetros (gauges) — top 6 críticos primeiro
            st.markdown('<div class="sec">Velocímetros — horímetro de troca</div>', unsafe_allow_html=True)
            df_gauge = df_lub.sort_values("horas_restantes", ascending=True).head(6)

            for i in range(0, len(df_gauge), 2):
                gcols = st.columns(2)
                for j, col in enumerate(gcols):
                    idx = i + j
                    if idx >= len(df_gauge): break
                    row = df_gauge.iloc[idx]

                    h_na   = float(row["h_na_troca"])      if pd.notna(row["h_na_troca"])      else 0
                    h_prox = float(row["h_proxima_troca"]) if pd.notna(row["h_proxima_troca"]) else h_na + 250
                    h_at   = float(row["h_atual"])         if pd.notna(row["h_atual"])          else h_na
                    h_rest = float(row["horas_restantes"]) if pd.notna(row["horas_restantes"])  else 0
                    status = str(row["status_troca"])

                    cor = "#c0392b" if status == "EM ATRASO" else "#d4a017" if status == "PROXIMO" else "#4a9e3f"
                    escala_min = max(0, h_na - 50)
                    escala_max = h_prox + max(100, abs(min(0, h_rest)) + 50)

                    fig_g = go.Figure(go.Indicator(
                        mode="gauge+number+delta",
                        value=h_at,
                        number={"suffix":"h","font":{"color":"#e8edd0","size":18}},
                        delta={"reference": h_prox,
                               "valueformat":".0f",
                               "increasing":{"color":"#c0392b"},
                               "decreasing":{"color":"#4a9e3f"},
                               "suffix":"h"},
                        title={"text": f"<b>{row['vehicle']}</b><br>"
                                       f"<span style='font-size:10px;color:#8aab80'>"
                                       f"Troca: {fmt(h_na)}h → {fmt(h_prox)}h · "
                                       f"{'Atrasado' if h_rest<0 else 'Restam'}: {fmt(abs(h_rest))}h</span>",
                               "font":{"color":"#e8edd0","size":12}},
                        gauge={
                            "axis":{"range":[escala_min, escala_max],
                                    "tickcolor":"#4a6644","tickfont":{"color":"#4a6644","size":9}},
                            "bar":{"color":cor,"thickness":0.25},
                            "bgcolor":"#0d180c",
                            "bordercolor":"#1e2e1c",
                            "steps":[
                                {"range":[escala_min, h_prox-100], "color":"#1a3318"},
                                {"range":[h_prox-100, h_prox],     "color":"#2a2200"},
                                {"range":[h_prox, escala_max],     "color":"#2a1010"},
                            ],
                            "threshold":{"line":{"color":"#c0392b","width":3},
                                         "thickness":0.8,"value":h_prox},
                        }
                    ))
                    fig_g.update_layout(
                        paper_bgcolor="#111c10", plot_bgcolor="#111c10",
                        height=200, margin=dict(l=10,r=10,t=55,b=5)
                    )
                    with col:
                        st.plotly_chart(fig_g, use_container_width=True,
                                        key=f"gauge_{row['vehicle']}_{idx}")

            # Tabela resumo lubrificação
            st.markdown('<div class="sec">Lista completa — ordenada por urgência</div>', unsafe_allow_html=True)
            def badge_st(s):
                m = {"OK":"🟢","PROXIMO":"🟡","EM ATRASO":"🔴"}
                return f"{m.get(s,'⚪')} {s}"

            df_lub_tbl = df_lub[["vehicle","h_na_troca","h_proxima_troca",
                                  "h_atual","horas_restantes","status_troca"]].copy()
            df_lub_tbl["horas_restantes"] = df_lub_tbl["horas_restantes"].apply(
                lambda v: f"{v:+.0f}h" if pd.notna(v) else "—")
            df_lub_tbl["status_troca"] = df_lub_tbl["status_troca"].apply(badge_st)
            df_lub_tbl.columns = ["Frota","H.Troca","Próxima(h)","H.Atual","Restante","Status"]
            st.dataframe(df_lub_tbl, use_container_width=True, hide_index=True,
                         height=300, key="tbl_lub_full")

# ══════════════════════════════════════════════════════════════
# TAB 3 — COMBOIO
# ══════════════════════════════════════════════════════════════
with tab3:
    CAP = 5000

    if df_abast.empty and df_transf.empty:
        st.warning("Sem dados de comboio.")
    else:
        # Calcular saldo
        transf_comboio = df_transf[df_transf["destino"].str.upper().str.contains("COMBOIO", na=False)] if not df_transf.empty else pd.DataFrame()
        total_rec  = transf_comboio["quantidade_l"].sum() if not transf_comboio.empty else 0
        total_dist = df_abast["liters"].sum() if not df_abast.empty else 0
        saldo      = max(0, total_rec - total_dist)
        pct        = min(100, (saldo / CAP) * 100) if CAP > 0 else 0

        cor_saldo = "#c0392b" if pct <= 20 else "#d4a017" if pct <= 40 else "#4a9e3f"

        # KPIs
        k1,k2,k3,k4 = st.columns(4)
        k1.metric("🛢 Saldo Comboio",   f"{fmt(saldo)} L", f"{pct:.1f}% de {fmt(CAP)} L")
        k2.metric("📥 Total Recebido",  f"{fmt(total_rec)} L")
        k3.metric("📤 Total Distribuído", f"{fmt(total_dist)} L")
        abast_hoje_cb = df_abast[df_abast["data"] == hoje] if not df_abast.empty else pd.DataFrame()
        k4.metric("⛽ Litros Hoje",     f"{fmt(abast_hoje_cb['liters'].sum())} L",
                  f"{len(abast_hoje_cb)} eventos")

        # Gauge tanque
        st.markdown('<div class="sec">Nível do tanque comboio — 5.000 L</div>', unsafe_allow_html=True)
        fig_tank = go.Figure(go.Indicator(
            mode="gauge+number",
            value=pct,
            number={"suffix":"%","font":{"color":"#e8edd0","size":28}},
            title={"text":f"<b>Saldo: {fmt(saldo)} L</b><br>"
                          f"<span style='font-size:12px;color:#8aab80'>"
                          f"Recebido: {fmt(total_rec)} L · Distribuído: {fmt(total_dist)} L</span>",
                   "font":{"color":"#e8edd0","size":14}},
            gauge={
                "axis":{"range":[0,100],"ticksuffix":"%","tickcolor":"#4a6644",
                        "tickfont":{"color":"#4a6644","size":10}},
                "bar":{"color":cor_saldo,"thickness":0.3},
                "bgcolor":"#0d180c","bordercolor":"#1e2e1c",
                "steps":[
                    {"range":[0,20],  "color":"#2a1010"},
                    {"range":[20,40], "color":"#2a2200"},
                    {"range":[40,100],"color":"#1a3318"},
                ],
                "threshold":{"line":{"color":"#e74c3c","width":3},"thickness":0.8,"value":20},
            }
        ))
        fig_tank.update_layout(paper_bgcolor="#111c10",plot_bgcolor="#111c10",
                               height=280, margin=dict(l=30,r=30,t=60,b=10))
        st.plotly_chart(fig_tank, use_container_width=True, key="gauge_tanque")

        col_c1, col_c2 = st.columns(2)

        # ── 10 abastecimentos do dia ──
        with col_c1:
            st.markdown('<div class="sec">Abastecimentos hoje</div>', unsafe_allow_html=True)
            if abast_hoje_cb.empty:
                st.info("Nenhum abastecimento registrado hoje.")
            else:
                cols_ab = [c for c in ["created_at","vehicle","operator","fuel_type","liters","hourmeter"] if c in abast_hoje_cb.columns]
                df_ab_show = abast_hoje_cb.sort_values("created_at", ascending=False).head(10)[cols_ab].copy()
                if "created_at" in df_ab_show.columns:
                    df_ab_show["created_at"] = df_ab_show["created_at"].dt.strftime("%H:%M")
                df_ab_show.columns = [c.replace("_"," ").title() for c in cols_ab]
                st.dataframe(df_ab_show, use_container_width=True, hide_index=True,
                             height=min(380, 55+len(df_ab_show)*38), key="tbl_abast_hoje")

        # ── 3 últimas transferências posto → comboio ──
        with col_c2:
            st.markdown('<div class="sec">Últimas transferências posto → comboio</div>', unsafe_allow_html=True)
            if transf_comboio.empty:
                st.info("Nenhuma transferência registrada.")
            else:
                cols_tr = [c for c in ["data","combustivel","origem","quantidade_l","observacao"] if c in transf_comboio.columns]
                df_tr = transf_comboio.sort_values("data", ascending=False).head(3)[cols_tr].copy()
                if "data" in df_tr.columns:
                    df_tr["data"] = pd.to_datetime(df_tr["data"]).dt.strftime("%d/%m/%Y")
                df_tr.columns = [c.replace("_"," ").title() for c in cols_tr]
                st.dataframe(df_tr, use_container_width=True, hide_index=True,
                             height=180, key="tbl_transf")

            # Volume por frota no mês
            st.markdown('<div class="sec">Volume por frota no mês (L)</div>', unsafe_allow_html=True)
            if not df_abast.empty:
                df_mes_ab = df_abast[df_abast["data"] >= mes_ini]
                if not df_mes_ab.empty and "vehicle" in df_mes_ab.columns:
                    pf = df_mes_ab.groupby("vehicle")["liters"].sum().reset_index()
                    pf = pf.sort_values("liters", ascending=True).tail(8)
                    fig_vol = go.Figure(go.Bar(
                        y=pf["vehicle"], x=pf["liters"], orientation="h",
                        marker_color="#4a9e3f",
                        text=pf["liters"].apply(lambda v: f"{v:,.0f}L"),
                        textposition="outside",
                        textfont=dict(color="#e8edd0", size=11),
                    ))
                    fig_vol.update_layout(**PDARK, height=250,
                                         xaxis_gridcolor="#1e2e1c",
                                         yaxis_gridcolor="#1e2e1c",
                                         yaxis_tickfont=dict(color="#e8edd0", size=11))
                    st.plotly_chart(fig_vol, use_container_width=True, key="chart_vol_frota")

st.divider()
st.markdown("<div style='text-align:center;font-size:11px;color:#4a6644;'>"
            "Santa Vergínia Agropecuária e Florestal · Controladoria · Gestor Oficina</div>",
            unsafe_allow_html=True)
