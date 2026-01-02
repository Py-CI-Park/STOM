# -*- coding: utf-8 -*-
from traceback import print_exc

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib import gridspec

from backtester.output_paths import ensure_backtesting_output_dir, build_backtesting_output_path
from utility.mpl_setup import ensure_mpl_font
from .metrics_enhanced import DetectTimeframe
from backtester.analysis.memo_utils import build_strategy_memo_text, add_memo_box
from .utils import (
    ComputeStrategyKey,
    _extract_strategy_block_lines,
)

def CreateSynergyHeatmapData(filter_combinations, top_n=10):
    """
    필터 조합 분석 결과를 히트맵용 데이터로 변환합니다.

    Args:
        filter_combinations: 필터 조합 분석 결과 리스트
        top_n: 표시할 필터 수

    Returns:
        tuple: (filter_names, heatmap_matrix, annotations)
    """
    if not filter_combinations or len(filter_combinations) == 0:
        return None, None, None

    # 2개 조합만 추출
    two_combos = [c for c in filter_combinations if c['조합유형'] == '2개 조합']

    if len(two_combos) == 0:
        return None, None, None

    # 사용된 필터 목록 추출
    filter_set = set()
    for combo in two_combos[:30]:
        filter_set.add(combo['필터1'])
        filter_set.add(combo['필터2'])

    filter_names = sorted(list(filter_set))[:top_n]
    n = len(filter_names)

    if n < 2:
        return None, None, None

    # 히트맵 매트릭스 초기화
    heatmap_matrix = np.zeros((n, n))
    annotations = [['' for _ in range(n)] for _ in range(n)]

    # 조합 정보 채우기
    for combo in two_combos:
        f1, f2 = combo['필터1'], combo['필터2']
        if f1 in filter_names and f2 in filter_names:
            i, j = filter_names.index(f1), filter_names.index(f2)
            synergy = combo['시너지비율']
            heatmap_matrix[i, j] = synergy
            heatmap_matrix[j, i] = synergy  # 대칭

            # 주석 (시너지 효과 금액)
            synergy_effect = combo['시너지효과']
            if synergy_effect >= 0:
                annotations[i][j] = f'+{synergy_effect/1000000:.1f}M'
            else:
                annotations[i][j] = f'{synergy_effect/1000000:.1f}M'
            annotations[j][i] = annotations[i][j]

    # 필터명 축약
    short_names = [name[:15] for name in filter_names]

    return short_names, heatmap_matrix, annotations

def PrepareThresholdCurveData(optimal_thresholds, top_n=5):
    """
    최적 임계값 탐색 결과에서 효율성 곡선용 데이터를 준비합니다.

    Args:
        optimal_thresholds: 최적 임계값 분석 결과 리스트
        top_n: 표시할 컬럼 수

    Returns:
        list: 각 컬럼별 곡선 데이터 리스트
    """
    if not optimal_thresholds or len(optimal_thresholds) == 0:
        return []

    curve_data = []

    for i, opt in enumerate(optimal_thresholds[:top_n]):
        try:
            column = opt['column']
            direction = opt['direction']
            all_thresholds = opt.get('all_thresholds', [])

            if not all_thresholds or not isinstance(all_thresholds, list):
                continue

            # 데이터 추출
            thresholds = [t['threshold'] for t in all_thresholds]
            improvements = [t['improvement'] for t in all_thresholds]
            efficiencies = [t['efficiency'] for t in all_thresholds]
            excluded_ratios = [t['excluded_ratio'] for t in all_thresholds]

            curve_data.append({
                'column': column,
                'direction': direction,
                'thresholds': thresholds,
                'improvements': improvements,
                'efficiencies': efficiencies,
                'excluded_ratios': excluded_ratios,
                'optimal_threshold': opt['optimal_threshold'],
                'optimal_improvement': opt['improvement'],
                'filter_name': opt.get('필터명', f'{column} 필터')
            })
        except:
            continue

    return curve_data

def _FindNearestIndex(values, target):
    try:
        arr = np.asarray(values, dtype=float)
        tgt = float(target)
        return int(np.nanargmin(np.abs(arr - tgt)))
    except Exception:
        return 0

def PltEnhancedAnalysisCharts(df_tsg, save_file_name, teleQ,
                              filter_results=None, filter_results_lookahead=None,
                              feature_importance=None,
                              optimal_thresholds=None, filter_combinations=None,
                              filter_stability=None, generated_code=None,
                              buystg: str = None, sellstg: str = None,
                              buystg_name: str = None, sellstg_name: str = None,
                              startday=None, endday=None, starttime=None, endtime=None):
    """
    강화된 분석 차트를 생성합니다.

    신규 차트:
    - 필터 효과 통계 요약 테이블
    - 특성 중요도 막대 차트
    - 최적 임계값 탐색 결과 (NEW)
    - 필터 조합 시너지 히트맵 (NEW)
    - 최적 임계값 효율성 곡선 (NEW)
    - (진단용) 룩어헤드 포함 필터 효과 Top (NEW)
    """
    if len(df_tsg) < 5:
        return

    try:
        # 차트용 복사본 (원본 df_tsg에 구간 컬럼 등이 추가되는 부작용 방지)
        df_tsg = df_tsg.copy()

        # 한글 폰트 설정
        # - 요약 텍스트 등에서 기본 monospace(DejaVu Sans Mono)로 fallback 되면 한글이 깨질 수 있어,
        #   family/monospace 모두에 한글 폰트를 우선 지정합니다.
        ensure_mpl_font(set_monospace=True)

        # 타임프레임 감지
        tf_info = DetectTimeframe(df_tsg, save_file_name)

        memo_text = build_strategy_memo_text(
            buystg_name,
            sellstg_name,
            save_file_name,
            startday=startday,
            endday=endday,
            starttime=starttime,
            endtime=endtime,
        )

        fig = plt.figure(figsize=(20, 38))
        fig.suptitle(f'백테스팅 필터 분석 차트 - {save_file_name} ({tf_info["label"]})',
                     fontsize=16, fontweight='bold')

        gs = gridspec.GridSpec(8, 3, figure=fig, hspace=0.45, wspace=0.3)

        color_profit = '#2ECC71'
        color_loss = '#E74C3C'
        color_neutral = '#3498DB'

        # ============ Chart 1: 필터 효과 순위 ============
        ax1 = fig.add_subplot(gs[0, :2])
        if filter_results and len(filter_results) > 0:
            top_10 = [f for f in filter_results if f['수익개선금액'] > 0][:10]
            if top_10:
                names = [f['필터명'][:20] for f in top_10]
                improvements = [f['수익개선금액'] for f in top_10]
                colors = [color_profit for _ in improvements]

                y_pos = range(len(names))
                ax1.barh(y_pos, improvements, color=colors, edgecolor='black', linewidth=0.5)
                ax1.set_yticks(y_pos)
                ax1.set_yticklabels(names, fontsize=9)
                ax1.set_xlabel('수익 개선 금액')
                ax1.set_title('Top 10 필터 효과 (수익개선 기준)')

                # 값 표시
                for i, v in enumerate(improvements):
                    ax1.text(v + max(improvements) * 0.01, i, f'{v:,}원', va='center', fontsize=8)

                ax1.invert_yaxis()

        # ============ Chart 2: 통계적 유의성 요약 ============
        ax2 = fig.add_subplot(gs[0, 2])
        if filter_results and len(filter_results) > 0:
            significant_count = sum(1 for f in filter_results if f.get('유의함') == '예')
            total_count = len(filter_results)

            sizes = [significant_count, total_count - significant_count]
            labels = [f'유의함\n({significant_count})', f'비유의\n({total_count - significant_count})']
            colors = [color_profit, '#CCCCCC']

            ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax2.set_title('필터 통계적 유의성 분포')

        # ============ Chart 3: 특성 중요도 ============
        ax3 = fig.add_subplot(gs[1, 0])
        if feature_importance and 'feature_importance' in feature_importance:
            fi = feature_importance['feature_importance'][:8]
            names = [x[0] for x in fi]
            values = [x[1] for x in fi]

            y_pos = range(len(names))
            ax3.barh(y_pos, values, color=color_neutral, edgecolor='black', linewidth=0.5)
            ax3.set_yticks(y_pos)
            ax3.set_yticklabels(names, fontsize=9)
            ax3.set_xlabel('중요도')
            test_acc = feature_importance.get("model_accuracy", 0)
            base_acc = feature_importance.get("baseline_accuracy", 0)
            ax3.set_title(f"ML 특성 중요도 (정확도 test: {test_acc}%, 기준선: {base_acc}%)")
            ax3.invert_yaxis()

        # ============ Chart 4: 효과 크기 분포 ============
        ax4 = fig.add_subplot(gs[1, 1])
        if filter_results and len(filter_results) > 0:
            effect_sizes = [f['효과크기'] for f in filter_results if '효과크기' in f]
            if effect_sizes:
                ax4.hist(effect_sizes, bins=20, color=color_neutral, edgecolor='black', alpha=0.7)
                ax4.axvline(x=0.2, color='orange', linestyle='--', label='작은 효과')
                ax4.axvline(x=0.5, color='red', linestyle='--', label='중간 효과')
                ax4.axvline(x=0.8, color='purple', linestyle='--', label='큰 효과')
                ax4.set_xlabel('Cohen\'s d 효과 크기')
                ax4.set_ylabel('필터 수')
                ax4.set_title('필터 효과 크기 분포')
                ax4.legend(fontsize=8)

        # ============ Chart 5: 필터 적용 시 예상 수익 개선 효과 (Top 15) ============
        ax5 = fig.add_subplot(gs[1, 2])
        if filter_results and len(filter_results) > 0:
            df_filter = pd.DataFrame(filter_results)
            if '수익개선금액' in df_filter.columns and '필터명' in df_filter.columns:
                df_filter = df_filter[df_filter['수익개선금액'] > 0].sort_values('수익개선금액', ascending=False).head(15)

                if len(df_filter) > 0:
                    x_pos = range(len(df_filter))
                    ax5.bar(x_pos, df_filter['수익개선금액'], color=color_profit, edgecolor='black', linewidth=0.5)
                    ax5.set_xticks(list(x_pos))
                    ax5.set_xticklabels([str(x)[:18] for x in df_filter['필터명']],
                                        rotation=45, ha='right', fontsize=7)
                    ax5.set_ylabel('수익 개선 금액')
                    ax5.set_title('필터 적용 시 예상 수익 개선 효과 (Top 15)\n(막대=개별개선, 빨간선=누적(동시적용/중복반영))')
                    ax5.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)

                    try:
                        if '조건식' in df_filter.columns and '수익금' in df_tsg.columns:
                            safe_globals = {"__builtins__": {}}
                            safe_locals = {"df_tsg": df_tsg, "np": np, "pd": pd}
                            profit_arr_local = df_tsg['수익금'].to_numpy(dtype=np.float64)
                            excluded_mask = np.zeros(len(df_tsg), dtype=bool)
                            cum_values = []
                            cum = 0.0
                            for expr in df_filter['조건식'].tolist():
                                cond = eval(expr, safe_globals, safe_locals)
                                cond_arr = cond.to_numpy(dtype=bool) if hasattr(cond, 'to_numpy') else np.asarray(cond, dtype=bool)
                                add_mask = cond_arr & (~excluded_mask)
                                cum += -float(np.sum(profit_arr_local[add_mask]))
                                excluded_mask |= cond_arr
                                cum_values.append(cum)

                            denom = float(cum_values[-1]) if cum_values else 0.0
                            if denom <= 0:
                                # 누적 개선이 0 이하로 끝나는 케이스는 비율 표시가 왜곡될 수 있어
                                # 기존(단순 합산) 누적비율로 폴백합니다.
                                cumsum = df_filter['수익개선금액'].cumsum()
                                denom = float(cumsum.iloc[-1]) if len(cumsum) > 0 else 0.0
                                cumsum_pct = (cumsum / denom * 100) if denom else [0 for _ in cumsum]
                            else:
                                cumsum_pct = [(v / denom * 100) for v in cum_values]
                        else:
                            cumsum = df_filter['수익개선금액'].cumsum()
                            denom = float(cumsum.iloc[-1]) if len(cumsum) > 0 else 0.0
                            cumsum_pct = (cumsum / denom * 100) if denom else [0 for _ in cumsum]

                        ax5_twin = ax5.twinx()
                        ax5_twin.plot(list(x_pos), cumsum_pct, 'ro-', markersize=3, linewidth=1.2)
                        ax5_twin.set_ylabel('누적 비율 (%)', color='red')
                        ax5_twin.tick_params(axis='y', labelcolor='red')
                        ax5_twin.set_ylim(0, 110)
                    except:
                        pass
                else:
                    ax5.text(0.5, 0.5, '개선 효과(+) 필터 없음', ha='center', va='center',
                             fontsize=12, transform=ax5.transAxes)
                    ax5.axis('off')
            else:
                ax5.text(0.5, 0.5, '필터 결과 컬럼 누락', ha='center', va='center',
                         fontsize=12, transform=ax5.transAxes)
                ax5.axis('off')
        else:
            ax5.text(0.5, 0.5, '필터 분석 데이터 없음', ha='center', va='center',
                     fontsize=12, transform=ax5.transAxes)
            ax5.axis('off')

        # ============ Chart 6-8: 필터 개선 핵심 보조 지표 ============
        # Chart 6: 기간별 안정성(일관성) Top
        ax6 = fig.add_subplot(gs[2, 0])
        if filter_stability and len(filter_stability) > 0:
            top_stable = sorted(filter_stability, key=lambda x: x.get('일관성점수', 0), reverse=True)[:10]
            names = [str(x.get('필터명', ''))[:18] for x in top_stable]
            scores = [x.get('일관성점수', 0) for x in top_stable]
            colors = []
            for x in top_stable:
                grade = x.get('안정성등급', '')
                if grade == '안정':
                    colors.append(color_profit)
                elif grade == '보통':
                    colors.append('#F1C40F')
                else:
                    colors.append(color_loss)

            y_pos = range(len(names))
            ax6.barh(y_pos, scores, color=colors, edgecolor='black', linewidth=0.5)
            ax6.set_yticks(y_pos)
            ax6.set_yticklabels(names, fontsize=8)
            ax6.set_xlabel('일관성점수(0-100)')
            ax6.set_title('필터 안정성 Top 10')
            ax6.invert_yaxis()
            for i, item in enumerate(top_stable):
                avg_imp = item.get('평균개선', 0)
                ax6.text(scores[i] + 1, i, f"+{avg_imp/10000:.0f}만", va='center', fontsize=7)
        else:
            ax6.text(0.5, 0.5, '안정성 분석 데이터 없음', ha='center', va='center',
                     fontsize=12, transform=ax6.transAxes)
            ax6.axis('off')

        # Chart 7: 최적 임계값 요약 (Top)
        ax7 = fig.add_subplot(gs[2, 1])
        ax7.axis('off')
        if optimal_thresholds and len(optimal_thresholds) > 0:
            top_thr = optimal_thresholds[:8]
            table_data = []
            for t in top_thr:
                name = t.get('필터명') or str(t.get('column', ''))[:22]
                improvement = t.get('improvement', 0)
                excluded_ratio = t.get('excluded_ratio', 0)
                efficiency = t.get('efficiency', '')
                table_data.append([str(name)[:22], f"{int(improvement):,}", f"{excluded_ratio}", f"{efficiency}"])

            tbl = ax7.table(
                cellText=table_data,
                colLabels=['필터명', '개선(원)', '제외(%)', '효율'],
                loc='center'
            )
            tbl.auto_set_font_size(False)
            tbl.set_fontsize(7)
            tbl.scale(1, 1.4)
            ax7.set_title('최적 임계값 요약 (Top)', fontsize=10)
        else:
            ax7.text(0.5, 0.5, '임계값 분석 데이터 없음', ha='center', va='center',
                     fontsize=12, transform=ax7.transAxes)

        # Chart 8: 필터 조합 시너지 상위
        ax8 = fig.add_subplot(gs[2, 2])
        ax8.axis('off')
        if filter_combinations and len(filter_combinations) > 0:
            top_combo = sorted(filter_combinations, key=lambda x: x.get('시너지효과', 0), reverse=True)[:8]
            lines = []
            for c in top_combo:
                combo_type = c.get('조합유형', '')
                f1 = str(c.get('필터1', ''))[:14]
                f2 = str(c.get('필터2', ''))[:14]
                f3 = str(c.get('필터3', ''))[:14]
                if combo_type == '3개 조합' and f3:
                    name = f"{f1}+{f2}+{f3}"
                else:
                    name = f"{f1}+{f2}"
                lines.append(
                    f"- {name}: 시너지 {int(c.get('시너지효과', 0)):,}원 ({c.get('시너지비율', 0)}%)"
                )
            text = "\n".join(lines) if lines else '조합 분석 데이터 없음'
            ax8.text(0.02, 0.98, text, transform=ax8.transAxes, va='top', fontsize=8,
                     bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
            ax8.set_title('필터 조합 시너지 Top', fontsize=10)
        else:
            ax8.text(0.5, 0.5, '조합 분석 데이터 없음', ha='center', va='center',
                     fontsize=12, transform=ax8.transAxes)

        # ============ Chart 9: 거래품질점수별 수익금 ============
        ax9 = fig.add_subplot(gs[3, 0])
        if '거래품질점수' in df_tsg.columns:
            bins = [0, 30, 40, 50, 60, 70, 100]
            labels = ['~30', '30-40', '40-50', '50-60', '60-70', '70+']
            df_tsg['품질구간'] = pd.cut(df_tsg['거래품질점수'], bins=bins, labels=labels, right=False)
            df_qual = df_tsg.groupby('품질구간', observed=True).agg({'수익금': 'sum', '종목명': 'count'}).reset_index()
            df_qual.columns = ['품질구간', '수익금', '거래수']
            colors = [color_profit if x >= 0 else color_loss for x in df_qual['수익금']]
            bars = ax9.bar(range(len(df_qual)), df_qual['수익금'], color=colors, edgecolor='black', linewidth=0.5)
            ax9.set_xticks(range(len(df_qual)))
            ax9.set_xticklabels(df_qual['품질구간'], rotation=45)
            ax9.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
            ax9.set_xlabel('거래품질 점수')
            ax9.set_ylabel('총 수익금')
            ax9.set_title('거래품질 점수별 수익금 (NEW)')

            # 거래수 표시
            for i, (bar, cnt) in enumerate(zip(bars, df_qual['거래수'])):
                ax9.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                        f'n={cnt}', ha='center', va='bottom' if bar.get_height() >= 0 else 'top', fontsize=8)

        # ============ Chart 10: 매수 위험도점수별 수익금 ============
        ax10 = fig.add_subplot(gs[3, 1])
        if '위험도점수' in df_tsg.columns:
            # 동적 bins 생성: 데이터 분포에 기반
            risk_min = df_tsg['위험도점수'].min()
            risk_max = df_tsg['위험도점수'].max()
            if risk_max - risk_min > 50:
                bins = [0, 20, 40, 60, 80, 100]
            else:
                # 데이터 범위가 좁으면 더 세분화
                bins = list(range(int(risk_min), int(risk_max) + 20, 10))
                if bins[-1] < 100:
                    bins.append(100)
            labels = [f'{bins[i]}-{bins[i+1]}' for i in range(len(bins)-1)]
            df_tsg['위험도구간'] = pd.cut(df_tsg['위험도점수'], bins=bins, labels=labels, right=False)
            df_risk = df_tsg.groupby('위험도구간', observed=True).agg({'수익금': 'sum', '종목명': 'count'}).reset_index()
            df_risk.columns = ['위험도구간', '수익금', '거래수']
            colors = [color_profit if x >= 0 else color_loss for x in df_risk['수익금']]
            bars = ax10.bar(range(len(df_risk)), df_risk['수익금'], color=colors, edgecolor='black', linewidth=0.5)
            ax10.set_xticks(range(len(df_risk)))
            ax10.set_xticklabels(df_risk['위험도구간'], rotation=45)
            ax10.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
            ax10.set_xlabel('매수 위험도 점수')
            ax10.set_ylabel('총 수익금')
            
            # 위험도 공식 표시 (매수 시점 기반 / 룩어헤드 제거)
            risk_formula = (
                "위험도(매수 시점) 공식:\n"
                "- 매수등락율>=20:+20, >=25:+10, >=30:+10\n"
                "- 매수체결강도<80:+15, <60:+10 | 과열>=150:+10, >=200:+10, >=250:+10\n"
                "- 거래대금(억=매수당일거래대금/100)<50:+15, <100:+10\n"
                "- 시총(억)<1000:+15, <5000:+10 | 호가잔량비<90:+10, <70:+15\n"
                "- 스프레드>=0.5:+10, >=1.0:+10 | 회전율<10:+5, <5:+10\n"
                "- 변동폭비율>=7.5:+10, >=10:+10, >=15:+10"
            )
            ax10.set_title(f'매수 위험도 점수별 수익금 (룩어헤드 없음)\n{risk_formula}', fontsize=8, loc='left')

        # ============ Chart 11: 리스크조정수익률 분포 ============
        ax11 = fig.add_subplot(gs[3, 2])
        if '리스크조정수익률' in df_tsg.columns:
            profit_trades = df_tsg[df_tsg['수익금'] > 0]['리스크조정수익률']
            loss_trades = df_tsg[df_tsg['수익금'] <= 0]['리스크조정수익률']

            ax11.hist(profit_trades, bins=30, alpha=0.6, color=color_profit, label='이익 거래', edgecolor='black')
            ax11.hist(loss_trades, bins=30, alpha=0.6, color=color_loss, label='손실 거래', edgecolor='black')
            ax11.axvline(x=0, color='gray', linestyle='--', linewidth=0.8)
            ax11.set_xlabel('리스크 조정 수익률')
            ax11.set_ylabel('거래 수')
            ax11.set_title('리스크 조정 수익률 분포 (NEW)')
            ax11.legend(fontsize=9)

        # ============ Chart 12: 필터 결과 요약 테이블 ============
        ax12 = fig.add_subplot(gs[4, :2])
        ax12.axis('off')
        if filter_results and len(filter_results) > 0:
            top_filters = [f for f in filter_results if f.get('수익개선금액', 0) > 0][:12]
            if not top_filters:
                top_filters = filter_results[:12]

            table_data = []
            for f in top_filters:
                name = str(f.get('필터명', ''))[:26]
                improvement = int(f.get('수익개선금액', 0) or 0)
                excluded = f.get('제외비율', '')
                p_value = f.get('p값', '')
                significant = f.get('유의함', '')
                effect_size = f.get('효과크기', '')
                recommend = str(f.get('적용권장', ''))
                table_data.append([
                    name,
                    f"{improvement:,}",
                    f"{excluded}",
                    f"{p_value}",
                    f"{significant}",
                    f"{effect_size}",
                    recommend
                ])

            tbl = ax12.table(
                cellText=table_data,
                colLabels=['필터명', '개선(원)', '제외(%)', 'p값', '유의', '효과(d)', '권장'],
                loc='center'
            )
            tbl.auto_set_font_size(False)
            tbl.set_fontsize(7)
            tbl.scale(1, 1.55)
            ax12.set_title('필터 결과 요약 (Top)', fontsize=11)

            try:
                for row_idx, f in enumerate(top_filters, start=1):
                    stars = str(f.get('적용권장', ''))
                    is_sig = str(f.get('유의함', '')) == '예'
                    if stars.count('★') >= 3:
                        row_color = '#E8F8F5'
                    elif is_sig:
                        row_color = '#FEF9E7'
                    else:
                        row_color = 'white'
                    for col_idx in range(7):
                        tbl[(row_idx, col_idx)].set_facecolor(row_color)
            except:
                pass
        else:
            ax12.text(0.5, 0.5, '필터 분석 결과 없음', ha='center', va='center',
                      fontsize=12, transform=ax12.transAxes)

        # ============ Chart 13: 자동 생성 조건식 요약 ============
        ax13 = fig.add_subplot(gs[4, 2])
        ax13.axis('off')
        if generated_code and generated_code.get('code_text'):
            summary = generated_code.get('summary', {}) or {}
            code_text = str(generated_code.get('code_text', '') or '')
            code_lines = [ln.rstrip() for ln in code_text.splitlines() if ln is not None]
            snippet = "\n".join(code_lines[:18])
            if len(code_lines) > 18:
                snippet += "\n..."

            header_lines = [
                "=== 자동 생성 코드 요약 ===",
                f"- 필터 수: {int(summary.get('total_filters', 0) or 0):,}",
                f"- 예상 총 개선(동시적용): {int(summary.get('total_improvement_combined', summary.get('total_improvement_naive', 0)) or 0):,}원",
                f"- 개별개선합/중복: {int(summary.get('total_improvement_naive', 0) or 0):,}원 / {int(summary.get('overlap_loss', 0) or 0):+,}원",
            ]
            categories = summary.get('categories') or []
            if categories:
                shown = ", ".join([str(x) for x in categories[:6]])
                header_lines.append(f"- 카테고리: {shown}" + (" ..." if len(categories) > 6 else ""))

            ax13.text(
                0.02, 0.98,
                "\n".join(header_lines) + "\n\n" + snippet,
                transform=ax13.transAxes,
                va='top',
                fontsize=8,
                family='monospace',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
            )
            ax13.set_title('조건식 코드 생성', fontsize=10)
        else:
            ax13.text(0.5, 0.5, '코드 생성 결과 없음', ha='center', va='center',
                      fontsize=12, transform=ax13.transAxes)

        # ============ Chart 14: 필터 조합 시너지 히트맵 (NEW) ============
        ax14 = fig.add_subplot(gs[5, 0])
        if filter_combinations and len(filter_combinations) > 0:
            filter_names, heatmap_matrix, annotations = CreateSynergyHeatmapData(
                filter_combinations, top_n=8
            )

            if filter_names is not None and heatmap_matrix is not None:
                vmin = float(np.nanmin(heatmap_matrix)) if np.isfinite(heatmap_matrix).any() else -100.0
                vmax = float(np.nanmax(heatmap_matrix)) if np.isfinite(heatmap_matrix).any() else 100.0
                vmin = min(vmin, -100.0)
                vmax = max(vmax, 100.0)
                im = ax14.imshow(heatmap_matrix, cmap='RdYlGn', aspect='auto',
                                vmin=vmin, vmax=vmax)
                ax14.set_xticks(range(len(filter_names)))
                ax14.set_yticks(range(len(filter_names)))
                ax14.set_xticklabels(filter_names, rotation=45, ha='right', fontsize=7)
                ax14.set_yticklabels(filter_names, fontsize=7)
                ax14.set_title('필터 조합 시너지 히트맵 (NEW)\n(음수=시너지↓, 양수=시너지↑)',
                              fontsize=9)

                # 값 표시
                for i in range(len(filter_names)):
                    for j in range(len(filter_names)):
                        if annotations[i][j]:
                            ax14.text(j, i, annotations[i][j], ha='center', va='center',
                                     fontsize=6,
                                     color='white' if abs(heatmap_matrix[i, j]) > 50 else 'black')

                plt.colorbar(im, ax=ax14, shrink=0.8, label='시너지비율(%)')
            else:
                ax14.text(0.5, 0.5, '조합 분석 데이터 없음', ha='center', va='center',
                         fontsize=12, transform=ax14.transAxes)
                ax14.axis('off')
        else:
            ax14.text(0.5, 0.5, '조합 분석 데이터 없음', ha='center', va='center',
                     fontsize=12, transform=ax14.transAxes)
            ax14.axis('off')

        # ============ Chart 15: 최적 임계값 효율성 곡선 (NEW) ============
        ax15 = fig.add_subplot(gs[5, 1])
        if optimal_thresholds and len(optimal_thresholds) > 0:
            curve_data = PrepareThresholdCurveData(optimal_thresholds, top_n=3)

            if curve_data:
                colors = ['#E74C3C', '#3498DB', '#2ECC71']
                for i, data in enumerate(curve_data):
                    color = colors[i % len(colors)]
                    # 제외비율 대비 효율성 곡선
                    ax15.plot(data['excluded_ratios'],
                             [e/1000000 for e in data['efficiencies']],
                             marker='o', markersize=3, label=data['column'][:12],
                             color=color, linewidth=1.5)
                    # 최적점 표시
                    opt_idx = _FindNearestIndex(data.get('thresholds', []), data.get('optimal_threshold'))
                    ax15.scatter(data['excluded_ratios'][opt_idx],
                                data['efficiencies'][opt_idx]/1000000,
                                s=100, marker='*', color=color, edgecolors='black',
                                zorder=5)

                ax15.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
                ax15.set_xlabel('제외 비율 (%)')
                ax15.set_ylabel('효율성 (백만원)')
                ax15.set_title('최적 임계값 효율성 곡선 (NEW)\n(★=최적점)', fontsize=9)
                ax15.legend(fontsize=7, loc='best')
                ax15.grid(True, alpha=0.3)
            else:
                ax15.text(0.5, 0.5, '임계값 분석 데이터 없음', ha='center', va='center',
                         fontsize=12, transform=ax15.transAxes)
                ax15.axis('off')
        else:
            ax15.text(0.5, 0.5, '임계값 분석 데이터 없음', ha='center', va='center',
                     fontsize=12, transform=ax15.transAxes)
            ax15.axis('off')

        # ============ Chart 16: 요약 통계 텍스트 ============
        ax16 = fig.add_subplot(gs[5, 2])
        ax16.axis('off')

        total_trades = len(df_tsg)
        total_profit = df_tsg['수익금'].sum()
        win_rate = (df_tsg['수익금'] > 0).mean() * 100
        avg_profit = df_tsg['수익률'].mean()

        summary_text = f"""
        === 분석 요약 ({tf_info['label']}) ===

        총 거래 수: {total_trades:,}
        총 수익금: {total_profit:,}원
        승률: {win_rate:.1f}%
        평균 수익률: {avg_profit:.2f}%

        === 주요 발견 ===
        """

        if filter_results:
            top_filter = filter_results[0] if filter_results else None
            if top_filter and top_filter['수익개선금액'] > 0:
                summary_text += f"""
        최적 필터: {top_filter['필터명'][:25]}
        예상 개선: {top_filter['수익개선금액']:,}원
        통계적 유의성: {top_filter.get('유의함', 'N/A')}
                """

        if feature_importance:
            top_feature = feature_importance['top_features'][0] if feature_importance.get('top_features') else None
            if top_feature:
                summary_text += f"""
        가장 중요한 변수: {top_feature[0]}
        중요도: {top_feature[1]:.3f}
                """

        # 최적 임계값 정보 추가
        if optimal_thresholds and len(optimal_thresholds) > 0:
            top_threshold = optimal_thresholds[0]
            summary_text += f"""
        === 최적 임계값 ===
        {top_threshold.get('필터명', 'N/A')}
        개선: {top_threshold.get('improvement', 0):,.0f}원
                """

        # 매수/매도 조건식(요약) 추가 (공부/검증 목적)
        try:
            if buystg or sellstg:
                sk = ComputeStrategyKey(buystg=buystg, sellstg=sellstg)
                sk_short = (str(sk)[:12] + '...') if sk else 'N/A'
                buy_block = _extract_strategy_block_lines(
                    buystg, start_marker='if 매수:', end_marker='if 매도:', max_lines=5
                )
                sell_block = _extract_strategy_block_lines(
                    sellstg, start_marker='if 매도:', end_marker=None, max_lines=5
                )

                summary_text += f"""
        === 조건식(요약) ===
        전략키: {sk_short}
        매수:
        """ + ("\n".join([f"        {ln}" for ln in buy_block]) if buy_block else "        (없음)") + """
        매도:
        """ + ("\n".join([f"        {ln}" for ln in sell_block]) if sell_block else "        (없음)")
        except Exception:
            pass

        ax16.text(0.1, 0.9, summary_text, transform=ax16.transAxes, fontsize=10,
                 verticalalignment='top',
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        # ============ Chart 18: 자동 생성 필터 조합 적용 시 수익금 변화 (NEW) ============
        ax18 = fig.add_subplot(gs[6, :])
        if generated_code and generated_code.get('combine_steps') and '수익금' in df_tsg.columns:
            try:
                steps = generated_code.get('combine_steps') or []
                base_profit = float(pd.to_numeric(df_tsg['수익금'], errors='coerce').fillna(0).sum())

                labels = ['기준']
                cum_imp = [0.0]
                ex_pct = [0.0]
                for st in steps[:8]:
                    labels.append(str(st.get('필터명', ''))[:16])
                    cum_imp.append(float(st.get('누적개선(동시적용)', 0) or 0))
                    ex_pct.append(float(st.get('누적제외비율', 0) or 0))

                x = list(range(len(labels)))
                profit_after = [base_profit + v for v in cum_imp]

                ax18.plot(x, profit_after, 'o-', color=color_profit, linewidth=2.2, markersize=5, label='예상 수익금(원)')
                ax18.axhline(y=base_profit, color='gray', linestyle='--', linewidth=0.8, alpha=0.8)
                ax18.set_xticks(x)
                ax18.set_xticklabels(labels, rotation=20, ha='right', fontsize=9)
                ax18.set_ylabel('예상 수익금(원)')
                ax18.set_title('자동 생성 필터 조합 적용 시 예상 수익금 변화\n(누적개선=동시 적용/중복 반영, 단계별 제외비율 함께 표시)', fontsize=11)
                ax18.grid(axis='y', alpha=0.4)

                ax18_t = ax18.twinx()
                ax18_t.plot(x, ex_pct, 's--', color='red', linewidth=1.6, markersize=4, label='누적 제외(%)')
                ax18_t.set_ylabel('누적 제외 비율(%)', color='red')
                ax18_t.tick_params(axis='y', labelcolor='red')
                ax18_t.set_ylim(0, min(100, max(ex_pct) * 1.2 + 5))

                # 값 라벨
                for xi, p in zip(x, profit_after):
                    ax18.text(xi, p, f"{int(p):,}", fontsize=8, ha='center', va='bottom')
            except Exception:
                ax18.text(0.5, 0.5, '필터 조합 변화 그래프 생성 실패', ha='center', va='center',
                          fontsize=12, transform=ax18.transAxes)
                ax18.axis('off')
        else:
            ax18.text(0.5, 0.5, '자동 생성 코드(combine_steps) 또는 수익금 컬럼 없음', ha='center', va='center',
                      fontsize=12, transform=ax18.transAxes)
            ax18.axis('off')

        # ============ Chart 17: (진단용) 룩어헤드 포함 필터 효과 Top ============
        ax17 = fig.add_subplot(gs[7, :])
        if filter_results_lookahead and len(filter_results_lookahead) > 0:
            top_15 = [f for f in filter_results_lookahead if f.get('수익개선금액', 0) > 0][:15]
            if top_15:
                names = [str(f.get('필터명', ''))[:26] for f in top_15]
                improvements = [int(f.get('수익개선금액', 0)) for f in top_15]

                y_pos = range(len(names))
                ax17.barh(y_pos, improvements, color='#F39C12', alpha=0.85, edgecolor='black', linewidth=0.5)
                ax17.set_yticks(y_pos)
                ax17.set_yticklabels(names, fontsize=9)
                ax17.set_xlabel('수익 개선 금액(원)')
                ax17.set_title('사후진단(룩어헤드) Top 15 필터 효과\n※ 매도 확정 정보 포함 → 실거래/자동 조건식에는 사용 금지', fontsize=11)
                ax17.invert_yaxis()

                # 값/제외비율 표시
                max_val = max(improvements) if improvements else 0
                for i, f in enumerate(top_15):
                    v = int(f.get('수익개선금액', 0))
                    ex = f.get('제외비율', 0)
                    ax17.text(v + max_val * 0.01, i, f"{v:,}원 (제외 {ex}%)", va='center', fontsize=8)
            else:
                ax17.text(0.5, 0.5, '사후진단 결과(양수 개선) 없음', ha='center', va='center',
                          fontsize=12, transform=ax17.transAxes)
                ax17.axis('off')
        else:
            ax17.text(0.5, 0.5, '사후진단(룩어헤드) 분석 데이터 없음', ha='center', va='center',
                      fontsize=12, transform=ax17.transAxes)
            ax17.axis('off')

        # 저장 및 전송
        # tight_layout은 colorbar/그리드와 함께 경고가 자주 발생하여(subplot 배치가 깨질 수 있음),
        # 고정 margins로 레이아웃을 안정화합니다.
        fig.subplots_adjust(left=0.05, right=0.98, bottom=0.04, top=0.94, hspace=0.55, wspace=0.3)
        output_dir = ensure_backtesting_output_dir(save_file_name)
        analysis_path = str(build_backtesting_output_path(save_file_name, "_enhanced.png", output_dir=output_dir))
        add_memo_box(fig, memo_text)
        plt.savefig(analysis_path, dpi=120, bbox_inches='tight', facecolor='white')
        plt.close(fig)

        if teleQ is not None:
            teleQ.put(analysis_path)

        return analysis_path

    except Exception as e:
        print_exc()
        try:
            plt.close('all')
        except:
            pass
        return None
