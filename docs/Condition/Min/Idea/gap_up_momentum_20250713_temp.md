<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# 시초 급등주 분봉 매수·매도 조건식

> 본 문서는 `Back_Testing_Guideline_Min.md`의 변수 체계와 `condition_*.md` 템플릿을 그대로 준수하여, **시초 급등주(갭-업 + 장초반 거래량 폭발 종목)** 전용 분봉 매수·매도 조건식을 설계한 것입니다. 모든 변수는 1 분봉 데이터 기준으로 동작하며, **거래량 필터**를 핵심 트리거로 사용합니다 [^1][^2].

## 1. 전략 개요

- **대상 종목**
전일 종가 대비 시가 갭-업이 **+5% 이상**이면서, 장 시작 5 분 내 분당거래대금이 **20 일 평균의 2 배** 이상 터진 종목 [^1].
- **매매 철학**

1) 장초 강한 수급·심리 모멘텀에 편승해 **짧게 진입-청산**
2) 실시간 **체결강도·분당거래대금** ↓ 시 즉시 이탈
3) **오전 10 시 이전** 포지션 정리(관성 약화 구간 회피) [^3].
- **사용 데이터**
1 분봉 시가·고가·저가·종가, 분당거래대금, 분당매수·매도 수량, 체결강도, VI 변수 등.


## 2. 핵심 변수 정의

| 변수 | 설명 | 사용 예 |
| :-- | :-- | :-- |
| 갭등락율 계산 | (분봉시가−전일종가)/전일종가×100 | `갭등락율계산 ≥ 5` |
| 분당거래대금 `분당거래대금`, 평균 `분당거래대금평균(20)` | 1 분당 거래대금, 최근 20 분 평균 | `분당거래대금 ≥ 분당거래대금평균(20)×2` |
| 체결강도 `체결강도` | 매수/매도 체결비 (0–500) | `체결강도 ≥ 130` |
| 전일동시간비 `전일동시간비` | 전일 동시간대 거래량 대비 당일거래량의 비율 | `전일동시간비 ≥ 200` |
| 시분초 `시분초` | HHMMSS 서버 시각 | 093000 ≤ `시분초` ≤ 100000 |

## 3. 매수 조건식 `C_MIN_GAPUP_2025_B`

```python
# =============================================================================
# 시초 급등주 분봉 매수 조건식 (Gap-Up Momentum Buy)
# =============================================================================
매수 = False

# 갭등락율 계산 (분봉시가 기준)
갭등락율계산 = ((분봉시가 - 시가) / 시가) * 100 if 시가 != 0 else 0

# 0. 거래 가능 시간대 (09:30:00 ~ 10:00:00)
if not (시분초 >= 93000 and 시분초 <= 100000):
    매수 = False

# 1. 시가 갭-업 필터 (+5 % 이상)
elif not (갭등락율계산 >= 5):
    매수 = False

# 2. 장초 거래량 폭발
elif not (분당거래대금 >= 분당거래대금평균(20) * 2):
    매수 = False
elif not (전일동시간비 >= 200):      # 전일 동시간 대비 2배 이상
    매수 = False

# 3. 체결강도·수급 확인
elif not (체결강도 >= 130 and 체결강도 >= 체결강도N(1)):
    매수 = False
elif not (분당매수수량 > 분당매도수량):
    매수 = False

# 4. 가격 모멘텀 – 5 분봉 고가 돌파
elif not (현재가 >= 최고분봉고가(5, 1) * 1.005):
    매수 = False

# 5. 라운드피겨 리스크 회피
elif 라운드피겨위5호가이내:
    매수 = False

# 6. 최종 진입 (매수 = True로 설정)
else:
    매수 = True
```


### 설명

1. **갭·볼륨 콤보**로 시초 강세를 정량화.
2. 거래량은 **절대치**(분당거래대금)와 **상대치**(RelativeVol) 이중 필터.
3. **5 분 전 고가**를 0.5% 이상 돌파할 때만 추격 진입해 “숨 고르기” 돌파를 회피.
4. **라운드 피겨** 구간(10 원 단위 위 5호가)에서 점프 실패 확률을 배제.

## 4. 매도 조건식 `C_MIN_GAPUP_2025_S`

```python
# =============================================================================
# 시초 급등주 분봉 매도 조건식 (Gap-Up Momentum Sell)
# =============================================================================
매도 = False

# A. 기본 강제 청산
if 시분초 >= 100000:                                  # 10시 이후 보유 금지
    매도 = True
    매도사유 = "시간청산"

# B. 목표 수익·손실
elif 수익률 >= 5.0:                                # +5% 이익 실현
    매도 = True
    매도사유 = "목표수익"
elif 수익률 <= -3.0:                               # -3% 손절
    매도 = True
    매도사유 = "손절"

# C. 체결강도 약화 & 거래량 급감
elif 체결강도 <= 90 and 체결강도N(1) > 120:
    매도 = True
    매도사유 = "체결강도약화"
elif 분당거래대금 < 분당거래대금평균(10) * 0.5:
    매도 = True
    매도사유 = "거래량감소"

# D. 가격 반전 신호
elif 현재가 < 이동평균(5) and 이동평균(5) < 이동평균(5, 1):
    매도 = True
    매도사유 = "단기이평하향"
elif 현재가 < 분봉시가:                             # 시가 이탈
    매도 = True
    매도사유 = "시가이탈"

# 최종 매도 실행 (매도 = True로 설정)
if 매도:
    매도 = True
```


### 설명

- **시간 기반 청산**을 우선 적용해 장중 변동성 확산 전에 위험 차단.
- **분당거래대금 급감**·**체결강도 역전**을 빠르게 감지해 이익 보호.
- **단기 5 분 이동평균** 하향 + 시가 붕괴는 가격-구조 경고로 간주.


## 5. 최적화 변수 범위

| 변수 | 범위 | 기본값 | 비고 |
| :-- | :-- | :-- | :-- |
| `갭등락율_하한` | 4 – 8% (1%) | 5% | 갭 폭 |
| `전일동시간비_하한` | 150 – 300 (25) | 200 | 거래량 상대배수 |
| `체결강도_하한` | 110 – 150 (5) | 130 | 수급 세기 |
| `목표수익률` | 3 – 8% (1%) | 5% | 익절 기준 |
| `손절률` | –5% – –2% (0.5%) | –3% | 손실 제한 |
| `시간청산` | 09:50 – 10:30 | 10:00 | 포지션 유지 한계 |

## 6. 적용 팁 \& 주의사항

1. **초단타 환경**
    - 장 초반 고빈도 체결로 인해 **슬리피지 발생** 가능. 호가 폭이 2 틱 이상 벌어질 경우 진입 취소.
2. **VI(변동성완화장치)**
    - 갭-업 폭이 10% 이상일 때 VI 발동 가능성을 확인, `VI가격`·`VI해제시간` 변수 활용.
3. **데이터 정확도**
    - `전일동시간비` 사용 시 **전일·전전일 거래중단** 종목은 평균값 왜곡 → 리스트에서 제외.
4. **시장 상황 연동**
    - 전체 지수 급락(코스닥 –1%↓) 시 전략 비활성화:

```python
if 코스닥등락율 <= -1.0: 매매허용 = False
```


### 참고 / 근거 자료

시초 갭-업 전략 및 거래량 기반 필터의 실효성은 Gap-and-Go 기법 및 Opening Range Breakout 연구에서 통계적으로 검증됨 [^1][^4][^3]. 거래량 급감이 추세 종료를 선행한다는 사실은 장중 상대 거래량 분석 결과와 일치 [^2].

**작성일 : 2025-07-13**
**버전 : 1.0**

<div style="text-align: center">⁂</div>

[^1]: https://www.warriortrading.com/gap-go/

[^2]: https://zerodha.com/varsity/chapter/volumes/

[^3]: https://www.tradingsim.com/blog/early-morning-range-breakout

[^4]: https://fxopen.com/blog/en/opening-range-breakout-strategy/

[^5]: Back_Testing_Guideline_Min.md

[^6]: Condition_Advanced_Algorithm.md

[^7]: Condition_Comprehensive_Strategy_20250101.md

[^8]: https://www.etoday.co.kr/news/view/168940

[^9]: https://stock79.tistory.com/entry/장초반-갭하락-작은-것이-좋은가-큰-것이-좋은가-81

[^10]: https://hyochullab.tistory.com/29

[^11]: https://200won-highwind.com/Diary/?bmode=view\&idx=14204003

[^12]: https://contents.premium.naver.com/stockforce/stforce/contents/241223195153763fx

[^13]: https://wikidocs.net/213431

[^14]: https://www.youtube.com/watch?v=1N-dLzvnCn4

[^15]: https://www.youtube.com/watch?v=lwAheYJnwII

[^16]: https://ldhggg.tistory.com/26

[^17]: https://brunch.co.kr/@@4gFr/908

[^18]: https://notorius.tistory.com/72

[^19]: https://dglim0710.tistory.com/790

[^20]: https://cafe.daum.net/stockpapa/1wTi/2467

[^21]: https://www.youtube.com/watch?v=iqw7bfiAU5I

[^22]: https://contents.premium.naver.com/chess1004/chessschool/contents/250204110413531ep

[^23]: https://www.youtube.com/watch?v=6JSPB9-lYUc

[^24]: https://zezemini.tistory.com/entry/급등주-놓치지-않는-방법-대장주-상따-매매-패턴과-타이밍

[^25]: https://lilys.ai/notes/815314

[^26]: https://200won-highwind.com/Diary/?bmode=view\&idx=14395979

[^27]: https://www.youtube.com/watch?v=DNtjVuQlgLE

[^28]: https://www.youtube.com/watch?v=qkChxbuUqvU

[^29]: https://www.latimes.com/la-volumesurge-story.html

[^30]: https://www.tradersdna.com/trading-tips-the-breakaway-gap/

[^31]: https://www.topstep.com/blog/gartleys-opening-gap-trading-strategy-explained/

[^32]: https://seekingalpha.com/article/4055176-trading-volume-speaks-volumes

[^33]: https://traders.mba/support/gap-trading-breakout-strategy/

[^34]: https://appreciatewealth.com/blog/gap-up-gap-down

[^35]: https://www.youtube.com/watch?v=PKJ-wIfjKkc

[^36]: https://blog.market-pulse.in/scanning-breakout-strategies-3-gap-opening-range-breakout/

[^37]: https://www.investopedia.com/articles/trading/05/playinggaps.asp

[^38]: https://www.youtube.com/watch?v=0VwT3MwlBSI

[^39]: https://www.investing.com/analysis/3-proper-buy-entry-points-to-score-big-gains-from-breakaway-gaps-200607604

[^40]: https://www.stockopedia.com/ratios/recent-volume-surge-5009/

[^41]: https://marketsecrets.in/blog/algo-trading-using-gap-breakout-strategy/

[^42]: https://wire.insiderfinance.io/this-one-strategy-will-boost-your-profits-d3fa74fa21d2?gi=f116f61c8e25

[^43]: https://www.investopedia.com/articles/active-trading/052015/simple-way-read-intraday-volume.asp

[^44]: https://pocketoption.com/blog/en/interesting/trading-strategies/gap-trading-strategies/

[^45]: https://www.marketscreener.com/top-records/price-change/unusual-volumes/

[^46]: https://www.reddit.com/r/FuturesTrading/comments/1js3b4x/morning_strike_strategy_a_simple_and_effective/

[^47]: https://www.youtube.com/watch?v=uAuisQGLRVA

[^48]: https://dotnettutorials.net/lesson/opening-range-breakout/

[^49]: https://trade-ideas.com/help/filter/RV/

[^50]: https://www.myespresso.com/bootcamp/module/technical-analysis-indicators-patterns/gap-up-and-gap-down-in-price-charts

[^51]: https://kr.tradingview.com/script/zbLlB1Qe-Opening-Range-Breakout/

[^52]: https://www.trade-ideas.com/help/filter/PV/

[^53]: https://kr.tradingview.com/scripts/volumespike/

[^54]: https://in.tradingview.com/scripts/gaptrading/

[^55]: https://www.quantconnect.com/research/18444/opening-range-breakout-for-stocks-in-play/

[^56]: https://www.reddit.com/r/Daytrading/comments/12uy0jp/gap_strategy/

[^57]: https://papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID3101695_code2872537.pdf?abstractid=3101695\&mirid=1

[^58]: https://www.tradingsim.com/blog/volume-analysis-technical-indicator

[^59]: https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/gap-trading-strategies

[^60]: https://chartswatcher.com/pages/blog/a-trader-s-guide-to-open-range-breakout-strategy

[^61]: https://www.tastylive.com/concepts-strategies/gap-trading

[^62]: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3101695

