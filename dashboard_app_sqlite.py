import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import os

# ------------------------
# Configurações iniciais
# ------------------------
st.set_page_config(page_title="Dashboard de Saúde (SQLite)", layout="wide")
st.title("📊 Dashboard de Atendimento das Unidades de Saúde")

DB_FILE = "dados_dashboard.sqlite"
TABLE_NAME = "atendimentos"

# Colunas esperadas
EXPECTED_COLUMNS = [
    "Data",
    "Unidade",
    "Paciente",
    "Atendimento",
    "Equipe_Profissional",
    "Quantidade"  # campo base para todas as contabilizações
]


# ------------------------
# Funções de persistência
# ------------------------
def conectar_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    return conn


def carregar_dados():
    conn = conectar_db()
    try:
        df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", conn, parse_dates=["Data"])
        for c in EXPECTED_COLUMNS:
            if c not in df.columns:
                df[c] = pd.NA

        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df["Quantidade"] = pd.to_numeric(df["Quantidade"], errors="coerce").fillna(0).astype(int)

        conn.close()
        return df[EXPECTED_COLUMNS]
    except Exception:
        conn.close()
        return pd.DataFrame(columns=EXPECTED_COLUMNS)


def salvar_dados(df):
    conn = conectar_db()
    df_to_save = df.copy()
    df_to_save["Data"] = pd.to_datetime(df_to_save["Data"], errors="coerce").dt.date
    df_to_save.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)
    conn.close()


# ------------------------
# Inicializa DataFrame na sessão
# ------------------------
if "df" not in st.session_state:
    st.session_state.df = carregar_dados()

# ------------------------
# Inserção manual
# ------------------------
st.sidebar.header("➕ Inserção / Importação")
modo = st.sidebar.radio("Modo:", ["Manual", "Importar Planilha CSV/Excel"])

if modo == "Manual":
    st.sidebar.subheader("Inserção manual")
    with st.sidebar.form("form_manual"):
        data = st.date_input("Data")
        unidade = st.text_input("Unidade de Saúde")
        paciente = st.text_input("Nome do Paciente")
        atendimento = st.selectbox("Tipo de Atendimento", ["Consulta", "Exame", "Retorno", "Vacina", "Outro"])
        equipe = st.text_input("Equipe x Profissional")
        qtd = st.number_input("Quantidade (Atendimento pelo Sistema e pelo PEC no mês)", min_value=0, step=1, value=0)

        submitted = st.form_submit_button("Adicionar")
        if submitted:
            novo = pd.DataFrame([{
                "Data": pd.to_datetime(data).date(),
                "Unidade": unidade,
                "Paciente": paciente,
                "Atendimento": atendimento,
                "Equipe_Profissional": equipe,
                "Quantidade": int(qtd)
            }])
            st.session_state.df = pd.concat([st.session_state.df, novo], ignore_index=True)
            salvar_dados(st.session_state.df)
            st.success("✅ Registro adicionado com sucesso!")

# ------------------------
# Importação CSV/Excel
# ------------------------
if modo == "Importar Planilha CSV/Excel":
    st.sidebar.subheader("📂 Importar arquivo")
    uploaded_file = st.sidebar.file_uploader("Escolha um CSV ou Excel", type=["csv", "xlsx"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_uploaded = pd.read_csv(uploaded_file)
            else:
                df_uploaded = pd.read_excel(uploaded_file)

            # Garantir colunas
            for col in EXPECTED_COLUMNS:
                if col not in df_uploaded.columns:
                    if col == "Quantidade":
                        df_uploaded[col] = 0
                    else:
                        df_uploaded[col] = pd.NA

            df_uploaded["Data"] = pd.to_datetime(df_uploaded["Data"], errors="coerce").dt.date
            df_uploaded["Quantidade"] = pd.to_numeric(df_uploaded["Quantidade"], errors="coerce").fillna(0).astype(int)

            st.session_state.df = pd.concat([st.session_state.df, df_uploaded[EXPECTED_COLUMNS]], ignore_index=True)
            salvar_dados(st.session_state.df)
            st.success(f"📥 Importação concluída: {len(df_uploaded)} registros importados.")
        except Exception as e:
            st.error(f"❌ Erro ao processar o arquivo: {e}")

# ------------------------
# Relatórios e ferramentas
# ------------------------
st.header("📑 Relatórios e Ferramentas")

# Exclusão
with st.expander("🗑️ Excluir dados"):
    if st.session_state.df.empty:
        st.info("Nenhum dado disponível para exclusão.")
    else:
        idx = st.number_input("Índice a excluir (começa em 0)", min_value=0,
                              max_value=max(len(st.session_state.df) - 1, 0), step=1, value=0)
        if st.button("Excluir registro selecionado"):
            st.session_state.df = st.session_state.df.drop(index=idx).reset_index(drop=True)
            salvar_dados(st.session_state.df)
            st.success(f"Registro {idx} excluído.")
        if st.button("Excluir todos os registros"):
            st.session_state.df = st.session_state.df.iloc[0:0]
            salvar_dados(st.session_state.df)
            st.success("Todos os registros foram excluídos.")

# ------------------------
# Filtros
# ------------------------
st.subheader("🔍 Filtros")
df_filtrado = st.session_state.df.copy()
if df_filtrado.empty:
    st.info("Nenhum dado cadastrado.")
else:
    # Intervalo de datas
    df_filtrado["Data"] = pd.to_datetime(df_filtrado["Data"], errors="coerce")
    min_date = df_filtrado["Data"].min().date()
    max_date = df_filtrado["Data"].max().date()
    date_range = st.date_input("Intervalo de datas", [min_date, max_date])
    if isinstance(date_range, list) and len(date_range) == 2:
        start, end = date_range
        df_filtrado = df_filtrado[
            (df_filtrado["Data"] >= pd.to_datetime(start)) & (df_filtrado["Data"] <= pd.to_datetime(end))]

    # Unidade
    unidades_options = sorted(df_filtrado["Unidade"].dropna().unique())
    unidades_sel = st.multiselect("Unidade", options=unidades_options, default=unidades_options)
    if unidades_sel:
        df_filtrado = df_filtrado[df_filtrado["Unidade"].isin(unidades_sel)]

    # Equipe/Profissional
    equipes_options = sorted(df_filtrado["Equipe_Profissional"].dropna().unique())
    equipes_sel = st.multiselect("Equipe x Profissional", options=equipes_options, default=equipes_options)
    if equipes_sel:
        df_filtrado = df_filtrado[df_filtrado["Equipe_Profissional"].isin(equipes_sel)]

    # Tipo de atendimento
    tipos_options = sorted(df_filtrado["Atendimento"].dropna().unique())
    tipos_sel = st.multiselect("Tipo de Atendimento", options=tipos_options, default=tipos_options)
    if tipos_sel:
        df_filtrado = df_filtrado[df_filtrado["Atendimento"].isin(tipos_sel)]

    # ------------------------
    # Gráficos (baseados em Quantidade)
    # ------------------------
    st.subheader("📊 Gráficos")

    # 1) Atendimentos por Unidade
    grp_unidade = df_filtrado.groupby("Unidade")["Quantidade"].sum().reset_index()
    fig1 = px.bar(grp_unidade, x="Unidade", y="Quantidade", title="Atendimentos por Unidade")
    st.plotly_chart(fig1, use_container_width=True)

    # 2) Atendimentos por Equipe/Profissional
    grp_equipe = df_filtrado.groupby("Equipe_Profissional")["Quantidade"].sum().reset_index().sort_values(
        "Quantidade", ascending=False)
    fig2 = px.bar(grp_equipe, x="Equipe_Profissional", y="Quantidade", title="Atendimentos por Equipe/Profissional")
    st.plotly_chart(fig2, use_container_width=True)

    # 3) Distribuição por Tipo de Atendimento
    grp_tipo = df_filtrado.groupby("Atendimento")["Quantidade"].sum().reset_index()
    fig3 = px.pie(grp_tipo, names="Atendimento", values="Quantidade", title="Distribuição por Tipo de Atendimento")
    st.plotly_chart(fig3, use_container_width=True)

    # ------------------------
    # Exportação
    # ------------------------
    csv_export = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button("💾 Exportar dados filtrados para CSV", data=csv_export,
                       file_name="dados_filtrados.csv", mime="text/csv")

# ------------------------
# Rodapé informativo
# ------------------------
st.markdown("---")
st.markdown("🩺 **Ter saúde é conseguir estar presente por inteiro nos momentos que importam.**")
