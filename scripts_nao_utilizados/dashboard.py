import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
from sqlalchemy import create_engine

# --------------------------------------------------------
# Simular conexão com o banco de dados (substitua com seus dados)
engine = create_engine('sqlite:///redeescola.db')

# Consultas de exemplo (ajuste conforme suas tabelas)
query_alunos = "SELECT escola_id, raca, sexo FROM alunos"
query_notas = "SELECT disciplina_id, nota FROM notas"
query_frequencia = "SELECT aluno_id, presente FROM frequencia_alunos"
query_funcionarios = "SELECT cargo, COUNT(*) as total FROM funcionarios GROUP BY cargo"

# Carregar dados
df_alunos = pd.read_sql(query_alunos, engine)
df_notas = pd.read_sql(query_notas, engine)
df_frequencia = pd.read_sql(query_frequencia, engine)
df_funcionarios = pd.read_sql(query_funcionarios, engine)
# --------------------------------------------------------

# Inicializar o app Dash
app = dash.Dash(__name__)

# Layout do dashboard
app.layout = html.Div([
    html.H1("Dashboard Educacional - RedeEscola", style={'textAlign': 'center'}),
    
    # Linha 1: Gráficos de distribuição
    html.Div([
        dcc.Graph(
            id='alunos-por-escola',
            figure=px.bar(df_alunos['escola_id'].value_counts().reset_index(), 
                         x='index', y='escola_id', 
                         title='Alunos por Escola',
                         labels={'index': 'Escola', 'escola_id': 'Total'})
        ),
        dcc.Graph(
            id='notas-disciplinas',
            figure=px.box(df_notas, x='disciplina_id', y='nota', 
                          title='Distribuição de Notas por Disciplina')
        )
    ], style={'display': 'flex', 'gap': '20px'}),
    
    # Linha 2: Gráficos de frequência e diversidade
    html.Div([
        dcc.Graph(
            id='frequencia-media',
            figure=px.pie(df_frequencia, names='presente', 
                         title='Taxa de Presença Geral',
                         values=df_frequencia.groupby('presente').size())
        ),
        dcc.Graph(
            id='distribuicao-raca',
            figure=px.pie(df_alunos, names='raca', 
                         title='Distribuição por Raça/Cor')
        )
    ], style={'display': 'flex', 'gap': '20px'}),
    
    # Linha 3: Gráfico de funcionários
    html.Div([
        dcc.Graph(
            id='funcionarios-por-cargo',
            figure=px.bar(df_funcionarios, x='cargo', y='total', 
                         title='Funcionários por Cargo',
                         color='cargo')
        )
    ])
])

# Executar o servidor
if __name__ == '__main__':
    app.run_server(debug=True)