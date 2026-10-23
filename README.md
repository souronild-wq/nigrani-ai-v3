# Nigrani AI

Nigrani AI is a Streamlit-based invoice auditing prototype.

## Features
- Single invoice auditing
- Bulk CSV auditing
- High-price and budget-overrun checks
- Invoice total mismatch detection
- Duplicate invoice detection
- Isolation Forest anomaly detection

## Installation and Setup

```powershell
python -m pip install -r requirements.txt
python generate_data.py
python train_model.py
streamlit run app.py
```

## Run Tests

```powershell
python test_duplicates.py
```

## Main Files
- `app.py` - Streamlit dashboard
- `detector.py` - Invoice analysis
- `bulk_audit.py` - Bulk auditing
- `duplicate_detector.py` - Duplicate detection
- `generate_data.py` - Demo data generation
- `train_model.py` - Model training
- `test_duplicates.py` - Duplicate detection tests

## Important
This project uses synthetic demo data. Flagged transactions require manual review and are not proof of fraud.
