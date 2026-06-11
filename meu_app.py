import streamlit as st
import pandas as pd

# Configuração da página para ocupar a tela toda
st.set_page_config(page_title="Minha Biblioteca Webnovel", layout="wide")

# Inicializa o controle de página no sistema caso não exista
if 'pag_input' not in st.session_state:
    st.session_state['pag_input'] = 1

# O Cache impede que o arquivo pesado seja lido do zero toda vez que você mexe num filtro
@st.cache_data
def carregar_dados():
    # Lendo o arquivo ZIP direto para driblar o limite de 25MB do GitHub
    df = pd.read_csv('webnovel_dados_finais.zip', sep=';', on_bad_lines='skip', dtype={'Book_ID': str}, compression='zip')
    df.fillna({
        'Nome': 'Desconhecido', 'Categoria': 'Nenhuma', 'Idioma': 'Desconhecido',
        'Tags': '', 'Capitulos': 0, 'Views': 0, 
        'Nota_Total': 0, 'Score_Review': 0, 'Total_Reviews': 0
    }, inplace=True)
    return df

df = carregar_dados()

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("Filtros Avançados")

# Busca focada apenas no Título e aceitando múltiplas palavras separadas
busca_titulo = st.sidebar.text_input("Buscar por Título (Ex: magic cultivation):")

# Filtro 2: Capítulos (Slider Duplo)
max_capitulos_banco = int(df['Capitulos'].max()) if not df.empty else 5000
min_cap, max_cap = st.sidebar.slider(
    "Quantidade de Capítulos", 
    min_value=0, 
    max_value=max_capitulos_banco, 
    value=(0, 1000)
)

# Filtro 3: Nota Mínima
nota_minima = st.sidebar.slider("Nota Mínima (Score)", 0.0, 5.0, 4.0, 0.1)

# Filtro 4: Mínimo de Views
views_minimas = st.sidebar.number_input("Visualizações Mínimas (Views)", min_value=0, value=10000, step=10000)

# Filtro 5: Categorias Múltiplas
categorias_unicas = sorted(df['Categoria'].unique().tolist())
categorias_selecionadas = st.sidebar.multiselect("Categorias", categorias_unicas)

# Filtro 6: Idioma (Opcional)
idiomas_unicos = sorted(df['Idioma'].astype(str).unique().tolist())
idiomas_selecionados = st.sidebar.multiselect("Idioma (Opcional)", idiomas_unicos)

# Filtro 7: Tags Específicas (Opcional - Combinação Obrigatória)
todas_tags = df['Tags'].astype(str).str.split(',').explode().str.strip()
tags_unicas = sorted(todas_tags[todas_tags != ''].unique().tolist())
tags_selecionadas = st.sidebar.multiselect("Tags (Ex: R18, System, Cultivation)", tags_unicas)


# --- MOTOR DE FILTRAGEM ---
df_filtrado = df.copy()

# MOTOR DE BUSCA POR TÍTULO: Quebra o texto e exige que TODAS as palavras digitadas estejam no título
if busca_titulo:
    palavras_chave = busca_titulo.split()
    for palavra in palavras_chave:
        df_filtrado = df_filtrado[df_filtrado['Nome'].str.contains(palavra.strip(), case=False, na=False, regex=False)]

# Aplica Capítulos, Notas e Views
df_filtrado = df_filtrado[(df_filtrado['Capitulos'] >= min_cap) & (df_filtrado['Capitulos'] <= max_cap)]
df_filtrado = df_filtrado[df_filtrado['Nota_Total'] >= nota_minima]
df_filtrado = df_filtrado[df_filtrado['Views'] >= views_minimas]

if categorias_selecionadas:
    df_filtrado = df_filtrado[df_filtrado['Categoria'].isin(categorias_selecionadas)]

if idiomas_selecionados:
    df_filtrado = df_filtrado[df_filtrado['Idioma'].isin(idiomas_selecionados)]

if tags_selecionadas:
    for tag in tags_selecionadas:
        df_filtrado = df_filtrado[df_filtrado['Tags'].str.contains(tag, case=False, na=False, regex=False)]

# Ordenar por melhores notas primeiro
df_filtrado = df_filtrado.sort_values(by='Nota_Total', ascending=False)


# --- PROCESSAMENTO DA PAGINAÇÃO ---
RESULTADOS_POR_PAGINA = 40
total_paginas = max(1, (len(df_filtrado) // RESULTADOS_POR_PAGINA) + (1 if len(df_filtrado) % RESULTADOS_POR_PAGINA > 0 else 0))

# Se o usuário aplicar um filtro que reduza drasticamente as páginas, ajusta para não estourar o limite
if st.session_state['pag_input'] > total_paginas:
    st.session_state['pag_input'] = total_paginas

pagina_atual = st.session_state['pag_input']

# Corta o banco de dados para exibir apenas as 40 novels da página correspondente
inicio = (pagina_atual - 1) * RESULTADOS_POR_PAGINA
fim = inicio + RESULTADOS_POR_PAGINA
df_exibicao = df_filtrado.iloc[inicio:fim]


# --- INTERFACE PRINCIPAL ---
st.title("📚 Biblioteca Master: Webnovel")
st.subheader(f"Encontradas {len(df_filtrado)} novels com esses critérios.")

if len(df_filtrado) > 0:
    # --- EXIBIÇÃO DA GRADE (6 COLUNAS NO PC, AUTOMATICAMENTE 1 NO CELULAR) ---
    colunas_por_linha = 6
    st.write("")

    for i in range(0, len(df_exibicao), colunas_por_linha):
        cols = st.columns(colunas_por_linha)
        
        for j, col in enumerate(cols):
            indice = i + j
            if indice < len(df_exibicao):
                livro = df_exibicao.iloc[indice]
                id_livro = str(livro['Book_ID']).strip().replace('.0', '')
                
                capa_url = f"https://book-pic.webnovel.com/bookcover/{id_livro}/180.jpg"
                link_leitura = f"https://www.webnovel.com/book/{id_livro}"
                
                with col:
                    # DESIGN RESPONSIVO: Moldura Rígida Premium (aspect-ratio e object-fit) + Anti-Hotlink
                    st.markdown(f'''
                        <div style="width: 100%; aspect-ratio: 3/4; border-radius: 8px; overflow: hidden; margin-bottom: 10px; box-shadow: 0px 4px 10px rgba(0,0,0,0.5); background-color: #222;">
                            <img src="{capa_url}" referrerpolicy="no-referrer" style="width: 100%; height: 100%; object-fit: cover; display: block;">
                        </div>
                    ''', unsafe_allow_html=True)
                    
                    st.markdown(f"**{livro['Nome']}**")
                    st.write(f"⭐ **{livro['Nota_Total']}** ({livro['Total_Reviews']} av.)")
                    st.write(f"📖 {livro['Capitulos']} caps | 👁️ {int(livro['Views'])} views")
                    st.caption(f"Cat: {livro['Categoria']} | Idioma: {livro['Idioma']}")
                    
                    st.link_button("Abrir no Webnovel", link_leitura, use_container_width=True)
                    st.divider()

    # SELETOR DE PÁGINAS RESPONSIVO NO FINAL
    st.divider()
    # Injeta um CSS para limitar o tamanho do botão e centralizar tanto no celular quanto no PC
    st.markdown('<style>div[data-testid="stNumberInput"] {max-width: 200px; margin: 0 auto;}</style>', unsafe_allow_html=True)
    
    st.number_input(
        f"Página (1 a {total_paginas})", 
        min_value=1, 
        max_value=total_paginas, 
        key='pag_input'
    )
else:
    st.warning("Nenhuma novel encontrada com esses filtros. Tente expandir sua busca.")