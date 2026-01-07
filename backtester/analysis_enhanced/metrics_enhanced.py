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

def CalculateEnhancedDerivedMetrics(df_tsg, timeframe: str = 'auto', save_file_name: str = ''):
    """
    강화된 파생 지표를 계산합니다.

    기존 지표 + 추가 지표:
    - 모멘텀 지표
    - 변동성 지표
    - 연속 손익 패턴
    - 리스크 조정 수익률
    - 시장 타이밍 점수

    [2026-01-07] 타임프레임별 변수 분리:
    - 틱 모드: 초당매수수량, 초당매도수량, 초당거래대금 사용
    - 분봉 모드: 분당매수수량, 분당매도수량, 분당거래대금 사용
    - 변환 금지: 초당* = 분당*/60 같은 변환은 하지 않음

    Args:
        df_tsg: 백테스팅 결과 DataFrame
        timeframe: 'tick', 'min', 또는 'auto' (자동 감지)
        save_file_name: 저장 파일명 (타임프레임 자동 감지용)

    Returns:
        DataFrame: 강화된 파생 지표가 추가된 DataFrame
    """
    df = df_tsg.copy()

    # 타임프레임 자동 감지
    if timeframe == 'auto':
        tf_info = DetectTimeframe(df, save_file_name)
        timeframe = tf_info.get('timeframe', 'tick')
    
    # 타임프레임 정보를 DataFrame에 저장 (디버깅/검증용)
    df.attrs['timeframe'] = timeframe

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
        # 런타임과 동일한 고정 스케일 기반 모멘텀 점수 계산
        등락율_norm = df['매수등락율'] / 10
        체결강도_norm = (df['매수체결강도'] - 100) / 50
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

    # === 13. 지표 조합 비율 - 타임프레임별 분기 (2026-01-07 개선) ===
    # [핵심 원칙] 분봉 모드에서는 분당* 변수만 사용, 틱 모드에서는 초당* 변수만 사용
    # 변환 금지: 초당* = 분당*/60 같은 변환은 하지 않음
    
    if timeframe == 'tick':
        # === 13-TICK. 틱 모드 전용 지표 조합 ===
        
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

        # 13.6 현재가 위치 비율
        if '매수가' in df.columns and '매수고가' in df.columns and '매수저가' in df.columns:
            price_range = df['매수고가'] - df['매수저가']
            df['현재가_고저범위_위치'] = np.where(
                price_range > 0,
                (df['매수가'] - df['매수저가']) / price_range * 100,
                50
            )

        # 13.7 초당거래대금 관련 지표 (거래 강도)
        if '매수초당거래대금' in df.columns and '매수당일거래대금' in df.columns:
            df['초당거래대금_당일비중'] = np.where(
                df['매수당일거래대금'] > 0,
                df['매수초당거래대금'] / df['매수당일거래대금'] * 10000,
                0
            )

        # 13.8 초당순매수금액
        if '매수초당매수수량' in df.columns and '매수초당매도수량' in df.columns and '매수가' in df.columns:
            df['초당순매수수량'] = df['매수초당매수수량'] - df['매수초당매도수량']
            df['초당순매수금액'] = df['초당순매수수량'] * df['매수가'] / 1_000_000

        # 13.9 초당순매수비율
        if '매수초당매수수량' in df.columns and '매수초당매도수량' in df.columns:
            total_volume = df['매수초당매수수량'] + df['매수초당매도수량']
            df['초당순매수비율'] = np.where(
                total_volume > 0,
                df['매수초당매수수량'] / total_volume * 100,
                50
            )

    else:
        # === 13-MIN. 분봉 모드 전용 지표 조합 (2026-01-07 신규) ===
        # 분당* 변수만 직접 사용, 초당* 변수로의 변환 금지
        
        # 13.1-MIN 분당매수수량 / 매도총잔량 비율 (매수세 강도)
        if '매수분당매수수량' in df.columns and '매수매도총잔량' in df.columns:
            df['분당매수수량_매도총잔량_비율'] = np.where(
                df['매수매도총잔량'] > 0,
                df['매수분당매수수량'] / df['매수매도총잔량'] * 100,
                0
            )

        # 13.2-MIN 매도총잔량 / 매수총잔량 비율 (호가 불균형 - 매도 우위)
        if '매수매도총잔량' in df.columns and '매수매수총잔량' in df.columns:
            df['매도잔량_매수잔량_비율'] = np.where(
                df['매수매수총잔량'] > 0,
                df['매수매도총잔량'] / df['매수매수총잔량'],
                0
            )

        # 13.3-MIN 매수총잔량 / 매도총잔량 비율 (호가 불균형 - 매수 우위)
        if '매수매수총잔량' in df.columns and '매수매도총잔량' in df.columns:
            df['매수잔량_매도잔량_비율'] = np.where(
                df['매수매도총잔량'] > 0,
                df['매수매수총잔량'] / df['매수매도총잔량'],
                0
            )

        # 13.4-MIN 분당매도수량 / 분당매수수량 비율 (매도 압력)
        if '매수분당매도수량' in df.columns and '매수분당매수수량' in df.columns:
            df['분당매도_매수_비율'] = np.where(
                df['매수분당매수수량'] > 0,
                df['매수분당매도수량'] / df['매수분당매수수량'],
                0
            )

        # 13.5-MIN 분당매수수량 / 분당매도수량 비율 (매수 압력)
        if '매수분당매수수량' in df.columns and '매수분당매도수량' in df.columns:
            df['분당매수_매도_비율'] = np.where(
                df['매수분당매도수량'] > 0,
                df['매수분당매수수량'] / df['매수분당매도수량'],
                0
            )

        # 13.6-MIN 현재가 위치 비율 (분봉 고저가 사용)
        if '매수가' in df.columns and '매수분봉고가' in df.columns and '매수분봉저가' in df.columns:
            price_range = df['매수분봉고가'] - df['매수분봉저가']
            df['현재가_분봉고저범위_위치'] = np.where(
                price_range > 0,
                (df['매수가'] - df['매수분봉저가']) / price_range * 100,
                50
            )
        # 폴백: 일반 고가/저가 사용
        elif '매수가' in df.columns and '매수고가' in df.columns and '매수저가' in df.columns:
            price_range = df['매수고가'] - df['매수저가']
            df['현재가_고저범위_위치'] = np.where(
                price_range > 0,
                (df['매수가'] - df['매수저가']) / price_range * 100,
                50
            )

        # 13.7-MIN 분당거래대금 관련 지표 (거래 강도)
        if '매수분당거래대금' in df.columns and '매수당일거래대금' in df.columns:
            df['분당거래대금_당일비중'] = np.where(
                df['매수당일거래대금'] > 0,
                df['매수분당거래대금'] / df['매수당일거래대금'] * 10000,
                0
            )

        # 13.8-MIN 분당순매수금액
        if '매수분당매수수량' in df.columns and '매수분당매도수량' in df.columns and '매수가' in df.columns:
            df['분당순매수수량'] = df['매수분당매수수량'] - df['매수분당매도수량']
            df['분당순매수금액'] = df['분당순매수수량'] * df['매수가'] / 1_000_000

        # 13.9-MIN 분당순매수비율
        if '매수분당매수수량' in df.columns and '매수분당매도수량' in df.columns:
            total_volume = df['매수분당매수수량'] + df['매수분당매도수량']
            df['분당순매수비율'] = np.where(
                total_volume > 0,
                df['매수분당매수수량'] / total_volume * 100,
                50
            )

    # === 14. 매도 시점 지표 조합 - 타임프레임별 분기 ===
    
    if timeframe == 'tick':
        # === 14-TICK. 틱 모드 매도 시점 지표 ===
        
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

    else:
        # === 14-MIN. 분봉 모드 매도 시점 지표 (2026-01-07 신규) ===
        
        # 14.1-MIN 매도 시점 분당매수/매도 비율
        if '매도분당매수수량' in df.columns and '매도분당매도수량' in df.columns:
            df['매도시_분당매수_매도_비율'] = np.where(
                df['매도분당매도수량'] > 0,
                df['매도분당매수수량'] / df['매도분당매도수량'],
                0
            )

        # 14.2-MIN 분당 지표 변화 (매도 - 매수)
        if '매수분당매수수량' in df.columns and '매도분당매수수량' in df.columns:
            df['분당매수수량변화'] = df['매도분당매수수량'] - df['매수분당매수수량']

        if '매수분당매도수량' in df.columns and '매도분당매도수량' in df.columns:
            df['분당매도수량변화'] = df['매도분당매도수량'] - df['매수분당매도수량']

        if '매수분당거래대금' in df.columns and '매도분당거래대금' in df.columns:
            df['분당거래대금변화'] = df['매도분당거래대금'] - df['매수분당거래대금']
            df['분당거래대금변화율'] = np.where(
                df['매수분당거래대금'] > 0,
                df['매도분당거래대금'] / df['매수분당거래대금'],
                1.0
            )

    # === 15. 당일거래대금 시계열 비율 (NEW 2025-12-28) ===
    # 거래 흐름 상의 당일거래대금 변화율을 분석하여 유동성 증감 트렌드 파악

    # 15.1 당일거래대금 전틱/분봉 대비 비율 (거래대금 증감 트렌드)
    # - 의미: 현재 거래의 당일거래대금이 직전 거래 대비 얼마나 변화했는지
    # - 비율 > 1: 거래대금 증가 (유동성 증가)
    # - 비율 < 1: 거래대금 감소 (유동성 감소)
    # - 활용: 필터 조건 (예: 당일거래대금_전틱분봉_비율 >= 1.2)
    if '매수당일거래대금' in df.columns:
        has_trade_ratio = '당일거래대금_전틱분봉_비율' in df.columns
        has_trade_avg_ratio = '당일거래대금_5틱분봉평균_비율' in df.columns
        if has_trade_ratio:
            existing = pd.to_numeric(df['당일거래대금_전틱분봉_비율'], errors='coerce').fillna(0)
            has_trade_ratio = existing.ne(0).any()
        if has_trade_avg_ratio:
            existing = pd.to_numeric(df['당일거래대금_5틱분봉평균_비율'], errors='coerce').fillna(0)
            has_trade_avg_ratio = existing.ne(0).any()
        group_cols = []
        if '종목명' in df.columns:
            group_cols.append('종목명')
        if '매수일자' in df.columns:
            group_cols.append('매수일자')
        if group_cols:
            grouped = df.groupby(group_cols, sort=False)['매수당일거래대금']
            prev_trade_money = grouped.shift(1)
            rolling_avg = grouped.rolling(window=5, min_periods=1).mean().reset_index(level=group_cols, drop=True)
        else:
            prev_trade_money = df['매수당일거래대금'].shift(1)
            rolling_avg = df['매수당일거래대금'].rolling(window=5, min_periods=1).mean()

        if not has_trade_ratio:
            df['당일거래대금_전틱분봉_비율'] = np.where(
                prev_trade_money > 0,
                df['매수당일거래대금'] / (prev_trade_money + 1e-6),
                0.0
            )

    # 15.2 매도 시점 당일거래대금 비율 (매수→매도 간 거래대금 변화)
    # - 의미: 매수 시점 대비 매도 시점의 당일거래대금 변화율
    # - 비율 > 1: 보유 기간 동안 시장 유동성 증가
    # - 비율 < 1: 보유 기간 동안 시장 유동성 감소
    # - 활용: 매도 타이밍 분석, 시장 활성도 변화 파악
    if '매수당일거래대금' in df.columns and '매도당일거래대금' in df.columns:
        df['당일거래대금_매수매도_비율'] = np.where(
            df['매수당일거래대금'] > 0,
            df['매도당일거래대금'] / df['매수당일거래대금'],
            1.0
        )

    # 15.3 N틱/분봉 평균 대비 당일거래대금 비율 (단기 트렌드 파악)
    # - 의미: 최근 5틱/분봉 평균 대비 현재 당일거래대금 비율
    # - 비율 > 1: 평균 대비 높은 유동성 (거래 활성화)
    # - 비율 < 1: 평균 대비 낮은 유동성 (거래 둔화)
    # - 활용: 노이즈 감소, 장기 트렌드 기반 필터 조건
        if not has_trade_avg_ratio:
            df['당일거래대금_5틱분봉평균_비율'] = np.where(
                rolling_avg > 0,
                df['매수당일거래대금'] / (rolling_avg + 1e-6),
                0.0
            )

    return df
