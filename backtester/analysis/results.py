import numpy as np
import pandas as pd
from numba import jit
from utility.setting import columns_bt, columns_btf

def GetResultDataframe(ui_gubun, list_tsg, arry_bct):
    # [2025-12-10] 확장된 50개 컬럼 사용 (매수/매도 시점 시장 데이터 포함)
    # list_tsg에는 'index'가 포함되지만 '수익금합계'는 없음 (나중에 cumsum으로 계산)
    if ui_gubun in ['CT', 'CF']:
        # 코인: 포지션 컬럼 사용
        columns_without_sum = [col for col in columns_btf if col != '수익금합계']
        columns1 = ['index'] + columns_without_sum
        columns2 = columns_btf
    else:
        # 주식: 시가총액 컬럼 사용
        columns_without_sum = [col for col in columns_bt if col != '수익금합계']
        columns1 = ['index'] + columns_without_sum
        columns2 = columns_bt

    df_tsg = pd.DataFrame(list_tsg, columns=columns1)
    df_tsg.set_index('index', inplace=True)
    df_tsg.sort_index(inplace=True)
    df_tsg['수익금합계'] = df_tsg['수익금'].cumsum()
    df_tsg = df_tsg[columns2]
    arry_bct = arry_bct[arry_bct[:, 1] > 0]
    df_bct = pd.DataFrame(arry_bct[:, 1:], columns=['보유종목수', '보유금액'], index=arry_bct[:, 0])
    df_bct.index = df_bct.index.astype(str)
    return df_tsg, df_bct


def AddMdd(arry_tsg, result):
    """
    arry_tsg
    보유시간, 매도시간, 수익률, 수익금, 수익금합계
      0       1       2       3      4
    """
    try:
        array = arry_tsg[:, 4]
        lower = np.argmax(np.maximum.accumulate(array) - array)
        upper = np.argmax(array[:lower])
        mdd   = round(abs(array[upper] - array[lower]) / (array[upper] + result[10]) * 100, 2)
        mdd_  = int(abs(array[upper] - array[lower]))
    except:
        mdd   = abs(result[7])
        mdd_  = abs(result[8])
    result = result + (mdd, mdd_)
    return result


@jit(nopython=True, cache=True)
def GetBackResult(arry_tsg, arry_bct, betting, ui_gubun, day_count):
    """ dtype = 'float64'
    arry_tsg
    보유시간, 매도시간, 수익률, 수익금, 수익금합계
      0       1       2       3      4
    arry_bct
    체결시간, 보유중목수, 보유금액
      0         1        2
    """
    tc, atc, pc, mc, wr, ah, app, tpp, tsg, mhct, seed, cagr, tpi = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    tc = len(arry_tsg)
    if tc > 0:
        arry_p = arry_tsg[arry_tsg[:, 3] >= 0]
        arry_m = arry_tsg[arry_tsg[:, 3] < 0]
        atc    = round(tc / day_count, 1)
        pc     = len(arry_p)
        mc     = len(arry_m)
        wr     = round(pc / tc * 100, 2)
        ah     = round(arry_tsg[:, 0].sum() / tc, 2)
        app    = round(arry_tsg[:, 2].sum() / tc, 2)
        tsg    = int(arry_tsg[:, 3].sum())
        appp   = arry_p[:, 2].mean() if len(arry_p) > 0 else 0
        ampp   = abs(arry_m[:, 2].mean()) if len(arry_m) > 0 else 0
        try:    mhct = int(arry_bct[int(len(arry_bct) * 0.01):, 1].max())
        except: mhct = 0
        try:    seed = int(arry_bct[int(len(arry_bct) * 0.01):, 2].max())
        except: seed = betting
        tpp    = round(tsg / (seed if seed != 0 else betting) * 100, 2)
        cagr   = round(tpp / day_count * (250 if ui_gubun == 'S' else 365), 2)
        tpi    = round(wr / 100 * (1 + appp / ampp), 2) if ampp != 0 else 1.0

    return tc, atc, pc, mc, wr, ah, app, tpp, tsg, mhct, seed, cagr, tpi


