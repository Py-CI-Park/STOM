<!-- Parent: ../AGENTS.md -->
# 2단계: 검토 진행 중 (Under Review)

## Purpose
백테스팅이 실행되고 있거나 결과 분석이 진행 중인 틱 전략 조건식 저장소. 이 단계에서는 전략의 실제 성능을 검증하고, 파라미터 최적화를 수행하며, 개선 방안을 도출합니다.

## Overview
- **전략 수**: 12개 조건 파일
- **상태**: 백테스팅 실행 또는 결과 분석 중
- **이전 단계**: `1_To_be_reviewed/`에서 이동
- **다음 단계**: `3_Review_finished/`로 이동 (검증 완료 시)
- **문서 준수**: 98.3%+ 가이드라인 준수 목표

## Key Files

### Production-Ready Candidate (⭐⭐⭐⭐⭐)
**`Condition_Tick_902_905_update_2.md`** - Gold Standard
- 09:02-09:05 시간대 특화 전략
- 완전한 백테스팅 결과 포함
- 최적화 섹션 완비 (BO/BOR/SO/SOR/OR/GAR)
- 개선 연구 문서화
- 프로덕션 배포 준비 완료
- **Status**: Ready for `3_Review_finished/`

**`Condition_Tick_900_920_Enhanced.md`** - Multi-Tier Strategy
- 시가총액 3단계 차등 적용
- 4개 시간대 조합 (09:00-09:20)
- 고급 최적화 기법 적용
- **Status**: Final validation pending

### Evolution Series (진화 버전)

#### 09:02 Series (초기 버전)
**`Condition_Tick_902.md`** - Version 1
- 초기 09:02 전략 개념
- 기본 모멘텀 로직
- **Status**: Superseded by later versions

**`Condition_Tick_902_Update.md`** - Version 2
- 개선된 진입 조건
- 추가 필터링 로직
- **Status**: Under optimization

#### 09:02-09:05 Series (확장 버전)
**`Condition_Tick_902_905.md`** - Version 1
- 시간 범위 확장 (09:02 → 09:05)
- 다단계 진입 로직
- **Status**: Baseline for later versions

**`Condition_Tick_902_905_update.md`** - Version 2
- 체결강도 지표 추가
- 거래량 필터 강화
- **Status**: Performance analysis ongoing

**`Condition_Tick_902_905_update_2.md`** - Version 3 (Gold Standard)
- 종합 최적화 완료
- 백테스팅 검증 완료
- **Status**: Production ready

**`Condition_Tick_902_905_update_3.md`** - Version 4 (Experimental)
- 추가 개선 실험
- 신규 지표 테스트
- **Status**: Experimental validation

### Source Files (원본 참조)
**`Condition_Tick_902_update_source.md`**
- 902_Update 전략의 원본 소스
- 개발 히스토리 추적
- 코드 변경 이력 보존

**`Condition_Tick_902_905_update_source.md`**
- 902_905_update 전략의 원본 소스
- 진화 과정 문서화
- 비교 분석용 참조

**`Condition_Tick_902_905_update_2_source.md`**
- Gold standard 전략의 원본 소스
- 최종 최적화 전 상태
- Rollback 참조용

### Study Files (연구 자료)
**`Condition_tick_900_920_study.md`**
- 09:00-09:20 시간대 심층 연구
- 다양한 지표 조합 실험
- Enhanced 버전의 기초 연구
- **Status**: Research completed, findings applied

**`Condition_Tick_900_920_Enhanced copy.md`**
- Enhanced 버전의 백업/임시 복사본
- 개발 중간 단계 보존
- **Status**: Archive/backup

## For AI Agents

### When Working with Files in This Stage

1. **Backtesting Validation**
   - Execute backtesting with `backtester/backtest.py`
   - Analyze results from `_database/backtest.db`
   - Compare performance across versions
   - Document findings in strategy file

2. **Performance Analysis**
   - Track metrics: Win rate, profit factor, max drawdown
   - Compare against baseline (Version 1)
   - Identify optimal parameter ranges
   - Document statistical significance

3. **Optimization Process**
   - Start with grid search (`backtester/optimiz.py`)
   - Apply genetic algorithm for refinement
   - Update optimization sections (BO/BOR/SO/SOR/OR/GAR)
   - Validate against out-of-sample data

4. **Version Control**
   - Maintain source files for traceability
   - Document changes between versions
   - Keep evolution history clear
   - Use version numbers in filenames

5. **Moving to Review Finished**
   ```
   Quality Gates:
   ✅ Backtesting completed with statistically significant results
   ✅ Win rate ≥55%, profit factor ≥1.3
   ✅ All optimization sections complete and validated
   ✅ Improvement research documented
   ✅ Code-documentation alignment verified
   ✅ 98.3%+ template compliance achieved
   ✅ Ready for production deployment
   ```

### Critical Rules for This Stage

1. **Document All Testing**
   - Record every backtesting run
   - Document parameter changes
   - Track performance metrics
   - Note unexpected behaviors

2. **Preserve Evolution History**
   - Never delete previous versions
   - Maintain source files separately
   - Document version differences
   - Keep backup copies for critical files

3. **Optimization Discipline**
   - Start with wide parameter ranges (BOR/SOR)
   - Narrow down to top 10 variables (OR)
   - Apply GA for final tuning (GAR)
   - Validate on separate time periods

4. **Quality Before Promotion**
   - No promotion to finished without backtesting proof
   - Require statistical significance
   - Demand consistent performance across periods
   - Ensure documentation completeness

5. **Comparison Analysis**
   - Compare versions systematically
   - Identify what improvements actually worked
   - Document lessons learned
   - Apply findings to other strategies

### Version Management Strategy

**Naming Convention:**
```
Base: Condition_Tick_902.md
Update: Condition_Tick_902_Update.md
Extended: Condition_Tick_902_905.md
Iteration: Condition_Tick_902_905_update_2.md
Source: Condition_Tick_902_905_update_2_source.md
```

**Evolution Tracking:**
1. Create new version with incremented number
2. Copy previous version to `*_source.md` if significant
3. Document changes in header
4. Update backtesting results section
5. Maintain performance comparison table

### Common Backtesting Issues

**Performance Issues:**
- Low win rate (<50%) → Review entry conditions
- High drawdown (>20%) → Tighten stop loss
- Low profit factor (<1.2) → Adjust take profit levels
- Inconsistent results → Add filters or reduce noise

**Data Issues:**
- Missing tick data → Check database integrity
- Anomalous prices → Add data cleaning filters
- Time gaps → Verify market hours filter
- Duplicate entries → Review data collection process

**Logic Issues:**
- Condition never triggered → Review threshold values
- Too many signals → Add stricter filters
- Late entries → Adjust time windows
- Early exits → Review exit conditions

## Dependencies

### Required Reading
- **Parent**: `../AGENTS.md` - Tick strategy overview
- **Previous Stage**: `../1_To_be_reviewed/AGENTS.md`
- **Gold Standard**: `Condition_Tick_902_905_update_2.md`
- **Template**: `docs/Guideline/Condition_Document_Template_Guideline.md`
- **Guideline**: `docs/Guideline/Back_Testing_Guideline_Tick.md`

### Backtesting Infrastructure
- **Main Engine**: `backtester/backtest.py`
- **Tick Engine**: `backtester/backengine_stock_tick.py`
- **Optimization**: `backtester/optimiz.py`
- **GA Optimization**: `backtester/optimiz_genetic_algorithm.py`
- **Results DB**: `_database/backtest.db`
- **Test DB**: `_database/stock_tick_back.db`

### Performance Benchmarks
```yaml
minimum_requirements:
  win_rate: 55%
  profit_factor: 1.3
  max_drawdown: 15%
  sharpe_ratio: 1.0

production_ready:
  win_rate: 60%+
  profit_factor: 1.5+
  max_drawdown: 10%
  sharpe_ratio: 1.5+
```

### Review Criteria

**Stage 2 Entry Requirements:**
- ✅ From `1_To_be_reviewed/`
- ✅ Document structure complete
- ✅ Backtesting initiated

**Stage 3 Promotion Requirements:**
- ✅ Backtesting completed
- ✅ Performance benchmarks met
- ✅ Optimization validated
- ✅ Documentation complete (98.3%+)
- ✅ Production deployment approved

## Statistics
- **Total Files**: 12 condition files
- **Gold Standard**: 1 file (ready for production)
- **Active Development**: 6 files (evolution series)
- **Source Files**: 3 files (version control)
- **Study Files**: 2 files (research/backup)
- **Previous Stage**: 63 files in `1_To_be_reviewed/`
- **Next Stage**: 0 files in `3_Review_finished/` (not yet created)

## Notes

### Development Priority
1. **Immediate**: Validate `Condition_Tick_902_905_update_2.md` for production
2. **High**: Complete `Condition_Tick_900_920_Enhanced.md` validation
3. **Medium**: Analyze `Condition_Tick_902_905_update_3.md` experimental results
4. **Low**: Archive superseded versions (902.md, 902_Update.md)

### Version Evolution Insights
- Early versions (902) focused on single time point
- Mid versions (902_905) extended to time windows
- Late versions (update_2) added comprehensive optimization
- Latest versions (update_3) explore experimental indicators

### Best Practices from Gold Standard
- Document every optimization iteration
- Include statistical significance tests
- Maintain separate source files
- Provide clear improvement research section
- Use consistent variable naming (Korean)
- Follow template compliance strictly (98.3%+)

### Future Improvements
- Create `3_Review_finished/` directory for completed strategies
- Implement automated backtesting pipeline
- Add performance comparison dashboard
- Develop version diff tool for strategy comparison
