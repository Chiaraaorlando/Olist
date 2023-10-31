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


def real_vs_esperado(orders, is_delivered=True):
    #filtrar por entregados y crea la varialbe tiempo de espera previsto
    if is_delivered:
        orders = orders.query("order_status == 'delivered'").copy()
    # compute wait time
    orders['real_vs_esperado'] = (orders['order_estimated_delivery_date'] -
                                  orders['order_purchase_timestamp']) / np.timedelta64(1, 'D')
    # set negative wait times to 0
    orders['real_vs_esperado'] = np.where(orders['real_vs_esperado'] < 0, 0, orders['real_vs_esperado'])
    
    return orders

