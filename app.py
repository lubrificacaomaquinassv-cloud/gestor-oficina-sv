import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
import re

st.set_page_config(page_title="Gestor Oficina — Santa Vergínia", layout="wide", page_icon="🔧")

st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:#0a1409;}
[data-testid="stSidebar"]{background:#111c10;border-right:1px solid #1e2e1c;}
[data-testid="stHeader"]{background:#0a1409;}
h1,h2,h3{color:#e8edd0;}
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

PDARK = dict(
    paper_bgcolor='#111c10', plot_bgcolor='#0d180c',
    font=dict(color='#e8edd0', family='Barlow Condensed'),
    margin=dict(l=10, r=10, t=30, b=10)
)

def dark_table(df, height=300):
    rows = "".join(
        "<tr>" + "".join(
            f"<td style='padding:8px 12px;border-bottom:1px solid #1e2e1c;"
            f"color:#e8edd0;font-size:12px;background:#111c10;white-space:nowrap'>{v}</td>"
            for v in row) + "</tr>"
        for _, row in df.iterrows())
    headers = "".join(
        f"<th style='padding:8px 12px;background:#172015;color:#6fcf60;font-size:11px;"
        f"font-weight:700;letter-spacing:1px;text-transform:uppercase;"
        f"border-bottom:2px solid #2d5a2a;white-space:nowrap'>{c}</th>"
        for c in df.columns)
    h_css = f"max-height:{height}px;overflow-y:auto;overflow-x:auto;" if height else "overflow-x:auto;"
    st.markdown(
        f"<div style='background:#111c10;border:1px solid #1e2e1c;border-radius:8px;overflow:hidden;{h_css}'>"
        f"<table style='width:100%;border-collapse:collapse;background:#111c10'>"
        f"<thead><tr>{headers}</tr></thead><tbody>{rows}</tbody></table></div>",
        unsafe_allow_html=True)

from st_supabase_connection import SupabaseConnection
conn = st.connection("supabase", type=SupabaseConnection, ttl=300)

def sb(table):
    try:
        r = conn.client.table(table).select("*").execute()
    except Exception:
        r = conn.query("*", table=table).execute()
    return pd.DataFrame(r.data)

def parse_dt(series):
    """Parse timestamp preservando o offset original (-03)."""
    dt = pd.to_datetime(series, errors="coerce", utc=False)
    try:
        if dt.dt.tz is not None:
            dt = dt.dt.tz_localize(None)
    except Exception:
        pass
    return dt

def is_trator(v):
    """Apenas frotas com exatamente 4 dígitos numéricos."""
    return bool(re.fullmatch(r'\d{4}', str(v).strip()))

@st.cache_data(ttl=120, show_spinner=False)
def load_os(_c):
    df = sb("ordem_servico")
    if df.empty: return df
    df["dt"] = parse_dt(df["created_at"])
    df["data_os"] = df["dt"].dt.date
    df["dt_fmt"] = df["dt"].dt.strftime("%d/%m/%Y %H:%M")
    df["tempo_min"] = pd.to_numeric(df["tempo_min"], errors="coerce").fillna(0)
    return df

@st.cache_data(ttl=120, show_spinner=False)
def load_bor(_c):
    df = sb("os_borracharia")
    if df.empty: return df
    df["dt"] = parse_dt(df["criado_em"])
    df["data_os"] = df["dt"].dt.date
    df["dt_fmt"] = df["dt"].dt.strftime("%d/%m/%Y %H:%M")
    return df

@st.cache_data(ttl=120, show_spinner=False)
def load_lub(_c):
    df = sb("vw_proxima_troca_v4")
    if df.empty: return df
    for col in ["horas_restantes","h_atual","h_proxima_troca","h_na_troca"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

@st.cache_data(ttl=120, show_spinner=False)
def load_abast(_c):
    df = sb("vw_abastecimento_consolidado")
    if df.empty: return df
    df["dt"] = parse_dt(df["created_at"])
    df["data_os"] = df["dt"].dt.date
    df["dt_fmt"] = df["dt"].dt.strftime("%H:%M")
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
    # Usa view filtrada: somente EQUIPAMENTO da dim_frota
    df = sb("vw_disponibilidade_equipamentos")
    if df.empty: return df
    df["mes"] = pd.to_datetime(df["mes"], errors="coerce", utc=False)
    try:
        if df["mes"].dt.tz is not None:
            df["mes"] = df["mes"].dt.tz_localize(None)
    except Exception:
        pass
    for col in ["dias_com_apontamento","horas_trabalhadas","horas_parada","disponibilidade_pct","total_os"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df

def fmt(n, dec=0):
    if pd.isna(n): return "—"
    return f"{n:,.{dec}f}".replace(",","X").replace(".",",").replace("X",".")

# ── HEADER ────────────────────────────────────────────────────
h1, h2, h3 = st.columns([1, 8, 2])
with h1:
    st.markdown("<div style='background:#1a2e18;border:1px solid #1e2e1c;border-radius:8px;"
                "width:52px;height:52px;display:flex;align-items:center;justify-content:center;"
                "font-family:Barlow Condensed,sans-serif;font-weight:800;font-size:18px;"
                "color:#6fcf60;margin-top:4px'>SV</div>", unsafe_allow_html=True)
with h2:
    st.markdown("<div style='font-family:Barlow Condensed,sans-serif;font-weight:800;font-size:22px;"
                "letter-spacing:2px;color:#e8edd0;'>GESTOR DA OFICINA — SANTA VERGÍNIA</div>"
                "<div style='font-size:11px;color:#8aab80;letter-spacing:1px;'>"
                "OS · Lubrificação · Borracharia · Comboio · Disponibilidade</div>",
                unsafe_allow_html=True)
with h3:
    if st.button("🔄 Atualizar", key="refresh"):
        st.cache_data.clear(); st.rerun()
    agora_br = datetime.utcnow() - timedelta(hours=3)
    st.caption(agora_br.strftime("%d/%m/%Y %H:%M") + " (Brasília)")

st.divider()

df_os    = load_os(conn)
df_bor   = load_bor(conn)
df_lub   = load_lub(conn)
df_abast = load_abast(conn)
df_transf= load_transf(conn)
df_disp  = load_disp(conn)

hoje    = (datetime.utcnow() - timedelta(hours=3)).date()
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
        os_hoje = df_os[df_os["data_os"] == hoje]
        os_mes  = df_os[df_os["data_os"] >= mes_ini]
        os_aber = df_os[df_os["status"].str.upper().str.contains("ABERTO|ANDAMENTO|PENDENTE", na=False)]
        os_fin  = os_mes[os_mes["status"].str.upper().str.contains("FINAL", na=False)]

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("🔧 OS Hoje",        len(os_hoje))
        c2.metric(f"📋 OS em {mes_ini.strftime('%b/%Y')}", len(os_mes))
        c3.metric("🔴 Em Aberto/Pendente", len(os_aber))
        c4.metric("✅ Finalizadas no Mês", len(os_fin))

        # OS do dia — se não houver hoje mostra mensagem limpa
        st.markdown('<div class="sec">OS do dia</div>', unsafe_allow_html=True)
        if os_hoje.empty:
            st.info(f"Nenhuma OS registrada hoje ({hoje.strftime('%d/%m/%Y')}). "
                    f"Última OS: {df_os['numero_os'].iloc[0]} em {df_os['dt_fmt'].iloc[0]}")
        else:
            df_t = os_hoje.sort_values("dt", ascending=False)[
                ["numero_os","id_frota","sistema","tipo_manutencao","status","mecanico","dt_fmt"]].copy()
            df_t.columns = ["OS","Frota","Sistema","Tipo","Status","Mecânico","Data/Hora"]
            dark_table(df_t, height=260)

        # OS em aberto sempre visível
        if not os_aber.empty:
            st.markdown('<div class="sec">OS em aberto / pendente</div>', unsafe_allow_html=True)
            df_ab = os_aber.sort_values("dt", ascending=False).head(10)[
                ["numero_os","id_frota","sistema","tipo_manutencao","status","mecanico","dt_fmt"]].copy()
            df_ab.columns = ["OS","Frota","Sistema","Tipo","Status","Mecânico","Abertura"]
            dark_table(df_ab, height=300)

        # Rankings do mês
        if not os_mes.empty:
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.markdown(f'<div class="sec">Sistemas mais acionados — {mes_ini.strftime("%b/%Y")}</div>', unsafe_allow_html=True)
                r = os_mes.groupby("sistema").size().reset_index(name="qtd").sort_values("qtd",ascending=True).tail(8)
                fig = go.Figure(go.Bar(
                    y=r["sistema"], x=r["qtd"], orientation="h",
                    marker_color="#2980b9",
                    text=r["qtd"], textposition="outside",
                    textfont=dict(color="#e8edd0",size=13),
                    hovertemplate="<b>%{y}</b><br>OS: %{x}<extra></extra>"))
                fig.update_layout(**PDARK, height=280,
                    xaxis=dict(gridcolor="#1e2e1c",tickfont=dict(color="#e8edd0")),
                    yaxis=dict(gridcolor="#1e2e1c",tickfont=dict(color="#e8edd0",size=12)))
                st.plotly_chart(fig, use_container_width=True, key="k_sis")

            with col_r2:
                st.markdown(f'<div class="sec">Equipamentos com mais OS — {mes_ini.strftime("%b/%Y")}</div>', unsafe_allow_html=True)
                r = os_mes.groupby("id_frota").size().reset_index(name="qtd").sort_values("qtd",ascending=True).tail(8)
                fig = go.Figure(go.Bar(
                    y=r["id_frota"], x=r["qtd"], orientation="h",
                    marker_color="#c0392b",
                    text=r["qtd"], textposition="outside",
                    textfont=dict(color="#e8edd0",size=13),
                    hovertemplate="<b>Frota %{y}</b><br>OS: %{x}<extra></extra>"))
                fig.update_layout(**PDARK, height=280,
                    xaxis=dict(gridcolor="#1e2e1c",tickfont=dict(color="#e8edd0")),
                    yaxis=dict(gridcolor="#1e2e1c",tickfont=dict(color="#e8edd0",size=12)))
                st.plotly_chart(fig, use_container_width=True, key="k_frota")

            st.markdown(f'<div class="sec">Corretiva × Preventiva — {mes_ini.strftime("%b/%Y")}</div>', unsafe_allow_html=True)
            r = os_mes["tipo_manutencao"].str.upper().value_counts().reset_index()
            r.columns = ["tipo","qtd"]
            cores = {"CORRETIVA":"#c0392b","PREVENTIVA":"#4a9e3f"}
            fig = go.Figure(go.Bar(
                x=r["tipo"], y=r["qtd"],
                marker_color=[cores.get(t,"#2980b9") for t in r["tipo"]],
                text=r["qtd"], textposition="outside",
                textfont=dict(color="#e8edd0",size=14),
                hovertemplate="<b>%{x}</b><br>Quantidade: %{y}<extra></extra>"))
            fig.update_layout(**PDARK, height=220,
                xaxis=dict(gridcolor="#1e2e1c",tickfont=dict(color="#e8edd0",size=13)),
                yaxis=dict(gridcolor="#1e2e1c",tickfont=dict(color="#e8edd0")))
            st.plotly_chart(fig, use_container_width=True, key="k_tipo")

# ══════════════════════════════════════════════════════════════
# TAB 2 — LUBRIFICAÇÃO (em cima) + BORRACHARIA (embaixo)
# ══════════════════════════════════════════════════════════════
with tab2:

    # ── LUBRIFICAÇÃO ── (seção principal, topo)
    st.markdown('<div class="sec">Lubrificação — horímetros de troca de óleo</div>', unsafe_allow_html=True)
    if df_lub.empty:
        st.info("Sem dados de lubrificação.")
    else:
        ok  = (df_lub["status_troca"]=="OK").sum()
        prx = (df_lub["status_troca"]=="PROXIMO").sum()
        atr = (df_lub["status_troca"]=="EM ATRASO").sum()
        l1,l2,l3,l4 = st.columns(4)
        l1.metric("✅ OK",            ok)
        l2.metric("⚠️ Próximo ≤100h", prx)
        l3.metric("🔴 Em Atraso",     atr)
        l4.metric("📋 Total",         len(df_lub))

        # Velocímetros — 3 por linha
        st.markdown('<div class="sec">Velocímetros — ordenados por urgência</div>', unsafe_allow_html=True)
        dg = df_lub.sort_values("horas_restantes", ascending=True).head(9)
        for i in range(0, len(dg), 3):
            cols3 = st.columns(3)
            for j, col in enumerate(cols3):
                idx = i + j
                if idx >= len(dg): break
                row = dg.iloc[idx]
                h_na  = float(row["h_na_troca"])      if pd.notna(row["h_na_troca"])      else 0
                h_prox= float(row["h_proxima_troca"]) if pd.notna(row["h_proxima_troca"]) else h_na+250
                h_at  = float(row["h_atual"])         if pd.notna(row["h_atual"])          else h_na
                h_rest= float(row["horas_restantes"]) if pd.notna(row["horas_restantes"])  else 0
                st_   = str(row["status_troca"])
                cor   = "#c0392b" if st_=="EM ATRASO" else "#d4a017" if st_=="PROXIMO" else "#4a9e3f"
                emin  = max(0, h_na-50)
                emax  = h_prox + max(100, abs(min(0,h_rest))+50)
                fg = go.Figure(go.Indicator(
                    mode="gauge+number+delta", value=h_at,
                    number={"suffix":"h","font":{"color":"#e8edd0","size":18}},
                    delta={"reference":h_prox,"valueformat":".0f",
                           "increasing":{"color":"#c0392b"},
                           "decreasing":{"color":"#4a9e3f"},"suffix":"h"},
                    title={"text":f"<b style='color:#e8edd0'>{row['vehicle']}</b><br>"
                                  f"<span style='font-size:9px;color:#c8d8c0'>"
                                  f"Troca: {fmt(h_na)}h → {fmt(h_prox)}h<br>"
                                  f"{'⚠ Atrasado' if h_rest<0 else '✓ Restam'}: {fmt(abs(h_rest))}h</span>",
                           "font":{"color":"#e8edd0","size":11}},
                    gauge={
                        "axis":{"range":[emin,emax],
                                "tickcolor":"#4a6644","tickfont":{"color":"#c8d8c0","size":8}},
                        "bar":{"color":cor,"thickness":0.3},
                        "bgcolor":"#0d180c","bordercolor":"#1e2e1c",
                        "steps":[
                            {"range":[emin,h_prox-100],"color":"#1a3318"},
                            {"range":[h_prox-100,h_prox],"color":"#2a2200"},
                            {"range":[h_prox,emax],"color":"#2a1010"},
                        ],
                        "threshold":{"line":{"color":"#c0392b","width":3},
                                     "thickness":0.8,"value":h_prox},
                    }
                ))
                fg.update_layout(paper_bgcolor="#111c10",plot_bgcolor="#111c10",
                                 height=190,margin=dict(l=8,r=8,t=60,b=5))
                with col:
                    st.plotly_chart(fg, use_container_width=True, key=f"g_{row['vehicle']}_{idx}")

        # Tabela lubrificação completa
        st.markdown('<div class="sec">Lista completa — ordenada por urgência</div>', unsafe_allow_html=True)
        def badge(s): return {"OK":"🟢 OK","PROXIMO":"🟡 PRÓXIMO","EM ATRASO":"🔴 EM ATRASO"}.get(s,f"⚪ {s}")
        dt = df_lub[["vehicle","h_na_troca","h_proxima_troca","h_atual","horas_restantes","status_troca"]].copy()
        dt["horas_restantes"] = dt["horas_restantes"].apply(lambda v: f"{v:+.0f}h" if pd.notna(v) else "—")
        dt["status_troca"] = dt["status_troca"].apply(badge)
        dt.columns = ["Frota","H. Troca","Próxima (h)","H. Atual","Restante","Status"]
        dark_table(dt, height=300)

    st.divider()

    # ── BORRACHARIA ── (seção secundária, abaixo)
    st.markdown('<div class="sec">Borracharia — OS recentes</div>', unsafe_allow_html=True)
    if df_bor.empty:
        st.info("Sem registros de borracharia.")
    else:
        bk1,bk2,bk3 = st.columns(3)
        bk1.metric("OS no Mês", len(df_bor[df_bor["data_os"]>=mes_ini]))
        bk2.metric("Hoje",      len(df_bor[df_bor["data_os"]==hoje]))
        bk3.metric("Total",     len(df_bor))

        cols_b = [c for c in ["numero_os","id_frota","tipo_manutencao","borracheiro","status","descricao","dt_fmt"] if c in df_bor.columns]
        db = df_bor.sort_values("dt",ascending=False).head(5)[cols_b].copy()
        db.columns = [c.replace("dt_fmt","Data/Hora").replace("_"," ").title() for c in cols_b]
        dark_table(db, height=280)

# ══════════════════════════════════════════════════════════════
# TAB 3 — COMBOIO
# ══════════════════════════════════════════════════════════════
with tab3:
    CAP = 5000
    tcb  = df_transf[df_transf["destino"].str.upper().str.contains("COMBOIO",na=False)] if not df_transf.empty else pd.DataFrame()
    trec = tcb["quantidade_l"].sum() if not tcb.empty else 0
    tdist= df_abast["liters"].sum() if not df_abast.empty else 0
    saldo= max(0, trec-tdist)
    pct  = min(100,(saldo/CAP)*100) if CAP>0 else 0
    cor_s= "#c0392b" if pct<=20 else "#d4a017" if pct<=40 else "#4a9e3f"
    ah   = df_abast[df_abast["data_os"]==hoje] if not df_abast.empty else pd.DataFrame()

    k1,k2,k3,k4 = st.columns(4)
    k1.metric("🛢 Saldo Comboio",    f"{fmt(saldo)} L", f"{pct:.1f}% de {fmt(CAP)} L")
    k2.metric("📥 Total Recebido",   f"{fmt(trec)} L")
    k3.metric("📤 Total Distribuído",f"{fmt(tdist)} L")
    k4.metric("⛽ Litros Hoje",      f"{fmt(ah['liters'].sum())} L", f"{len(ah)} eventos")

    st.markdown('<div class="sec">Nível do tanque comboio — 5.000 L</div>', unsafe_allow_html=True)
    fig_tank = go.Figure(go.Indicator(
        mode="gauge+number", value=round(pct,1),
        number={"suffix":"%","font":{"color":"#e8edd0","size":28}},
        title={"text":f"<b style='color:#e8edd0'>Saldo: {fmt(saldo)} L</b><br>"
                      f"<span style='font-size:12px;color:#c8d8c0'>"
                      f"Recebido: {fmt(trec)} L · Distribuído: {fmt(tdist)} L</span>",
               "font":{"color":"#e8edd0","size":14}},
        gauge={"axis":{"range":[0,100],"ticksuffix":"%","tickcolor":"#4a6644",
                       "tickfont":{"color":"#c8d8c0","size":10}},
               "bar":{"color":cor_s,"thickness":0.3},
               "bgcolor":"#0d180c","bordercolor":"#1e2e1c",
               "steps":[{"range":[0,20],"color":"#2a1010"},
                        {"range":[20,40],"color":"#2a2200"},
                        {"range":[40,100],"color":"#1a3318"}],
               "threshold":{"line":{"color":"#e74c3c","width":3},"thickness":0.8,"value":20}}))
    fig_tank.update_layout(paper_bgcolor="#111c10",plot_bgcolor="#111c10",
                           height=260,margin=dict(l=30,r=30,t=60,b=10))
    st.plotly_chart(fig_tank, use_container_width=True, key="k_tank")

    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown('<div class="sec">Abastecimentos hoje — top 10</div>', unsafe_allow_html=True)
        if ah.empty:
            st.info(f"Nenhum abastecimento hoje ({hoje.strftime('%d/%m/%Y')}).")
        else:
            cols_a = [c for c in ["dt_fmt","vehicle","operator","fuel_type","liters","hourmeter"] if c in ah.columns]
            da = ah.sort_values("dt",ascending=False).head(10)[cols_a].copy()
            da.columns = [c.replace("dt_fmt","Hora").replace("_"," ").title() for c in cols_a]
            dark_table(da, height=350)

    with cc2:
        st.markdown('<div class="sec">Últimas 3 transferências posto → comboio</div>', unsafe_allow_html=True)
        if tcb.empty:
            st.info("Nenhuma transferência registrada.")
        else:
            cols_t = [c for c in ["data","combustivel","origem","quantidade_l","observacao"] if c in tcb.columns]
            dt2 = tcb.sort_values("data",ascending=False).head(3)[cols_t].copy()
            dt2["data"] = pd.to_datetime(dt2["data"]).dt.strftime("%d/%m/%Y")
            dt2["quantidade_l"] = dt2["quantidade_l"].apply(lambda v: f"{fmt(v)} L")
            dt2.columns = [c.replace("_"," ").title() for c in cols_t]
            dark_table(dt2, height=180)

        st.markdown(f'<div class="sec">Volume por frota — {mes_ini.strftime("%b/%Y")} (L)</div>', unsafe_allow_html=True)
        if not df_abast.empty:
            dm = df_abast[df_abast["data_os"]>=mes_ini]
            if not dm.empty and "vehicle" in dm.columns:
                pf = dm.groupby("vehicle")["liters"].sum().reset_index().sort_values("liters",ascending=True).tail(8)
                fig = go.Figure(go.Bar(
                    y=pf["vehicle"], x=pf["liters"], orientation="h",
                    marker_color="#4a9e3f",
                    text=pf["liters"].apply(lambda v: f"{v:,.0f}L"),
                    textposition="outside",
                    textfont=dict(color="#e8edd0",size=12),
                    hovertemplate="<b>Frota %{y}</b><br>Litros: %{x:,.0f} L<extra></extra>"))
                fig.update_layout(**PDARK, height=250,
                    xaxis=dict(gridcolor="#1e2e1c",tickfont=dict(color="#e8edd0")),
                    yaxis=dict(gridcolor="#1e2e1c",tickfont=dict(color="#e8edd0",size=12)))
                st.plotly_chart(fig, use_container_width=True, key="k_vol")

# ══════════════════════════════════════════════════════════════
# TAB 4 — PARADO × OPERANDO
# ══════════════════════════════════════════════════════════════
with tab4:
    if df_disp.empty:
        st.warning("Sem dados de disponibilidade.")
    else:
        dmes = df_disp[
            (df_disp["mes"].dt.month == hoje.month) &
            (df_disp["mes"].dt.year  == hoje.year)
        ].copy()
        if dmes.empty:
            dmes = df_disp.copy()

        mlabel = dmes["mes"].dt.strftime("%B/%Y").iloc[0] if not dmes.empty else "—"
        dm  = dmes["disponibilidade_pct"].mean()
        ht  = dmes["horas_trabalhadas"].sum()
        hp  = dmes["horas_parada"].sum()
        nf  = dmes["id_frota"].nunique()
        cr  = (dmes["disponibilidade_pct"]<70).sum()

        st.markdown(
            f'<div class="sec">Equipamentos (tratores/carregadeiras) · {mlabel} · {nf} equipamentos · '
            f'Horas acumuladas desde 01/{hoje.strftime("%m/%Y")}</div>',
            unsafe_allow_html=True)

        k1,k2,k3,k4,k5 = st.columns(5)
        k1.metric("📊 Disponib. Média",  f"{dm:.1f}%")
        k2.metric("⚙️ H. Trabalhadas",   f"{fmt(ht)}h", help=f"Acumulado em {mlabel}")
        k3.metric("🔴 H. Paradas",        f"{fmt(hp)}h", help="OS abertas e manutenção")
        k4.metric("🚜 Equipamentos",      nf)
        k5.metric("⚠️ Críticos <70%",     cr)

        cor_d = "#c0392b" if dm<70 else "#d4a017" if dm<85 else "#4a9e3f"
        fg = go.Figure(go.Indicator(
            mode="gauge+number", value=round(dm,1),
            number={"suffix":"%","font":{"color":"#e8edd0","size":36}},
            title={"text":f"<b style='color:#e8edd0'>Disponibilidade Média · {mlabel}</b><br>"
                          f"<span style='font-size:12px;color:#c8d8c0'>"
                          f"{nf} equipamentos · {fmt(ht)}h trabalhadas · {fmt(hp)}h paradas</span>",
                   "font":{"color":"#e8edd0","size":14}},
            gauge={"axis":{"range":[0,100],"ticksuffix":"%","tickcolor":"#4a6644",
                           "tickfont":{"color":"#c8d8c0","size":10}},
                   "bar":{"color":cor_d,"thickness":0.3},
                   "bgcolor":"#0d180c","bordercolor":"#1e2e1c",
                   "steps":[{"range":[0,70],"color":"#2a1010"},
                             {"range":[70,85],"color":"#2a2200"},
                             {"range":[85,100],"color":"#1a3318"}],
                   "threshold":{"line":{"color":"#d4a017","width":2},"thickness":0.8,"value":85}}))
        fg.update_layout(paper_bgcolor="#111c10",plot_bgcolor="#111c10",
                         height=260,margin=dict(l=30,r=30,t=60,b=10))
        st.plotly_chart(fg, use_container_width=True, key="k_disp_g")

        cd1, cd2 = st.columns(2)
        with cd1:
            st.markdown(f'<div class="sec">H. trabalhadas × paradas por frota · {mlabel}</div>', unsafe_allow_html=True)
            dd = dmes.sort_values("horas_trabalhadas", ascending=True)
            fig = go.Figure()
            fig.add_trace(go.Bar(
                name="Trabalhadas", y=dd["id_frota"], x=dd["horas_trabalhadas"],
                orientation="h", marker_color="#4a9e3f",
                text=dd["horas_trabalhadas"].apply(lambda v: f"{v:.0f}h"),
                textposition="inside", textfont=dict(color="#ffffff",size=11),
                hovertemplate="<b>Frota %{y}</b><br>Trabalhadas: %{x:.0f}h<extra></extra>"))
            fig.add_trace(go.Bar(
                name="Paradas", y=dd["id_frota"], x=dd["horas_parada"],
                orientation="h", marker_color="#c0392b",
                text=dd["horas_parada"].apply(lambda v: f"{v:.0f}h" if v>0 else ""),
                textposition="inside", textfont=dict(color="#ffffff",size=11),
                hovertemplate="<b>Frota %{y}</b><br>Paradas: %{x:.0f}h<extra></extra>"))
            fig.update_layout(**PDARK, barmode="stack",
                height=max(300,len(dd)*30),
                legend=dict(orientation="h",y=1.05,x=0,font=dict(color="#e8edd0",size=12)),
                xaxis=dict(title="Horas",gridcolor="#1e2e1c",tickfont=dict(color="#e8edd0")),
                yaxis=dict(gridcolor="#1e2e1c",tickfont=dict(color="#e8edd0",size=12)))
            st.plotly_chart(fig, use_container_width=True, key="k_stack")

        with cd2:
            st.markdown(f'<div class="sec">Disponibilidade % por frota · {mlabel}</div>', unsafe_allow_html=True)
            dd2 = dmes.sort_values("disponibilidade_pct", ascending=True)
            cores = dd2["disponibilidade_pct"].apply(
                lambda v: "#c0392b" if v<70 else "#d4a017" if v<85 else "#4a9e3f")
            fig = go.Figure(go.Bar(
                y=dd2["id_frota"], x=dd2["disponibilidade_pct"],
                orientation="h", marker_color=cores.tolist(),
                text=dd2["disponibilidade_pct"].apply(lambda v: f"{v:.1f}%"),
                textposition="outside", textfont=dict(color="#e8edd0",size=12),
                hovertemplate="<b>Frota %{y}</b><br>Disponibilidade: %{x:.1f}%<extra></extra>"))
            fig.add_vline(x=85,line_color="#4a9e3f",line_dash="dot",line_width=1,
                annotation_text="Meta 85%",annotation_font_color="#6fcf60",
                annotation_position="top right")
            fig.add_vline(x=70,line_color="#c0392b",line_dash="dash",line_width=1,
                annotation_text="Crítico 70%",annotation_font_color="#e74c3c",
                annotation_position="bottom right")
            fig.update_layout(**PDARK, height=max(300,len(dd2)*30),
                xaxis_range=[0,115],
                xaxis=dict(gridcolor="#1e2e1c",tickfont=dict(color="#e8edd0")),
                yaxis=dict(gridcolor="#1e2e1c",tickfont=dict(color="#e8edd0",size=12)))
            st.plotly_chart(fig, use_container_width=True, key="k_disp_bar")

        st.markdown(f'<div class="sec">Resumo por equipamento · {mlabel}</div>', unsafe_allow_html=True)
        def bd(v): return f"🔴 {v:.1f}%" if v<70 else f"🟡 {v:.1f}%" if v<85 else f"🟢 {v:.1f}%"
        dt3 = dmes[["id_frota","dias_com_apontamento","horas_trabalhadas",
                    "horas_parada","disponibilidade_pct","total_os"]].copy()
        dt3 = dt3.sort_values("disponibilidade_pct", ascending=True)
        dt3["disponibilidade_pct"] = dt3["disponibilidade_pct"].apply(bd)
        dt3["horas_trabalhadas"] = dt3["horas_trabalhadas"].apply(lambda v: f"{v:.0f}h")
        dt3["horas_parada"] = dt3["horas_parada"].apply(lambda v: f"{v:.0f}h")
        dt3.columns = ["Frota","Dias Ativos","H. Trabalhadas","H. Paradas","Disponib. %","OS no Mês"]
        dark_table(dt3, height=380)

st.divider()
st.markdown("<div style='text-align:center;font-size:11px;color:#4a6644;'>"
            "Santa Vergínia Agropecuária e Florestal · Controladoria · Gestor Oficina</div>",
            unsafe_allow_html=True)
