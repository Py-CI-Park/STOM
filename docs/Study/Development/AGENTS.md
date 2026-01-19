<!-- Parent: ../AGENTS.md -->
# Development Studies

## Purpose

This directory contains feature implementation plans, system enhancement proposals, development roadmaps, and technical design decisions. It serves as the central repository for:

- **Feature Planning**: Comprehensive implementation strategies for new features
- **Enhancement Proposals**: System improvement designs with technical specifications
- **Development Roadmaps**: Multi-phase implementation plans with milestones
- **Design Decisions**: Architectural choices, technology selections, trade-off analysis
- **Technical Specifications**: Detailed requirements, API designs, database schemas

**Key Objectives**:
- Document development initiatives before implementation
- Define clear technical requirements and success criteria
- Plan phased rollouts with risk mitigation
- Coordinate cross-module changes
- Ensure alignment with STOM architecture patterns

## Key Files

### ICOS (Iterative Condition Optimizer System) Development

**20260114_ICOS_Complete_Implementation_Plan.md**
- Comprehensive implementation strategy for ICOS system
- Multi-phase development plan with clear milestones
- Technical architecture design (UI, backend, optimizer)
- Database schema modifications
- Integration points with existing backtesting system
- Risk assessment and mitigation strategies

**20260113_ICOS_Dialog_Enhancement_Plan.md**
- ICOS dialog UI/UX improvement proposals
- User workflow optimization
- Form validation enhancements
- Progress visualization design
- Error handling improvements

## For AI Agents

### When Adding Development Study Documents

1. **File Naming Convention**: Use `YYYYMMDD_Feature_Name_Plan.md` format
   - Examples: `20260114_ICOS_Complete_Implementation_Plan.md`, `20260120_ML_Model_Integration_Design.md`
2. **Document Structure**: Include the following sections:
   - **Executive Summary**: Feature purpose, business value, scope
   - **Requirements**: Functional and non-functional requirements
   - **Technical Design**: Architecture, components, data flow
   - **Implementation Plan**: Phased approach with milestones
   - **Risk Assessment**: Potential issues and mitigation strategies
   - **Success Criteria**: Measurable outcomes and validation methods
   - **Dependencies**: Required libraries, modules, external services
   - **Timeline**: Estimated effort and delivery schedule
3. **Cross-Reference**: Link to related code files, documentation, and studies
4. **Update Parent README.md**: Add entry with plan status (proposed, in-progress, completed)
5. **Version Control**: Track plan updates and decision changes

### When Creating Implementation Plans

1. **Pre-Planning Analysis**:
   ```markdown
   ## Requirements Gathering
   - [ ] Review user feedback and pain points
   - [ ] Analyze existing system limitations
   - [ ] Survey similar implementations in codebase
   - [ ] Consult stakeholders and domain experts
   - [ ] Define success metrics and KPIs

   ## Feasibility Assessment
   - [ ] Technical feasibility (libraries, APIs, performance)
   - [ ] Resource availability (time, personnel, infrastructure)
   - [ ] Risk assessment (complexity, dependencies, unknowns)
   - [ ] Cost-benefit analysis (development vs. value)
   - [ ] Alternative approaches comparison
   ```

2. **Technical Design Components**:
   - **Architecture Diagram**: Show component interactions and data flow
   - **Database Schema**: New tables, columns, indexes, migrations
   - **API Specification**: REST endpoints, WebSocket messages, queue commands
   - **UI Mockups**: Screen layouts, user workflows, interaction patterns
   - **Process Flow**: Multiprocess coordination, queue communication
   - **Error Handling**: Exception types, recovery strategies, user feedback

3. **Implementation Phasing**:
   ```markdown
   ## Phase 1: Foundation (Week 1-2)
   - Core data models
   - Database schema creation
   - Basic API endpoints
   - Unit tests for core logic

   ## Phase 2: Business Logic (Week 3-4)
   - Algorithm implementation
   - Integration with existing modules
   - Validation logic
   - Integration tests

   ## Phase 3: User Interface (Week 5-6)
   - UI component development
   - Event handler implementation
   - Progress indicators
   - Error messaging

   ## Phase 4: Testing & Polish (Week 7-8)
   - End-to-end testing
   - Performance optimization
   - Bug fixes
   - Documentation updates
   ```

4. **Risk Mitigation Strategies**:
   - **Technical Risks**: Proof-of-concept prototypes, spike solutions
   - **Integration Risks**: Incremental integration, feature flags, rollback plans
   - **Performance Risks**: Profiling, load testing, optimization strategies
   - **Data Risks**: Backup plans, migration scripts, validation checks
   - **User Risks**: Beta testing, phased rollout, user training

5. **Success Criteria Definition**:
   - **Functional**: All requirements implemented and tested
   - **Performance**: Response times, throughput, resource usage within targets
   - **Quality**: Code coverage ≥80%, no critical bugs, guideline compliance
   - **User Experience**: Usability testing passed, user satisfaction ≥4/5
   - **Documentation**: User guides, API docs, code comments updated

### Development Plan Template

```markdown
# [Feature Name] Implementation Plan

## Executive Summary

**Purpose**: [One sentence describing feature value]

**Scope**: [What is included and excluded]

**Success Criteria**:
1. [Measurable outcome 1]
2. [Measurable outcome 2]
3. [Measurable outcome 3]

**Timeline**: [X weeks/months, Start date - End date]

## 1. Requirements

### Functional Requirements
1. **FR-1**: [Requirement description]
2. **FR-2**: [Requirement description]

### Non-Functional Requirements
1. **NFR-1**: Performance - [Specific target]
2. **NFR-2**: Reliability - [Specific target]
3. **NFR-3**: Usability - [Specific target]

## 2. Technical Design

### Architecture Overview
[Diagram or description of component architecture]

### Component Breakdown

#### 2.1 Backend Components
- **Module**: `[path/to/module.py]`
- **Purpose**: [Description]
- **Key Classes**: [List]
- **Key Functions**: [List]

#### 2.2 Database Changes
- **Tables**: [New tables with schema]
- **Columns**: [New columns in existing tables]
- **Indexes**: [New indexes for performance]
- **Migrations**: [Migration scripts needed]

#### 2.3 UI Components
- **Screens**: [List of new/modified screens]
- **Widgets**: [Custom widgets needed]
- **Event Handlers**: [New event handlers]
- **Styling**: [CSS/style changes]

#### 2.4 Process Communication
- **Queues**: [New queues needed (extend qlist)]
- **Messages**: [Message formats and protocols]
- **ZMQ**: [ZMQ socket patterns if applicable]

### Data Flow
1. [Step 1 with component interactions]
2. [Step 2 with component interactions]
3. [Step 3 with component interactions]

## 3. Implementation Plan

### Phase 1: [Name] (Duration)
**Deliverables**:
- [ ] [Deliverable 1]
- [ ] [Deliverable 2]

**Validation**:
- [ ] [Test 1]
- [ ] [Test 2]

### Phase 2: [Name] (Duration)
[Similar structure]

### Phase 3: [Name] (Duration)
[Similar structure]

## 4. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| [Risk 1] | High/Med/Low | High/Med/Low | [Strategy] |
| [Risk 2] | High/Med/Low | High/Med/Low | [Strategy] |

## 5. Dependencies

### Internal Dependencies
- **Modules**: [List of STOM modules used]
- **Utilities**: [Utility functions required]
- **Databases**: [Database tables accessed]

### External Dependencies
- **Libraries**: [New libraries needed (add to pip_install_64.bat)]
- **APIs**: [External APIs or services]
- **Tools**: [Development tools required]

## 6. Testing Strategy

### Unit Tests
- [ ] [Component 1 tests]
- [ ] [Component 2 tests]

### Integration Tests
- [ ] [Integration 1 tests]
- [ ] [Integration 2 tests]

### End-to-End Tests
- [ ] [User workflow 1]
- [ ] [User workflow 2]

### Performance Tests
- [ ] [Performance benchmark 1]
- [ ] [Performance benchmark 2]

## 7. Documentation Requirements

- [ ] Update `docs/Manual/` with feature documentation
- [ ] Create user guide in `docs/Guideline/사용설명서/`
- [ ] Update API documentation (if applicable)
- [ ] Add code comments and docstrings
- [ ] Update CLAUDE.md if architectural changes

## 8. Rollout Plan

### Pre-Release
- [ ] Code review completed
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Backup database created

### Release
- [ ] Deploy to test environment
- [ ] Smoke tests passed
- [ ] Beta user testing
- [ ] Deploy to production

### Post-Release
- [ ] Monitor logs for errors
- [ ] Collect user feedback
- [ ] Performance monitoring
- [ ] Bug fix iterations

## 9. Success Metrics

**Immediate (Week 1)**:
- [Metric 1 with target]
- [Metric 2 with target]

**Short-term (Month 1)**:
- [Metric 1 with target]
- [Metric 2 with target]

**Long-term (Quarter 1)**:
- [Metric 1 with target]
- [Metric 2 with target]

## 10. References

- Related code files: [Links]
- Related documentation: [Links]
- Related studies: [Links]
- External resources: [Links]
```

### Integration with Other Studies

**With ResearchReports/**:
- Implement AI/ML findings from `AI_ML_Trading_Strategy_Automation_Research.md`
- Apply optimization methods from `Segmented_Filter_Optimization_Research.md`
- Integrate risk assessment from `Overfitting_Risk_Assessment_Filter_Segment_Analysis.md`

**With SystemAnalysis/**:
- Address improvement proposals from `STOM_Optimization_System_Improvements.md` (15 items)
- Implement metric enhancements from `Backtesting_Output_System_Analysis.md`
- Apply ML insights from `ML/ML_Model_Improvement_Study.md`

**With Guides/**:
- Follow `New_Metrics_Development_Process_Guide.md` for metric additions
- Apply `Segment_Filter_Condition_Integration_Guide.md` for filter integration
- Use checklists from `Segment_Filter_Verification_Checklist.md`

**With CodeReview/**:
- Conduct code reviews during implementation phases
- Address architectural consistency requirements
- Apply quality scoring criteria (0-10 scale)

### Development Best Practices

1. **Architecture Alignment**:
   - Respect multiprocess boundaries (15 queues, qlist indices)
   - Follow naming conventions (`*_receiver_*.py`, `*_strategy_*.py`)
   - Use Template Method pattern for strategy extensions
   - Preserve Korean variable names (현재가, 시가, 고가, 저가)

2. **Database Management**:
   - Add new database paths to `utility/setting.py`
   - Update `utility/query.py` for new queries
   - Run `utility/database_check.py` after schema changes
   - Maintain index integrity for performance

3. **UI Development**:
   - Define layouts in `ui/set_*.py` files
   - Implement event handlers in `ui/ui_button_clicked_*.py`
   - Update rendering in `ui/ui_draw_*.py`
   - Apply styling in `ui/set_style.py`

4. **Testing Requirements**:
   - Unit tests for core logic
   - Integration tests for module interactions
   - Backtester validation for trading strategies
   - Performance benchmarks (reference `/lecture/testcode/`)

5. **Documentation Standards**:
   - Update condition documents for strategy changes (98.3% compliance)
   - Add code comments for complex algorithms
   - Create user guides for new features
   - Update CLAUDE.md for architectural changes

### Common Development Patterns

**Multiprocess Communication**:
```python
# Adding new queue to qlist
qlist = [
    windowQ, soundQ, queryQ, teleQ, chartQ,
    hogaQ, webcQ, backQ, creceivQ, ctraderQ,
    cstgQ, liveQ, kimpQ, wdzservQ, totalQ,
    newFeatureQ  # Index 15 - New feature queue
]
```

**Database Schema Addition**:
```python
# In utility/setting.py
DB_NEW_FEATURE = f'{DB_PATH}/new_feature.db'

# In utility/query.py
def ProcessQuery(qlist):
    while True:
        q = qlist[2].get()
        if type(q) == tuple:
            query, values, db, *args = q
            # Add new database case
```

**Strategy Extension**:
```python
# New strategy file: stock/kiwoom_strategy_new.py
class NewStrategy(Receiver):
    def __init__(self, qlist, ...):
        super().__init__(qlist, ...)
        self.InitializeParameters()

    def StrategyLogic(self, data):
        # Implement template method
        pass
```

## Dependencies

### Development Tools
- **IDE**: PyCharm, VSCode with Python extensions
- **Version Control**: Git, GitHub for repository management
- **Profiling**: cProfile, memory_profiler, line_profiler
- **Testing**: pytest, unittest for test frameworks
- **Documentation**: Markdown editors, diagram tools

### STOM Framework
- **Core Modules**: `utility/`, `stock/`, `coin/`, `backtester/`, `ui/`
- **Settings**: `utility/setting.py` (15 database paths, global configuration)
- **Queue System**: 15 queues for multiprocess communication
- **Database**: SQLite (15 databases), schema management

### External Libraries
- **UI**: PyQt5 ecosystem (WebEngine, pyqtgraph)
- **Data**: NumPy, pandas, TA-Lib
- **APIs**: pyupbit, python-binance, Kiwoom OpenAPI
- **Optimization**: Optuna, CMA-ES, genetic algorithms
- **Communication**: ZeroMQ, WebSockets

### Domain Knowledge
- **Trading Systems**: Order execution, risk management, position sizing
- **Korean Market**: Kiwoom API, market rules, conventions
- **Cryptocurrency**: Upbit/Binance APIs, exchange differences
- **Backtesting**: LOOKAHEAD-FREE, walk-forward validation
- **Technical Analysis**: Indicator calculations, pattern recognition

### Related Documentation
- **Manual**: `02_Architecture/`, `03_Modules/`, `07_Trading/`
- **Guidelines**: Development standards, coding patterns
- **Condition Templates**: `Condition_Document_Template_Guideline.md`
- **API Documentation**: Module APIs, database schemas

---

**Last Updated**: 2026-01-19
**Total Documents**: 2 files
**Current Focus**: ICOS (Iterative Condition Optimizer System) implementation
**Development Status**: Planning phase, multi-phase rollout approach
