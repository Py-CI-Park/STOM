import os
import sys
import sqlite3
import pandas as pd
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from utility.setting import DB_BACKTEST, BACKVC_PATH
from utility.static import now, pickle_read, pickle_write, pickle_delete


i = 0
print(f'[{now()}] 이전 최적화 데이터의 정리를 시작합니다.')

try:
    con = sqlite3.connect(DB_BACKTEST)
    df  = pd.read_sql('SELECT * FROM back_vc_list', con)
    df.sort_values(by=['index'], ascending=False, inplace=True)
    df.set_index('index', inplace=True)

    for index in df.index:
        if not os.path.isfile(f'{BACKVC_PATH}/{index}.pkl'):
            df.drop(index=index, inplace=True)
            print(f'[{now()}] {index}.pkl 파일이 존재하지 않아 back_vc_list에서 삭제하였습니다.')

    del_file_list = []
    for index in df.index:
        df2 = df[(df['배팅금액'] == df['배팅금액'][index]) & (df['시작일자'] == df['시작일자'][index]) &
                 (df['종료일자'] <= df['종료일자'][index]) & (df['시작시간'] == df['시작시간'][index]) &
                 (df['종료시간'] == df['종료시간'][index]) & (df['매수전략'] == df['매수전략'][index]) &
                 (df['매도전략'] == df['매도전략'][index]) & (df['주관적용'] == df['주관적용'][index]) &
                 (df['매수주관'] == df['매수주관'][index]) & (df['매도주관'] == df['매도주관'][index])]

        if len(df2) > 1:
            for std_file_name in df2.index:
                j = 0
                last_vars_list = list(pickle_read(f'{BACKVC_PATH}/{std_file_name}').keys())
                for fix_file_name in df2.index:
                    if fix_file_name < std_file_name:
                        delete = False
                        data = pickle_read(f'{BACKVC_PATH}/{fix_file_name}')
                        k = 0
                        for key in list(data.keys()):
                            if key in last_vars_list:
                                del data[key]
                                delete = True
                                i += 1
                                j += 1
                                k += 1
                        if delete:
                            if len(data) > 0:
                                pickle_write(f'{BACKVC_PATH}/{fix_file_name}', data)
                                print(f'[{now()}] {fix_file_name}.pkl 파일에서 중복된 데이터 {k}개를 삭제하였습니다.')
                            else:
                                if fix_file_name not in del_file_list:
                                    del_file_list.append(fix_file_name)
                if j == 0:
                    print(f'[{now()}] {std_file_name}.pkl 파일과 중복된 데이터가 없습니다.')

    if len(del_file_list) > 0:
        for file in del_file_list:
            pickle_delete(f'{BACKVC_PATH}/{file}')
            df.drop(index=file, inplace=True)
            print(f'[{now()}] {file}.pkl 파일 및 back_vc_list에서 삭제하였습니다.')

    df.to_sql('back_vc_list', con, if_exists='replace', chunksize=1000)
    con.close()
except:
    pass

if i == 0:
    print(f'[{now()}] 이전 최적화 데이터에 중복된 데이터가 없습니다.')
print(f'[{now()}] 이전 최적화 데이터의 정리를 완료하였습니다.')
