import pandas as pd
import os

def get_airport_list():
    file_path = os.path.join("data", "airports.xlsx")
    df = pd.read_excel(file_path)
    return df["Name"].dropna().tolist()

def get_hotel_list():
    file_path = os.path.join("data", "hotels.xlsx")
    df = pd.read_excel(file_path)
    return df["Name"].dropna().tolist()
