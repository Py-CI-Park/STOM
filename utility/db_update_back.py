import os
import sys
import sqlite3
import pandas as pd
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from utility.static import now
from utility.setting import DB_PATH


def convert(index):
    if index in df_mt.index and code in df_mt['거래대금순위'][index]:
        return 1
    return 0


print(f'[{now()}]백테디비 관심종목 칼럼 업데이트 시작')

file_list = os.listdir(DB_PATH)
file_list = [x for x in file_list if '_tick_back.db' in x]
for db_name in file_list:
    con   = sqlite3.connect(f'{DB_PATH}/{db_name}')
    df_mt = pd.read_sql("SELECT * FROM moneytop", con).set_index('index')
    df_tb = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con)
    table_list = df_tb['name'].to_list()
    table_list.remove('moneytop')
    table_list.remove('codename')
    last = len(table_list)
    for i, code in enumerate(table_list):
        df = pd.read_sql(f"SELECT * FROM '{code}'", con)
        df['관심종목'] = df['index'].apply(lambda x: convert(x))
        df.to_sql(code, con, index=False, if_exists='replace', chunksize=1000)
        print(f'[{now()}]백테디비 관심종목 칼럼 업데이트 중 ... [{i + 1}/{last}]')
    con.close()

print(f'[{now()}]백테디비 관심종목 칼럼 업데이트 완료')
