<!-- Parent: ../AGENTS.md -->
# Study Guides

## Purpose

This directory contains practical guides for optimization workflows, metric development, system integration, and verification processes. It serves as the central repository for:

- **Process Documentation**: Step-by-step workflows for common development tasks
- **Validation Checklists**: Comprehensive verification procedures
- **Integration Guides**: System integration and deployment procedures
- **Best Practices**: Proven patterns and methodologies
- **Reference Materials**: Variable catalogs, parameter definitions, optimization methods

**Key Objectives**:
- Provide actionable guidance for development tasks
- Standardize workflows and verification processes
- Document proven patterns from successful implementations
- Reduce learning curve for new features and systems
- Ensure consistency across development activities

## Key Files

### Optimization & Analysis

**Condition_Optimization_and_Analysis_Guide.md** (13KB)
- **Variable Catalog**: 826 tick variables, 752 minute variables
- **Optimization Methods**: Grid search, genetic algorithms, Bayesian optimization
- **Analysis Techniques**: Statistical validation, overfitting detection, walk-forward testing
- **Performance Metrics**: Profit factor, Sharpe ratio, max drawdown, win rate
- **Best Practices**: Sample size requirements, parameter tuning strategies

### Metric Development

**New_Metrics_Development_Process_Guide.md** (52KB)
- **10-Step Process**: Comprehensive metric development workflow
- **LOOKAHEAD-FREE Verification**: Ensuring no future data leakage
- **Code Templates**: Sample implementations for common patterns
- **Integration Checklist**: Database, UI, backtester integration steps
- **Validation Methods**: Statistical tests, cross-validation, performance benchmarks
- **Quality Gates**: Requirement verification at each development stage

### Integration Workflows

**Segment_Filter_Condition_Integration_Guide.md** (8KB)
- Integration workflow for segment filters (market cap, time-based)
- Database schema modifications required
- UI component updates for filter configuration
- Backtester integration procedures
- Testing and validation steps

**Segment_Filter_Daily_Block_Implementation_Guide.md**
- Daily block filter implementation specifics
- Time-based segmentation patterns
- Performance optimization considerations
- Edge case handling

### Verification & Quality

**Segment_Filter_Verification_Checklist.md**
- Comprehensive checklist for segment filter validation
- Data integrity verification steps
- Performance validation criteria
- Integration testing requirements
- Common issues and troubleshooting

## For AI Agents

### When Adding Guide Documents

1. **File Naming Convention**: Use `[Topic]_[Type]_Guide.md` format
   - Examples: `Condition_Optimization_and_Analysis_Guide.md`, `API_Integration_Guide.md`
2. **Document Structure**: Include the following sections:
   - **Overview**: Purpose, scope, prerequisites, estimated time
   - **Prerequisites**: Required knowledge, tools, access
   - **Step-by-Step Process**: Numbered steps with clear actions
   - **Code Examples**: Practical templates and snippets
   - **Validation Checklist**: Verification steps for each phase
   - **Common Issues**: Troubleshooting guide with solutions
   - **Best Practices**: Proven patterns and tips
   - **References**: Related documentation and external resources
3. **Usability Focus**: Write for target audience (junior vs senior developers)
4. **Visual Aids**: Include diagrams, tables, examples
5. **Update Parent README.md**: Add entry with guide scope and key topics

### When Writing Process Guides

1. **Process Definition Template**:
   ```markdown
   # [Process Name] Guide

   ## Overview
   **Purpose**: [What this process accomplishes]
   **Audience**: [Target users - junior/senior developers, analysts, etc.]
   **Prerequisites**: [Required knowledge, tools, permissions]
   **Estimated Time**: [X hours/days]
   **Difficulty**: [Easy/Moderate/Advanced]

   ## Prerequisites Checklist
   - [ ] [Prerequisite 1]
   - [ ] [Prerequisite 2]
   - [ ] [Prerequisite 3]

   ## Process Overview
   [High-level diagram or flowchart]

   1. [Phase 1]: [Purpose] (Time: X)
   2. [Phase 2]: [Purpose] (Time: Y)
   3. [Phase 3]: [Purpose] (Time: Z)

   ## Step-by-Step Instructions

   ### Phase 1: [Name]

   #### Step 1.1: [Action]
   **Purpose**: [Why this step]
   **Input**: [What you need]
   **Output**: [What you produce]

   **Instructions**:
   1. [Detailed action 1]
   2. [Detailed action 2]

   **Code Example**:
   ```python
   # Example implementation
   ```

   **Validation**:
   - [ ] [Check 1]
   - [ ] [Check 2]

   **Common Issues**:
   - **Issue**: [Description]
   - **Solution**: [Fix]

   #### Step 1.2: [Action]
   [Similar structure]

   ### Phase 2: [Name]
   [Similar structure]

   ## Complete Checklist
   - [ ] Phase 1 completed and validated
   - [ ] Phase 2 completed and validated
   - [ ] Phase 3 completed and validated
   - [ ] All tests passing
   - [ ] Documentation updated

   ## Success Criteria
   - [Measurable outcome 1]
   - [Measurable outcome 2]

   ## Troubleshooting

   ### Issue 1: [Title]
   **Symptoms**: [What you see]
   **Cause**: [Why it happens]
   **Solution**: [How to fix]
   **Prevention**: [How to avoid]

   ### Issue 2: [Title]
   [Similar structure]

   ## Best Practices
   1. **[Practice 1]**: [Description and rationale]
   2. **[Practice 2]**: [Description and rationale]

   ## References
   - Code files: [Links]
   - Related guides: [Links]
   - External resources: [Links]
   ```

2. **Checklist Design Principles**:
   - **Atomic**: Each item is a single, clear action
   - **Testable**: Verification criteria are objective
   - **Ordered**: Sequence reflects dependencies
   - **Complete**: No implicit assumptions or hidden steps
   - **Actionable**: Clear who, what, when, where, why

3. **Code Template Guidelines**:
   ```python
   # Template structure
   # 1. Import statements
   # 2. Constants and configuration
   # 3. Helper functions (if needed)
   # 4. Main implementation
   # 5. Validation/testing code
   # 6. Usage example

   # Example: New metric implementation template
   import pandas as pd
   import numpy as np
   from utility.setting import DB_STOCK_TICK

   # Configuration
   METRIC_NAME = 'new_metric'
   LOOKBACK_PERIOD = 20

   def calculate_new_metric(df, period=LOOKBACK_PERIOD):
       """
       Calculate new metric.

       Args:
           df (DataFrame): OHLCV data with columns [시간, 현재가, 시가, 고가, 저가, 거래량]
           period (int): Lookback period for calculation

       Returns:
           DataFrame: Input df with new metric column added

       Example:
           >>> df = load_tick_data('005930')
           >>> df = calculate_new_metric(df, period=20)
           >>> print(df['new_metric'].head())
       """
       # Implementation
       df['new_metric'] = df['현재가'].rolling(window=period).mean()

       # Validation: Check for LOOKAHEAD bias
       assert df['new_metric'].isna().sum() == period - 1, "Unexpected NaN count"

       return df

   # Usage example
   if __name__ == '__main__':
       # Test implementation
       pass
   ```

4. **Integration Checklist Template**:
   ```markdown
   ## Integration Checklist

   ### Database Integration
   - [ ] Database schema defined (see `utility/setting.py`)
   - [ ] Tables created with appropriate indexes
   - [ ] Column data types validated
   - [ ] Migration scripts written and tested
   - [ ] Query functions added to `utility/query.py`
   - [ ] Database integrity check updated (`utility/database_check.py`)

   ### Backend Integration
   - [ ] Core logic implemented in appropriate module
   - [ ] Unit tests written and passing
   - [ ] Integration tests written and passing
   - [ ] Error handling implemented
   - [ ] Logging added for debugging
   - [ ] Performance benchmarks met

   ### UI Integration
   - [ ] UI components designed (mockups approved)
   - [ ] Layout defined in `ui/set_*.py`
   - [ ] Event handlers implemented in `ui/ui_button_clicked_*.py`
   - [ ] Display updates in `ui/ui_update_*.py`
   - [ ] Chart rendering in `ui/ui_draw_*.py` (if applicable)
   - [ ] Styling applied in `ui/set_style.py`
   - [ ] User testing completed

   ### Backtester Integration
   - [ ] Metric calculations added to backtesting engines
   - [ ] Output columns added to result tables
   - [ ] Optimization parameters defined (OR, GAR ranges)
   - [ ] Validation scripts updated
   - [ ] Performance impact assessed (<10% slowdown target)

   ### Documentation Integration
   - [ ] User guide created/updated
   - [ ] API documentation added
   - [ ] Code comments comprehensive
   - [ ] Examples provided
   - [ ] Troubleshooting section added
   - [ ] CLAUDE.md updated (if architectural changes)

   ### Testing & Validation
   - [ ] Unit tests: 80%+ coverage
   - [ ] Integration tests: Critical paths covered
   - [ ] Performance tests: Benchmarks met
   - [ ] User acceptance tests: Passed
   - [ ] Edge cases tested and handled

   ### Deployment
   - [ ] Code review completed
   - [ ] All tests passing in CI/CD
   - [ ] Database backup created
   - [ ] Rollback plan documented
   - [ ] Deployment runbook prepared
   - [ ] Monitoring alerts configured
   ```

### Specialized Guide Types

#### 1. Optimization Workflow Guides
- Grid search parameter tuning
- Genetic algorithm optimization
- Bayesian optimization processes
- Walk-forward validation procedures
- Overfitting detection methods

#### 2. Analysis Methodology Guides
- Statistical significance testing
- Effect size calculations
- Cross-validation techniques
- Sensitivity analysis procedures
- Performance attribution methods

#### 3. Integration Guides
- Database schema integration
- UI component integration
- Process communication setup
- External API integration
- Third-party library integration

#### 4. Verification Guides
- LOOKAHEAD-FREE verification
- Data integrity validation
- Performance validation
- Cross-timeframe compatibility
- Regression testing procedures

#### 5. Development Workflow Guides
- Git branching strategy
- Code review process
- Testing requirements
- Documentation standards
- Deployment procedures

### Best Practices for Guide Writing

1. **Clarity**:
   - Use active voice ("Click the button" not "The button should be clicked")
   - One action per step
   - Avoid jargon or explain technical terms
   - Use consistent terminology throughout

2. **Completeness**:
   - Include all prerequisites explicitly
   - Don't skip "obvious" steps
   - Provide context for each action
   - Link to related documentation
   - Cover edge cases and exceptions

3. **Usability**:
   - Test the guide by following it yourself
   - Have someone unfamiliar with the process review it
   - Include screenshots or diagrams where helpful
   - Provide estimated times for each step
   - Add troubleshooting for common issues

4. **Maintainability**:
   - Use version numbers for referenced tools/libraries
   - Date the guide and note last update
   - Link to code files with line numbers
   - Note when guide needs updating (e.g., "After schema changes")
   - Keep guides in sync with code changes

5. **Actionability**:
   - Every step should be executable
   - Provide exact commands, file paths, values
   - Include validation steps after key actions
   - Offer alternative approaches when appropriate
   - Link to automated scripts when available

### Integration with Other Studies

**With Development/**:
- Guides support implementation plans
- Provide detailed steps for planned features
- Standardize development workflows

**With ResearchReports/**:
- Implement research findings as practical workflows
- Apply optimization methods from research
- Translate theoretical concepts to actionable steps

**With ConditionStudies/**:
- Guide condition analysis processes
- Standardize overfitting assessment
- Provide statistical validation workflows

**With CodeReview/**:
- Review checklist guides for code quality
- Integration verification procedures
- Testing requirement guidelines

**With SystemAnalysis/**:
- Implement improvement proposals as guides
- Document optimization workflows
- Standardize analysis procedures

### Common Guide Topics

**Development Processes**:
- New feature development workflow
- Bug fix process
- Refactoring procedures
- Code review standards
- Git workflow (branching, merging, PRs)

**Testing & Validation**:
- Unit testing guidelines
- Integration testing procedures
- Performance testing methods
- User acceptance testing
- Regression testing workflows

**Optimization & Analysis**:
- Parameter optimization workflows
- Backtesting analysis procedures
- Statistical validation methods
- Performance profiling guides
- Overfitting detection processes

**Integration & Deployment**:
- Database integration steps
- UI component integration
- API integration procedures
- Deployment workflows
- Monitoring setup guides

**Maintenance & Operations**:
- Database maintenance procedures
- Performance monitoring guides
- Log analysis methods
- Backup and recovery procedures
- System health checks

## Dependencies

### Guide Development Tools
- **Diagrams**: draw.io, Mermaid for flowcharts and architecture diagrams
- **Screenshots**: Snipping Tool, Lightshot for UI examples
- **Code Formatting**: Markdown syntax, code block highlighting
- **Validation**: Spell checkers, grammar checkers, technical reviewers
- **Version Control**: Git for tracking guide changes

### STOM Framework Knowledge
- **Architecture**: Multiprocess patterns, queue communication (15 queues)
- **Database**: SQLite schema (15 databases), query patterns
- **UI Framework**: PyQt5 components, signal/slot patterns
- **Trading Logic**: Strategy patterns, backtesting procedures
- **Optimization**: Grid search, genetic algorithms, Optuna

### Development Standards
- **Naming Conventions**: `*_receiver_*.py`, `*_strategy_*.py`, Korean variable names
- **Code Patterns**: Template Method, Strategy, Observer patterns
- **Documentation**: 98.3% guideline compliance target
- **Testing**: Unit tests, integration tests, backtester validation
- **Quality**: Code reviews, linting, type checking

### Domain Expertise
- **Trading Systems**: Strategy development, risk management, execution
- **Korean Market**: Kiwoom API, market rules, conventions
- **Cryptocurrency**: Upbit/Binance APIs, exchange differences
- **Technical Analysis**: Indicator calculations (826 tick variables, 752 minute variables)
- **Backtesting**: LOOKAHEAD-FREE verification, walk-forward validation

### Related Documentation
- **Manual/**: System architecture, module documentation
- **Guideline/**: `Back_Testing_Guideline_Tick.md` (826 variables), `Condition_Document_Template_Guideline.md`
- **Condition/**: 133 condition files for strategy reference
- **Study/**: Research reports, system analysis for background

---

**Last Updated**: 2026-01-19
**Total Documents**: 5 files (13KB + 52KB + 8KB + others)
**Key Topics**: Optimization (826 variables), metric development (10-step process), integration workflows, verification checklists
**Usage**: Practical guidance for development, testing, and deployment tasks
