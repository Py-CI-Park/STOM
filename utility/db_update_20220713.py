import os
import sys
import sqlite3
import pandas as pd
from multiprocessing import Process
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from utility.setting import DB_PATH


def Updater(gubun, file_list_):
    print(f'[{gubun}] VI해제시간 업데이트 시작')
    last = len(file_list_)
    for k, db_name in enumerate(file_list_):
        con = sqlite3.connect(f'{DB_PATH}/{db_name}')
        cur = con.cursor()
        df = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con)
        table_list = df['name'].to_list()
        for code in table_list:
            if code != 'moneytop':
                df = pd.read_sql(f"SELECT * FROM '{code}'", con).set_index('index')
                df[['VI해제시간']] = df[['VI해제시간']].astype('int64')
                df.to_sql(code, con, if_exists='replace', chunksize=1000)
        con.commit()
        cur.execute('VACUUM;')
        con.close()
        print(f'[{gubun}] {db_name} VI해제시간 업데이트 중 ... [{k + 1}/{last}]')
    print(f'[{gubun}] VI해제시간 업데이트 완료')


if __name__ == '__main__':
    file_list = os.listdir(DB_PATH)
    file_list = [x for x in file_list if 'stock_tick_' in x and 'back' not in x and '.zip' not in x]

    file_lists = []
    for i in range(4):
        file_lists.append([file for j, file in enumerate(file_list) if j % 4 == i])

    proc_list = []
    for i, file_list in enumerate(file_lists):
        p = Process(target=Updater, args=(i + 1, file_list), daemon=True)
        p.start()
        proc_list.append(p)

    for p in proc_list:
        p.join()
