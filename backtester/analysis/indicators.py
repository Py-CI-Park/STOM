import math
from talib import stream

def AddAvgData(df, round_unit, is_tick, avg_list):
    if is_tick:
        df['이평0060'] = df['현재가'].rolling(window=60).mean().round(round_unit)
        df['이평0300'] = df['현재가'].rolling(window=300).mean().round(round_unit)
        df['이평0600'] = df['현재가'].rolling(window=600).mean().round(round_unit)
        df['이평1200'] = df['현재가'].rolling(window=1200).mean().round(round_unit)
    else:
        df['이평005'] = df['현재가'].rolling(window=5).mean().round(round_unit)
        df['이평010'] = df['현재가'].rolling(window=10).mean().round(round_unit)
        df['이평020'] = df['현재가'].rolling(window=20).mean().round(round_unit)
        df['이평060'] = df['현재가'].rolling(window=60).mean().round(round_unit)
        df['이평120'] = df['현재가'].rolling(window=120).mean().round(round_unit)
    for avg in avg_list:
        df[f'최고현재가{avg}'] = df['현재가'].rolling(window=avg).max()
        df[f'최저현재가{avg}'] = df['현재가'].rolling(window=avg).min()
        if not is_tick:
            df[f'최고분봉고가{avg}'] = df['분봉고가'].rolling(window=avg).max()
            df[f'최저분봉저가{avg}'] = df['분봉저가'].rolling(window=avg).min()
        df[f'체결강도평균{avg}'] = df['체결강도'].rolling(window=avg).mean().round(3)
        df[f'최고체결강도{avg}'] = df['체결강도'].rolling(window=avg).max()
        df[f'최저체결강도{avg}'] = df['체결강도'].rolling(window=avg).min()
        if is_tick:
            df[f'최고초당매수수량{avg}'] = df['초당매수수량'].rolling(window=avg).max()
            df[f'최고초당매도수량{avg}'] = df['초당매도수량'].rolling(window=avg).max()
            df[f'누적초당매수수량{avg}'] = df['초당매수수량'].rolling(window=avg).sum()
            df[f'누적초당매도수량{avg}'] = df['초당매도수량'].rolling(window=avg).sum()
            df[f'초당거래대금평균{avg}'] = df['초당거래대금'].rolling(window=avg).mean().round(0)
        else:
            df[f'최고분당매수수량{avg}'] = df['분당매수수량'].rolling(window=avg).max()
            df[f'최고분당매도수량{avg}'] = df['분당매도수량'].rolling(window=avg).max()
            df[f'누적분당매수수량{avg}'] = df['분당매수수량'].rolling(window=avg).sum()
            df[f'누적분당매도수량{avg}'] = df['분당매도수량'].rolling(window=avg).sum()
            df[f'분당거래대금평균{avg}'] = df['분당거래대금'].rolling(window=avg).mean().round(0)
        if round_unit == 3:
            df2 = df[['등락율', '당일거래대금', '전일비']].copy()
            df2[f'등락율N{avg}'] = df2['등락율'].shift(avg - 1)
            df2['등락율차이'] = df2['등락율'] - df2[f'등락율N{avg}']
            df2[f'당일거래대금N{avg}'] = df2['당일거래대금'].shift(avg - 1)
            df2['당일거래대금차이'] = df2['당일거래대금'] - df2[f'당일거래대금N{avg}']
            df2[f'전일비N{avg}'] = df2['전일비'].shift(avg - 1)
            df2['전일비차이'] = df2['전일비'] - df2[f'전일비N{avg}']
            df['등락율각도'] = df2['등락율차이'].apply(lambda x: round(math.atan2(x * 5, avg) / (2 * math.pi) * 360, 2))
            df['당일거래대금각도'] = df2['당일거래대금차이'].apply(lambda x: round(math.atan2(x / 100, avg) / (2 * math.pi) * 360, 2))
            df['전일비각도'] = df2['전일비차이'].apply(lambda x: round(math.atan2(x, avg) / (2 * math.pi) * 360, 2))
        else:
            df2 = df[['등락율', '당일거래대금']].copy()
            df2[f'등락율N{avg}'] = df2['등락율'].shift(avg - 1)
            df2['등락율차이'] = df2['등락율'] - df2[f'등락율N{avg}']
            df2[f'당일거래대금N{avg}'] = df2['당일거래대금'].shift(avg - 1)
            df2['당일거래대금차이'] = df2['당일거래대금'] - df2[f'당일거래대금N{avg}']
            df['등락율각도'] = df2['등락율차이'].apply(lambda x: round(math.atan2(x * 10, avg) / (2 * math.pi) * 360, 2))
            df['당일거래대금각도'] = df2['당일거래대금차이'].apply(lambda x: round(math.atan2(x / 100_000_000, avg) / (2 * math.pi) * 360, 2))
    return df


def GetIndicator(mc, mh, ml, mv, k):
    AD, ADOSC, ADXR, APO, AROOND, AROONU, ATR, BBU, BBM, BBL, CCI, DIM, DIP, MACD, MACDS, MACDH, MFI, MOM, OBV, PPO, \
        ROC, RSI, SAR, STOCHSK, STOCHSD, STOCHFK, STOCHFD, WILLR = \
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    try:    AD                     = stream.AD(      mh, ml, mc, mv)
    except: AD                     = 0
    if k[0] != 0:
        try:    ADOSC              = stream.ADOSC(   mh, ml, mc, mv, fastperiod=k[0], slowperiod=k[1])
        except: ADOSC              = 0
    if k[2] != 0:
        try:    ADXR               = stream.ADXR(    mh, ml, mc,     timeperiod=k[2])
        except: ADXR               = 0
    if k[3] != 0:
        try:    APO                = stream.APO(     mc,             fastperiod=k[3], slowperiod=k[4], matype=k[5])
        except: APO                = 0
    if k[6] != 0:
        try:    AROOND, AROONU     = stream.AROON(   mh, ml,         timeperiod=k[6])
        except: AROOND, AROONU     = 0, 0
    if k[7] != 0:
        try:    ATR                = stream.ATR(     mh, ml, mc,     timeperiod=k[7])
        except: ATR                = 0
    if k[8] != 0:
        try:    BBU, BBM, BBL      = stream.BBANDS(  mc,             timeperiod=k[8], nbdevup=k[9], nbdevdn=k[10], matype=k[11])
        except: BBU, BBM, BBL      = 0, 0, 0
    if k[12] != 0:
        try:    CCI                = stream.CCI(     mh, ml, mc,     timeperiod=k[12])
        except: CCI                = 0
    if k[13] != 0:
        try:    DIM, DIP           = stream.MINUS_DI(mh, ml, mc,     timeperiod=k[13]), stream.PLUS_DI( mh, ml, mc, timeperiod=k[13])
        except: DIM, DIP           = 0, 0
    if k[14] != 0:
        try:    MACD, MACDS, MACDH = stream.MACD(    mc,             fastperiod=k[14], slowperiod=k[15], signalperiod=k[16])
        except: MACD, MACDS, MACDH = 0, 0, 0
    if k[17] != 0:
        try:    MFI                = stream.MFI(     mh, ml, mc, mv, timeperiod=k[17])
        except: MFI                = 0
    if k[18] != 0:
        try:    MOM                = stream.MOM(     mc,             timeperiod=k[18])
        except: MOM                = 0
    try:    OBV                    = stream.OBV(     mc, mv)
    except: OBV                    = 0
    if k[19] != 0:
        try:    PPO                = stream.PPO(     mc,             fastperiod=k[19], slowperiod=k[20], matype=k[21])
        except: PPO                = 0
    if k[22] != 0:
        try:    ROC                = stream.ROC(     mc,             timeperiod=k[22])
        except: ROC                = 0
    if k[23] != 0:
        try:    RSI                = stream.RSI(     mc,             timeperiod=k[23])
        except: RSI                = 0
    if k[24] != 0:
        try:    SAR                = stream.SAR(     mh, ml,         acceleration=k[24], maximum=k[25])
        except: SAR                = 0
    if k[26] != 0:
        try:    STOCHSK, STOCHSD   = stream.STOCH(   mh, ml, mc,     fastk_period=k[26], slowk_period=k[27], slowk_matype=k[28], slowd_period=k[29], slowd_matype=k[30])
        except: STOCHSK, STOCHSD   = 0, 0
    if k[31] != 0:
        try:    STOCHFK, STOCHFD   = stream.STOCHF(  mh, ml, mc,     fastk_period=k[31], fastd_period=k[32], fastd_matype=k[33])
        except: STOCHFK, STOCHFD   = 0, 0
    if k[34] != 0:
        try:    WILLR              = stream.WILLR(   mh, ml, mc,     timeperiod=k[34])
        except: WILLR              = 0
    return AD, ADOSC, ADXR, APO, AROOND, AROONU, ATR, BBU, BBM, BBL, CCI, DIM, DIP, MACD, MACDS, MACDH, MFI, MOM, OBV, PPO, ROC, RSI, SAR, STOCHSK, STOCHSD, STOCHFK, STOCHFD, WILLR


# ============================================================================
# [2025-12-08] 백테스팅 분석 차트 (8개 차트)
# ============================================================================

