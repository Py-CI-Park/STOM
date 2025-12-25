# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

def DetectTimeframe(df_tsg, save_file_name=''):
    """
    백테스팅 데이터의 타임프레임(Tick/Min)을 자동 감지합니다.

    Args:
        df_tsg: 백테스팅 결과 DataFrame
        save_file_name: 저장 파일명 (선택적)

    Returns:
        dict: 타임프레임 정보
            - timeframe: 'tick' 또는 'min'
            - scale_factor: 스케일 조정 계수
            - time_unit: 시간 단위 ('초' 또는 '분')
            - holding_bins: 보유시간 bins
            - holding_labels: 보유시간 라벨
            - label: 표시용 라벨
    """
    # 파일명에서 감지
    name_lower = save_file_name.lower()
    if 'tick' in name_lower or '_t_' in name_lower:
        timeframe = 'tick'
    elif 'min' in name_lower or '_m_' in name_lower:
        timeframe = 'min'
    else:
        # 인덱스 형식에서 감지 (YYYYMMDDHHMMSS vs YYYYMMDDHHMM)
        try:
            first_idx = str(df_tsg.index[0])
            if len(first_idx) >= 14:  # 초까지 있으면 Tick
                timeframe = 'tick'
            else:
                timeframe = 'min'
        except:
            timeframe = 'tick'  # 기본값

    # 스케일 조정
    if timeframe == 'tick':
        return {
            'timeframe': 'tick',
            'scale_factor': 1,
            'time_unit': '초',
            'holding_bins': [0, 30, 60, 120, 300, 600, 1200, 3600],
            'holding_labels': ['~30초', '30-60초', '1-2분', '2-5분',
                              '5-10분', '10-20분', '20분+'],
            'label': 'Tick 데이터'
        }
    else:
        return {
            'timeframe': 'min',
            'scale_factor': 60,
            'time_unit': '분',
            'holding_bins': [0, 1, 3, 5, 10, 30, 60, 1440],
            'holding_labels': ['~1분', '1-3분', '3-5분', '5-10분',
                              '10-30분', '30-60분', '1시간+'],
            'label': 'Min 데이터'
        }

def CalculateEnhancedDerivedMetrics(df_tsg):
    """
    강화된 파생 지표를 계산합니다.

    기존 지표 + 추가 지표:
    - 모멘텀 지표
    - 변동성 지표
    - 연속 손익 패턴
    - 리스크 조정 수익률
    - 시장 타이밍 점수

    Args:
        df_tsg: 백테스팅 결과 DataFrame

    Returns:
        DataFrame: 강화된 파생 지표가 추가된 DataFrame
    """
    df = df_tsg.copy()

    # 기존 매도 시점 컬럼 확인
    sell_columns = ['매도등락율', '매도체결강도', '매도당일거래대금', '매도전일비', '매도회전율', '매도호가잔량비']
    has_sell_data = all(col in df.columns for col in sell_columns)

    if has_sell_data:
        # === 1. 변화량 지표 (매도 - 매수) ===
        df['등락율변화'] = df['매도등락율'] - df['매수등락율']
        df['체결강도변화'] = df['매도체결강도'] - df['매수체결강도']
        df['전일비변화'] = df['매도전일비'] - df['매수전일비']
        df['회전율변화'] = df['매도회전율'] - df['매수회전율']
        df['호가잔량비변화'] = df['매도호가잔량비'] - df['매수호가잔량비']

        # === 2. 변화율 지표 (매도 / 매수) ===
        df['거래대금변화율'] = np.where(
            df['매수당일거래대금'] > 0,
            df['매도당일거래대금'] / df['매수당일거래대금'],
            1.0
        )
        df['체결강도변화율'] = np.where(
            df['매수체결강도'] > 0,
            df['매도체결강도'] / df['매수체결강도'],
            1.0
        )

        # === 3. 추세 판단 지표 ===
        df['등락추세'] = df['등락율변화'].apply(lambda x: '상승' if x > 0 else ('하락' if x < 0 else '유지'))
        df['체결강도추세'] = df['체결강도변화'].apply(lambda x: '강화' if x > 10 else ('약화' if x < -10 else '유지'))
        df['거래량추세'] = df['거래대금변화율'].apply(lambda x: '증가' if x > 1.2 else ('감소' if x < 0.8 else '유지'))

        # === 4. 위험 신호 지표 ===
        df['급락신호'] = (df['등락율변화'] < -3) & (df['체결강도변화'] < -20)
        df['매도세증가'] = df['호가잔량비변화'] < -0.2
        df['거래량급감'] = df['거래대금변화율'] < 0.5

        # === 5. 매수/매도 위험도 점수 (0-100, 사후 진단용) ===
        # - 매도 시점 확정 정보(매도-매수 변화량 등)를 포함하는 위험도 점수입니다.
        # - "매수 진입 필터"로 쓰면 룩어헤드가 되므로, 비교/진단 차트용으로만 사용합니다.
        df['매수매도위험도점수'] = 0
        df.loc[df['등락율변화'] < -2, '매수매도위험도점수'] += 15
        df.loc[df['등락율변화'] < -5, '매수매도위험도점수'] += 10  # 추가 가중치
        df.loc[df['체결강도변화'] < -15, '매수매도위험도점수'] += 15
        df.loc[df['체결강도변화'] < -30, '매수매도위험도점수'] += 10  # 추가 가중치
        df.loc[df['호가잔량비변화'] < -0.3, '매수매도위험도점수'] += 15
        df.loc[df['거래대금변화율'] < 0.6, '매수매도위험도점수'] += 15
        if '매수등락율' in df.columns:
            df.loc[df['매수등락율'] > 20, '매수매도위험도점수'] += 10
            df.loc[df['매수등락율'] > 25, '매수매도위험도점수'] += 10  # 추가 가중치
        df['매수매도위험도점수'] = df['매수매도위험도점수'].clip(0, 100)

    # === 6. 모멘텀 점수 (NEW) ===
    if '매수등락율' in df.columns and '매수체결강도' in df.columns:
        # 등락율과 체결강도를 정규화하여 모멘텀 점수 계산
        등락율_norm = (df['매수등락율'] - df['매수등락율'].mean()) / (df['매수등락율'].std() + 0.001)
        체결강도_norm = (df['매수체결강도'] - 100) / 50  # 100을 기준으로 정규화
        df['모멘텀점수'] = round((등락율_norm * 0.4 + 체결강도_norm * 0.6) * 10, 2)

    # === 7. 변동성 지표 (NEW) ===
    if '매수고가' in df.columns and '매수저가' in df.columns:
        df['매수변동폭'] = df['매수고가'] - df['매수저가']
        df['매수변동폭비율'] = np.where(
            df['매수저가'] > 0,
            (df['매수고가'] - df['매수저가']) / df['매수저가'] * 100,
            0
        )

    if has_sell_data and '매도고가' in df.columns:
        df['매도변동폭비율'] = np.where(
            df['매도저가'] > 0,
            (df['매도고가'] - df['매도저가']) / df['매도저가'] * 100,
            0
        )
        df['변동성변화'] = df['매도변동폭비율'] - df['매수변동폭비율']

    # === 7.5. 매수 시점 위험도 점수 (0-100, LOOKAHEAD-FREE) ===
    # - 필터 분석은 "매수를 안 하는 조건(진입 회피)"을 찾는 것이므로,
    #   매도 시점 정보(매도등락율/변화량/보유시간 등)를 사용하면 룩어헤드가 됩니다.
    # - 위험도점수는 매수 시점에서 알 수 있는 정보만으로 계산합니다.
    df['위험도점수'] = 0

    # 1) 과열(추격 매수) 위험: 매수등락율
    if '매수등락율' in df.columns:
        buy_ret = pd.to_numeric(df['매수등락율'], errors='coerce')
        df.loc[buy_ret >= 20, '위험도점수'] += 20
        df.loc[buy_ret >= 25, '위험도점수'] += 10
        df.loc[buy_ret >= 30, '위험도점수'] += 10

    # 2) 매수체결강도 약세 위험
    if '매수체결강도' in df.columns:
        buy_power = pd.to_numeric(df['매수체결강도'], errors='coerce')
        df.loc[buy_power < 80, '위험도점수'] += 15
        df.loc[buy_power < 60, '위험도점수'] += 10
        # 과열(초고 체결강도)도 손실로 이어지는 경우가 있어 별도 가중(룩어헤드 없음)
        df.loc[buy_power >= 150, '위험도점수'] += 10
        df.loc[buy_power >= 200, '위험도점수'] += 10
        df.loc[buy_power >= 250, '위험도점수'] += 10

    # 3) 유동성 위험: 매수당일거래대금 (원본 단위가 '백만' 또는 '억' 혼재 가능)
    if '매수당일거래대금' in df.columns:
        trade_money_raw = pd.to_numeric(df['매수당일거래대금'], errors='coerce')
        # STOM: 당일거래대금 단위 = 백만 → 억 환산(÷100)
        trade_money_eok = trade_money_raw / 100.0
        df.loc[trade_money_eok < 50, '위험도점수'] += 15
        df.loc[trade_money_eok < 100, '위험도점수'] += 10

    # 4) 소형주 위험: 시가총액(억)
    if '시가총액' in df.columns:
        mcap = pd.to_numeric(df['시가총액'], errors='coerce')
        df.loc[mcap < 1000, '위험도점수'] += 15
        df.loc[mcap < 5000, '위험도점수'] += 10

    # 5) 매도우위(호가) 위험: 매수호가잔량비
    if '매수호가잔량비' in df.columns:
        hoga = pd.to_numeric(df['매수호가잔량비'], errors='coerce')
        df.loc[hoga < 90, '위험도점수'] += 10
        df.loc[hoga < 70, '위험도점수'] += 15

    # 6) 슬리피지/비유동 위험: 매수스프레드(%)
    if '매수스프레드' in df.columns:
        spread = pd.to_numeric(df['매수스프레드'], errors='coerce')
        df.loc[spread >= 0.5, '위험도점수'] += 10
        df.loc[spread >= 1.0, '위험도점수'] += 10

    # 6.5) 유동성(회전율) 기반 위험도(룩어헤드 없음)
    if '매수회전율' in df.columns:
        turn = pd.to_numeric(df['매수회전율'], errors='coerce')
        df.loc[turn < 10, '위험도점수'] += 5
        df.loc[turn < 5, '위험도점수'] += 10

    # 7) 변동성 위험: 매수변동폭비율(%)
    if '매수변동폭비율' in df.columns:
        vol_pct = pd.to_numeric(df['매수변동폭비율'], errors='coerce')
        df.loc[vol_pct >= 7.5, '위험도점수'] += 10
        df.loc[vol_pct >= 10, '위험도점수'] += 10
        df.loc[vol_pct >= 15, '위험도점수'] += 10

    df['위험도점수'] = df['위험도점수'].clip(0, 100)

    # === 8. 시장 타이밍 점수 (NEW) ===
    if '매수시' in df.columns:
        # 시간대별 평균 수익률을 기반으로 타이밍 점수 계산
        hour_profit = df.groupby('매수시')['수익률'].mean()
        df['시간대평균수익률'] = df['매수시'].map(hour_profit)
        df['타이밍점수'] = round((df['시간대평균수익률'] - df['시간대평균수익률'].mean()) /
                               (df['시간대평균수익률'].std() + 0.001) * 10, 2)

    # === 9. 연속 손익 패턴 (NEW) ===
    df['이익여부'] = (df['수익금'] > 0).astype(int)
    df['연속이익'] = 0
    df['연속손실'] = 0

    consecutive_win = 0
    consecutive_loss = 0
    for i in range(len(df)):
        if df.iloc[i]['이익여부'] == 1:
            consecutive_win += 1
            consecutive_loss = 0
        else:
            consecutive_loss += 1
            consecutive_win = 0
        df.iloc[i, df.columns.get_loc('연속이익')] = consecutive_win
        df.iloc[i, df.columns.get_loc('연속손실')] = consecutive_loss

    # === 10. 리스크 조정 점수 (NEW) ===
    if '매수등락율' in df.columns and '보유시간' in df.columns:
        # 수익률 / (위험 요소들의 가중 합)
        risk_factor = (df['매수등락율'].abs() / 10 +
                       df['보유시간'] / 300 +
                       1)  # 최소값 보장
        df['리스크조정수익률'] = round(df['수익률'] / risk_factor, 4)

    # === 11. 스프레드 영향도 (NEW) ===
    if '매수스프레드' in df.columns:
        df['스프레드영향'] = np.where(
            df['매수스프레드'] > 0.5, '높음',
            np.where(df['매수스프레드'] > 0.2, '중간', '낮음')
        )

    # === 12. 거래 품질 점수 (NEW) - 종합 점수 ===
    df['거래품질점수'] = 50  # 기본값

    # 긍정적 요소 가산
    if '매수체결강도' in df.columns:
        df.loc[df['매수체결강도'] >= 120, '거래품질점수'] += 10
        df.loc[df['매수체결강도'] >= 150, '거래품질점수'] += 10

    if '매수호가잔량비' in df.columns:
        df.loc[df['매수호가잔량비'] >= 100, '거래품질점수'] += 10

    if '시가총액' in df.columns:
        df.loc[(df['시가총액'] >= 1000) & (df['시가총액'] <= 10000), '거래품질점수'] += 10

    # 부정적 요소 감산
    if '매수등락율' in df.columns:
        df.loc[df['매수등락율'] >= 25, '거래품질점수'] -= 15
        df.loc[df['매수등락율'] >= 30, '거래품질점수'] -= 10

    if '매수스프레드' in df.columns:
        df.loc[df['매수스프레드'] >= 0.5, '거래품질점수'] -= 10

    df['거래품질점수'] = df['거래품질점수'].clip(0, 100)

    # === 13. 지표 조합 비율 (NEW 2025-12-14) ===
    # 조건식에서 사용하는 주요 지표 조합을 파생 지표로 추가

    # 13.1 초당매수수량 / 매도총잔량 비율 (매수세 강도)
    if '매수초당매수수량' in df.columns and '매수매도총잔량' in df.columns:
        df['초당매수수량_매도총잔량_비율'] = np.where(
            df['매수매도총잔량'] > 0,
            df['매수초당매수수량'] / df['매수매도총잔량'] * 100,
            0
        )

    # 13.2 매도총잔량 / 매수총잔량 비율 (호가 불균형 - 매도 우위)
    if '매수매도총잔량' in df.columns and '매수매수총잔량' in df.columns:
        df['매도잔량_매수잔량_비율'] = np.where(
            df['매수매수총잔량'] > 0,
            df['매수매도총잔량'] / df['매수매수총잔량'],
            0
        )

    # 13.3 매수총잔량 / 매도총잔량 비율 (호가 불균형 - 매수 우위)
    if '매수매수총잔량' in df.columns and '매수매도총잔량' in df.columns:
        df['매수잔량_매도잔량_비율'] = np.where(
            df['매수매도총잔량'] > 0,
            df['매수매수총잔량'] / df['매수매도총잔량'],
            0
        )

    # 13.4 초당매도수량 / 초당매수수량 비율 (매도 압력)
    if '매수초당매도수량' in df.columns and '매수초당매수수량' in df.columns:
        df['초당매도_매수_비율'] = np.where(
            df['매수초당매수수량'] > 0,
            df['매수초당매도수량'] / df['매수초당매수수량'],
            0
        )

    # 13.5 초당매수수량 / 초당매도수량 비율 (매수 압력)
    if '매수초당매수수량' in df.columns and '매수초당매도수량' in df.columns:
        df['초당매수_매도_비율'] = np.where(
            df['매수초당매도수량'] > 0,
            df['매수초당매수수량'] / df['매수초당매도수량'],
            0
        )

    # 13.6 현재가 위치 비율: 매수가 / (고가 - (고가-저가)*factor) 형태
    # 고가 근처에서 거래 중인지 확인 (저가 대비 현재가 위치)
    if '매수가' in df.columns and '매수고가' in df.columns and '매수저가' in df.columns:
        price_range = df['매수고가'] - df['매수저가']
        df['현재가_고저범위_위치'] = np.where(
            price_range > 0,
            (df['매수가'] - df['매수저가']) / price_range * 100,
            50  # 범위가 0이면 중간값
        )

    # 13.7 초당거래대금 관련 지표 (거래 강도)
    if '매수초당거래대금' in df.columns and '매수당일거래대금' in df.columns:
        # 초당거래대금 비중 (당일거래대금 대비)
        df['초당거래대금_당일비중'] = np.where(
            df['매수당일거래대금'] > 0,
            df['매수초당거래대금'] / df['매수당일거래대금'] * 10000,  # 만분율
            0
        )

    # 13.8 초당순매수금액 (초당매수수량 - 초당매도수량) * 현재가
    if '매수초당매수수량' in df.columns and '매수초당매도수량' in df.columns and '매수가' in df.columns:
        df['초당순매수수량'] = df['매수초당매수수량'] - df['매수초당매도수량']
        df['초당순매수금액'] = df['초당순매수수량'] * df['매수가'] / 1_000_000  # 백만원 단위

    # 13.9 초당매수수량 / 초당매도수량 순매수 비율 (0~200 범위로 정규화)
    if '매수초당매수수량' in df.columns and '매수초당매도수량' in df.columns:
        total_volume = df['매수초당매수수량'] + df['매수초당매도수량']
        df['초당순매수비율'] = np.where(
            total_volume > 0,
            df['매수초당매수수량'] / total_volume * 100,
            50  # 거래 없으면 중립
        )

    # === 14. 매도 시점 지표 조합 (NEW 2025-12-14) ===
    # 매도 시점에서의 지표 변화도 분석에 활용

    # 14.1 매도 시점 초당매수/매도 비율
    if '매도초당매수수량' in df.columns and '매도초당매도수량' in df.columns:
        df['매도시_초당매수_매도_비율'] = np.where(
            df['매도초당매도수량'] > 0,
            df['매도초당매수수량'] / df['매도초당매도수량'],
            0
        )

    # 14.2 초당 지표 변화 (매도 - 매수)
    if '매수초당매수수량' in df.columns and '매도초당매수수량' in df.columns:
        df['초당매수수량변화'] = df['매도초당매수수량'] - df['매수초당매수수량']

    if '매수초당매도수량' in df.columns and '매도초당매도수량' in df.columns:
        df['초당매도수량변화'] = df['매도초당매도수량'] - df['매수초당매도수량']

    if '매수초당거래대금' in df.columns and '매도초당거래대금' in df.columns:
        df['초당거래대금변화'] = df['매도초당거래대금'] - df['매수초당거래대금']
        df['초당거래대금변화율'] = np.where(
            df['매수초당거래대금'] > 0,
            df['매도초당거래대금'] / df['매수초당거래대금'],
            1.0
        )

    return df
