#!/usr/bin/env python
# coding: utf-8

# # Curso Grátis - Acessando a API da Betfair
# 
# Bem vindo ao nosso curso grátis sobre como acessar a API da Betfair e começar a extrair os seus próprios dados para apoiar a sua tomada de decisão no trade esportivo e dar os primeiros passos na análise de dados com Python.
# 
# Antes de iniciarmos, vamos nos apresentar. A Academia dos Bots tem por objetivo trazer cursos voltados para análise de dados de futebol, criação de bots para apoio na tomada de decisão nas apostas, extração de dados da internet por meio de crawlers, modelagem estatística voltada para o futebol e muito mais, tudo isto utilizando Python, R e SQL.
# 
# Ao longo deste material, aprenderemos de maneira simples e intuitiva como é o funcionamento básico da API e como realizar a primeira extração das odds de algum jogo. 
# 

# *Importante* - Este material é parte integrante da série de vídeos que encontra-se neste link <https://www.youtube.com/channel/UCvQwP2UX2b6Ov_F7eagUleQ>

# # A estrutura da API da Betfair
# Antes de mais nada, você sabe o que é uma API? De maneira resumida, uma API permite que uma aplicação A tenha acesso a recursos da aplicação B, sem ter a necessidade de conhecer todo o processo de desenvolvimento e realização de integrações complexas. Em nosso caso, nós somos a aplicação A que irá buscar os dados da aplicação B (Betfair).
# 
# Para termos uma noção do que queremos acessar, vamos olhar a origem dos dados e entender como ele está estruturado. Observando o site, logo de cara nos deparamos com uma infinidade de informações.
# 
# ![teste alt](images/curso_gratis_01/betfair.png)
# 

# Aqui, vamos fazer o nosso primeiro filtro: queremos obter as cotações (odds) de algum mercado (gols, Match Odds, cantos, etc.) de um jogo (evento) pertencente a uma competição de algum esporte. Percebeu a relação? Para acessar os dados, assim que entender esta relação nosso trabalho ficará muito mais simples.
# 
# Na Betfair, teremos uma sequência de etapas a serem realizadas e que estão diretamente relacionadas com a relação citada anteriormente. Abaixo, vamos entender este processo por meio de um diagrama:
# 
# ![fluxo](images/curso_gratis_01/fluxo.png)

# Legal este fluxo né!? Vamos colocar a mão na massa?!

# # Imports e arquivos de configuração

# In[84]:


import datetime
import pandas as pd
import betfairlightweight
import time


# In[4]:


username = "seu_email_betfair"
pw = "sua_senha_betfair"
app_key = "sua_appkey"


# # Abrindo uma conexão

# In[5]:


#Abrindo a conexão com a lib betfairlightweight
trading = betfairlightweight.APIClient(username, pw, app_key=app_key, cert_files=('./certs/tt_app_test.crt','./certs/client-2048.key'))
trading.login()


# # Listando Eventos

# In[39]:


# Definindo os filtros de Mercado
filtros_mercado = betfairlightweight.filters.market_filter(
    event_type_ids=['1'], # ID para Futebol
    competition_ids=[321319], #Competições
    market_start_time={
        'to': (datetime.datetime.utcnow() + datetime.timedelta(days=1)).strftime("%Y-%m-%dT%TZ")
    }
)

#listando os eventos a partir dos filtros pré definidos acima
eventos_futebol = trading.betting.list_events(
    filter=filtros_mercado
)

#listando as competições de futebol disponíveis
competicoes_futebol = trading.betting.list_competitions(
    filter=filtros_mercado
)

planilha_eventos_futebol = pd.DataFrame({
    'NomeEvento': [obj_evento.event.name for obj_evento in eventos_futebol],
    'IDEvento': [obj_evento.event.id for obj_evento in eventos_futebol],
    'LocalEvento': [obj_evento.event.venue for obj_evento in eventos_futebol],
    'CodPais': [obj_evento.event.country_code for obj_evento in eventos_futebol],
    'TimeZone': [obj_evento.event.time_zone for obj_evento in eventos_futebol],
    'DataAbertura': [obj_evento.event.open_date for obj_evento in eventos_futebol],
    'TotalMercados': [obj_evento.market_count for obj_evento in eventos_futebol],
    'DataLocal': [obj_evento.event.open_date.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None) 
                        for obj_evento in eventos_futebol]
})

planilha_eventos_futebol


# # Listando Mercados

# In[40]:


id_evento = 31065573

filtro_catalogo_mercados = betfairlightweight.filters.market_filter(event_ids=[id_evento])

catalogos_mercado = trading.betting.list_market_catalogue(
    filter=filtro_catalogo_mercados,
    max_results='100',
    sort='FIRST_TO_START',
    market_projection=['RUNNER_METADATA']
)


# Create a DataFrame for each market catalogue
planilha_mercados = pd.DataFrame({
    'NomeMercado': [market_cat_object.market_name for market_cat_object in catalogos_mercado],
    'IDMercado': [market_cat_object.market_id for market_cat_object in catalogos_mercado],
    'TotalCorrespondido': [market_cat_object.total_matched for market_cat_object in catalogos_mercado],
    'Home' : [market_cat_object.runners[0].runner_name for market_cat_object in catalogos_mercado],
    'Home_id' : [market_cat_object.runners[0].selection_id for market_cat_object in catalogos_mercado],
    'Away' : [market_cat_object.runners[1].runner_name for market_cat_object in catalogos_mercado],
    'Away_id' : [market_cat_object.runners[1].selection_id for market_cat_object in catalogos_mercado],
    'Draw' : [market_cat_object.runners[2].runner_name if len(market_cat_object.runners) > 2 else '' for market_cat_object in catalogos_mercado],
    'Draw_id' : [market_cat_object.runners[2].selection_id if len(market_cat_object.runners) > 2 else 0 for market_cat_object in catalogos_mercado]
})

planilha_mercados


# # Obtendo Odds

# In[91]:


df_final = pd.DataFrame()
for i in range(0,60):
    order_filter = betfairlightweight.filters.ex_best_offers_overrides(
        best_prices_depth=3
    )

    price_filter = betfairlightweight.filters.price_projection(
        price_data=['EX_BEST_OFFERS'],
        ex_best_offers_overrides=order_filter
    )

    # Obtendo odds para o mercado
    market_books = trading.betting.list_market_book(
        market_ids=['1.190674822'],
        price_projection=price_filter
    )

    #Lista de runners
    runners = market_books[0].runners

    back = []
    for i in range(0,3):
        try:
            back.append([runner_book.ex.available_to_back[i].price
                                    if runner_book.ex.available_to_back
                                    else 1.01
                                    for runner_book
                                    in runners])
        except:
            back.append([1.01,1.01])

    lay = []
    for i in range(0,3):
        try:
            lay.append([runner_book.ex.available_to_lay[i].price
                                    if runner_book.ex.available_to_lay
                                    else 1.01
                                    for runner_book
                                    in runners])
        except:
            lay.append([[1.01,1.01,1.01]])


    df_back = pd.DataFrame(back,columns=['Casa','Visitante','Empate'])
    df_back['data'] = datetime.datetime.now()
    df_back['Jogo'] = planilha_eventos_futebol.query('IDEvento=="31065573"').NomeEvento.values[0]
    df_final = df_final.append(df_back)
    time.sleep(2)


# # Exportando arquivo final

# In[90]:


df_final.to_csv('2021_11_15_serieb_londrina_vs_ponte.csv',index=False)

