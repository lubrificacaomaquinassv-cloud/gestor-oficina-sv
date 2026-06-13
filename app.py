import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Conferir no site apos publicar: deve aparecer este codigo no canto superior direito
PAINEL_BUILD = "2026-06-13-camada2f"

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
.stButton button{background:#4a9e3f!important;color:#ffffff!important;border:1px solid #6fcf60!important;
 font-family:'Barlow Condensed',sans-serif;font-weight:700;letter-spacing:1px;text-transform:uppercase;border-radius:8px;}
.stButton button:hover{background:#3d8534!important;border-color:#9fe790!important;}
.stButton button p{color:#ffffff!important;font-weight:700;}
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


def label_trator(row):
    frota = row.get("id_frota") or row.get("frota") or "—"
    modelo = row.get("modelo")
    if pd.notna(modelo) and str(modelo).strip():
        return f"{modelo} · {frota}"
    return str(frota)


def filtrar_tratores(df, df_frota=None, df_painel=None):
    """Disponibilidade de frota: somente tratores (exclui implementos)."""
    if df.empty:
        return df
    out = df.copy()
    if "id_frota" not in out.columns and "frota" in out.columns:
        out["id_frota"] = out["frota"]

    for col in ("frota", "id_frota"):
        if col in out.columns:
            out = out[~out[col].astype(str).str.upper().str.contains(
                r"IMPLEMENTO|IMPL\.|^IMP\b|REBOQUE|CARRETA", na=False, regex=True)]

    if df_frota is not None and not df_frota.empty and "id_frota" in out.columns:
        frota_col = "id_frota" if "id_frota" in df_frota.columns else "frota"
        if frota_col not in df_frota.columns:
            frota_col = df_frota.columns[0]
        cat_map = mapa_categoria_frota(df_frota, df_painel)
        out["_cat"] = out["id_frota"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True).map(
            lambda f: norm_categoria((cat_map.get(f) or {}).get("categoria", ""))
        )
        out["_mod"] = out["id_frota"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True).map(
            lambda f: str((cat_map.get(f) or {}).get("modelo", "")).upper()
        )
        out = out[
            ~out.apply(
                lambda r: eh_implemento(r["_cat"], r["_mod"])
                or eh_terceiro(r["_cat"], r["_mod"], r["id_frota"])
                or excluir_disponibilidade(r["_cat"], r["id_frota"]),
                axis=1,
            )
        ]
        return out.drop(columns=["_cat", "_mod"], errors="ignore")

    for col in ["tipo", "categoria", "tipo_equipamento", "grupo", "classe", "familia"]:
        if col in out.columns:
            out = out[~out[col].astype(str).str.upper().str.contains(
                "IMPLEMENTO|REBOQUE|CARRETA|PLATAFORMA", na=False, regex=True)]
            break

    if "modelo" in out.columns:
        out = out[~out["modelo"].astype(str).str.upper().str.contains(
            "IMPLEMENTO|REBOQUE|CARRETA|PLATAFORMA", na=False, regex=True)]

    return out

def mapa_categoria_frota(df_frota, df_painel=None):
    """id_frota -> {categoria, modelo}. dim_frota_painel sobrescreve dim_frota."""
    out = {}
    if df_frota is not None and not df_frota.empty:
        col = "id_frota" if "id_frota" in df_frota.columns else "frota"
        if col not in df_frota.columns:
            col = df_frota.columns[0]
        cat = next((c for c in df_frota.columns if c.lower() in (
            "categoria", "tipo", "tipo_equipamento", "grupo", "classe", "familia")), None)
        cols = [col]
        if cat:
            cols.append(cat)
        if "modelo" in df_frota.columns:
            cols.append("modelo")
        tmp = df_frota[cols].copy()
        tmp[col] = tmp[col].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
        for _, row in tmp.iterrows():
            fid = str(row[col]).strip()
            meta = {"categoria": "", "modelo": ""}
            if cat:
                meta["categoria"] = str(row.get(cat) or "").strip().upper()
            if "modelo" in row.index:
                meta["modelo"] = str(row.get("modelo") or "").strip().upper()
            out[fid] = meta
    if df_painel is not None and not df_painel.empty:
        for _, row in df_painel.iterrows():
            fid = str(row.get("id_frota", "")).strip()
            if not fid:
                continue
            out[fid] = {
                "categoria": str(row.get("categoria_painel") or row.get("categoria") or "").strip().upper(),
                "modelo": str(row.get("modelo") or "").strip().upper(),
            }
    return out


def norm_categoria(c):
    return str(c or "").upper().strip().replace("Á", "A").replace("Ã", "A")


# Taxonomia dim_frota.categoria (padrao SV)
_CAT_IMPLEMENTO = frozenset({"IMPLEMENTO", "REBOQUE", "CARRETA", "PLATAFORMA"})
_CAT_MOTOR = frozenset({
    "EQUIPAMENTO", "TRATOR", "MAQUINA", "CAMINHAO", "MOTO",
    "COLHEIT", "COLHEITADEIRA", "VEICULO_PESADO", "VEICULO_LEVE",
})
_FROTA_TERCEIRO = frozenset({"9999", "920K", "920"})


def eh_terceiro(categoria="", modelo="", id_frota=""):
    """Frota alugada/terceirizada — fora do painel da frota propria."""
    fid = str(id_frota or "").strip().upper()
    if fid in _FROTA_TERCEIRO:
        return True
    c = norm_categoria(categoria)
    if c == "TERCEIRO":
        return True
    m = str(modelo or "").upper().strip()
    return m in ("TERCEIRO", "TERCEIROS")


def eh_implemento(categoria, modelo=""):
    """Implemento acoplado: sem operador proprio (operador esta no trator)."""
    c = norm_categoria(categoria)
    m = str(modelo or "").upper().strip()
    if c in _CAT_MOTOR:
        return False
    if c in _CAT_IMPLEMENTO:
        return True
    # Legado: categoria vazia/antiga — inferir pelo modelo (match exato de palavra, nao substring)
    _motor_m = (
        "TRATOR", "COLHEIT", "CAMINH", "MAQUINA", "GERADOR", "MOTO", "XRE", "CRF",
        "AGRALE", "PULVER", "PLANTIO", "GRUA", "ESCAV", "T7", "T6", "PATROL",
    )
    if any(x in m for x in _motor_m):
        return False
    _impl_m = (
        "GRADE", "SULCAD", "CALCARE", "PLAINA", "ROLO", "ESCAR",
        "IMPLEMENTO", "REBOQUE", "CARRETA", "PLATAFORMA",
    )
    if any(x in m for x in _impl_m):
        return True
    return False


def excluir_disponibilidade(categoria, id_frota=""):
    """Parado x Operando: fora implemento, moto, caminhao e terceiros."""
    if eh_terceiro(categoria, id_frota=id_frota):
        return True
    c = norm_categoria(categoria)
    if eh_implemento(c, ""):
        return True
    return c in ("MOTO", "CAMINHAO", "VEICULO_LEVE", "VEICULO_PESADO", "TERCEIRO")



from st_supabase_connection import SupabaseConnection
conn = st.connection("supabase", type=SupabaseConnection, ttl=300)


def sb(table, order_col=None, desc=True):
    """Busca todos os registros (Supabase limita ~1000 por página)."""
    all_data = []
    page_size = 1000
    offset = 0
    while True:
        try:
            q = conn.client.table(table).select("*")
            if order_col:
                q = q.order(order_col, desc=desc)
            r = q.range(offset, offset + page_size - 1).execute()
        except Exception:
            try:
                r = (
                    conn.client.table(table)
                    .select("*")
                    .range(offset, offset + page_size - 1)
                    .execute()
                )
            except Exception:
                return pd.DataFrame()
        batch = r.data or []
        all_data.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size
    return pd.DataFrame(all_data)


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


def parse_mes_key(series):
    """Normaliza coluna de mês para string YYYY-MM."""
    if series is None or len(series) == 0:
        return pd.Series(dtype=str)
    raw = series.astype(str).str.strip()
    ym = raw.str.extract(r"(\d{4})[-/](\d{1,2})", expand=True)
    out = pd.Series(index=series.index, dtype="object")
    ok = ym[0].notna() & ym[1].notna()
    out.loc[ok] = ym.loc[ok, 0] + "-" + ym.loc[ok, 1].str.zfill(2)
    miss = ~ok
    if miss.any():
        dt = parse_dt(series[miss])
        out.loc[miss] = dt.dt.strftime("%Y-%m")
    return out


def fmt_mes_label(mes_key):
    """2026-06 -> Jun/2026 (eixo legivel, sem confundir com dias)."""
    try:
        return pd.Period(str(mes_key), freq="M").strftime("%b/%Y")
    except Exception:
        return str(mes_key)


def agregar_custo_mes(df, n=6, mes_ref=None):
    """Soma custo_total por mes (YYYY-MM). Ultimos n meses; meses vazios = zero."""
    if df.empty:
        return pd.DataFrame(columns=["mes_key", "mes_label", "custo_total"])
    tmp = df.copy()
    if "criado_em" in tmp.columns:
        tmp["mes_key"] = parse_mes_key(parse_dt(tmp["criado_em"]))
    elif "mes_key" in tmp.columns:
        tmp["mes_key"] = parse_mes_key(tmp["mes_key"])
    else:
        return pd.DataFrame(columns=["mes_key", "mes_label", "custo_total"])
    tmp["custo_total"] = pd.to_numeric(tmp["custo_total"], errors="coerce").fillna(0)
    tmp = tmp[tmp["mes_key"].notna() & (tmp["mes_key"].astype(str).str.len() >= 7)]
    g = tmp.groupby("mes_key", as_index=False)["custo_total"].sum()
    if mes_ref:
        fim = pd.Period(str(mes_ref), freq="M")
        chaves = [str(fim - i) for i in range(n - 1, -1, -1)]
        g = g.set_index("mes_key").reindex(chaves, fill_value=0).reset_index()
        g.columns = ["mes_key", "custo_total"]
    else:
        g = g.sort_values("mes_key").tail(n)
    g["mes_label"] = g["mes_key"].map(fmt_mes_label)
    return g


def meses_disponiveis(series, mes_atual_str, n=6):
    """Meses com dados + mês atual e anterior sempre visíveis."""
    meses = sorted({str(m) for m in series.dropna().unique() if str(m) not in ("", "NaT", "None")}, reverse=True)
    mes_atual = pd.Period(mes_atual_str, freq="M")
    mes_ant = mes_atual - 1
    for m in [str(mes_atual), str(mes_ant)]:
        if m not in meses:
            meses.insert(0, m)
    return sorted(set(meses), reverse=True)[:n]


@st.cache_data(ttl=120, show_spinner=False)
def load_disp(_c):
    df = sb("vw_disponibilidade_equipamentos", order_col="mes", desc=True)
    if df.empty:
        return df
    col_mes = next((c for c in ("mes", "mes_referencia", "competencia", "periodo") if c in df.columns), "mes")
    df["mes_key"] = parse_mes_key(df[col_mes])
    df["mes"] = pd.to_datetime(df["mes_key"] + "-01", errors="coerce")
    for col in ["dias_com_apontamento", "horas_trabalhadas", "horas_parada", "disponibilidade_pct", "total_os"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


@st.cache_data(ttl=120, show_spinner=False)
def load_horas_frota(_c, mes_atual_str):
    """View ao vivo do mês corrente (usada pelo painel de frota)."""
    df = sb("vw_horas_frota", order_col="disponibilidade_pct", desc=False)
    if df.empty:
        return df
    if "frota" in df.columns and "id_frota" not in df.columns:
        df["id_frota"] = df["frota"]
    if "modelo" not in df.columns and "frota" in df.columns:
        df["modelo"] = df["frota"]
    df["mes_key"] = mes_atual_str
    df["mes"] = pd.to_datetime(mes_atual_str + "-01", errors="coerce")
    if "dias_com_apontamento" not in df.columns:
        df["dias_com_apontamento"] = 0
    for col in ["dias_com_apontamento", "horas_trabalhadas", "horas_parada", "disponibilidade_pct", "total_os"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        else:
            df[col] = 0
    return df


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
    df = sb("vw_painel_os", order_col="created_at", desc=True)
    if df.empty:
        df = sb("ordem_servico", order_col="created_at", desc=True)
    if df.empty:
        return df
    df = df.copy()
    if "tipo_manutencao" not in df.columns:
        extra = sb("ordem_servico", order_col="created_at", desc=True)
        if not extra.empty and "tipo_manutencao" in extra.columns and "numero_os" in extra.columns:
            ex = extra[["numero_os", "tipo_manutencao"]].drop_duplicates(subset=["numero_os"], keep="first")
            df = df.merge(ex, on="numero_os", how="left")
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


def status_lub(hr):
    if pd.isna(hr):
        return "—"
    if hr < 0:
        return "EM ATRASO"
    if hr <= 100:
        return "PROXIMO"
    return "OK"


def horimetro_placeholder(h_atual, h_proxima):
    """Leitura 1/1 (ou igual e baixa) usada so para fechar OS — nao e horimetro real."""
    try:
        a = float(h_atual)
        p = float(h_proxima)
    except (TypeError, ValueError):
        return False
    return a <= 10 and p == a


def _aplicar_flags_horimetro(df, df_painel=None):
    """Placeholder OS + monitora_horimetro=false + frota fora do cadastro painel."""
    if "horimetro_placeholder" in df.columns:
        df["_placeholder"] = df["horimetro_placeholder"].fillna(False).astype(bool)
    else:
        df["_placeholder"] = df.apply(
            lambda r: horimetro_placeholder(r.get("h_atual"), r.get("h_proxima_troca")),
            axis=1,
        )
    if df_painel is not None and not df_painel.empty:
        ids_painel = set(df_painel["id_frota"].astype(str).str.strip())
        df["_fora_cadastro"] = ~df["_fid"].isin(ids_painel)
        if "monitora_horimetro" in df_painel.columns:
            mon_map = (
                df_painel.assign(id_frota=df_painel["id_frota"].astype(str).str.strip())
                .set_index("id_frota")["monitora_horimetro"]
            )
            df["_horimetro_quebrado"] = df["_fid"].map(
                lambda f: f in ids_painel and not bool(mon_map.get(str(f).strip(), True))
            )
        else:
            df["_horimetro_quebrado"] = False
    else:
        df["_fora_cadastro"] = False
        df["_horimetro_quebrado"] = False
    df["_sem_horimetro"] = (
        df["_sem_horimetro"]
        | df["_placeholder"]
        | df["_horimetro_quebrado"]
        | df["_fora_cadastro"]
    )
    return df


def filtrar_fin_lub_painel(df, df_painel):
    """Custos lub: so frotas cadastradas no painel e elegiveis (motorizadas)."""
    if df.empty or df_painel is None or df_painel.empty or "id_frota" not in df.columns:
        return df, 0
    painel = df_painel.copy()
    painel["id_frota"] = painel["id_frota"].astype(str).str.strip()
    elegiveis = painel[
        painel["monitora_horimetro"].fillna(True).astype(bool)
        & ~painel["categoria_painel"].isin(["IMPLEMENTO", "TERCEIRO"])
    ]["id_frota"]
    ids_ok = set(elegiveis.astype(str))
    df = df.copy()
    df["_fid"] = df["id_frota"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    mask = df["_fid"].isin(ids_ok) & (pd.to_numeric(df["custo_total"], errors="coerce").fillna(0) > 0)
    n_excl = int((~mask).sum())
    return df.loc[mask].drop(columns=["_fid"], errors="ignore"), n_excl


def enriquecer_lub(df_lub, df_frota, df_painel=None):
    """Marca implementos e linhas sem horímetro válido (não entram nos gráficos)."""
    if df_lub.empty:
        return df_lub
    df = df_lub.copy()
    col_frota = "vehicle" if "vehicle" in df.columns else ("id_frota" if "id_frota" in df.columns else "frota")
    df["_fid"] = (
        df[col_frota].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    )

    for col in ("h_atual", "h_proxima_troca", "horas_restantes"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["_sem_horimetro"] = df["h_atual"].isna() | df["h_proxima_troca"].isna() | df["horas_restantes"].isna()

    if "monitoravel" in df.columns:
        if "eh_terceiro" in df.columns:
            df["_terceiro"] = df["eh_terceiro"].fillna(False).astype(bool)
        else:
            cat_map = mapa_categoria_frota(df_frota, df_painel)
            df["_terceiro"] = df["_fid"].map(
                lambda fid: eh_terceiro(
                    (cat_map.get(str(fid).strip(), {}) or {}).get("categoria", ""),
                    (cat_map.get(str(fid).strip(), {}) or {}).get("modelo", ""),
                    fid,
                )
            )
        if "categoria_painel" in df.columns:
            df["_implemento"] = df.apply(
                lambda r: not r["_terceiro"] and eh_implemento(
                    r.get("categoria_painel", ""), r.get("modelo", "")
                ),
                axis=1,
            )
        else:
            df["_implemento"] = False
        df = _aplicar_flags_horimetro(df, df_painel)
        df["_monitoravel"] = (
            df["monitoravel"].fillna(False).astype(bool)
            & ~df["_placeholder"]
            & ~df["_horimetro_quebrado"]
            & ~df["_fora_cadastro"]
        )
        return df

    cat_map = mapa_categoria_frota(df_frota, df_painel)

    def eh_impl_frota(fid):
        meta = cat_map.get(str(fid).strip(), {})
        if eh_implemento(meta.get("categoria", ""), meta.get("modelo", "")):
            return True
        return False

    df["_implemento"] = df["_fid"].map(eh_impl_frota)
    df["_terceiro"] = df["_fid"].map(
        lambda fid: eh_terceiro(
            (cat_map.get(str(fid).strip(), {}) or {}).get("categoria", ""),
            (cat_map.get(str(fid).strip(), {}) or {}).get("modelo", ""),
            fid,
        )
    )
    if "modelo" in df.columns:
        m = df["modelo"].astype(str).str.upper()
        df["_implemento"] = df["_implemento"] | m.str.contains(
            r"GRADE|SULCAD|CALCARE|PLAINA|ROLO|\bIMP\b|REBOQUE|CARRETA|PLATAFORMA",
            na=False, regex=True)

    for col in ("h_atual", "h_proxima_troca", "horas_restantes"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["_sem_horimetro"] = df["h_atual"].isna() | df["h_proxima_troca"].isna() | df["horas_restantes"].isna()
    df = _aplicar_flags_horimetro(df, df_painel)
    df["_monitoravel"] = ~df["_implemento"] & ~df["_terceiro"] & ~df["_sem_horimetro"]
    return df


@st.cache_data(ttl=120, show_spinner=False)
def load_lub_painel(_c):
    """Camada painel: vw_painel_lub_status (classificacao + monitoravel no SQL)."""
    df = sb("vw_painel_lub_status", order_col="data_ref", desc=True)
    if df.empty:
        return df
    df = df.copy()
    df["vehicle"] = df["id_frota"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    for col in ("h_atual", "h_proxima_troca", "horas_restantes"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "status_troca" in df.columns:
        df.loc[df["status_troca"] == "SEM_HORIMETRO", "status_troca"] = pd.NA
    df["h_na_troca"] = pd.NA
    df["_fonte"] = "vw_painel_lub_status"
    if "fonte_horimetro" in df.columns:
        df["_fonte_horimetro"] = df["fonte_horimetro"].fillna("—")
    return df


@st.cache_data(ttl=120, show_spinner=False)
def load_lub_v4(_c):
    df = sb("vw_proxima_troca_v4")
    if df.empty:
        return df
    for col in ["horas_restantes", "h_atual", "h_proxima_troca", "h_na_troca"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "horas_restantes" not in df.columns and {"h_proxima_troca", "h_atual"}.issubset(df.columns):
        df["horas_restantes"] = df["h_proxima_troca"] - df["h_atual"]
    if "status_troca" not in df.columns and "horas_restantes" in df.columns:
        df["status_troca"] = df["horas_restantes"].apply(status_lub)
    df["_fonte"] = "vw_proxima_troca_v4"
    return df


@st.cache_data(ttl=120, show_spinner=False)
def load_lub_gestor(_c):
    """Painel lub: prioriza lubrificacao_v3 + ultima_troca_lubri (import Excel / app novo)."""
    df_v3 = sb("lubrificacao_v3", order_col="data_servico", desc=True)
    if df_v3.empty:
        return load_lub_v4(_c)

    df = (
        df_v3.sort_values("data_servico", ascending=False)
        .drop_duplicates(subset=["vehicle"], keep="first")
        .copy()
    )
    df["vehicle"] = df["vehicle"].astype(str).str.strip()
    df["h_atual"] = pd.to_numeric(df["hourmeter_atual"], errors="coerce")
    df["h_proxima_troca"] = pd.to_numeric(df["hourmeter_prox"], errors="coerce")

    df_ult = sb("ultima_troca_lubri")
    if not df_ult.empty:
        df_ult = df_ult.copy()
        df_ult["frota"] = df_ult["frota"].astype(str).str.strip()
        df = df.merge(
            df_ult[["frota", "horimetro_ultima_troca"]],
            left_on="vehicle",
            right_on="frota",
            how="left",
        )
        df["h_na_troca"] = pd.to_numeric(df["horimetro_ultima_troca"], errors="coerce")
    else:
        df["h_na_troca"] = pd.NA

    df_equip = sb("dim_equipamento_lubri")
    if not df_equip.empty:
        df_equip = df_equip.copy()
        df_equip["frota"] = df_equip["frota"].astype(str).str.strip()
        df = df.merge(
            df_equip[["frota", "modelo", "intervalo_horas"]],
            left_on="vehicle",
            right_on="frota",
            how="left",
            suffixes=("", "_eq"),
        )

    miss = df["h_na_troca"].isna() & df["observation"].notna()
    if miss.any():
        ext = df.loc[miss, "observation"].astype(str).str.extract(r"trocado\s+(\d+)", expand=False)
        df.loc[miss, "h_na_troca"] = pd.to_numeric(ext, errors="coerce")

    df["horas_restantes"] = df["h_proxima_troca"] - df["h_atual"]
    df["status_troca"] = df["horas_restantes"].apply(status_lub)
    df["_fonte"] = "lubrificacao_v3"
    return df


@st.cache_data(ttl=120, show_spinner=False)
def load_lub(_c):
    df = load_lub_painel(_c)
    if not df.empty:
        return df
    return load_lub_gestor(_c)


@st.cache_data(ttl=120, show_spinner=False)
def load_fin_lub(_c):
    df = sb("vw_painel_lub_fin", order_col="criado_em", desc=True)
    fonte = "vw_painel_lub_fin"
    if df.empty:
        df = sb("financeiro_lubrificacao", order_col="criado_em", desc=True)
        fonte = "financeiro_lubrificacao"
    if df.empty:
        return df
    df = df.copy()
    df["_fonte"] = fonte
    df["custo_total"] = pd.to_numeric(df["custo_total"], errors="coerce").fillna(0)
    if "criado_em" in df.columns:
        df["mes_key"] = parse_mes_key(parse_dt(df["criado_em"]))
    elif "mes_key" in df.columns:
        df["mes_key"] = parse_mes_key(df["mes_key"])
    return df


@st.cache_data(ttl=120, show_spinner=False)
def load_fin_lanc(_c):
    """Carrega financeiro_lancamento (NF-e de peças/serviços por frota)."""
    df = sb("financeiro_lancamento", order_col="data", desc=True)
    if df.empty:
        return df
    df = df.copy()
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df["mes_key"] = df["data"].dt.strftime("%Y-%m")
    df["data_fmt"] = df["data"].dt.strftime("%d/%m/%Y")
    for col in ("tipo_manutencao", "item", "id_frota", "nfe", "id_fornecedor_sap"):
        if col in df.columns:
            df[col] = df[col].fillna("—").astype(str)
    return df


def sem_acento(s):
    """Normaliza nomes para comparação: sem acento, maiúsculo, sem espaços nas pontas."""
    import unicodedata
    def _norm(x):
        x = "" if x is None else str(x)
        x = unicodedata.normalize("NFKD", x)
        x = x.encode("ascii", "ignore").decode("ascii")
        return x.strip().upper()
    return s.map(_norm)

def norm_frota_id(s):
    """3369 e 3369.0 viram a mesma chave (OS x apontamento_campo)."""
    return s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True)


def operador_apontamento(frota, data_os, df_apont):
    """Ultimo operador em apontamento_campo ate a data da OS (sem outras fontes)."""
    if df_apont is None or df_apont.empty:
        return ""
    fid = norm_frota_id(pd.Series([frota])).iloc[0]
    cand = df_apont[df_apont["frota"] == fid].sort_values("data")
    if cand.empty:
        return ""
    if pd.notna(data_os):
        ate = cand[cand["data"] <= data_os]
        return str(ate.iloc[-1]["operador"]) if not ate.empty else ""
    return str(cand.iloc[-1]["operador"])


@st.cache_data(ttl=300, show_spinner=False)
def load_apont(_c):
    """apontamento_campo: quem operou cada frota em cada data."""
    df = sb("apontamento_campo")
    if df.empty:
        return df
    df = df.copy()
    df["data"] = pd.to_datetime(df["data"], errors="coerce").dt.date
    df["frota"] = norm_frota_id(df["frota"])
    df["operador"] = sem_acento(df["operador"])
    return df.dropna(subset=["data"]).sort_values("data")


@st.cache_data(ttl=300, show_spinner=False)
def load_colab(_c):
    """dim_colaborador: custo_hora por nome (mecânicos e operadores)."""
    df = sb("dim_colaborador")
    if df.empty:
        return df
    df = df.copy()
    df["_nome"] = sem_acento(df["nome"])
    df["custo_hora"] = pd.to_numeric(df["custo_hora"], errors="coerce").fillna(0)
    return df[df["custo_hora"] > 0].drop_duplicates(subset=["_nome"], keep="first")

@st.cache_data(ttl=300, show_spinner=False)
def load_operadores(_c):
    """dim_operador_frota: vínculo frota ↔ operador (sem valor)."""
    df = sb("dim_operador_frota")
    if df.empty:
        return df
    df = df.copy()
    if "ativo" in df.columns:
        df = df[df["ativo"].astype(str).str.upper().isin(["TRUE", "1", "SIM", "S"])]
    df["id_frota"] = norm_frota_id(df["id_frota"])
    df["operador"] = sem_acento(df["operador"])
    return df.drop_duplicates(subset=["id_frota"], keep="first")


def mapa_busca_custo_hora(df_colab):
    """Retorna funcao nome -> custo_hora (dim_colaborador)."""
    if df_colab is None or df_colab.empty:
        return lambda _n: 0.0
    _ch = df_colab.set_index("_nome")["custo_hora"]
    _ch_fl = {}
    for _n, _v in _ch.items():
        _ts = str(_n).split()
        if len(_ts) >= 2:
            _k = (_ts[0], _ts[-1])
            _ch_fl[_k] = None if _k in _ch_fl else float(_v)

    def busca_ch(nome):
        nome = str(nome or "").strip()
        if not nome:
            return 0.0
        if nome in _ch.index:
            return float(_ch[nome])
        _ts = nome.split()
        if len(_ts) >= 2:
            _v = _ch_fl.get((_ts[0], _ts[-1]))
            if _v is not None:
                return _v
        if len(_ts) == 1:
            _pre = _ts[0]
            hits = [n for n in _ch.index if n == _pre or n.startswith(_pre + " ")]
            if len(hits) == 1:
                return float(_ch[hits[0]])
        return 0.0

    return busca_ch


def calc_parada_os(df_os, df_colab, df_apont, df_oper, df_frota, df_painel):
    """Tempo parada + operador + custo (mecanico + operador) por OS."""
    if df_os.empty:
        return df_os
    busca_ch = mapa_busca_custo_hora(df_colab)
    out = df_os.copy()
    out["_h"] = pd.to_numeric(out["tempo_min"], errors="coerce").fillna(0) / 60.0
    out["_mec"] = sem_acento(out["mecanico"]) if "mecanico" in out.columns else ""
    out["_c_mec"] = out["_h"] * out["_mec"].map(busca_ch)

    _cat_map = mapa_categoria_frota(df_frota, df_painel)
    _frotas_apont = set()
    if df_apont is not None and not df_apont.empty and "frota" in df_apont.columns:
        _frotas_apont = set(df_apont["frota"].astype(str).str.strip())

    def _eh_impl_frota(f):
        f = str(f).strip()
        if f in _frotas_apont:
            return False
        meta = _cat_map.get(f) or {}
        if eh_terceiro(meta.get("categoria", ""), meta.get("modelo", ""), f):
            return True
        return eh_implemento(meta.get("categoria", ""), meta.get("modelo", ""))

    out["_impl"] = out["id_frota"].astype(str).str.strip().str.replace(
        r"\.0$", "", regex=True).map(_eh_impl_frota)

    out["_oper"] = ""
    if "operador" in out.columns:
        out["_oper"] = sem_acento(out["operador"])
        out.loc[out["_oper"].isin(["NAN", "NONE", "<NA>", "NULL", "N/A", "-"]), "_oper"] = ""
    if df_apont is not None and not df_apont.empty and out["_oper"].eq("").any():
        for _i in out.index[out["_oper"].eq("") & ~out["_impl"]]:
            _op = operador_apontamento(out.at[_i, "id_frota"], out.at[_i, "data_os"], df_apont)
            if _op:
                out.at[_i, "_oper"] = _op
    if df_oper is not None and not df_oper.empty:
        _fmap = df_oper.set_index("id_frota")["operador"]
        _falta = out["_oper"].eq("") & ~out["_impl"]
        out.loc[_falta, "_oper"] = (
            norm_frota_id(out.loc[_falta, "id_frota"]).map(_fmap).fillna(""))
    out["_oper"] = sem_acento(out["_oper"])
    out.loc[out["_impl"], "_oper"] = ""
    out["_c_op"] = out["_h"] * out["_oper"].map(busca_ch)
    out.loc[out["_impl"], "_c_op"] = 0.0
    out["_c_tot"] = out["_c_mec"] + out["_c_op"]
    return out


@st.cache_data(ttl=120, show_spinner=False)
def load_abast(_c):
    df = sb("vw_painel_abastecimento", order_col="created_at", desc=True)
    if df.empty:
        df = sb("vw_abastecimento_consolidado", order_col="created_at", desc=True)
    if df.empty:
        return df
    df["dt"] = parse_dt(df["created_at"])
    df["data_os"] = df["dt"].dt.date
    df["dt_fmt"] = df["dt"].dt.strftime("%H:%M")
    df["liters"] = pd.to_numeric(df["liters"], errors="coerce").fillna(0)
    return df


@st.cache_data(ttl=120, show_spinner=False)
def load_transf(_c):
    df = sb("vw_painel_transferencias")
    if df.empty:
        df = sb("combustivel_transferencia")
    if df.empty:
        return df
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df["quantidade_l"] = pd.to_numeric(df["quantidade_l"], errors="coerce").fillna(0)
    return df


@st.cache_data(ttl=120, show_spinner=False)
def load_frota_painel(_c):
    df = sb("dim_frota_painel")
    if df.empty:
        return df
    df = df.copy()
    df["id_frota"] = df["id_frota"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    return df


@st.cache_data(ttl=120, show_spinner=False)
def load_frota(_c):
    for table in ("dim_frota", "frota", "cadastro_frota", "equipamentos", "vw_frota"):
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


def fmtR(n):
    if pd.isna(n):
        return "—"
    return f"R$ {n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def colunas_custo(df):
    """Detecta colunas de custo na tabela ordem_servico."""
    if df.empty:
        return {}
    lower = {c.lower(): c for c in df.columns}
    out = {}
    for key, aliases in {
        "pecas": ("custo_pecas", "valor_pecas", "custo_peca", "valor_peca", "pecas"),
        "mo": ("custo_mo", "valor_mo", "custo_mao_obra", "valor_mao_obra", "mao_obra"),
        "total": ("custo_total", "valor_total", "custo_os", "valor_os"),
    }.items():
        for a in aliases:
            if a in lower:
                out[key] = lower[a]
                break
    return out


@st.cache_data(ttl=120, show_spinner=False)
def load_financeiro(_c):
    """Carrega financeiro_os (repo sigcf-financeiro / financeiro_app.py)."""
    try:
        df = sb("financeiro_os", order_col="criado_em", desc=True)
        if df.empty:
            df = sb("financeiro_os")
    except Exception:
        return pd.DataFrame()
    if df.empty:
        return df
    df = df.copy()
    # Colunas reais: peca_valor, quantidade, valor_total_pecas, custo_mo, custo_total_os, criado_em, tipo_os
    if "valor_total_pecas" in df.columns:
        df["v_peca"] = pd.to_numeric(df["valor_total_pecas"], errors="coerce").fillna(0)
    elif "peca_valor" in df.columns and "quantidade" in df.columns:
        df["v_peca"] = (
            pd.to_numeric(df["peca_valor"], errors="coerce").fillna(0)
            * pd.to_numeric(df["quantidade"], errors="coerce").fillna(1)
        )
    elif "valor_unitario" in df.columns and "quantidade" in df.columns:
        df["v_peca"] = (
            pd.to_numeric(df["valor_unitario"], errors="coerce").fillna(0)
            * pd.to_numeric(df["quantidade"], errors="coerce").fillna(1)
        )
    else:
        df["v_peca"] = 0
    df["custo_mo"] = pd.to_numeric(
        df["custo_mo"] if "custo_mo" in df.columns else 0, errors="coerce"
    ).fillna(0)
    dt_col = "criado_em" if "criado_em" in df.columns else "created_at"
    if dt_col in df.columns:
        df["mes_key"] = parse_mes_key(parse_dt(df[dt_col]))
    mod_col = "tipo_os" if "tipo_os" in df.columns else None
    if mod_col:
        df["modulo"] = df[mod_col].astype(str).str.upper()
    return df


def norm_os(series):
    return series.astype(str).str.strip().str.upper()


def financeiro_do_mes(df_fin, df_os_mes, mes_label):
    """Custos das OS do mês selecionado (por numero_os, não só data do lançamento)."""
    if df_fin.empty:
        return df_fin
    if not df_os_mes.empty and "numero_os" in df_os_mes.columns and "numero_os" in df_fin.columns:
        nums = set(norm_os(df_os_mes["numero_os"]))
        out = df_fin[norm_os(df_fin["numero_os"]).isin(nums)].copy()
        if not out.empty:
            return out
    if "mes_key" in df_fin.columns:
        out = df_fin[df_fin["mes_key"] == mes_label].copy()
        if not out.empty:
            return out
    return df_fin.copy()


def resumo_financeiro_os(df_fin):
    """Agrega financeiro_os por OS (várias linhas = várias peças)."""
    if df_fin.empty or "numero_os" not in df_fin.columns:
        return pd.DataFrame()
    g = df_fin.groupby("numero_os")
    res = g["v_peca"].sum().rename("pecas").to_frame().join(
        g["custo_mo"].max().rename("custo_mo")
    ).reset_index()
    if "id_frota" in df_fin.columns:
        res = res.merge(g["id_frota"].first().reset_index(), on="numero_os", how="left")
    if "custo_total_os" in df_fin.columns:
        res = res.merge(g["custo_total_os"].max().reset_index(), on="numero_os", how="left")
        res = res.drop(columns=["custo_total_os"])
    res["total"] = res["pecas"] + res["custo_mo"]
    return res


# ── HEADER ────────────────────────────────────────────────────
h1, h2, h3 = st.columns([1, 8, 2])
with h1:
    st.image("https://raw.githubusercontent.com/lubrificacaomaquinassv-cloud/painel-frota-sv/main/icons/logo_sv.png", width=92)
with h2:
    st.markdown(
        '<div style="font-family:Barlow Condensed,sans-serif;">'
        '<div style="font-size:22px;font-weight:700;color:#e8edd0;letter-spacing:1px;">'
        'GESTOR DA OFICINA — SANTA VERGÍNIA</div>'
        '<div style="font-size:11px;color:#8aab80;letter-spacing:2px;margin-top:2px;">'
        'OS · Lubrificação · Borracharia · Comboio · Disponibilidade · Camada Painel</div></div>',
        unsafe_allow_html=True,
    )
with h3:
    if st.button("🔄 Atualizar", key="refresh"):
        st.cache_data.clear()
        st.rerun()
    agora_br = datetime.utcnow() - timedelta(hours=3)
    st.caption(agora_br.strftime("%d/%m/%Y %H:%M") + " (Brasília)")
    st.caption(f"Build {PAINEL_BUILD}")

st.divider()

hoje = (datetime.utcnow() - timedelta(hours=3)).date()
mes_ini = hoje.replace(day=1)
mes_atual_str = pd.Period(hoje, freq="M").strftime("%Y-%m")

df_os = load_os(conn)
df_bor = load_bor(conn)
df_lub = load_lub(conn)
df_fin_lub = load_fin_lub(conn)
df_abast = load_abast(conn)
df_transf = load_transf(conn)
df_disp = load_disp(conn)
df_horas = load_horas_frota(conn, mes_atual_str)
df_frota = load_frota(conn)
df_painel = load_frota_painel(conn)
df_fin = load_financeiro(conn)
df_fin_lanc = load_fin_lanc(conn)
df_colab = load_colab(conn)
df_oper = load_operadores(conn)
df_apont = load_apont(conn)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔧 Ordens de Serviço",
    "🛢 Lubrificação & Borracharia",
    "⛽ Comboio",
    "📊 Parado × Operando",
    "💰 Financeiro",
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
        meses_label = meses_disponiveis(df_os["mes_os"], mes_atual_str, n=8)
        idx_default = meses_label.index(mes_atual_str) if mes_atual_str in meses_label else 0
        mes_sel_label = st.selectbox(
            "Selecionar mês:",
            options=meses_label,
            index=idx_default,
            key="sel_mes_os",
        )
        mes_sel = pd.Period(mes_sel_label, freq="M")
        df_mes_sel = df_os[df_os["mes_os"] == mes_sel].sort_values(["os_num", "dt"], ascending=False)

        # fallback: se mês atual tem OS hoje mas mes_os falhou no parse
        if df_mes_sel.empty and mes_sel_label == mes_atual_str and not os_hoje.empty:
            df_mes_sel = os_hoje.sort_values(["os_num", "dt"], ascending=False)
        elif df_mes_sel.empty and mes_sel_label == mes_atual_str and not os_mes.empty:
            df_mes_sel = os_mes.sort_values(["os_num", "dt"], ascending=False)

        st.caption(f"{len(df_mes_sel)} OS em {mes_sel_label}")

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
                    **PDARK, height=260,
                    xaxis={**PLOT_AXIS},
                    yaxis={**PLOT_AXIS, "tickfont": dict(color="#e8edd0", size=12)},
                )
                st.plotly_chart(fig, use_container_width=True, key="k_sis")

            with col_r2:
                st.markdown(
                    f'<div class="sec">Mecânicos — produtividade · {mes_sel_label}</div>',
                    unsafe_allow_html=True,
                )
                r = (
                    df_mes_sel.groupby("mecanico")
                    .agg(qtd=("numero_os", "count"), tempo_h=("tempo_min", lambda x: x.sum() / 60))
                    .reset_index()
                    .sort_values("qtd", ascending=True)
                    .tail(8)
                )
                r["mecanico"] = r["mecanico"].fillna("Não informado")
                fig = go.Figure(go.Bar(
                    y=r["mecanico"], x=r["qtd"], orientation="h",
                    marker_color="#2980b9",
                    text=r["qtd"], textposition="outside",
                    textfont=dict(color="#e8edd0", size=13),
                    customdata=r["tempo_h"].round(1),
                    hovertemplate=(
                        "Mecânico: %{y}<br>OS no período: %{x}<br>"
                        "Tempo total: %{customdata:.1f}h<extra></extra>"
                    ),
                ))
                fig.update_layout(
                    **PDARK, height=260,
                    xaxis={**PLOT_AXIS, "title": "Quantidade de OS"},
                    yaxis={**PLOT_AXIS, "tickfont": dict(color="#e8edd0", size=12)},
                )
                st.plotly_chart(fig, use_container_width=True, key="k_mec")

        if df_mes_sel.empty:
            st.info(f"Nenhuma OS em {mes_sel_label}.")
        else:
            st.markdown(
                f'<div class="sec">Lista de OS — {mes_sel_label}</div>',
                unsafe_allow_html=True,
            )
            cols_t = ["numero_os", "id_frota", "sistema", "tipo_manutencao", "status", "mecanico", "dt_fmt"]
            df_t = df_mes_sel[cols_t].copy()
            dfp = calc_parada_os(df_mes_sel, df_colab, df_apont, df_oper, df_frota, df_painel)
            df_t["parada"] = dfp["_h"].apply(
                lambda v: f"{v * 60:.0f} min ({v:.1f}h)" if v > 0 else "—")
            df_t["operador"] = dfp.apply(
                lambda r: "N/A — implemento" if r.get("_impl") else (
                    r["_oper"] if r.get("_oper") else "—"),
                axis=1,
            )
            names = ["OS", "Frota", "Sistema", "Tipo", "Status", "Mecânico", "Data/Hora", "Parada", "Operador"]
            if not df_colab.empty:
                df_t["custo_parada"] = dfp["_c_tot"].apply(lambda v: fmtR(v) if v > 0 else "—")
                names.append("Custo parada")
            df_t.columns = names
            st.caption(
                "Parada e operador vêm da OS/apontamento. "
                "Custo parada = tempo × custo_hora (detalhe na aba Financeiro). "
                "Peças/NF-e ficam em Financeiro → Lançamentos."
            )
            dark_table(df_t, height=420)

# ══════════════════════════════════════════════════════════════
# TAB 2 — LUBRIFICAÇÃO + BORRACHARIA
# ══════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="sec">Lubrificação — painel analítico</div>', unsafe_allow_html=True)

    if df_lub.empty:
        st.info("Sem dados de lubrificação (vw_painel_lub_status).")
    else:
        fonte = df_lub["_fonte"].iloc[0] if "_fonte" in df_lub.columns else "—"
        col_frota = (
            "vehicle" if "vehicle" in df_lub.columns
            else "id_frota" if "id_frota" in df_lub.columns
            else "frota"
        )
        df_lub_e = enriquecer_lub(df_lub, df_frota, df_painel)
        df_mon = df_lub_e[df_lub_e["_monitoravel"]].copy()
        df_excl = df_lub_e[~df_lub_e["_monitoravel"]].copy()

        n_impl = int(df_excl["_implemento"].sum())
        n_sem_h = int((~df_excl["_implemento"] & df_excl["_sem_horimetro"]).sum())
        n_ph = int(df_excl.get("_placeholder", pd.Series(False, index=df_excl.index)).sum())
        n_quebr = int(df_excl.get("_horimetro_quebrado", pd.Series(False, index=df_excl.index)).sum())
        n_fora = int(df_excl.get("_fora_cadastro", pd.Series(False, index=df_excl.index)).sum())
        df_lub_u = df_mon.sort_values("horas_restantes", ascending=True)

        ok = int((df_lub_u["status_troca"] == "OK").sum())
        prx = int((df_lub_u["status_troca"] == "PROXIMO").sum())
        atr = int((df_lub_u["status_troca"] == "EM ATRASO").sum())
        st.caption(
            f"Fonte horímetros: {fonte} · {len(df_mon)} motorizados com horímetro · "
            f"{len(df_lub_e)} cadastrados no total"
        )
        if not df_excl.empty:
            st.caption(
                f"Fora dos gráficos: {n_impl} implemento(s) · {n_quebr} horímetro quebrado · "
                f"{n_ph} placeholder OS · {n_fora} fora do cadastro painel · {n_sem_h} sem horímetro."
            )

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("✅ OK", ok)
        m2.metric("⚠️ Próximo ≤100h", prx)
        m3.metric("🔴 Em atraso", atr)
        m4.metric("📋 Monitorados", len(df_mon))

        g1, g2 = st.columns([1, 2])
        with g1:
            fig_st = go.Figure(go.Pie(
                labels=["OK", "Próximo", "Em atraso"],
                values=[ok, prx, atr],
                hole=0.55,
                marker=dict(colors=["#4a9e3f", "#d4a017", "#c0392b"]),
                textinfo="label+value",
                textfont=dict(color="#e8edd0", size=11),
            ))
            fig_st.update_layout(
                **PDARK, height=280,
                title=dict(text="Status — só motorizados", font=dict(size=13, color="#8aab80")),
                showlegend=False,
            )
            st.plotly_chart(fig_st, use_container_width=True, key="k_lub_status")

        with g2:
            top_u = df_lub_u[
                df_lub_u["status_troca"].isin(["EM ATRASO", "PROXIMO"])
                & df_lub_u["horas_restantes"].notna()
            ].head(12)
            if top_u.empty:
                st.info("Nenhum motorizado em atraso ou próximo da troca.")
            else:
                cores = top_u["status_troca"].map({
                    "OK": "#4a9e3f", "PROXIMO": "#d4a017", "EM ATRASO": "#c0392b",
                }).fillna("#666")
                fig_u = go.Figure(go.Bar(
                    y=top_u[col_frota].astype(str),
                    x=top_u["horas_restantes"],
                    orientation="h",
                    marker_color=cores,
                    text=top_u["horas_restantes"].apply(lambda v: f"{v:+.0f}h"),
                    textposition="outside",
                    textfont=dict(color="#e8edd0", size=11),
                ))
                fig_u.update_layout(
                    **PDARK, height=280,
                    title=dict(
                        text="Urgência — horas restantes (próxima − atual)",
                        font=dict(size=13, color="#8aab80"),
                    ),
                    xaxis={**PLOT_AXIS, "title": "Horas restantes", "zeroline": True},
                    yaxis={**PLOT_AXIS, "autorange": "reversed"},
                )
                fig_u.add_vline(x=0, line_dash="dash", line_color="#888", line_width=1)
                fig_u.add_vline(x=100, line_dash="dot", line_color="#d4a017", line_width=1)
                st.plotly_chart(fig_u, use_container_width=True, key="k_lub_urg")
                st.caption(
                    "Negativo = passou da troca · 0 a 100h = alerta · implementos não entram neste gráfico."
                )

        if not df_excl.empty:
            with st.expander(f"Cadastros fora do painel de horímetro ({len(df_excl)})"):
                dx = df_excl[[col_frota]].copy()
                dx["Motivo"] = df_excl.apply(
                    lambda r: "Implemento (sem horímetro de troca)"
                    if r["_implemento"]
                    else "Horímetro quebrado (cadastro painel)"
                    if r.get("_horimetro_quebrado")
                    else "Leitura placeholder (1/1 na OS)"
                    if r.get("_placeholder")
                    else "Frota fora do cadastro painel"
                    if r.get("_fora_cadastro")
                    else "Frota de terceiros"
                    if r.get("_terceiro")
                    else "Sem horímetro válido",
                    axis=1,
                )
                if "modelo" in df_excl.columns:
                    dx["Modelo"] = df_excl["modelo"].fillna("—")
                dx = dx.rename(columns={col_frota: "Frota"})
                dark_table(dx, height=180)

        st.markdown('<div class="sec">Detalhe horímetros — motorizados</div>', unsafe_allow_html=True)

        def badge(s):
            return {"OK": "🟢 OK", "PROXIMO": "🟡 PRÓXIMO", "EM ATRASO": "🔴 EM ATRASO"}.get(s, f"⚪ {s}")

        cols_show = [col_frota, "h_na_troca", "h_proxima_troca", "h_atual", "horas_restantes", "status_troca"]
        cols_show = [c for c in cols_show if c in df_lub_u.columns]
        dt = df_lub_u.head(20)[cols_show].copy()
        dt["h_na_troca"] = dt["h_na_troca"].apply(lambda v: f"{v:.0f}" if pd.notna(v) else "—")
        dt["h_proxima_troca"] = dt["h_proxima_troca"].apply(lambda v: f"{v:.0f}" if pd.notna(v) else "—")
        dt["h_atual"] = dt["h_atual"].apply(lambda v: f"{v:.0f}" if pd.notna(v) else "—")
        dt["horas_restantes"] = dt["horas_restantes"].apply(
            lambda v: f"{v:+.0f}h" if pd.notna(v) else "—")
        dt["status_troca"] = dt["status_troca"].apply(badge)
        dt = dt.rename(columns={
            col_frota: "Frota", "h_na_troca": "H. Troca", "h_proxima_troca": "Próxima (h)",
            "h_atual": "H. Atual", "horas_restantes": "Restante", "status_troca": "Status",
        })
        dark_table(dt, height=380)

    st.divider()
    st.markdown('<div class="sec">Custos lubrificação — vw_painel_lub_fin</div>', unsafe_allow_html=True)

    if df_fin_lub.empty or "mes_key" not in df_fin_lub.columns:
        st.info("Sem lançamentos em vw_painel_lub_fin.")
    else:
        meses_lub = meses_disponiveis(df_fin_lub["mes_key"], mes_atual_str, n=8)
        idx_lub = meses_lub.index(mes_atual_str) if mes_atual_str in meses_lub else 0
        mes_lub_sel = st.selectbox(
            "Mês dos custos:",
            options=meses_lub,
            index=idx_lub,
            key="sel_mes_lub",
        )
        fin_m_raw = df_fin_lub[df_fin_lub["mes_key"] == mes_lub_sel].copy()
        fin_m, n_fin_excl = filtrar_fin_lub_painel(fin_m_raw, df_painel)
        fin_fonte = df_fin_lub["_fonte"].iloc[0] if "_fonte" in df_fin_lub.columns else "vw_painel_lub_fin"
        if fin_m.empty:
            st.info(
                "Nenhum custo elegivel neste mes "
                "(implementos, terceiros e horimetro quebrado ficam fora do painel)."
            )
        fin_m["custo_total"] = pd.to_numeric(fin_m["custo_total"], errors="coerce").fillna(0)
        fin_m["quantidade"] = pd.to_numeric(fin_m.get("quantidade", 0), errors="coerce").fillna(0)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 Total", fmtR(fin_m["custo_total"].sum()))
        c2.metric("📋 Itens", len(fin_m))
        c3.metric("🚜 Frotas", fin_m["id_frota"].nunique() if "id_frota" in fin_m.columns else 0)
        c4.metric("🛢 Litros (aprox.)", fmt(fin_m["quantidade"].sum(), 1))

        evo = agregar_custo_mes(df_fin_lub, n=6, mes_ref=mes_lub_sel)
        cg1, cg2, cg3 = st.columns([1, 1, 1])
        with cg1:
            if not evo.empty:
                cores_evo = ["#4a9e3f" if v > 0 else "#2a3a28" for v in evo["custo_total"]]
                fig_evo = go.Figure(go.Bar(
                    x=evo["mes_label"],
                    y=evo["custo_total"],
                    marker_color=cores_evo,
                    text=evo["custo_total"].apply(lambda v: fmtR(v) if v > 0 else ""),
                    textposition="outside",
                    textfont=dict(color="#e8edd0", size=10),
                ))
                fig_evo.update_layout(
                    **PDARK, height=260,
                    title=dict(text="Evolução mensal (R$)", font=dict(size=12, color="#8aab80")),
                    xaxis={**PLOT_AXIS, "type": "category", "title": "Mês"},
                    yaxis={**PLOT_AXIS, "title": "Total"},
                )
                st.plotly_chart(fig_evo, use_container_width=True, key="k_lub_evo")
                st.caption("Histórico completo do financeiro (todos os lançamentos).")

        with cg2:
            if not fin_m.empty and "id_frota" in fin_m.columns:
                fm = fin_m.copy()
                fm["_fid"] = norm_frota_id(fm["id_frota"])
                rf = (
                    fm[fm["custo_total"] > 0]
                    .groupby("_fid", as_index=False)["custo_total"].sum()
                    .sort_values("custo_total", ascending=True)
                    .tail(8)
                )
                if rf.empty:
                    st.caption("Sem custo por frota neste mês.")
                else:
                    rf["frota"] = rf["_fid"].astype(str)
                    fig_f = go.Figure(go.Bar(
                        y=rf["frota"], x=rf["custo_total"], orientation="h",
                        marker_color="#2980b9",
                        text=rf["custo_total"].apply(fmtR), textposition="inside",
                        insidetextanchor="end",
                        textfont=dict(color="#ffffff", size=11),
                    ))
                    fig_f.update_layout(
                        **PDARK,
                        height=max(160, len(rf) * 44 + 60),
                        title=dict(text=f"Custo por frota — {mes_lub_sel}", font=dict(size=12, color="#8aab80")),
                        xaxis={**PLOT_AXIS, "title": "R$"},
                        yaxis={**PLOT_AXIS, "type": "category", "categoryorder": "total ascending"},
                    )
                    st.plotly_chart(fig_f, use_container_width=True, key="k_lub_frota")

        with cg3:
            if not fin_m.empty and "insumo_nome" in fin_m.columns:
                ri = (
                    fin_m[fin_m["custo_total"] > 0]
                    .groupby("insumo_nome")["custo_total"].sum()
                    .reset_index().sort_values("custo_total", ascending=True).tail(8)
                )
                if ri.empty:
                    st.caption("Sem insumos com custo neste mês.")
                else:
                    fig_i = go.Figure(go.Bar(
                        y=ri["insumo_nome"].astype(str), x=ri["custo_total"], orientation="h",
                        marker_color="#8e44ad",
                        text=ri["custo_total"].apply(fmtR), textposition="inside",
                        insidetextanchor="end",
                        textfont=dict(color="#ffffff", size=10),
                    ))
                    fig_i.update_layout(
                        **PDARK,
                        height=max(160, len(ri) * 40 + 60),
                        title=dict(text=f"Top insumos — {mes_lub_sel}", font=dict(size=12, color="#8aab80")),
                        xaxis={**PLOT_AXIS, "title": "R$"},
                        yaxis={**PLOT_AXIS, "type": "category", "categoryorder": "total ascending"},
                    )
                    st.plotly_chart(fig_i, use_container_width=True, key="k_lub_insumo")

        st.caption(
            f"Fonte: {fin_fonte} · exibindo só frotas motorizadas do painel "
            f"({n_fin_excl} linha(s) do mês excluídas: implemento/terceiro/horimetro quebrado). "
            "lubrificacao_v2 (litros campo) nao entra aqui — use AUDITAR_LUBRIFICACAO_V2.sql."
        )
        cols_fin = [c for c in ["id_frota", "insumo_nome", "quantidade", "valor_unitario",
                                "custo_total", "order_number", "localizacao"]
                    if c in fin_m.columns]
        dfin = fin_m.sort_values("custo_total", ascending=False)[cols_fin].copy()
        if "quantidade" in dfin.columns:
            dfin["quantidade"] = dfin["quantidade"].apply(lambda v: fmt(v, 1))
        if "valor_unitario" in dfin.columns:
            dfin["valor_unitario"] = dfin["valor_unitario"].apply(fmtR)
        if "custo_total" in dfin.columns:
            dfin["custo_total"] = dfin["custo_total"].apply(fmtR)
        dfin = dfin.rename(columns={
            "id_frota": "Frota", "insumo_nome": "Insumo", "quantidade": "Qtd",
            "valor_unitario": "R$/un", "custo_total": "Total", "order_number": "Ordem",
            "localizacao": "Local",
        })
        dark_table(dfin, height=320)

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
        f'<div class="sec">Volume diário abastecido — {mes_ini.strftime("%b/%Y")} (L)</div>',
        unsafe_allow_html=True,
    )
    if not df_abast.empty:
        dm = df_abast[df_abast["data_os"] >= mes_ini].copy()
        if not dm.empty:
            dm["dia"] = pd.to_datetime(dm["data_os"]).dt.strftime("%d/%m")
            pd_dia = dm.groupby("dia")["liters"].sum().reset_index()
            fig = go.Figure(go.Bar(
                x=pd_dia["dia"], y=pd_dia["liters"],
                marker_color="#4a9e3f",
                text=pd_dia["liters"].apply(lambda v: f"{v:,.0f}L"),
                textposition="outside",
                textfont=dict(color="#e8edd0", size=11),
                hovertemplate="Dia %{x}<br>Volume: %{y:,.0f} L<extra></extra>",
            ))
            fig.update_layout(
                **PDARK, height=250,
                xaxis={**PLOT_AXIS, "title": "Dia do mês"},
                yaxis={**PLOT_AXIS, "title": "Litros"},
            )
            st.plotly_chart(fig, use_container_width=True, key="k_vol_dia")
        elif "fuel_type" in df_abast.columns:
            pf = df_abast.groupby("fuel_type")["liters"].sum().reset_index()
            fig = go.Figure(go.Pie(
                labels=pf["fuel_type"], values=pf["liters"],
                textinfo="label+percent", textfont=dict(color="#e8edd0"),
                marker=dict(colors=["#4a9e3f", "#2980b9", "#d4a017"]),
            ))
            fig.update_layout(**PDARK, height=250)
            st.plotly_chart(fig, use_container_width=True, key="k_vol_tipo")

# ══════════════════════════════════════════════════════════════
# TAB 4 — PARADO × OPERANDO (somente tratores)
# ══════════════════════════════════════════════════════════════
with tab4:
    if df_disp.empty and df_horas.empty:
        st.warning("Sem dados de disponibilidade.")
    else:
        meses_hist = (
            meses_disponiveis(df_disp["mes_key"], mes_atual_str, n=6)
            if not df_disp.empty else []
        )
        meses_d_label = list(meses_hist)
        if not df_horas.empty and mes_atual_str not in meses_d_label:
            meses_d_label.insert(0, mes_atual_str)
        if not meses_d_label:
            meses_d_label = [mes_atual_str]

        idx_d = meses_d_label.index(mes_atual_str) if mes_atual_str in meses_d_label else 0
        mes_d_sel = st.selectbox(
            "Mês de referência:",
            options=meses_d_label,
            index=idx_d,
            key="sel_mes_disp",
        )

        # Junho (mês atual) → view ao vivo vw_horas_frota | demais → histórico
        if mes_d_sel == mes_atual_str and not df_horas.empty:
            dmes_raw = df_horas.copy()
            fonte = "vw_horas_frota (mês corrente)"
        elif not df_disp.empty:
            dmes_raw = df_disp[df_disp["mes_key"] == mes_d_sel].copy()
            fonte = "vw_disponibilidade_equipamentos"
        else:
            dmes_raw = pd.DataFrame()
            fonte = ""

        dmes = filtrar_tratores(dmes_raw, df_frota, df_painel)
        if not dmes.empty:
            dmes["label"] = dmes.apply(label_trator, axis=1)
        excluidos = len(dmes_raw) - len(dmes)

        if dmes.empty:
            if not dmes_raw.empty:
                st.warning(
                    f"Encontrados {len(dmes_raw)} registros em {mes_d_sel}, "
                    "mas nenhum trator após excluir implementos."
                )
            else:
                st.info(f"Sem dados de tratores para {mes_d_sel}.")
        else:
            mlabel = mes_d_sel
            if mes_d_sel == mes_atual_str:
                st.caption(f"Fonte: {fonte} · dados atualizados em tempo real")
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
                    y=dd["label"], x=dd["horas_trabalhadas"],
                    orientation="h", marker_color="#4a9e3f",
                    text=dd["horas_trabalhadas"].apply(lambda v: f"{v:.0f}h"),
                    textposition="inside", textfont=dict(color="#e8edd0", size=11),
                    hovertemplate="%{y}<br>Horas trabalhadas: %{x:.0f}h<extra></extra>",
                ))
                fig.add_trace(go.Bar(
                    name="🔴 Paradas",
                    y=dd["label"], x=dd["horas_parada"],
                    orientation="h", marker_color="#c0392b",
                    text=dd["horas_parada"].apply(lambda v: f"{v:.0f}h" if v > 0 else ""),
                    textposition="inside", textfont=dict(color="#e8edd0", size=11),
                    hovertemplate="%{y}<br>Horas paradas: %{x:.0f}h<extra></extra>",
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
                    y=dd2["label"], x=dd2["disponibilidade_pct"],
                    orientation="h", marker_color=cores.tolist(),
                    text=dd2["disponibilidade_pct"].apply(lambda v: f"{v:.1f}%"),
                    textposition="outside",
                    textfont=dict(color="#e8edd0", size=12),
                    hovertemplate="%{y}<br>Disponibilidade: %{x:.1f}%<extra></extra>",
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

# ══════════════════════════════════════════════════════════════
# TAB 5 — FINANCEIRO (financeiro_lancamento)
# ══════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="sec">Financeiro — lançamentos de manutenção (NF-e) · financeiro_lancamento</div>', unsafe_allow_html=True)
    if df_fin_lanc.empty:
        st.info("Sem lançamentos na tabela financeiro_lancamento.")
    else:
        meses_fin = meses_disponiveis(df_fin_lanc["mes_key"], mes_atual_str, n=8)
        idx_fin = meses_fin.index(mes_atual_str) if mes_atual_str in meses_fin else 0
        mes_fin_sel = st.selectbox(
            "Selecionar mês:",
            options=meses_fin,
            index=idx_fin,
            key="sel_mes_fin",
        )
        dfl = df_fin_lanc[df_fin_lanc["mes_key"] == mes_fin_sel].copy()

        f1, f2, f3, f4 = st.columns(4)
        f1.metric("💰 Total no Mês", fmtR(dfl["valor"].sum()))
        f2.metric("📋 Lançamentos", len(dfl))
        f3.metric("🚜 Frotas", dfl["id_frota"].nunique() if "id_frota" in dfl.columns else 0)
        f4.metric("📄 NF-e", dfl["nfe"].nunique() if "nfe" in dfl.columns else 0)

        if dfl.empty:
            st.info(f"Nenhum lançamento em {mes_fin_sel}.")
        else:
            cf1, cf2 = st.columns(2)

            with cf1:
                st.markdown(
                    f'<div class="sec">Custo por tipo de manutenção — {mes_fin_sel}</div>',
                    unsafe_allow_html=True,
                )
                if "tipo_manutencao" in dfl.columns:
                    r = (
                        dfl.groupby("tipo_manutencao")["valor"].sum().reset_index()
                        .sort_values("valor", ascending=True).tail(8)
                    )
                    fig = go.Figure(go.Bar(
                        y=r["tipo_manutencao"], x=r["valor"], orientation="h",
                        marker_color="#4a9e3f",
                        text=r["valor"].apply(fmtR), textposition="outside",
                        textfont=dict(color="#e8edd0", size=12),
                        hovertemplate="%{y}<br>R$ %{x:,.2f}<extra></extra>",
                    ))
                    fig.update_layout(
                        **PDARK, height=280,
                        xaxis={**PLOT_AXIS},
                        yaxis={**PLOT_AXIS, "tickfont": dict(color="#e8edd0", size=12)},
                    )
                    st.plotly_chart(fig, use_container_width=True, key="k_fin_tipo")

            with cf2:
                st.markdown(
                    f'<div class="sec">Top 10 frotas por custo — {mes_fin_sel}</div>',
                    unsafe_allow_html=True,
                )
                if "id_frota" in dfl.columns:
                    r = (
                        dfl.groupby("id_frota")["valor"].sum().reset_index()
                        .sort_values("valor", ascending=True).tail(10)
                    )
                    fig = go.Figure(go.Bar(
                        y=r["id_frota"].astype(str), x=r["valor"], orientation="h",
                        marker_color="#2980b9",
                        text=r["valor"].apply(fmtR), textposition="outside",
                        textfont=dict(color="#e8edd0", size=12),
                        hovertemplate="Frota %{y}<br>R$ %{x:,.2f}<extra></extra>",
                    ))
                    fig.update_layout(
                        **PDARK, height=280,
                        xaxis={**PLOT_AXIS},
                        yaxis={**PLOT_AXIS, "tickfont": dict(color="#e8edd0", size=12)},
                    )
                    st.plotly_chart(fig, use_container_width=True, key="k_fin_frota")

            st.markdown(f'<div class="sec">Custo da parada — hora mecânico + hora operador · {mes_fin_sel}</div>', unsafe_allow_html=True)
            df_os_fin = df_os[df_os["mes_os"].astype(str) == mes_fin_sel].copy() if not df_os.empty else pd.DataFrame()
            if df_os_fin.empty:
                st.info(f"Nenhuma OS em {mes_fin_sel} para calcular o custo da parada.")
            elif df_colab.empty:
                st.info("Cadastre o custo_hora na dim_colaborador para calcular o custo da parada.")
            else:
                _dfp = calc_parada_os(df_os_fin, df_colab, df_apont, df_oper, df_frota, df_painel)

                p1, p2, p3, p4 = st.columns(4)
                p1.metric("⏱ Horas Paradas", f"{fmt(_dfp['_h'].sum(), 1)}h",
                          help="Soma do tempo (hora entrada → saída) das OS do mês")
                p2.metric("🔧 Custo Mecânico", fmtR(_dfp["_c_mec"].sum()),
                          help="Tempo da OS × custo_hora do mecânico (dim_colaborador)")
                p3.metric("👨‍🌾 Custo Operador", fmtR(_dfp["_c_op"].sum()),
                          help="Tempo da OS × custo_hora do operador parado (dim_colaborador)")
                p4.metric("💸 Custo Total da Parada", fmtR(_dfp["_c_tot"].sum()))
                st.caption("Cálculo: tempo da OS × custo_hora da dim_colaborador. "
                           "Operador (só trator): 1º apontado na OS; 2º apontamento_campo até a data da OS. "
                           "Implementos acoplados: custo operador N/A (operador no trator).")

                _tp = _dfp[_dfp["_h"] > 0].sort_values("_c_tot", ascending=False).head(30)
                if _tp.empty:
                    st.info("As OS do mês não têm tempo de parada registrado (hora entrada/saída).")
                else:
                    _t = pd.DataFrame({
                        "OS": _tp["numero_os"],
                        "Frota": _tp["id_frota"],
                        "Parada": _tp["_h"].apply(lambda v: f"{v * 60:.0f} min ({v:.1f}h)"),
                        "Mecânico": _tp["mecanico"],
                        "R$ Mecânico": _tp["_c_mec"].apply(fmtR),
                        "Operador": _tp.apply(
                        lambda r: "N/A — implemento" if r.get("_impl") else (
                            r["_oper"] if r["_oper"] else "—"), axis=1),
                        "R$ Operador": _tp["_c_op"].apply(fmtR),
                        "Total Parada": _tp["_c_tot"].apply(fmtR),
                    })
                    dark_table(_t, height=420)

            st.markdown(f'<div class="sec">Lançamentos — {mes_fin_sel}</div>', unsafe_allow_html=True)
            cols_f = [c for c in ["data_fmt", "nfe", "id_fornecedor_sap", "item",
                                  "tipo_manutencao", "id_frota", "valor", "observacao"]
                      if c in dfl.columns]
            dtf = dfl.sort_values("data", ascending=False)[cols_f].copy()
            if "valor" in dtf.columns:
                dtf["valor"] = dtf["valor"].apply(fmtR)
            if "observacao" in dtf.columns:
                dtf["observacao"] = dtf["observacao"].fillna("—")
            ren = {
                "data_fmt": "Data", "nfe": "NF-e", "id_fornecedor_sap": "Fornecedor (SAP)",
                "item": "Item", "tipo_manutencao": "Tipo", "id_frota": "Frota",
                "valor": "Valor", "observacao": "Observação",
            }
            dtf.columns = [ren.get(c, c) for c in cols_f]
            dark_table(dtf, height=420)


st.divider()
st.markdown(
    '<div style="text-align:center;color:#4a6644;font-size:11px;font-family:Barlow Condensed,sans-serif;'
    'letter-spacing:1px;padding:8px 0;">'
    'Santa Vergínia Agropecuária e Florestal · Controladoria · Gestor Oficina</div>',
    unsafe_allow_html=True,
)
