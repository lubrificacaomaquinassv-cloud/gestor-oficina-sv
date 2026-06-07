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
/* Tabelas escuras */
[data-testid="stDataFrame"] iframe{background:#111c10!important;}
div[data-testid="stDataFrameResizable"]{background:#111c10;border:1px solid #1e2e1c;border-radius:8px;}
</style>
""", unsafe_allow_html=True)

PDARK = dict(paper_bgcolor='#111c10', plot_bgcolor='#0d180c',
             font=dict(color='#8aab80', family='Barlow Condensed'),
             margin=dict(l=10, r=10, t=30, b=10))

TABLE_CFG = dict(use_container_width=True, hide_index=True)

from st_supabase_connection import SupabaseConnection
conn = st.connection("supabase", type=SupabaseConnection, ttl=300)

def sb(table):
    try:
        r = conn.client.table(table).select("*").execute()
    except Exception:
        r = conn.query("*", table=table).execute()
    return pd.DataFrame(r.data)

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

@st.cache_data(ttl=120, show_spinner=False)
def load_disp(_c):
    df = sb("vw_disponibilidade_frota")
    if df.empty: return df
    df["mes"] = pd.to_datetime(df["mes"], errors="coerce", utc=True)
    for col in ["dias_com_apontamento","horas_trabalhadas","horas_parada","disponibilidade_pct","total_os"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df

def fmt(n, dec=0):
    if pd.isna(n): return "—"
    return f"{n:,.{dec}f}".replace(",","X").replace(".",",").replace("X",".")

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
                "OS · Lubrificação · Borracharia · Comboio · Disponibilidade · Tempo Real</div>",
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
df_disp  = load_disp(conn)

hoje    = date.today()
mes_ini = hoje.replace(day=1)

tab1, tab2, tab3, tab4 = st.tabs([
    "🔧 Ordens de Serviço",
    "🛢 Lubrificação & Borracharia",
    "⛽ Comboio",
    "📊 Parado × Operando",
])

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
        c1.metric("🔧 OS Hoje",        len(os_hoje))
        c2.metric("📋 OS no Mês",       len(os_mes))
        c3.metric("🔴 Em Aberto",       len(os_aberto))
        c4.metric("✅ Finalizadas Mês", len(os_mes[os_mes["status"].str.upper().str.contains("FINAL", na=False)]))

        # 5 OS do dia — se não houver hoje, mostra as 5 últimas
        st.markdown('<div class="sec">OS registradas hoje (ou últimas 5)</div>', unsafe_allow_html=True)
        df_os_show = os_hoje if not os_hoje.empty else df_os
        cols_os = [c for c in ["numero_os","id_frota","sistema","tipo_manutencao","status","mecanico","descricao"] if c in df_os_show.columns]
        df_os_tbl = df_os_show.sort_values("created_at", ascending=False).head(5)[cols_os].copy()
        df_os_tbl.columns = [c.replace("_"," ").title() for c in cols_os]

        if os_hoje.empty:
            st.caption("⚠️ Sem OS hoje — exibindo as 5 últimas registradas.")

        st.dataframe(df_os_tbl, **TABLE_CFG,
                     height=min(260, 55+len(df_os_tbl)*38), key="tbl_os_hoje")

        # OS em aberto
        if not os_aberto.empty:
            st.markdown('<div class="sec">OS em aberto</div>', unsafe_allow_html=True)
            cols_ab = [c for c in ["numero_os","id_frota","sistema","tipo_manutencao","mecanico","created_at"] if c in os_aberto.columns]
            df_ab = os_aberto.sort_values("created_at").head(10)[cols_ab].copy()
            if "created_at" in df_ab.columns:
                df_ab["created_at"] = df_ab["created_at"].dt.strftime("%d/%m %H:%M")
            df_ab.columns = [c.replace("_"," ").title() for c in cols_ab]
            st.dataframe(df_ab, **TABLE_CFG,
                         height=min(300, 55+len(df_ab)*38), key="tbl_os_aberto")

        # Rankings
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown('<div class="sec">Ocorrências mais solicitadas</div>', unsafe_allow_html=True)
            if "sistema" in os_mes.columns and not os_mes.empty:
                rank_sis = os_mes.groupby("sistema").size().reset_index(name="qtd").sort_values("qtd", ascending=True).tail(8)
                fig1 = go.Figure(go.Bar(
                    y=rank_sis["sistema"], x=rank_sis["qtd"], orientation="h",
                    marker_color="#2980b9",
                    text=rank_sis["qtd"], textposition="outside",
                    textfont=dict(color="#e8edd0", size=12),
                ))
                fig1.update_layout(**PDARK, height=280,
                                   xaxis_gridcolor="#1e2e1c", yaxis_gridcolor="#1e2e1c",
                                   yaxis_tickfont=dict(color="#e8edd0", size=11))
                st.plotly_chart(fig1, use_container_width=True, key="chart_rank_sis")

        with col_r2:
            st.markdown('<div class="sec">Equipamentos com mais OS</div>', unsafe_allow_html=True)
            if "id_frota" in os_mes.columns and not os_mes.empty:
                rank_frota = os_mes.groupby("id_frota").size().reset_index(name="qtd").sort_values("qtd", ascending=True).tail(8)
                fig2 = go.Figure(go.Bar(
                    y=rank_frota["id_frota"], x=rank_frota["qtd"], orientation="h",
                    marker_color="#c0392b",
                    text=rank_frota["qtd"], textposition="outside",
                    textfont=dict(color="#e8edd0", size=12),
                ))
                fig2.update_layout(**PDARK, height=280,
                                   xaxis_gridcolor="#1e2e1c", yaxis_gridcolor="#1e2e1c",
                                   yaxis_tickfont=dict(color="#e8edd0", size=11))
                st.plotly_chart(fig2, use_container_width=True, key="chart_rank_frota")

        # Corretiva × Preventiva
        st.markdown('<div class="sec">Corretiva × Preventiva no mês</div>', unsafe_allow_html=True)
        if "tipo_manutencao" in os_mes.columns and not os_mes.empty:
            tipo_cnt = os_mes["tipo_manutencao"].value_counts().reset_index()
            tipo_cnt.columns = ["tipo","qtd"]
            colors = {"CORRETIVA":"#c0392b","PREVENTIVA":"#4a9e3f"}
            fig3 = go.Figure(go.Bar(
                x=tipo_cnt["tipo"], y=tipo_cnt["qtd"],
                marker_color=[colors.get(str(t).upper(),"#2980b9") for t in tipo_cnt["tipo"]],
                text=tipo_cnt["qtd"], textposition="outside",
                textfont=dict(color="#e8edd0", size=13),
            ))
            fig3.update_layout(**PDARK, height=220,
                               xaxis_gridcolor="#1e2e1c", yaxis_gridcolor="#1e2e1c",
                               xaxis_tickfont=dict(color="#e8edd0", size=12))
            st.plotly_chart(fig3, use_container_width=True, key="chart_tipo_manut")

# ══════════════════════════════════════════════════════════════
# TAB 2 — LUBRIFICAÇÃO & BORRACHARIA
# ══════════════════════════════════════════════════════════════
with tab2:
    col_l, col_b = st.columns(2)

    with col_l:
        st.markdown('<div class="sec">Lubrificação — horímetros</div>', unsafe_allow_html=True)
        if df_lub.empty:
            st.info("Sem dados de lubrificação.")
        else:
            ok   = (df_lub["status_troca"]=="OK").sum()
            prox = (df_lub["status_troca"]=="PROXIMO").sum()
            atr  = (df_lub["status_troca"]=="EM ATRASO").sum()
            l1,l2,l3 = st.columns(3)
            l1.metric("✅ OK",       ok)
            l2.metric("⚠️ Próximo",  prox)
            l3.metric("🔴 Atrasado", atr)

            st.markdown('<div class="sec">Velocímetros — horímetro de troca</div>', unsafe_allow_html=True)
            df_gauge = df_lub.sort_values("horas_restantes", ascending=True).head(6)

            for i in range(0, len(df_gauge), 2):
                gcols = st.columns(2)
                for j, gcol in enumerate(gcols):
                    idx = i + j
                    if idx >= len(df_gauge): break
                    row = df_gauge.iloc[idx]
                    h_na   = float(row["h_na_troca"])      if pd.notna(row["h_na_troca"])      else 0
                    h_prox = float(row["h_proxima_troca"]) if pd.notna(row["h_proxima_troca"]) else h_na+250
                    h_at   = float(row["h_atual"])         if pd.notna(row["h_atual"])          else h_na
                    h_rest = float(row["horas_restantes"]) if pd.notna(row["horas_restantes"])  else 0
                    status = str(row["status_troca"])
                    cor = "#c0392b" if status=="EM ATRASO" else "#d4a017" if status=="PROXIMO" else "#4a9e3f"
                    escala_min = max(0, h_na-50)
                    escala_max = h_prox + max(100, abs(min(0,h_rest))+50)
                    fig_g = go.Figure(go.Indicator(
                        mode="gauge+number+delta",
                        value=h_at,
                        number={"suffix":"h","font":{"color":"#e8edd0","size":18}},
                        delta={"reference":h_prox,"valueformat":".0f",
                               "increasing":{"color":"#c0392b"},
                               "decreasing":{"color":"#4a9e3f"},
                               "suffix":"h"},
                        title={"text":f"<b>{row['vehicle']}</b><br>"
                                      f"<span style='font-size:10px;color:#8aab80'>"
                                      f"Troca: {fmt(h_na)}h → {fmt(h_prox)}h · "
                                      f"{'Atrasado' if h_rest<0 else 'Restam'}: {fmt(abs(h_rest))}h</span>",
                               "font":{"color":"#e8edd0","size":12}},
                        gauge={
                            "axis":{"range":[escala_min,escala_max],
                                    "tickcolor":"#4a6644","tickfont":{"color":"#4a6644","size":9}},
                            "bar":{"color":cor,"thickness":0.25},
                            "bgcolor":"#0d180c","bordercolor":"#1e2e1c",
                            "steps":[
                                {"range":[escala_min,h_prox-100],"color":"#1a3318"},
                                {"range":[h_prox-100,h_prox],    "color":"#2a2200"},
                                {"range":[h_prox,escala_max],    "color":"#2a1010"},
                            ],
                            "threshold":{"line":{"color":"#c0392b","width":3},
                                         "thickness":0.8,"value":h_prox},
                        }
                    ))
                    fig_g.update_layout(paper_bgcolor="#111c10",plot_bgcolor="#111c10",
                                        height=200,margin=dict(l=10,r=10,t=55,b=5))
                    with gcol:
                        st.plotly_chart(fig_g, use_container_width=True,
                                        key=f"gauge_{row['vehicle']}_{idx}")

            st.markdown('<div class="sec">Lista completa — ordenada por urgência</div>', unsafe_allow_html=True)
            def badge_st(s):
                m={"OK":"🟢","PROXIMO":"🟡","EM ATRASO":"🔴"}
                return f"{m.get(s,'⚪')} {s}"
            df_lub_tbl = df_lub[["vehicle","h_na_troca","h_proxima_troca",
                                  "h_atual","horas_restantes","status_troca"]].copy()
            df_lub_tbl["horas_restantes"] = df_lub_tbl["horas_restantes"].apply(
                lambda v: f"{v:+.0f}h" if pd.notna(v) else "—")
            df_lub_tbl["status_troca"] = df_lub_tbl["status_troca"].apply(badge_st)
            df_lub_tbl.columns = ["Frota","H.Troca","Próxima(h)","H.Atual","Restante","Status"]
            st.dataframe(df_lub_tbl, **TABLE_CFG, height=300, key="tbl_lub_full")

    with col_b:
        st.markdown('<div class="sec">Borracharia — OS recentes</div>', unsafe_allow_html=True)
        if df_bor.empty:
            st.info("Sem registros de borracharia.")
        else:
            bor_kpi1, bor_kpi2 = st.columns(2)
            bor_kpi1.metric("OS Borracharia Mês", len(df_bor[df_bor["data"]>=mes_ini]))
            bor_kpi2.metric("Hoje", len(df_bor[df_bor["data"]==hoje]))

            cols_bor = [c for c in ["numero_os","id_frota","tipo_manutencao","borracheiro","status","descricao","criado_em"] if c in df_bor.columns]
            df_bor_show = df_bor.sort_values("criado_em",ascending=False).head(5)[cols_bor].copy()
            if "criado_em" in df_bor_show.columns:
                df_bor_show["criado_em"] = pd.to_datetime(df_bor_show["criado_em"]).dt.strftime("%d/%m %H:%M")
            df_bor_show.columns = [c.replace("_"," ").title() for c in cols_bor]
            st.dataframe(df_bor_show, **TABLE_CFG,
                         height=min(280,55+len(df_bor_show)*38), key="tbl_bor")

            if "tipo_manutencao" in df_bor.columns:
                st.markdown('<div class="sec">Tipos mais frequentes</div>', unsafe_allow_html=True)
                rank_b = df_bor["tipo_manutencao"].value_counts().reset_index()
                rank_b.columns = ["tipo","qtd"]
                fig_b = go.Figure(go.Bar(
                    x=rank_b["tipo"], y=rank_b["qtd"],
                    marker_color="#d4a017",
                    text=rank_b["qtd"], textposition="outside",
                    textfont=dict(color="#e8edd0",size=12),
                ))
                fig_b.update_layout(**PDARK, height=200,
                                    xaxis_gridcolor="#1e2e1c", yaxis_gridcolor="#1e2e1c",
                                    xaxis_tickfont=dict(color="#e8edd0",size=11))
                st.plotly_chart(fig_b, use_container_width=True, key="chart_bor_tipo")

# ══════════════════════════════════════════════════════════════
# TAB 3 — COMBOIO
# ══════════════════════════════════════════════════════════════
with tab3:
    CAP = 5000
    transf_cb = df_transf[df_transf["destino"].str.upper().str.contains("COMBOIO",na=False)] if not df_transf.empty else pd.DataFrame()
    total_rec  = transf_cb["quantidade_l"].sum() if not transf_cb.empty else 0
    total_dist = df_abast["liters"].sum() if not df_abast.empty else 0
    saldo      = max(0, total_rec - total_dist)
    pct        = min(100,(saldo/CAP)*100) if CAP>0 else 0
    cor_saldo  = "#c0392b" if pct<=20 else "#d4a017" if pct<=40 else "#4a9e3f"
    abast_hoje_cb = df_abast[df_abast["data"]==hoje] if not df_abast.empty else pd.DataFrame()

    k1,k2,k3,k4 = st.columns(4)
    k1.metric("🛢 Saldo Comboio",    f"{fmt(saldo)} L", f"{pct:.1f}% de {fmt(CAP)} L")
    k2.metric("📥 Total Recebido",   f"{fmt(total_rec)} L")
    k3.metric("📤 Total Distribuído",f"{fmt(total_dist)} L")
    k4.metric("⛽ Litros Hoje",      f"{fmt(abast_hoje_cb['liters'].sum())} L",
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
                           height=280,margin=dict(l=30,r=30,t=60,b=10))
    st.plotly_chart(fig_tank, use_container_width=True, key="gauge_tanque")

    col_c1, col_c2 = st.columns(2)

    with col_c1:
        st.markdown('<div class="sec">Abastecimentos hoje (top 10)</div>', unsafe_allow_html=True)
        if abast_hoje_cb.empty:
            st.info("Nenhum abastecimento registrado hoje.")
        else:
            cols_ab = [c for c in ["created_at","vehicle","operator","fuel_type","liters","hourmeter"] if c in abast_hoje_cb.columns]
            df_ab_show = abast_hoje_cb.sort_values("created_at",ascending=False).head(10)[cols_ab].copy()
            if "created_at" in df_ab_show.columns:
                df_ab_show["created_at"] = df_ab_show["created_at"].dt.strftime("%H:%M")
            df_ab_show.columns = [c.replace("_"," ").title() for c in cols_ab]
            st.dataframe(df_ab_show, **TABLE_CFG,
                         height=min(380,55+len(df_ab_show)*38), key="tbl_abast_hoje")

    with col_c2:
        st.markdown('<div class="sec">Últimas 3 transferências posto → comboio</div>', unsafe_allow_html=True)
        if transf_cb.empty:
            st.info("Nenhuma transferência registrada.")
        else:
            cols_tr = [c for c in ["data","combustivel","origem","quantidade_l","observacao"] if c in transf_cb.columns]
            df_tr = transf_cb.sort_values("data",ascending=False).head(3)[cols_tr].copy()
            if "data" in df_tr.columns:
                df_tr["data"] = pd.to_datetime(df_tr["data"]).dt.strftime("%d/%m/%Y")
            if "quantidade_l" in df_tr.columns:
                df_tr["quantidade_l"] = df_tr["quantidade_l"].apply(lambda v: f"{fmt(v)} L")
            df_tr.columns = [c.replace("_"," ").title() for c in cols_tr]
            st.dataframe(df_tr, **TABLE_CFG, height=180, key="tbl_transf")

        st.markdown('<div class="sec">Volume por frota no mês (L)</div>', unsafe_allow_html=True)
        if not df_abast.empty:
            df_mes_ab = df_abast[df_abast["data"]>=mes_ini]
            if not df_mes_ab.empty and "vehicle" in df_mes_ab.columns:
                pf = df_mes_ab.groupby("vehicle")["liters"].sum().reset_index()
                pf = pf.sort_values("liters",ascending=True).tail(8)
                fig_vol = go.Figure(go.Bar(
                    y=pf["vehicle"], x=pf["liters"], orientation="h",
                    marker_color="#4a9e3f",
                    text=pf["liters"].apply(lambda v: f"{v:,.0f}L"),
                    textposition="outside",
                    textfont=dict(color="#e8edd0",size=11),
                ))
                fig_vol.update_layout(**PDARK, height=250,
                                      xaxis_gridcolor="#1e2e1c", yaxis_gridcolor="#1e2e1c",
                                      yaxis_tickfont=dict(color="#e8edd0",size=11))
                st.plotly_chart(fig_vol, use_container_width=True, key="chart_vol_frota")

# ══════════════════════════════════════════════════════════════
# TAB 4 — PARADO × OPERANDO
# ══════════════════════════════════════════════════════════════
with tab4:
    if df_disp.empty:
        st.warning("Sem dados de disponibilidade.")
    else:
        # Mês atual
        df_disp_mes = df_disp[df_disp["mes"].dt.month == hoje.month]
        if df_disp_mes.empty:
            df_disp_mes = df_disp  # fallback: todos os dados

        # KPIs gerais
        disp_media = df_disp_mes["disponibilidade_pct"].mean()
        ht_total   = df_disp_mes["horas_trabalhadas"].sum()
        hp_total   = df_disp_mes["horas_parada"].sum()
        criticos   = (df_disp_mes["disponibilidade_pct"] < 70).sum()

        k1,k2,k3,k4 = st.columns(4)
        k1.metric("📊 Disponib. Média",  f"{disp_media:.1f}%")
        k2.metric("⚙️ Horas Trabalhadas",f"{fmt(ht_total)}h")
        k3.metric("🔴 Horas Paradas",    f"{fmt(hp_total)}h")
        k4.metric("⚠️ Equip. Críticos",  criticos, help="Disponibilidade abaixo de 70%")

        # Gauge disponibilidade geral
        st.markdown('<div class="sec">Disponibilidade geral da frota</div>', unsafe_allow_html=True)
        cor_disp = "#c0392b" if disp_media<70 else "#d4a017" if disp_media<85 else "#4a9e3f"
        fig_disp_g = go.Figure(go.Indicator(
            mode="gauge+number",
            value=round(disp_media,1),
            number={"suffix":"%","font":{"color":"#e8edd0","size":32}},
            title={"text":"<b>Disponibilidade Média da Frota</b>",
                   "font":{"color":"#e8edd0","size":14}},
            gauge={
                "axis":{"range":[0,100],"ticksuffix":"%",
                        "tickcolor":"#4a6644","tickfont":{"color":"#4a6644","size":10}},
                "bar":{"color":cor_disp,"thickness":0.3},
                "bgcolor":"#0d180c","bordercolor":"#1e2e1c",
                "steps":[
                    {"range":[0,70], "color":"#2a1010"},
                    {"range":[70,85],"color":"#2a2200"},
                    {"range":[85,100],"color":"#1a3318"},
                ],
                "threshold":{"line":{"color":"#d4a017","width":2},"thickness":0.8,"value":85},
            }
        ))
        fig_disp_g.update_layout(paper_bgcolor="#111c10",plot_bgcolor="#111c10",
                                  height=260,margin=dict(l=30,r=30,t=50,b=10))
        st.plotly_chart(fig_disp_g, use_container_width=True, key="gauge_disp_geral")

        col_d1, col_d2 = st.columns(2)

        with col_d1:
            # Barras empilhadas: horas trabalhadas vs paradas por frota
            st.markdown('<div class="sec">Horas trabalhadas × paradas por frota</div>', unsafe_allow_html=True)
            df_d = df_disp_mes.sort_values("horas_trabalhadas", ascending=True).tail(12)
            fig_stack = go.Figure()
            fig_stack.add_trace(go.Bar(
                name="Trabalhadas", y=df_d["id_frota"], x=df_d["horas_trabalhadas"],
                orientation="h", marker_color="#4a9e3f",
                text=df_d["horas_trabalhadas"].apply(lambda v: f"{v:.0f}h"),
                textposition="inside", textfont=dict(color="#e8edd0",size=10),
            ))
            fig_stack.add_trace(go.Bar(
                name="Paradas", y=df_d["id_frota"], x=df_d["horas_parada"],
                orientation="h", marker_color="#c0392b",
                text=df_d["horas_parada"].apply(lambda v: f"{v:.0f}h"),
                textposition="inside", textfont=dict(color="#e8edd0",size=10),
            ))
            fig_stack.update_layout(
                **PDARK, barmode="stack", height=max(300,len(df_d)*28),
                legend=dict(orientation="h",y=1.05,x=0,font=dict(color="#e8edd0")),
                xaxis_gridcolor="#1e2e1c",
                yaxis_gridcolor="#1e2e1c",
                yaxis_tickfont=dict(color="#e8edd0",size=11),
            )
            st.plotly_chart(fig_stack, use_container_width=True, key="chart_horas_stack")

        with col_d2:
            # Disponibilidade % por frota — barras coloridas
            st.markdown('<div class="sec">Disponibilidade % por frota</div>', unsafe_allow_html=True)
            df_d2 = df_disp_mes.sort_values("disponibilidade_pct", ascending=True).tail(12)
            cores_disp = df_d2["disponibilidade_pct"].apply(
                lambda v: "#c0392b" if v<70 else "#d4a017" if v<85 else "#4a9e3f")
            fig_disp_bar = go.Figure(go.Bar(
                y=df_d2["id_frota"], x=df_d2["disponibilidade_pct"],
                orientation="h",
                marker_color=cores_disp.tolist(),
                text=df_d2["disponibilidade_pct"].apply(lambda v: f"{v:.1f}%"),
                textposition="outside",
                textfont=dict(color="#e8edd0",size=11),
            ))
            fig_disp_bar.add_vline(x=85, line_color="#4a9e3f", line_dash="dot", line_width=1,
                                   annotation_text="Meta 85%", annotation_font_color="#4a9e3f",
                                   annotation_position="top right")
            fig_disp_bar.add_vline(x=70, line_color="#c0392b", line_dash="dash", line_width=1,
                                   annotation_text="Crítico 70%", annotation_font_color="#c0392b",
                                   annotation_position="bottom right")
            fig_disp_bar.update_layout(
                **PDARK, height=max(300,len(df_d2)*28),
                xaxis_range=[0,110],
                xaxis_gridcolor="#1e2e1c",
                yaxis_gridcolor="#1e2e1c",
                yaxis_tickfont=dict(color="#e8edd0",size=11),
            )
            st.plotly_chart(fig_disp_bar, use_container_width=True, key="chart_disp_pct")

        # Tabela resumo disponibilidade
        st.markdown('<div class="sec">Resumo por equipamento</div>', unsafe_allow_html=True)
        def badge_disp(v):
            if v < 70:  return f"🔴 {v:.1f}%"
            if v < 85:  return f"🟡 {v:.1f}%"
            return f"🟢 {v:.1f}%"

        df_disp_tbl = df_disp_mes[["id_frota","dias_com_apontamento","horas_trabalhadas",
                                    "horas_parada","disponibilidade_pct","total_os"]].copy()
        df_disp_tbl["disponibilidade_pct"] = df_disp_tbl["disponibilidade_pct"].apply(badge_disp)
        df_disp_tbl["horas_trabalhadas"]   = df_disp_tbl["horas_trabalhadas"].apply(lambda v: f"{v:.0f}h")
        df_disp_tbl["horas_parada"]        = df_disp_tbl["horas_parada"].apply(lambda v: f"{v:.0f}h")
        df_disp_tbl = df_disp_tbl.sort_values("disponibilidade_pct")
        df_disp_tbl.columns = ["Frota","Dias Ativos","H.Trabalhadas","H.Paradas","Disponib.%","OS"]
        st.dataframe(df_disp_tbl, **TABLE_CFG, height=350, key="tbl_disp")

st.divider()
st.markdown("<div style='text-align:center;font-size:11px;color:#4a6644;'>"
            "Santa Vergínia Agropecuária e Florestal · Controladoria · Gestor Oficina</div>",
            unsafe_allow_html=True)
