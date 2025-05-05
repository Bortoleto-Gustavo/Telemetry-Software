import pandas as pd
import plotly.express as px
import streamlit as st
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import time
import os
import tempfile

# Cache para armazenar dados
data_cache = {"df": None, "last_updated": 0}

# Inicializando session_state para evitar loops
if "has_rerun" not in st.session_state:
    st.session_state["has_rerun"] = False

# Função para ler o CSV e atualizar cache
def read_csv_dynamic(file_path):
    try:
        df = pd.read_csv(file_path, parse_dates=True, infer_datetime_format=False)

        # Só atualiza se os dados mudaram
        if not df.equals(data_cache.get("df")):
            data_cache["df"] = df
            data_cache["last_updated"] = time.time()

            # Armazena o DataFrame na sessão para garantir a atualização do gráfico
            st.session_state["df"] = df

    except Exception as e:
        st.error(f"Erro ao ler o CSV: {e}")

# Watchdog handler
class CSVHandler(FileSystemEventHandler):
    def __init__(self, file_path):
        self.file_path = file_path

    def on_modified(self, event):
        if event.src_path == self.file_path:
            read_csv_dynamic(self.file_path)

# Inicia o watchdog para monitorar o arquivo
def start_file_watch(file_path):
    event_handler = CSVHandler(file_path)
    observer = Observer()
    watch_dir = os.path.dirname(file_path)

    if os.path.exists(watch_dir):
        observer.schedule(event_handler, path=watch_dir, recursive=False)
        observer.start()
        threading.Thread(target=observer.join).start()
    else:
        st.warning(f"Diretório para monitoramento não encontrado: {watch_dir}")

# Interface principal do Streamlit
def main():
    st.title("Visualizador de CSV com Filtros e Cálculos")

    file_path = st.file_uploader("Envie seu arquivo CSV", type=["csv"])

    # Se o arquivo for enviado
    if file_path:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(file_path.getvalue())
            temp_path = tmp.name

        # Chama a função para ler e atualizar os dados
        read_csv_dynamic(temp_path)
        start_file_watch(temp_path)

    # Verifica se os dados estão disponíveis
    df = st.session_state.get("df", None)

    if df is not None:
        st.success("Arquivo carregado!")

        # Usar a primeira coluna como padrão do eixo X
        default_x_col = df.columns[0]

        # Permitir seleção de coluna de data opcional
        st.subheader("Configuração de Eixo X / Tempo")
        date_columns = df.select_dtypes(include=["object", "datetime"]).columns.tolist()
        date_col = st.selectbox("Escolha uma coluna de data (opcional)", ["Usar primeira coluna"] + date_columns)

        if date_col == "Usar primeira coluna":
            x_axis = default_x_col
        else:
            try:
                df[date_col] = pd.to_datetime(df[date_col])
                df = df.sort_values(by=date_col)
                start_date = st.date_input("Data inicial", value=df[date_col].min().date())
                end_date = st.date_input("Data final", value=df[date_col].max().date())
                df = df[(df[date_col] >= pd.to_datetime(start_date)) & (df[date_col] <= pd.to_datetime(end_date))]
                x_axis = date_col
            except Exception as e:
                st.warning(f"Erro ao converter coluna para data: {e}")
                x_axis = default_x_col

        st.subheader("Filtragem de Colunas Numéricas")
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        selected_cols = st.multiselect("Selecione colunas para o gráfico", numeric_cols)

        if selected_cols:
            st.subheader("Gráfico Interativo")
            plot = px.line(df, x=x_axis, y=selected_cols)
            st.plotly_chart(plot)

            st.subheader("Cálculos com os dados")
            for col in selected_cols:
                st.write(f"**{col}**:")
                st.write(f"- Média: {df[col].mean():.2f}")
                st.write(f"- Soma: {df[col].sum():.2f}")
                st.write(f"- Máximo: {df[col].max():.2f}")
                st.write(f"- Mínimo: {df[col].min():.2f}")

# Executa o app
if __name__ == "__main__":
    main()
