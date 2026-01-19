<!-- Parent: ../AGENTS.md -->
# backtester/analysis_enhanced

## Purpose
Advanced analysis with enhanced metrics, machine learning integration, and comprehensive validation. Extends base analysis with ML-powered filters, ensemble methods, and statistical validation.

## Key Files
- `ml.py` - Machine learning model integration (prediction, training)
- `config.py` - Configuration management for enhanced analysis
- `thresholds.py` - Threshold optimization algorithms
- `plotting.py` - Enhanced visualization tools
- `filters.py` - Filter logic and application
- `metrics_enhanced.py` - Extended metrics calculations
- `utils.py` - Utility functions
- `stats.py` - Statistical analysis tools
- `advanced_analysis.py` - Advanced analytical methods
- `ensemble_filter.py` - Ensemble filter combinations
- `feature_selection.py` - Feature importance and selection
- `validation_enhanced.py` - Enhanced validation framework
- `validate_new_modules.py` - Module validation
- `analysis_logger.py` - Logging system
- `exports.py` - Export enhanced results
- `segment.py` - Segment-based analysis

## Subdirectories
- `models/strategies/` - Trained ML models organized by strategy hash
  - Each strategy has: `latest_ml_bundle.joblib`, `latest_ml_bundle_meta.json`, `strategy_code.txt`
  - `runs/` subdirectory contains historical model versions
  - `runs_index.jsonl` tracks all training runs

## For AI Agents
When working with enhanced analysis:
1. ML models stored in `models/strategies/{strategy_hash}/` with metadata
2. Use `ml.py` for training and prediction with joblib serialization
3. `ensemble_filter.py` combines multiple filter approaches
4. `feature_selection.py` identifies most important trading signals
5. Validation framework in `validation_enhanced.py` prevents overfitting
6. All models include metadata: timestamp, metrics, feature names
7. `thresholds.py` optimizes entry/exit thresholds using ML predictions
8. Logger outputs to `_log/` directory with detailed analysis traces

## Model Persistence
- Strategy identified by SHA256 hash of code
- `latest_ml_bundle.joblib` - Most recent model
- `runs/` - Historical versions with timestamps
- `runs_index.jsonl` - Searchable run history

## Dependencies
- scikit-learn - ML models (RandomForest, etc.)
- joblib - Model serialization
- optuna - Hyperparameter tuning
- numpy/pandas - Data processing
- All dependencies from `backtester/analysis/`
