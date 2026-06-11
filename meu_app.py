import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Webnovel Library", layout="wide")

# Injeção de CSS para o seletor de páginas e para remover margens desnecessárias no mobile
st.markdown('''
    <style>
        div[data-testid="stNumberInput"] {max-width: 150px; margin: 0 auto;}
        .block-container {padding-top: 2rem; padding-bottom: 2rem;}
        /* Remove padding entre colunas no mobile */
        [data-testid="column"] {padding: 0px 5px !important;}
    </style>
''', unsafe_allow_html=True)

if 'pag_input' not in st.session_state:
    st.session_state['pag_input'] = 1

@st.cache_data
def carregar_dados():
    # Lendo o ZIP para rodar online sem erro de limite
    df = pd.read_csv('webnovel_dados_finais.zip', sep=';', on_bad_lines='skip', 
                     dtype={'Book_ID': str}, compression='zip')
    df.fillna({
        'Nome': 'Desconhecido', 'Categoria': 'Nenhuma', 'Idioma': 'Desconhecido',
        'Tags': '', 'Capitulos': 0, 'Views': 0, 
        'Nota_Total': 0, 'Score_Review': 0, 'Total_Reviews': 0
    }, inplace=True)
    return df

df = carregar_dados()

# --- BARRA LATERAL ---
st.sidebar.header("Filtros")
busca_titulo = st.sidebar.text_input("Buscar Título:")

# DE VOLTA: Filtro de Capítulos
max_capitulos_banco = int(df['Capitulos'].max()) if not df.empty else 5000
min_cap, max_cap = st.sidebar.slider(
    "Quantidade de Capítulos", 
    min_value=0, 
    max_value=max_capitulos_banco, 
    value=(0, 1000)
)

nota_minima = st.sidebar.slider("Nota Mínima", 0.0, 5.0, 4.0, 0.1)
views_minimas = st.sidebar.number_input("Views Mínimas", min_value=0, value=10000, step=10000)

categorias_unicas = sorted(df['Categoria'].unique().tolist())
categorias_selecionadas = st.sidebar.multiselect("Categorias", categorias_unicas)

idiomas_unicos = sorted(df['Idioma'].astype(str).unique().tolist())
idiomas_selecionados = st.sidebar.multiselect("Idioma", idiomas_unicos)

todas_tags = df['Tags'].astype(str).str.split(',').explode().str.strip()
tags_unicas = sorted(todas_tags[todas_tags != ''].unique().tolist())
tags_selecionadas = st.sidebar.multiselect("Tags", tags_unicas)

# --- MOTOR DE FILTRAGEM ---
df_filtrado = df.copy()

if busca_titulo:
    for palavra in busca_titulo.split():
        df_filtrado = df_filtrado[df_filtrado['Nome'].str.contains(palavra.strip(), case=False, na=False, regex=False)]

# DE VOLTA: Aplicando a regra dos Capítulos
df_filtrado = df_filtrado[(df_filtrado['Capitulos'] >= min_cap) & (df_filtrado['Capitulos'] <= max_cap)]
df_filtrado = df_filtrado[(df_filtrado['Nota_Total'] >= nota_minima) & (df_filtrado['Views'] >= views_minimas)]

if categorias_selecionadas:
    df_filtrado = df_filtrado[df_filtrado['Categoria'].isin(categorias_selecionadas)]

if idiomas_selecionados:
    df_filtrado = df_filtrado[df_filtrado['Idioma'].isin(idiomas_selecionados)]

if tags_selecionadas:
    for tag in tags_selecionadas:
        df_filtrado = df_filtrado[df_filtrado['Tags'].str.contains(tag, case=False, na=False, regex=False)]

df_filtrado = df_filtrado.sort_values(by='Nota_Total', ascending=False)

# --- PAGINAÇÃO ---
RESULTADOS_POR_PAGINA = 30
total_paginas = max(1, (len(df_filtrado) // RESULTADOS_POR_PAGINA) + (1 if len(df_filtrado) % RESULTADOS_POR_PAGINA > 0 else 0))
if st.session_state['pag_input'] > total_paginas:
    st.session_state['pag_input'] = total_paginas

pagina_atual = st.session_state['pag_input']
inicio = (pagina_atual - 1) * RESULTADOS_POR_PAGINA
df_exibicao = df_filtrado.iloc[inicio:inicio + RESULTADOS_POR_PAGINA]

# --- INTERFACE ---
st.title("📚 Webnovel DB")
st.caption(f"Exibindo {len(df_filtrado)} resultados")

if len(df_filtrado) > 0:
    colunas_grade = st.columns(2)
    
    for i, (_, livro) in enumerate(df_exibicao.iterrows()):
        col_alvo = colunas_grade[i % 2]
        
        id_livro = str(livro['Book_ID']).strip().replace('.0', '')
        capa_url = f"https://book-pic.webnovel.com/bookcover/{id_livro}/180.jpg"
        link_leitura = f"https://www.webnovel.com/book/{id_livro}"
        
        with col_alvo:
            st.markdown(f'''
                <div style="display: flex; background-color: #1e1e1e; border-radius: 10px; padding: 10px; margin-bottom: 12px; border: 1px solid #333; height: 160px; overflow: hidden;">
                    <div style="flex: 0 0 100px; height: 140px;">
                        <img src="{capa_url}" referrerpolicy="no-referrer" style="width: 100%; height: 100%; object-fit: cover; border-radius: 5px;">
                    </div>
                    <div style="flex: 1; padding-left: 15px; display: flex; flex-direction: column; justify-content: space-between;">
                        <div style="overflow: hidden;">
                            <div style="font-size: 16px; font-weight: bold; color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{livro['Nome']}</div>
                            <div style="font-size: 14px; color: #ffcc00; margin-top: 4px;">⭐ {livro['Nota_Total']} <span style="color: #888; font-size: 12px;">({livro['Total_Reviews']})</span></div>
                            <div style="font-size: 12px; color: #bbb; margin-top: 4px;">👁️ {int(livro['Views']):,} | 📖 {int(livro['Capitulos'])} caps</div>
                            <div style="font-size: 11px; color: #777; margin-top: 2px;">{livro['Categoria']} | {livro['Idioma']}</div>
                        </div>
                        <a href="{link_leitura}" target="_blank" style="text-decoration: none;">
                            <div style="background-color: #007bff; color: white; text-align: center; padding: 6px; border-radius: 5px; font-size: 13px; font-weight: bold;">Ler Novel</div>
                        </a>
                    </div>
                </div>
            ''', unsafe_allow_html=True)

    st.divider()
    st.number_input(f"Página (1-{total_paginas})", min_value=1, max_value=total_paginas, key='pag_input')
else:
    st.warning("Nada encontrado.")
