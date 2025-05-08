import os
import json
import pandas as pd
from bs4 import BeautifulSoup
import mysql.connector
from datetime import datetime
import numpy as np

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='123456',
    database='visualsystem',
    charset='utf8mb4'
)
cursor = conn.cursor()

def clean_html(value):
    if isinstance(value, str) and '<' in value:
        return BeautifulSoup(value, 'html.parser').text
    return value

def clean_value(val):
    if pd.isna(val) or val in ["", "--", "*", "null", None]:
        return None
    return val

def clean_dataframe(df):
    return df.apply(lambda col: col.map(clean_html)).applymap(clean_value)

def parse_json_file(file_path, date_str):
    date_str = date_str.split('.')[0]
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    columns = [BeautifulSoup(col, 'html.parser').text.split('(')[0].strip() for col in data['thead']]
    df = pd.DataFrame(data['tbody'], columns=columns)
    df = clean_dataframe(df)
    df['date'] = pd.to_datetime(date_str, format="%Y-%m-%d")
    return df

all_data = []
root_path = "./水质数据（已清理）/water_data_clean"
for month_dir in os.listdir(root_path):
    month_path = os.path.join(root_path, month_dir)
    if os.path.isdir(month_path):
        for json_file in os.listdir(month_path):
            if json_file.endswith('.json'):
                full_path = os.path.join(month_path, json_file)
                date_str = json_file  # e.g., 2020-09-01
                df = parse_json_file(full_path, date_str)
                all_data.append(df)

df_all = pd.concat(all_data, ignore_index=True)

for _, row in df_all.iterrows():
    print("将要插入：", row.to_dict())
    try:
        monitor_time_raw = row.get('监测时间')
        if monitor_time_raw and isinstance(monitor_time_raw, str) and ':' in monitor_time_raw:
            time_part = monitor_time_raw.split()[0]
            monitor_time = f"{row['date'].strftime('%Y-%m-%d')} {time_part}:00"
        else:
            monitor_time = None

        cursor.execute("""
            INSERT INTO water_quality_data (
                source_date, province, river_basin, section_name, monitor_time, quality_level,
                water_temp, ph, dissolved_oxygen, conductivity, turbidity,
                cod_mn, ammonia_nitrogen, total_phosphorus, total_nitrogen,
                chlorophyll_a, algae_density, site_status, farm_id, farmer_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            clean_value(row.get('date')),
            clean_value(row.get('省份')),
            clean_value(row.get('流域')),
            clean_value(row.get('断面名称')),
            monitor_time,
            clean_value(row.get('水质类别')),
            clean_value(row.get('水温')),
            clean_value(row.get('pH')),
            clean_value(row.get('溶解氧')),
            clean_value(row.get('电导率')),
            clean_value(row.get('浊度')),
            clean_value(row.get('高锰酸盐指数')),
            clean_value(row.get('氨氮')),
            clean_value(row.get('总磷')),
            clean_value(row.get('总氮')),
            clean_value(row.get('叶绿素α')),
            clean_value(row.get('藻密度')),
            clean_value(row.get('站点情况')),
            clean_value(row.get('渔场ID')),
            clean_value(row.get('养殖户ID'))
        ))
    except Exception as e:
        print(f"插入出错，跳过当前行: {e}")
        continue

conn.commit()
cursor.close()
conn.close()
