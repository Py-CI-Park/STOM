<!-- Parent: ../AGENTS.md -->
# AI Strategy Ideas

## Purpose
AI 모델(Claude Opus, GPT-5)이 생성한 트레이딩 전략 아이디어 및 백테스팅 가이드라인 제안 저장소. 전략 개발 계획, ML/DL 백테스팅 최적화 아이디어, 프로그램 개발 문서 등을 포함합니다.

## Overview
- **Total files**: 26 markdown files
- **AI Models**: Claude Opus (12 files), GPT-5 (14 files)
- **Content types**: Strategy plans, backtesting guidelines, ML/DL ideas, development documentation
- **Status**: Conceptual phase - requires validation and implementation

## Subdirectories

### Plan_from_claude_opus/ (12 files)
Claude Opus 모델이 생성한 전략 계획 및 가이드라인 제안.

**Key files:**
- `Back_Testing_Guideline_Min.md` - 분봉 백테스팅 가이드라인 제안
- `Back_Testing_Guideline_Tick.md` - 틱 백테스팅 가이드라인 제안
- `Condition_Survey_Idea.md` - 조건식 서베이 아이디어
- `ML_DL_Backtesting_Optimization_Ideas.md` - ML/DL 최적화 아이디어
- `program_develop_document/` - 프로그램 개발 문서 폴더

**Characteristics:**
- Long-form, detailed analysis
- Comprehensive strategy frameworks
- Structured approach to problem-solving
- Focus on systematic methodology

### Plan_from_GPT5/ (14 files)
GPT-5 모델이 생성한 전략 계획 및 가이드라인 제안.

**Key files:**
- `Back_Testing_Guideline_Min.md` - 분봉 백테스팅 가이드라인 제안
- `Back_Testing_Guideline_Tick.md` - 틱 백테스팅 가이드라인 제안
- `Condition_Survey_Idea.md` - 조건식 서베이 아이디어
- `Condition_Survey_ML_DL_Plan.md` - ML/DL 조건식 계획
- `program_develop_document_versionG/` - 프로그램 개발 문서 폴더 (버전 G)

**Characteristics:**
- Concise, actionable recommendations
- Practical implementation focus
- Code-oriented solutions
- Rapid prototyping approach

## For AI Agents

### Using AI Strategy Ideas
1. **Validation required** - All AI-generated ideas must be validated through backtesting
2. **Cross-reference with existing strategies** - Compare with proven strategies in Tick/Min folders
3. **Incremental implementation** - Start with simple components, add complexity gradually
4. **Document thoroughly** - When implementing, follow template guidelines
5. **Version control** - Track which AI suggestions were implemented and results

### When Implementing AI Ideas
1. **Read the original AI plan** - Understand the full context and rationale
2. **Assess feasibility** - Check if required data/indicators are available
3. **Create prototype** - Implement minimal viable version first
4. **Backtest extensively** - Test across multiple time periods and market conditions
5. **Document results** - Record what worked, what didn't, and why
6. **Iterate** - Refine based on backtesting results
7. **Move to production** - If validated, create proper condition document in Tick/Min folders

### Comparing AI Outputs
**Claude Opus strengths:**
- Comprehensive system design
- Detailed explanation of reasoning
- Long-term strategic planning
- Risk analysis and edge case consideration

**GPT-5 strengths:**
- Quick prototyping suggestions
- Code-ready implementations
- Practical troubleshooting
- Clear step-by-step instructions

### Quality Standards for AI Ideas
- **Theoretical soundness** - Strategy logic must be theoretically valid
- **Implementation feasibility** - Must be implementable with available data
- **Backtestability** - Must be testable with existing backtesting framework
- **Documentation clarity** - Clear explanation of strategy logic and parameters
- **Risk awareness** - Acknowledgment of potential pitfalls and limitations

### Critical Evaluation Criteria
1. **Data availability** - Can we access required data fields?
2. **Computational feasibility** - Can it run in real-time?
3. **Over-optimization risk** - Is it too specific to training data?
4. **Market regime sensitivity** - Will it work in different market conditions?
5. **Transaction cost impact** - Does it account for realistic trading costs?
6. **Signal frequency** - Does it generate enough trading opportunities?
7. **Risk management** - Does it include position sizing and stop-loss?

## Integration with Main Strategies

### From Idea to Production
```
1. AI Idea Generation (Idea/)
   ↓
2. Feasibility Assessment
   ↓
3. Prototype Implementation
   ↓
4. Backtesting Validation
   ↓
5. Refinement & Optimization
   ↓
6. Documentation (follow template)
   ↓
7. Move to Tick/Min folders (1_To_be_reviewed)
   ↓
8. Review process (→ 2_Under_review → 3_Review_finished)
```

### Success Metrics
- **Sharpe Ratio** > 1.5
- **Win Rate** > 50%
- **Max Drawdown** < 20%
- **Profit Factor** > 1.5
- **Consistency** across multiple time periods
- **Robustness** to parameter variations

## Dependencies
- **Validation**: Backtesting engines (`backtester/backengine_*`)
- **Implementation**: Strategy engines (`stock/kiwoom_strategy_*`)
- **Documentation**: Template guidelines (`docs/Guideline/`)
- **Data**: Database schemas (`_database/*.db`)
- **Reference**: Existing strategies (`Tick/`, `Min/`)

## Related Documentation
- Parent: `../README.md` - Condition folder overview
- Implementation: `../Tick/`, `../Min/` - Production strategies
- Reference: `../Reference/` - External strategy references
- Guidelines: `../../Guideline/` - Documentation templates

## AI Model Comparison

### Claude Opus
**Best for:**
- System architecture design
- Complex multi-indicator strategies
- Risk management frameworks
- Long-term strategic planning

**Example outputs:**
- Comprehensive backtesting guideline proposals
- Multi-layered strategy systems
- ML/DL optimization frameworks

### GPT-5
**Best for:**
- Quick strategy prototypes
- Code implementation details
- Specific problem-solving
- Iterative refinement

**Example outputs:**
- Actionable code snippets
- Step-by-step implementation plans
- Debugging suggestions

## Notes
- **All ideas are conceptual** - No AI-generated strategy is production-ready without validation
- **Backtesting is mandatory** - Every idea must be tested before live trading
- **Documentation required** - Implemented strategies must follow template guidelines
- **Version tracking** - Keep original AI outputs for reference and comparison
- **Iterative refinement** - Expect multiple iterations from idea to production
- **Cross-model validation** - Consider using both AI models for different aspects
- **Human oversight critical** - AI suggestions require expert review and judgment
- **Market dynamics** - Strategies may need adjustment as market conditions evolve

## Statistics
- Total AI-generated documents: 26
- From Claude Opus: 12 (46%)
- From GPT-5: 14 (54%)
- Implemented strategies: 0 (all conceptual)
- Under evaluation: 26 (100%)
- Validation rate: 0% (requires backtesting)

## Future Directions
- Implement prototype strategies for top AI ideas
- Create validation framework for AI-generated strategies
- Track success rate of AI suggestions
- Build feedback loop: backtest results → AI model refinement
- Develop hybrid strategies combining multiple AI suggestions
- Create automated validation pipeline for AI ideas
