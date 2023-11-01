import pandas as pd
import numpy as np
import os

def transformar_columnas_datetime(dataframe, columns_to_transform):
    for column in columns_to_transform:
        if column in dataframe.columns:
            dataframe[column] = pd.to_datetime(dataframe[column])
    return dataframe


def tiempo_de_espera(dataframe, is_delivered):
    # filtrar por entregados y crea la varialbe tiempo de espera
    if is_delivered:
        dataframe = dataframe.query("order_status=='delivered'").copy()
    # compute wait time
    dataframe.loc[:, 'tiempo_de_espera'] = \
        (dataframe['order_delivered_customer_date'] -
         dataframe['order_purchase_timestamp']) / np.timedelta64(24, 'h')
    return dataframe

def tiempo_de_espera_previsto(dataframe, is_delivered):
    # filtrar por entregados y crea la varialbe tiempo de espera
    if is_delivered:
        dataframe = dataframe.query("order_status=='delivered'").copy()
    # compute wait time
    dataframe.loc[:, 'tiempo_de_espera_previsto'] = \
        (dataframe['order_estimated_delivery_date'] -
         dataframe['order_approved_at']) / np.timedelta64(24, 'h')
    return dataframe


def real_vs_esperado(dataframe, is_delivered=True):
    #filtrar por entregados y crea la varialbe tiempo de espera previsto
    if is_delivered:
        dataframe = dataframe.query("order_status == 'delivered'").copy()
    # compute wait time
    dataframe.loc[:, 'real_vs_esperado'] = \
        (dataframe['tiempo_de_espera'] -
         dataframe['tiempo_de_espera_previsto']) 
    # set negative wait times to 0
    dataframe['real_vs_esperado'] = np.where(dataframe['real_vs_esperado'] < 0, 0, dataframe['real_vs_esperado'])
    
    return dataframe

def puntaje_de_compra(df):
    def es_cinco_estrellas(col):
        return 1 if col == 5 else 0

    def es_una_estrella(col):
        return 1 if col == 1 else 0

    puntajes = pd.DataFrame()
    puntajes['order_id'] = df['order_id']
    puntajes['es_cinco_estrellas'] = df['review_score'].apply(es_cinco_estrellas)
    puntajes['es_una_estrella'] = df['review_score'].apply(es_una_estrella)
    puntajes['review_score'] = df['review_score']

    return puntajes

def calcular_numero_productos(dataframe):
        conteo_por_order_id = dataframe.groupby('order_id')['order_item_id'].count()
        conteo_por_order_id = conteo_por_order_id.reset_index() 
        conteo_por_order_id = conteo_por_order_id.rename(columns={'order_item_id': 'number_of_products'})
        return conteo_por_order_id


def vendedores_unicos(dataframe):
        conteo_por_vendedor_id = dataframe.groupby('order_id')['seller_id'].nunique()
        conteo_por_vendedor_id = conteo_por_vendedor_id.reset_index() 
        conteo_por_vendedor_id = conteo_por_vendedor_id.rename(columns={'order_item_id': 'vendedores_unicos'})
        return conteo_por_vendedor_id

def calcular_precio_y_transporte(dataframe):
     precio_y_transporte_por_orden = dataframe.groupby('order_id').agg({'price': 'sum', 'freight_value': 'sum'}).reset_index()
     return precio_y_transporte_por_orden

from math import radians, sin, cos, asin, sqrt

def haversine_distance(lon1, lat1, lon2, lat2):
    """
    Computa distancia entre dos pares (lat, lng)
    Ver - (https://en.wikipedia.org/wiki/Haversine_formula)
    """
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * 6371 * asin(sqrt(a))

def calcular_distancia_vendedor_comprador(data):
    for df in data:
        if df == 'order_items':
            order_items = data[df].copy()
        elif df == 'orders':
            orders = data[df].copy()
        elif df == 'sellers':
            sellers = data[df].copy()
        elif df == 'customers':
            customers = data[df].copy()
        elif df == 'geolocation':
            geolocation = data[df].copy()
            geo = geolocation.groupby('geolocation_zip_code_prefix').first()

    orders_customers = orders[['order_id', 'customer_id']]
    df_customers = pd.merge(orders_customers, customers,how= 'inner', on='customer_id')
    df_customers = df_customers.drop('customer_city', axis=1)
    df_customers = df_customers.drop('customer_state', axis=1)
    df_customers = df_customers.rename(columns={'customer_zip_code_prefix':'geolocation_zip_code_prefix'})
    df_customers = pd.merge(df_customers, geo, how='inner', on='geolocation_zip_code_prefix')
    df_customers = df_customers.rename(columns={'geolocation_lat': 'lat_customer', 'geolocation_lng':'lng_customer'})
    df_sellers = pd.merge(orders_customers, order_items, how='inner', on='order_id')
    columnas_excluir = ['order_item_id','product_id','shipping_limit_date','price', 'freight_value']
    df_sellers = df_sellers.drop(columnas_excluir, axis=1)
    df_sellers = pd.merge(df_sellers, sellers, how='inner', on='seller_id')
    columnas_excluir = ['seller_city', 'seller_state']
    df_sellers = df_sellers.drop(columnas_excluir, axis=1)
    df_sellers = df_sellers.rename(columns={'seller_zip_code_prefix':'geolocation_zip_code_prefix'})
    df_sellers = pd.merge(df_sellers, geo, how='inner', on='geolocation_zip_code_prefix')
    columnas_excluir = ['customer_id', 'geolocation_city','geolocation_state']
    df_sellers = df_sellers.drop(columnas_excluir, axis=1)
    df_sellers = df_sellers.rename(columns={'geolocation_lat': 'lat_seller', 'geolocation_lng':'lng_seller'})
    df_final = pd.merge(df_customers, df_sellers, how='inner', on='order_id')
    df_final = df_final.dropna()
    df_final['lat_seller'] = pd.to_numeric(df_final['lat_seller'], errors = 'coerce')
    df_final['lng_seller'] = pd.to_numeric(df_final['lng_seller'], errors = 'coerce')
    df_final['lat_customer'] = pd.to_numeric(df_final['lat_customer'], errors = 'coerce')
    df_final['lng_customer'] = pd.to_numeric(df_final['lng_customer'], errors = 'coerce')
    
    distances = []
    for index, row in df_final.iterrows():
        distance = haversine_distance(row['lng_customer'], row['lat_customer'], row['lng_seller'], row['lat_seller'])
        distances.append(distance)
    df_final['distancia_a_la_orden'] = distances


    return df_final[['order_id','distancia_a_la_orden']]

