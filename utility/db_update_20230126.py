import os
import sys
import sqlite3
import pandas as pd
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from utility.setting import DB_PATH
from utility.static import roundfigure_upper5


file_list = os.listdir(DB_PATH)
file_list = [x for x in file_list if 'stock_tick_' in x and 'back' not in x and '.zip' not in x and int(x.replace('stock_tick_', '').replace('.db', '')) > 20230124]

print('라운드피겨 업데이트 시작')
last = len(file_list)
for k, db_name in enumerate(file_list):
    con = sqlite3.connect(f'{DB_PATH}/{db_name}')
    cur = con.cursor()
    df = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con)
    table_list = df['name'].to_list()
    for code in table_list:
        if code != 'moneytop':
            df = pd.read_sql(f"SELECT * FROM '{code}'", con).set_index('index')
            df['라운드피겨위5호가이내'] = df['현재가'].apply(lambda x: 1. if roundfigure_upper5(x, 20230125000001) else 0.)
            df.to_sql(code, con, if_exists='replace', chunksize=1000)
    con.commit()
    cur.execute('VACUUM;')
    con.close()
    print(f'{db_name} 라운드피겨 업데이트 중 ... [{k + 1}/{last}]')
print('라운드피겨 업데이트 완료')
