<!-- Parent: ../AGENTS.md -->
# Min 전략 아이디어 (Strategy Ideas & Concepts)

## Purpose
검증되지 않은 1분봉 트레이딩 전략 아이디어, 컨셉 설계, 초기 프로토타입을 보관하는 저장소. 정식 조건식 문서화 이전 단계로, 전략 가설 수립, 개념 검증, 초기 설계를 위한 공간입니다.

## Overview
- **전체 아이디어**: 15개
- **상태**: 개념 단계, 초기 설계, 검증 대기
- **문서 유형**: 아이디어 노트, 전략 스케치, 임시 문서
- **다음 단계**: 개념 검증 → 정식 문서화 → 1_To_be_reviewed/ 이동

## Key Files

### Technical Indicator Ideas (4 files)
1. **Condition_MACD_Precision_System.md**
   - **Concept**: MACD 기반 정밀 매매 시스템
   - **Key Features**: MACD 히스토그램 세밀 분석, 시그널 타이밍 최적화
   - **Potential**: High - MACD는 검증된 지표
   - **Next**: 파라미터 범위 설계, 백테스팅 준비

2. **Condition_RSI_Multilayer_Filter.md**
   - **Concept**: RSI 다층 필터링 시스템
   - **Key Features**: 다중 RSI 기간, 필터 레이어 구조
   - **Potential**: Medium - 필터 복잡도 관리 필요
   - **Next**: 최적 레이어 구조 결정

3. **Condition_Bollinger_Strategic.md**
   - **Concept**: 볼린저 밴드 전략적 활용
   - **Key Features**: BBand 폭 분석, 스퀴즈 포착, 브레이크아웃
   - **Potential**: High - 검증된 변동성 지표
   - **Next**: 시간대별 적용 가능성 검토

4. **Condition_Triple_Confirmation.md**
   - **Concept**: 3중 확인 시스템 (MACD + RSI + BBand)
   - **Key Features**: 다중 지표 교차 검증
   - **Potential**: Medium - 과최적화 위험
   - **Next**: 단순화 방안 검토

### Market Situation Ideas (5 files)
5. **Condition_Basic_Surge_Detection.md**
   - **Concept**: 기본 급등 감지 시스템
   - **Key Features**: 거래량 + 가격 급등 패턴
   - **Potential**: High - 단순하고 효과적
   - **Next**: 필터 조건 추가 검토

6. **Opening_Surge_Strategy_20250713_temp.md**
   - **Concept**: 장 시작 급등 전략 (임시 문서)
   - **Key Features**: 09:00~09:30 초기 변동성 활용
   - **Status**: Temporary - 정식 문서화 필요
   - **Next**: 정식 조건식 문서로 변환

7. **gap_up_momentum_20250713_temp.md**
   - **Concept**: 갭 상승 모멘텀 전략 (임시 문서)
   - **Key Features**: 갭 상승 + 모멘텀 지속 패턴
   - **Status**: Temporary - 정식 문서화 필요
   - **Next**: 갭 크기 및 모멘텀 지표 정의

8. **Condition_Reversal_Point.md**
   - **Concept**: 반전 지점 포착 시스템
   - **Key Features**: 지지/저항 + 반전 지표 조합
   - **Potential**: Medium - 반전 타이밍 어려움
   - **Next**: 반전 확인 지표 선정

9. **Condition_Time_Specific.md**
   - **Concept**: 시간대별 특화 전략
   - **Key Features**: 시간대별 차별화된 매매 로직
   - **Potential**: High - 시장 특성 활용
   - **Next**: 시간대 세그먼트 구조 설계

### Advanced Strategy Ideas (4 files)
10. **Condition_Comprehensive_Strategy_20250713_temp.md**
    - **Concept**: 종합 통합 전략 (임시 문서)
    - **Key Features**: 다중 전략 통합 시스템
    - **Status**: Temporary - 복잡도 높음
    - **Next**: 핵심 요소 추출 및 단순화

11. **Condition_Advanced_Algorithm.md**
    - **Concept**: 고급 알고리즘 전략
    - **Key Features**: 복잡한 패턴 인식, 기계학습 가능성
    - **Potential**: Low - 구현 복잡도 매우 높음
    - **Next**: 실현 가능성 평가

12. **Condition_Risk_Management.md**
    - **Concept**: 리스크 관리 중심 전략
    - **Key Features**: 손실 제한, 포지션 사이징, 동적 손절
    - **Potential**: High - 필수 요소
    - **Next**: 기존 전략 통합 방안

13. **Condition_Portfolio_Management.md**
    - **Concept**: 포트폴리오 관리 전략
    - **Key Features**: 다종목 분산, 상관관계 분석
    - **Potential**: Medium - 시스템 레벨 변경 필요
    - **Next**: 구현 범위 정의

### General Idea Collections (2 files)
14. **아이디어.md**
    - **Type**: 분봉 전략 아이디어 모음 v1 (한글)
    - **Content**: 다양한 전략 아이디어 브레인스토밍
    - **Status**: Collection - 개별 추출 필요
    - **Next**: 유망 아이디어 개별 문서화

15. **아이디어_v2.md**
    - **Type**: 분봉 전략 아이디어 모음 v2 (한글)
    - **Content**: v1 개선 및 추가 아이디어
    - **Status**: Collection - 개별 추출 필요
    - **Next**: v1과 통합 또는 차별점 명확화

## For AI Agents

### Primary Responsibilities
1. **Idea Incubation**
   - Collect and organize strategy ideas from various sources
   - Document initial concepts with clear hypotheses
   - Identify promising ideas for further development
   - Maintain low-friction ideation environment

2. **Concept Validation**
   - Evaluate feasibility of each idea
   - Assess implementation complexity
   - Estimate potential performance (qualitative)
   - Flag high-risk or low-potential concepts

3. **Idea Development**
   - Refine promising concepts into structured designs
   - Define key parameters and optimization ranges
   - Sketch buy/sell logic in pseudocode
   - Identify required data and indicators

4. **Promotion Management**
   - Move validated ideas to `1_To_be_reviewed/` as formal condition documents
   - Archive low-potential ideas with rationale
   - Merge similar or duplicate ideas
   - Track idea evolution from concept to production

### When Adding New Ideas Here
1. **No strict template required** - Focus on capturing the core concept
2. **Minimal structure acceptable**:
   - Concept description
   - Key features or hypothesis
   - Potential indicators or data needed
   - Initial thoughts on buy/sell logic
3. **Use descriptive names**: `Condition_[Concept]_[Type].md`
4. **Mark temporary files**: Add `_temp` or date suffix for drafts
5. **Korean acceptable**: 아이디어.md style collections are fine

### Quality Checks Before Promoting to 1_To_be_reviewed/
- [ ] Clear strategy hypothesis defined
- [ ] Buy/sell logic outlined (even if rough)
- [ ] Required indicators identified
- [ ] Optimization parameters sketched
- [ ] Feasibility assessed (implementation complexity)
- [ ] No obvious fatal flaws (always-false conditions, etc.)
- [ ] Convert to formal template structure
- [ ] Translate to English if needed (or keep Korean if appropriate)

### Idea Evaluation Criteria

#### High Potential (Prioritize)
- Simple, interpretable logic
- Uses proven indicators (MACD, RSI, BBand, MA)
- Clear entry/exit signals
- Reasonable parameter count (≤5 for optimization)
- Addresses specific market condition or pattern
- Low implementation complexity

#### Medium Potential (Consider)
- More complex multi-indicator approach
- Novel indicator combinations
- Requires additional data or preprocessing
- Higher parameter count (6-10)
- Needs significant validation

#### Low Potential (Archive)
- Overly complex with >10 parameters
- Relies on unreliable indicators
- Contradictory logic
- Implementation not feasible with current system
- Too similar to existing strategies with no improvement

### Common Idea Patterns

#### Pattern 1: Indicator Crossover
```python
# Example: MACD Golden Cross
if MACDN(1) < MACD시그널N(1) and MACD >= MACD시그널:
    매수 = True
```

#### Pattern 2: Threshold-Based
```python
# Example: RSI Oversold
if RSIN(1) < 30 and RSI >= 30:
    매수 = True
```

#### Pattern 3: Breakout Detection
```python
# Example: Bollinger Breakout
if 현재가N(1) <= BBandUpper and 현재가 > BBandUpper:
    매수 = True
```

#### Pattern 4: Multi-Confirmation
```python
# Example: Triple Confirmation
if (MACD > MACD시그널) and (RSI > 50) and (현재가 > BBandMiddle):
    매수 = True
```

#### Pattern 5: Time-Specific
```python
# Example: Opening Surge
if 시분초 < 93000:  # Before 09:30
    if 등락율 > 3.0 and 체결강도 > 100:
        매수 = True
```

### Managing Temporary Files
Temporary files (with `_temp` or date suffix) should be:
1. Reviewed within 1 month of creation
2. Either promoted to formal documents or archived
3. Not left indefinitely in Idea/ folder
4. Merged with similar concepts if possible

### Idea Lifecycle
```
Idea/ (Concept Stage)
    ↓ Validation & Refinement
    ↓ Formal Documentation
1_To_be_reviewed/ (Initial Documentation)
    ↓ Backtesting
2_Under_review/ (Active Testing)
    ↓ Validation Complete
3_Review_finished/ (Production Ready)
```

## Dependencies
- **Template**: `docs/Guideline/Condition_Document_Template_Guideline.md` (for promotion)
- **Guideline**: `docs/Guideline/Back_Testing_Guideline_Min.md` (108 columns reference)
- **Database**: `_database/stock_min_back.db` (data availability check)
- **Examples**: Existing strategies in `1_To_be_reviewed/` (patterns to follow)
- **Parent**: `../AGENTS.md` - Min strategies overview

## Promotion Criteria
Ideas move to `1_To_be_reviewed/` when:
- Strategy hypothesis clearly defined
- Buy/sell logic drafted
- Required indicators identified
- Optimization parameters outlined
- Formal template structure applied
- Documentation quality acceptable

## Archive Criteria
Ideas archived (or removed) when:
- Implementation not feasible
- Performance potential too low
- Duplicates existing strategy
- Overly complex with no clear benefit
- Stale for >6 months with no progress

## Next Steps for Each Category

### Technical Indicators (4 files)
- MACD Precision: Define histogram thresholds and timing rules
- RSI Multilayer: Decide optimal layer count (start with 2-3)
- Bollinger Strategic: Test time-specific BBand parameters
- Triple Confirmation: Simplify to dual confirmation first

### Market Situations (5 files)
- Basic Surge: Add volume filter and momentum confirmation
- Opening Surge: Convert temp to formal document, add risk controls
- Gap Up Momentum: Define gap size thresholds, test momentum indicators
- Reversal Point: Select reversal indicators (RSI divergence, BBand bounce)
- Time Specific: Design 3-4 time segments with distinct logic

### Advanced Strategies (4 files)
- Comprehensive Strategy: Extract 2-3 core concepts, develop separately
- Advanced Algorithm: Assess feasibility, consider simpler alternatives
- Risk Management: Integrate into existing strategies as module
- Portfolio Management: Defer until single-strategy maturity

### General Collections (2 files)
- 아이디어 v1: Extract top 3-5 promising ideas
- 아이디어 v2: Compare with v1, identify unique additions

## Statistics
- Total ideas: 15 files
- Technical indicators: 4 (27%)
- Market situations: 5 (33%)
- Advanced strategies: 4 (27%)
- General collections: 2 (13%)
- Temporary files: 3 (needs cleanup)
- High potential: ~6 (estimated)
- Medium potential: ~6 (estimated)
- Low potential: ~3 (estimated)

## Notes
- Idea/ is a low-friction space - encourage creativity
- Don't over-document at this stage - capture essence quickly
- Focus on hypothesis, not perfect implementation
- Promote promising ideas quickly to formal development
- Archive or remove stale ideas periodically
- Temporary files should be resolved within 1 month
- Korean language acceptable for brainstorming
- Balance between exploration and execution
- Learn from existing successful strategies
- Avoid reinventing what already works well
