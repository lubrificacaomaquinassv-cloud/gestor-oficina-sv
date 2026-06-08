import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Gestor Oficina — Santa Vergínia", layout="wide", page_icon="🔧")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700&display=swap');
[data-testid="stAppViewContainer"]{background:#0a1409;}
[data-testid="stSidebar"]{background:#111c10;border-right:1px solid #1e2e1c;}
[data-testid="stHeader"]{background:#0a1409;}
h1,h2,h3,p,span,label{color:#e8edd0;}
.stCaption,[data-testid="stCaptionContainer"] p{color:#8aab80!important;}
.stMarkdown p,.stMarkdown li{color:#c8d8c0;}
.stAlert p{color:#e8edd0!important;}
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
div[data-testid="metric-container"] [data-testid="stMetricDelta"]{color:#8aab80!important;}
div[data-testid="stSelectbox"] label{color:#8aab80!important;}
div[data-testid="stSelectbox"] > div{background:#111c10!important;border:1px solid #1e2e1c!important;color:#e8edd0!important;}
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div{color:#e8edd0!important;}
</style>
""", unsafe_allow_html=True)

PDARK = dict(
    paper_bgcolor="#111c10", plot_bgcolor="#0d180c",
    font=dict(color="#e8edd0", family="Barlow Condensed"),
    margin=dict(l=10, r=10, t=40, b=10),
)

PLOT_AXIS = dict(
    gridcolor="#1e2e1c",
    tickfont=dict(color="#e8edd0"),
)


def dark_table(df, height=300):
    rows = "".join(
        "<tr>" + "".join(
            f'<td style="padding:6px 10px;border-bottom:1px solid #1e2e1c;color:#e8edd0;font-size:12px;">{v}</td>'
            for v in row) + "</tr>"
        for _, row in df.iterrows())
    headers = "".join(
        f'<th style="padding:7px 10px;background:#111c10;color:#8aab80;font-size:10px;'
        f'font-weight:700;text-transform:uppercase;letter-spacing:1px;border-bottom:2px solid #1e2e1c;">{c}</th>'
        for c in df.columns)
    st.markdown(
        f'<div style="max-height:{height}px;overflow-y:auto;overflow-x:auto;border:1px solid #1e2e1c;border-radius:10px;">'
        f'<table style="width:100%;border-collapse:collapse;background:#0d180c;font-family:Barlow Condensed,sans-serif;">'
        f'<thead><tr>{headers}</tr></thead><tbody>{rows}</tbody></table></div>',
        unsafe_allow_html=True)


def os_status_color(status):
    st_ = str(status).upper()
    if "FINAL" in st_:
        return "#4a9e3f"
    if "PEND" in st_ or "ANDAMENTO" in st_:
        return "#d4a017"
    return "#c0392b"


def os_cards(df_vis):
    n = len(df_vis)
    if n == 0:
        return
    cols = st.columns(min(5, n))
    for i, (_, row) in enumerate(df_vis.iterrows()):
        if i >= 5:
            break
        cor = os_status_color(row.get("status", ""))
        with cols[i]:
            st.markdown(
                f'<div style="background:#111c10;border:1px solid #1e2e1c;border-left:4px solid {cor};'
                f'border-radius:10px;padding:14px;min-height:130px;">'
                f'<div style="color:#6fcf60;font-size:17px;font-weight:700;font-family:Barlow Condensed,sans-serif;">'
                f'{row.get("numero_os", "—")}</div>'
                f'<div style="color:#e8edd0;font-size:13px;margin-top:6px;">'
                f'Frota {row.get("id_frota", "—")} · {row.get("sistema", "—")}</div>'
                f'<div style="color:#8aab80;font-size:11px;margin-top:4px;">{row.get("tipo_manutencao", "—")}</div>'
                f'<div style="color:{cor};font-size:11px;font-weight:700;margin-top:8px;">{row.get("status", "—")}</div>'
                f'<div style="color:#8aab80;font-size:10px;margin-top:6px;">'
                f'{row.get("mecanico", "—")} · {row.get("dt_fmt", "—")}</div></div>',
                unsafe_allow_html=True,
            )


def filtrar_tratores(df, df_frota=None):
    """Disponibilidade de frota: somente tratores (exclui implementos)."""
    if df.empty:
        return df
    out = df.copy()

    if df_frota is not None and not df_frota.empty and "id_frota" in out.columns:
        frota_col = "id_frota" if "id_frota" in df_frota.columns else df_frota.columns[0]
        tipo_cols = [c for c in df_frota.columns if c.lower() in (
            "tipo", "categoria", "tipo_equipamento", "grupo", "classe", "familia")]
        if tipo_cols:
            tc = tipo_cols[0]
            fmap = df_frota.set_index(frota_col)[tc].astype(str).str.upper()
            out["_tipo_frota"] = out["id_frota"].map(fmap).fillna("")
            out = out[~out["_tipo_frota"].str.contains(
                "IMPLEMENTO|REBOQUE|CARRETA|PLATAFORMA|SEM APONT", na=False, regex=True)]
            return out.drop(columns=["_tipo_frota"], errors="ignore")

    for col in ["tipo", "categoria", "tipo_equipamento", "grupo", "classe", "familia"]:
        if col in out.columns:
            out = out[~out[col].astype(str).str.upper().str.contains(
                "IMPLEMENTO|REBOQUE|CARRETA|PLATAFORMA", na=False, regex=True)]
            break

    if "modelo" in out.columns:
        out = out[~out["modelo"].astype(str).str.upper().str.contains(
            "IMPLEMENTO|REBOQUE|CARRETA|PLATAFORMA", na=False, regex=True)]

    if "id_frota" in out.columns:
        out = out[~out["id_frota"].astype(str).str.upper().str.contains(
            r"IMPLEMENTO|IMPL\.|^IMP\b", na=False, regex=True)]

    return out


from st_supabase_connection import SupabaseConnection
conn = st.connection("supabase", type=SupabaseConnection, ttl=300)


def sb(table):
    try:
        r = conn.client.table(table).select("*").execute()
    except Exception:
        r = conn.query("*", table=table).execute()
    return pd.DataFrame(r.data)


def parse_dt(series):
    """Converte timestamps para horário de Brasília (naive)."""
    raw = series.astype(str).str.strip()
    has_tz = raw.str.contains(r"[+-]\d{2}:\d{2}|Z$", regex=True, na=False)
    dt = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    if has_tz.any():
        dt.loc[has_tz] = (
            pd.to_datetime(raw[has_tz], errors="coerce", utc=True)
            .dt.tz_convert("America/Sao_Paulo")
            .dt.tz_localize(None)
        )
    if (~has_tz).any():
        dt.loc[~has_tz] = pd.to_datetime(raw[~has_tz], errors="coerce")
    return dt


def os_numero(series):
    return pd.to_numeric(
        series.astype(str).str.extract(r"(\d+)", expand=False),
        errors="coerce",
    ).fillna(0).astype(int)


def melhor_data_os(df):
    """Monta datetime da OS usando created_at e, se faltar, updated_at."""
    dt = parse_dt(df["created_at"]) if "created_at" in df.columns else pd.Series(pd.NaT, index=df.index)
    for col in ("updated_at", "data_abertura", "data_fechamento", "criado_em"):
        if col in df.columns:
            dt = dt.fillna(parse_dt(df[col]))
    return dt


@st.cache_data(ttl=120, show_spinner=False)
def load_os(_c):
    df = sb("ordem_servico")
    if df.empty:
        return df
    df["dt"] = melhor_data_os(df)
    df["data_os"] = df["dt"].dt.date
    df["mes_os"] = df["dt"].dt.to_period("M")
    df["dt_fmt"] = df["dt"].dt.strftime("%d/%m/%Y %H:%M")
    df["os_num"] = os_numero(df["numero_os"])
    df["tempo_min"] = pd.to_numeric(df["tempo_min"], errors="coerce").fillna(0)
    return df.sort_values(["os_num", "dt"], ascending=False)


@st.cache_data(ttl=120, show_spinner=False)
def load_bor(_c):
    df = sb("os_borracharia")
    if df.empty:
        return df
    df["dt"] = parse_dt(df["criado_em"])
    df["data_os"] = df["dt"].dt.date
    df["dt_fmt"] = df["dt"].dt.strftime("%d/%m/%Y %H:%M")
    return df


@st.cache_data(ttl=120, show_spinner=False)
def load_lub(_c):
    df = sb("vw_proxima_troca_v4")
    if df.empty:
        return df
    for col in ["horas_restantes", "h_atual", "h_proxima_troca", "h_na_troca"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data(ttl=120, show_spinner=False)
def load_abast(_c):
    df = sb("vw_abastecimento_consolidado")
    if df.empty:
        return df
    df["dt"] = parse_dt(df["created_at"])
    df["data_os"] = df["dt"].dt.date
    df["dt_fmt"] = df["dt"].dt.strftime("%H:%M")
    df["liters"] = pd.to_numeric(df["liters"], errors="coerce").fillna(0)
    return df


@st.cache_data(ttl=120, show_spinner=False)
def load_transf(_c):
    df = sb("combustivel_transferencia")
    if df.empty:
        return df
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df["quantidade_l"] = pd.to_numeric(df["quantidade_l"], errors="coerce").fillna(0)
    return df


@st.cache_data(ttl=120, show_spinner=False)
def load_disp(_c):
    df = sb("vw_disponibilidade_equipamentos")
    if df.empty:
        return df
    df["mes"] = parse_dt(df["mes"])
    for col in ["dias_com_apontamento", "horas_trabalhadas", "horas_parada", "disponibilidade_pct", "total_os"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


@st.cache_data(ttl=120, show_spinner=False)
def load_frota(_c):
    for table in ("frota", "cadastro_frota", "equipamentos", "vw_frota"):
        try:
            df = sb(table)
            if not df.empty:
                return df
        except Exception:
            continue
    return pd.DataFrame()


def fmt(n, dec=0):
    if pd.isna(n):
        return "—"
    return f"{n:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ── HEADER ────────────────────────────────────────────────────
h1, h2, h3 = st.columns([1, 8, 2])
with h1:
    st.markdown(
        '<div style="width:44px;height:44px;background:#4a9e3f;border-radius:8px;'
        'display:flex;align-items:center;justify-content:center;font-weight:700;'
        'color:#0a1409;font-family:Barlow Condensed,sans-serif;">SV</div>',
        unsafe_allow_html=True,
    )
with h2:
    st.markdown(
        '<div style="font-family:Barlow Condensed,sans-serif;">'
        '<div style="font-size:22px;font-weight:700;color:#e8edd0;letter-spacing:1px;">'
        'GESTOR DA OFICINA — SANTA VERGÍNIA</div>'
        '<div style="font-size:11px;color:#8aab80;letter-spacing:2px;margin-top:2px;">'
        'OS · Lubrificação · Borracharia · Comboio · Disponibilidade</div></div>',
        unsafe_allow_html=True,
    )
with h3:
    if st.button("🔄 Atualizar", key="refresh"):
        st.cache_data.clear()
        st.rerun()
    agora_br = datetime.utcnow() - timedelta(hours=3)
    st.caption(agora_br.strftime("%d/%m/%Y %H:%M") + " (Brasília)")

st.divider()

df_os = load_os(conn)
df_bor = load_bor(conn)
df_lub = load_lub(conn)
df_abast = load_abast(conn)
df_transf = load_transf(conn)
df_disp = load_disp(conn)
df_frota = load_frota(conn)

hoje = (datetime.utcnow() - timedelta(hours=3)).date()
mes_ini = hoje.replace(day=1)
mes_atual_str = pd.Period(hoje, freq="M").strftime("%Y-%m")

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
        mes_atual = pd.Period(mes_atual_str, freq="M")
        os_hoje = df_os[df_os["data_os"] == hoje]
        os_mes = df_os[df_os["mes_os"] == mes_atual]
        os_aber = df_os[df_os["status"].str.upper().str.contains("ABERTO|ANDAMENTO|PENDENTE", na=False)]
        os_fin = os_mes[os_mes["status"].str.upper().str.contains("FINAL", na=False)]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔧 OS Hoje", len(os_hoje))
        c2.metric(f"📋 OS em {mes_ini.strftime('%b/%Y')}", len(os_mes))
        c3.metric("🔴 Em Aberto/Pendente", len(os_aber))
        c4.metric("✅ Finalizadas no Mês", len(os_fin))

        # ── Visual: 5 OS mais recentes (hoje → junho → geral) ──
        st.markdown(
            f'<div class="sec">OS do dia — {hoje.strftime("%d/%m/%Y")}</div>',
            unsafe_allow_html=True,
        )
        if not os_hoje.empty:
            df_vis = os_hoje.sort_values(["os_num", "dt"], ascending=False).head(5)
            legenda = f"{len(os_hoje)} OS hoje — exibindo as 5 mais recentes"
        elif not os_mes.empty:
            df_vis = os_mes.sort_values(["os_num", "dt"], ascending=False).head(5)
            legenda = f"Sem OS hoje — exibindo as 5 mais recentes de {mes_atual_str}"
        else:
            df_vis = df_os.sort_values(["os_num", "dt"], ascending=False).head(5)
            legenda = "Sem OS no mês atual — exibindo as 5 OS mais recentes da base"

        if df_vis.empty:
            st.info("Nenhuma OS registrada.")
        else:
            os_cards(df_vis)
            st.caption(legenda)

        st.divider()

        # ── Filtro de mês + lista completa ──
        st.markdown('<div class="sec">OS do período</div>', unsafe_allow_html=True)
        meses_disp = sorted(df_os["mes_os"].dropna().unique(), reverse=True)
        meses_label = [str(m) for m in meses_disp]
        if mes_atual_str in meses_label:
            idx_default = meses_label.index(mes_atual_str)
        else:
            idx_default = 0
        mes_sel_label = st.selectbox(
            "Selecionar mês:",
            options=meses_label,
            index=idx_default,
            key="sel_mes_os",
        )
        mes_sel = pd.Period(mes_sel_label, freq="M")
        df_mes_sel = df_os[df_os["mes_os"] == mes_sel].sort_values(["os_num", "dt"], ascending=False)

        st.caption(f"{len(df_mes_sel)} OS em {mes_sel_label}")

        if df_mes_sel.empty:
            st.info(f"Nenhuma OS em {mes_sel_label}.")
        else:
            df_t = df_mes_sel[
                ["numero_os", "id_frota", "sistema", "tipo_manutencao", "status", "mecanico", "dt_fmt"]
            ].copy()
            df_t.columns = ["OS", "Frota", "Sistema", "Tipo", "Status", "Mecânico", "Data/Hora"]
            dark_table(df_t, height=380)

        if not df_mes_sel.empty:
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.markdown(
                    f'<div class="sec">Sistemas mais acionados — {mes_sel_label}</div>',
                    unsafe_allow_html=True,
                )
                r = (
                    df_mes_sel.groupby("sistema").size().reset_index(name="qtd")
                    .sort_values("qtd", ascending=True).tail(8)
                )
                fig = go.Figure(go.Bar(
                    y=r["sistema"], x=r["qtd"], orientation="h",
                    marker_color="#4a9e3f",
                    text=r["qtd"], textposition="outside",
                    textfont=dict(color="#e8edd0", size=13),
                    hovertemplate="%{y}<br>Quantidade de OS: %{x}<extra></extra>",
                ))
                fig.update_layout(
                    **PDARK, height=280,
                    xaxis={**PLOT_AXIS},
                    yaxis={**PLOT_AXIS, "tickfont": dict(color="#e8edd0", size=12)},
                )
                st.plotly_chart(fig, use_container_width=True, key="k_sis")

            with col_r2:
                st.markdown(
                    f'<div class="sec">Equipamentos com mais OS — {mes_sel_label}</div>',
                    unsafe_allow_html=True,
                )
                r = (
                    df_mes_sel.groupby("id_frota").size().reset_index(name="qtd")
                    .sort_values("qtd", ascending=True).tail(8)
                )
                fig = go.Figure(go.Bar(
                    y=r["id_frota"], x=r["qtd"], orientation="h",
                    marker_color="#6fcf60",
                    text=r["qtd"], textposition="outside",
                    textfont=dict(color="#e8edd0", size=13),
                    hovertemplate="Frota %{y}<br>Quantidade de OS: %{x}<extra></extra>",
                ))
                fig.update_layout(
                    **PDARK, height=280,
                    xaxis={**PLOT_AXIS},
                    yaxis={**PLOT_AXIS, "tickfont": dict(color="#e8edd0", size=12)},
                )
                st.plotly_chart(fig, use_container_width=True, key="k_frota")

            st.markdown(
                f'<div class="sec">Corretiva × Preventiva — {mes_sel_label}</div>',
                unsafe_allow_html=True,
            )
            r = df_mes_sel["tipo_manutencao"].str.upper().value_counts().reset_index()
            r.columns = ["tipo", "qtd"]
            cores = {"CORRETIVA": "#c0392b", "PREVENTIVA": "#4a9e3f"}
            fig = go.Figure(go.Bar(
                x=r["tipo"], y=r["qtd"],
                marker_color=[cores.get(t, "#2980b9") for t in r["tipo"]],
                text=r["qtd"], textposition="outside",
                textfont=dict(color="#e8edd0", size=14),
                hovertemplate="%{x}<br>Quantidade: %{y}<extra></extra>",
            ))
            fig.update_layout(
                **PDARK, height=220,
                xaxis={**PLOT_AXIS, "tickfont": dict(color="#e8edd0", size=13)},
                yaxis={**PLOT_AXIS},
            )
            st.plotly_chart(fig, use_container_width=True, key="k_tipo")

# ══════════════════════════════════════════════════════════════
# TAB 2 — LUBRIFICAÇÃO + BORRACHARIA
# ══════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="sec">Lubrificação — horímetros de troca de óleo</div>', unsafe_allow_html=True)
    if df_lub.empty:
        st.info("Sem dados de lubrificação.")
    else:
        ok = (df_lub["status_troca"] == "OK").sum()
        prx = (df_lub["status_troca"] == "PROXIMO").sum()
        atr = (df_lub["status_troca"] == "EM ATRASO").sum()
        l1, l2, l3, l4 = st.columns(4)
        l1.metric("✅ OK", ok)
        l2.metric("⚠️ Próximo ≤100h", prx)
        l3.metric("🔴 Em Atraso", atr)
        l4.metric("📋 Total", len(df_lub))

        st.markdown(
            '<div class="sec">Velocímetros — ordenados por urgência (3 por linha)</div>',
            unsafe_allow_html=True,
        )
        dg = df_lub.sort_values("horas_restantes", ascending=True).head(9)
        for i in range(0, len(dg), 3):
            cols3 = st.columns(3)
            for j, col in enumerate(cols3):
                idx = i + j
                if idx >= len(dg):
                    break
                row = dg.iloc[idx]
                h_na = float(row["h_na_troca"]) if pd.notna(row["h_na_troca"]) else 0
                h_prox = float(row["h_proxima_troca"]) if pd.notna(row["h_proxima_troca"]) else h_na + 250
                h_at = float(row["h_atual"]) if pd.notna(row["h_atual"]) else h_na
                h_rest = float(row["horas_restantes"]) if pd.notna(row["horas_restantes"]) else 0
                st_ = str(row["status_troca"])
                cor = "#c0392b" if st_ == "EM ATRASO" else "#d4a017" if st_ == "PROXIMO" else "#4a9e3f"
                emin = max(0, h_na - 50)
                emax = h_prox + max(100, abs(min(0, h_rest)) + 50)
                fg = go.Figure(go.Indicator(
                    mode="gauge+number+delta", value=h_at,
                    number={"suffix": "h", "font": {"color": "#e8edd0", "size": 20}},
                    delta={
                        "reference": h_prox, "valueformat": ".0f",
                        "increasing": {"color": "#c0392b"},
                        "decreasing": {"color": "#4a9e3f"}, "suffix": "h",
                    },
                    title={
                        "text": (
                            f"<b>{row['vehicle']}</b><br>"
                            f"<span style='font-size:10px;color:#8aab80'>"
                            f"Troca: {fmt(h_na)}h → {fmt(h_prox)}h<br>"
                            f"{'⚠ Atrasado' if h_rest < 0 else '✓ Restam'}: {fmt(abs(h_rest))}h</span>"
                        ),
                        "font": {"color": "#e8edd0", "size": 12},
                    },
                    gauge={
                        "axis": {
                            "range": [emin, emax],
                            "tickcolor": "#4a6644",
                            "tickfont": {"color": "#e8edd0", "size": 9},
                        },
                        "bar": {"color": cor, "thickness": 0.35},
                        "bgcolor": "#0d180c", "bordercolor": "#1e2e1c",
                        "steps": [
                            {"range": [emin, h_prox - 100], "color": "#1a3318"},
                            {"range": [h_prox - 100, h_prox], "color": "#2a2200"},
                            {"range": [h_prox, emax], "color": "#2a1010"},
                        ],
                        "threshold": {"line": {"color": "#c0392b", "width": 3}, "thickness": 0.8, "value": h_prox},
                    },
                ))
                fg.update_layout(
                    paper_bgcolor="#111c10", plot_bgcolor="#111c10",
                    font=dict(color="#e8edd0"),
                    height=200, margin=dict(l=8, r=8, t=65, b=5),
                )
                with col:
                    st.plotly_chart(fg, use_container_width=True, key=f"g_{row['vehicle']}_{idx}")

        st.markdown('<div class="sec">Lista completa — ordenada por urgência</div>', unsafe_allow_html=True)

        def badge(s):
            return {"OK": "🟢 OK", "PROXIMO": "🟡 PRÓXIMO", "EM ATRASO": "🔴 EM ATRASO"}.get(s, f"⚪ {s}")

        dt = (
            df_lub.sort_values("horas_restantes", ascending=True)[
                ["vehicle", "h_na_troca", "h_proxima_troca", "h_atual", "horas_restantes", "status_troca"]
            ].copy()
        )
        dt["horas_restantes"] = dt["horas_restantes"].apply(
            lambda v: f"{v:+.0f}h" if pd.notna(v) else "—")
        dt["status_troca"] = dt["status_troca"].apply(badge)
        dt.columns = ["Frota", "H. Troca", "Próxima (h)", "H. Atual", "Restante", "Status"]
        dark_table(dt, height=300)

    st.divider()
    st.markdown('<div class="sec">Borracharia — OS recentes</div>', unsafe_allow_html=True)
    if df_bor.empty:
        st.info("Sem registros de borracharia.")
    else:
        bk1, bk2, bk3 = st.columns(3)
        bk1.metric("OS no Mês", len(df_bor[df_bor["data_os"] >= mes_ini]))
        bk2.metric("Hoje", len(df_bor[df_bor["data_os"] == hoje]))
        bk3.metric("Total", len(df_bor))
        cols_b = [
            c for c in ["numero_os", "id_frota", "tipo_manutencao", "borracheiro", "status", "descricao", "dt_fmt"]
            if c in df_bor.columns
        ]
        db = df_bor.sort_values("dt", ascending=False).head(5)[cols_b].copy()
        db.columns = [c.replace("dt_fmt", "Data/Hora").replace("_", " ").title() for c in cols_b]
        dark_table(db, height=280)

# ══════════════════════════════════════════════════════════════
# TAB 3 — COMBOIO
# ══════════════════════════════════════════════════════════════
with tab3:
    CAP = 5000
    tcb = (
        df_transf[df_transf["destino"].str.upper().str.contains("COMBOIO", na=False)]
        if not df_transf.empty else pd.DataFrame()
    )
    trec = tcb["quantidade_l"].sum() if not tcb.empty else 0
    tdist = df_abast["liters"].sum() if not df_abast.empty else 0
    saldo = max(0, trec - tdist)
    pct = min(100, (saldo / CAP) * 100) if CAP > 0 else 0
    cor_s = "#c0392b" if pct <= 20 else "#d4a017" if pct <= 40 else "#4a9e3f"
    ah = df_abast[df_abast["data_os"] == hoje] if not df_abast.empty else pd.DataFrame()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🛢 Saldo Comboio", f"{fmt(saldo)} L", f"{pct:.1f}% de {fmt(CAP)} L")
    k2.metric("📥 Total Recebido", f"{fmt(trec)} L")
    k3.metric("📤 Total Distribuído", f"{fmt(tdist)} L")
    k4.metric("⛽ Litros Hoje", f"{fmt(ah['liters'].sum())} L" if not ah.empty else "0 L",
              f"{len(ah)} eventos")

    st.markdown('<div class="sec">Nível do tanque comboio — 5.000 L</div>', unsafe_allow_html=True)
    fig_tank = go.Figure(go.Indicator(
        mode="gauge+number", value=round(pct, 1),
        number={"suffix": "%", "font": {"color": "#e8edd0", "size": 32}},
        title={
            "text": (
                f"<span style='color:#e8edd0'>Saldo estimado: <b>{fmt(saldo)} L</b></span><br>"
                f"<span style='color:#8aab80;font-size:12px'>"
                f"Recebido do posto: {fmt(trec)} L · Distribuído às máquinas: {fmt(tdist)} L</span>"
            ),
            "font": {"color": "#e8edd0", "size": 14},
        },
        gauge={
            "axis": {
                "range": [0, 100], "ticksuffix": "%",
                "tickcolor": "#4a6644", "tickfont": {"color": "#e8edd0", "size": 11},
            },
            "bar": {"color": cor_s, "thickness": 0.3},
            "bgcolor": "#0d180c", "bordercolor": "#1e2e1c",
            "steps": [
                {"range": [0, 20], "color": "#2a1010"},
                {"range": [20, 40], "color": "#2a2200"},
                {"range": [40, 100], "color": "#1a3318"},
            ],
            "threshold": {"line": {"color": "#e74c3c", "width": 3}, "thickness": 0.8, "value": 20},
        },
    ))
    fig_tank.update_layout(
        paper_bgcolor="#111c10", plot_bgcolor="#111c10",
        font=dict(color="#e8edd0", family="Barlow Condensed"),
        height=260, margin=dict(l=30, r=30, t=80, b=10),
    )
    st.plotly_chart(fig_tank, use_container_width=True, key="k_tank")

    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown('<div class="sec">Abastecimentos hoje — top 10</div>', unsafe_allow_html=True)
        if ah.empty:
            st.info(f"Nenhum abastecimento hoje ({hoje.strftime('%d/%m/%Y')}).")
        else:
            cols_a = [c for c in ["dt_fmt", "vehicle", "operator", "fuel_type", "liters", "hourmeter"] if c in ah.columns]
            da = ah.sort_values("dt", ascending=False).head(10)[cols_a].copy()
            da.columns = [c.replace("dt_fmt", "Hora").replace("_", " ").title() for c in cols_a]
            dark_table(da, height=350)

    with cc2:
        st.markdown('<div class="sec">Últimas 3 transferências posto → comboio</div>', unsafe_allow_html=True)
        if tcb.empty:
            st.info("Nenhuma transferência registrada.")
        else:
            cols_t = [c for c in ["data", "combustivel", "origem", "quantidade_l", "observacao"] if c in tcb.columns]
            dt2 = tcb.sort_values("data", ascending=False).head(3)[cols_t].copy()
            dt2["data"] = pd.to_datetime(dt2["data"]).dt.strftime("%d/%m/%Y")
            dt2["quantidade_l"] = dt2["quantidade_l"].apply(lambda v: f"{fmt(v)} L")
            dt2.columns = [c.replace("_", " ").title() for c in cols_t]
            dark_table(dt2, height=180)

    st.markdown(
        f'<div class="sec">Volume por frota — {mes_ini.strftime("%b/%Y")} (L)</div>',
        unsafe_allow_html=True,
    )
    if not df_abast.empty:
        dm = df_abast[df_abast["data_os"] >= mes_ini]
        if not dm.empty and "vehicle" in dm.columns:
            pf = (
                dm.groupby("vehicle")["liters"].sum()
                .reset_index().sort_values("liters", ascending=True).tail(8)
            )
            fig = go.Figure(go.Bar(
                y=pf["vehicle"], x=pf["liters"], orientation="h",
                marker_color="#4a9e3f",
                text=pf["liters"].apply(lambda v: f"{v:,.0f}L"),
                textposition="outside",
                textfont=dict(color="#e8edd0", size=12),
                hovertemplate="Frota %{y}<br>Volume: %{x:,.0f} L<extra></extra>",
            ))
            fig.update_layout(
                **PDARK, height=250,
                xaxis={**PLOT_AXIS},
                yaxis={**PLOT_AXIS, "tickfont": dict(color="#e8edd0", size=12)},
            )
            st.plotly_chart(fig, use_container_width=True, key="k_vol")

# ══════════════════════════════════════════════════════════════
# TAB 4 — PARADO × OPERANDO (somente tratores)
# ══════════════════════════════════════════════════════════════
with tab4:
    if df_disp.empty:
        st.warning("Sem dados de disponibilidade.")
    else:
        meses_d = sorted(df_disp["mes"].dt.to_period("M").unique(), reverse=True)
        meses_d_label = [str(m) for m in meses_d]
        idx_d = meses_d_label.index(mes_atual_str) if mes_atual_str in meses_d_label else 0
        mes_d_sel = st.selectbox(
            "Mês de referência:",
            options=meses_d_label,
            index=idx_d,
            key="sel_mes_disp",
        )
        mp = pd.Period(mes_d_sel, freq="M")
        dmes_raw = df_disp[df_disp["mes"].dt.to_period("M") == mp].copy()
        dmes = filtrar_tratores(dmes_raw, df_frota)
        excluidos = len(dmes_raw) - len(dmes)

        if dmes.empty:
            st.info(f"Sem dados de tratores para {mes_d_sel}.")
        else:
            mlabel = mes_d_sel
            dm = dmes["disponibilidade_pct"].mean()
            ht = dmes["horas_trabalhadas"].sum()
            hp = dmes["horas_parada"].sum()
            nf = dmes["id_frota"].nunique()
            cr = (dmes["disponibilidade_pct"] < 70).sum()

            st.markdown(
                f'<div class="sec">Tratores · {mlabel} · {nf} máquinas · horas acumuladas no mês</div>',
                unsafe_allow_html=True,
            )
            if excluidos > 0:
                st.caption(f"Implementos e demais equipamentos sem apontamento excluídos ({excluidos} registros).")

            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("📊 Disponib. Média", f"{dm:.1f}%",
                      help="Média de disponibilidade dos tratores no mês")
            k2.metric("⚙️ H. Trabalhadas", f"{fmt(ht)}h",
                      help=f"Total de horas com apontamento de produção em {mlabel}")
            k3.metric("🔴 H. Paradas", f"{fmt(hp)}h",
                      help="Horas sem apontamento — manutenção ou inatividade")
            k4.metric("🚜 Tratores", nf,
                      help="Somente tratores com apontamento no mês")
            k5.metric("⚠️ Críticos <70%", cr,
                      help="Tratores abaixo da meta mínima de disponibilidade")

            cor_d = "#c0392b" if dm < 70 else "#d4a017" if dm < 85 else "#4a9e3f"
            fg = go.Figure(go.Indicator(
                mode="gauge+number", value=round(dm, 1),
                number={"suffix": "%", "font": {"color": "#e8edd0", "size": 36}},
                title={
                    "text": (
                        f"<span style='color:#e8edd0'>Disponibilidade Média · {mlabel}</span><br>"
                        f"<span style='color:#8aab80;font-size:12px'>"
                        f"{nf} tratores · {fmt(ht)}h trabalhadas · {fmt(hp)}h paradas</span>"
                    ),
                    "font": {"color": "#e8edd0", "size": 14},
                },
                gauge={
                    "axis": {
                        "range": [0, 100], "ticksuffix": "%",
                        "tickcolor": "#4a6644", "tickfont": {"color": "#e8edd0", "size": 11},
                    },
                    "bar": {"color": cor_d, "thickness": 0.3},
                    "bgcolor": "#0d180c", "bordercolor": "#1e2e1c",
                    "steps": [
                        {"range": [0, 70], "color": "#2a1010"},
                        {"range": [70, 85], "color": "#2a2200"},
                        {"range": [85, 100], "color": "#1a3318"},
                    ],
                    "threshold": {"line": {"color": "#d4a017", "width": 2}, "thickness": 0.8, "value": 85},
                },
            ))
            fg.update_layout(
                paper_bgcolor="#111c10", plot_bgcolor="#111c10",
                font=dict(color="#e8edd0", family="Barlow Condensed"),
                height=260, margin=dict(l=30, r=30, t=80, b=10),
            )
            st.plotly_chart(fg, use_container_width=True, key="k_disp_g")

            cd1, cd2 = st.columns(2)
            modelo_map = {}
            if "modelo" in dmes.columns:
                modelo_map = dict(zip(dmes["id_frota"], dmes["modelo"]))

            with cd1:
                st.markdown(
                    f'<div class="sec">H. trabalhadas × paradas · {mlabel}</div>',
                    unsafe_allow_html=True,
                )
                st.caption("Passe o mouse sobre as barras para ver os valores")
                dd = dmes.sort_values("horas_trabalhadas", ascending=True)
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    name="✅ Trabalhadas",
                    y=dd["id_frota"], x=dd["horas_trabalhadas"],
                    orientation="h", marker_color="#4a9e3f",
                    text=dd["horas_trabalhadas"].apply(lambda v: f"{v:.0f}h"),
                    textposition="inside", textfont=dict(color="#e8edd0", size=11),
                    hovertemplate=(
                        "Frota %{y}<br>"
                        + ("Modelo: %{customdata}<br>" if modelo_map else "")
                        + "Horas trabalhadas: %{x:.0f}h<extra></extra>"
                    ),
                    customdata=dd["id_frota"].map(modelo_map) if modelo_map else None,
                ))
                fig.add_trace(go.Bar(
                    name="🔴 Paradas",
                    y=dd["id_frota"], x=dd["horas_parada"],
                    orientation="h", marker_color="#c0392b",
                    text=dd["horas_parada"].apply(lambda v: f"{v:.0f}h" if v > 0 else ""),
                    textposition="inside", textfont=dict(color="#e8edd0", size=11),
                    hovertemplate=(
                        "Frota %{y}<br>"
                        + ("Modelo: %{customdata}<br>" if modelo_map else "")
                        + "Horas paradas: %{x:.0f}h (manutenção / sem apontamento)<extra></extra>"
                    ),
                    customdata=dd["id_frota"].map(modelo_map) if modelo_map else None,
                ))
                fig.update_layout(
                    **PDARK, barmode="stack",
                    height=max(320, len(dd) * 32),
                    legend=dict(orientation="h", y=1.05, x=0, font=dict(color="#e8edd0", size=12)),
                    xaxis={**PLOT_AXIS, "title": "Horas acumuladas no mês"},
                    yaxis={**PLOT_AXIS, "tickfont": dict(color="#e8edd0", size=12)},
                )
                st.plotly_chart(fig, use_container_width=True, key="k_stack")

            with cd2:
                st.markdown(
                    f'<div class="sec">Disponibilidade % · {mlabel}</div>',
                    unsafe_allow_html=True,
                )
                st.caption("🟢 ≥85% meta · 🟡 70–85% atenção · 🔴 <70% crítico")
                dd2 = dmes.sort_values("disponibilidade_pct", ascending=True)
                cores = dd2["disponibilidade_pct"].apply(
                    lambda v: "#c0392b" if v < 70 else "#d4a017" if v < 85 else "#4a9e3f")
                fig = go.Figure(go.Bar(
                    y=dd2["id_frota"], x=dd2["disponibilidade_pct"],
                    orientation="h", marker_color=cores.tolist(),
                    text=dd2["disponibilidade_pct"].apply(lambda v: f"{v:.1f}%"),
                    textposition="outside",
                    textfont=dict(color="#e8edd0", size=12),
                    customdata=dd2["id_frota"].map(modelo_map) if modelo_map else dd2["id_frota"],
                    hovertemplate=(
                        "Frota %{y}<br>Modelo: %{customdata}<br>"
                        "Disponibilidade: %{x:.1f}%<br>Meta: 85% · Crítico: 70%<extra></extra>"
                    ),
                ))
                fig.add_vline(
                    x=85, line_color="#4a9e3f", line_dash="dot", line_width=1,
                    annotation_text="Meta 85%",
                    annotation_font=dict(color="#6fcf60", size=11),
                    annotation_position="top right",
                )
                fig.add_vline(
                    x=70, line_color="#c0392b", line_dash="dash", line_width=1,
                    annotation_text="Crítico 70%",
                    annotation_font=dict(color="#e74c3c", size=11),
                    annotation_position="bottom right",
                )
                fig.update_layout(
                    **PDARK, height=max(320, len(dd2) * 32),
                    xaxis_range=[0, 115],
                    xaxis={**PLOT_AXIS},
                    yaxis={**PLOT_AXIS, "tickfont": dict(color="#e8edd0", size=12)},
                )
                st.plotly_chart(fig, use_container_width=True, key="k_disp_bar")

            st.markdown(f'<div class="sec">Resumo por trator · {mlabel}</div>', unsafe_allow_html=True)

            def bd(v):
                return f"🔴 {v:.1f}%" if v < 70 else f"🟡 {v:.1f}%" if v < 85 else f"🟢 {v:.1f}%"

            cols_t = ["id_frota", "dias_com_apontamento", "horas_trabalhadas",
                      "horas_parada", "disponibilidade_pct", "total_os"]
            if "modelo" in dmes.columns:
                cols_t = ["id_frota", "modelo"] + cols_t[1:]

            dt3 = dmes[cols_t].copy().sort_values("disponibilidade_pct", ascending=True)
            dt3["disponibilidade_pct"] = dt3["disponibilidade_pct"].apply(bd)
            dt3["horas_trabalhadas"] = dt3["horas_trabalhadas"].apply(lambda v: f"{v:.0f}h")
            dt3["horas_parada"] = dt3["horas_parada"].apply(lambda v: f"{v:.0f}h")

            if "modelo" in dt3.columns:
                dt3.columns = ["Frota", "Modelo", "Dias Ativos", "H. Trabalhadas",
                               "H. Paradas", "Disponib. %", "OS no Mês"]
            else:
                dt3.columns = ["Frota", "Dias Ativos", "H. Trabalhadas",
                               "H. Paradas", "Disponib. %", "OS no Mês"]
            dark_table(dt3, height=400)

st.divider()
st.markdown(
    '<div style="text-align:center;color:#4a6644;font-size:11px;font-family:Barlow Condensed,sans-serif;'
    'letter-spacing:1px;padding:8px 0;">'
    'Santa Vergínia Agropecuária e Florestal · Controladoria · Gestor Oficina</div>',
    unsafe_allow_html=True,
)
