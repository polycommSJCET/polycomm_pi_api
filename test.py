import json
import requests
import csv
from fpdf import FPDF
from docx import Document
from datetime import datetime
import pandas as pd

def clear_duplicates(m_id):

    file_path="__temp__/csv/"+m_id+".csv"
    df = pd.read_csv(file_path)

    print(len(df))

    i=0

    while(i<(len(df)-1)):
        #print(df.iloc[i]['speaker'])
        
        if((df.iloc[i]['speaker']==df.iloc[i+1]['speaker']) and (df.iloc[i]['translated_text'] in df.iloc[i+1]['translated_text'])):
            print("duplicate at index ",i)
            df.drop(i, axis=0, inplace=True)
            df.reset_index(drop=True, inplace=True)
            if i>0:
                i-=1


        else:
            i+=1

    df.to_csv(file_path, index=False)
    return file_path

clear_duplicates('2ff9e237-6ef8-44dd-a9a1-dd3d3fec6927')
