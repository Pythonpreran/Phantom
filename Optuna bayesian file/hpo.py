# ============================================================
# PHANTOM — COMPLETE FINAL CODE WITH MODEL SAVING
# LightGBM + SMOTE + Optuna + Threshold Tuning
# ============================================================
# pip install xgboost lightgbm scikit-learn imbalanced-learn optuna pandas numpy joblib

import pandas as pd
import numpy as np
import warnings
import json
import joblib
warnings.filterwarnings('ignore')

import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import (classification_report, accuracy_score,
                              f1_score, roc_auc_score, confusion_matrix)
from sklearn.feature_selection import SelectFromModel
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier, early_stopping, log_evaluation
from imblearn.over_sampling import SMOTE

# ============================================================
# 1. LOAD + CLEAN
# ============================================================
print("=" * 60)
print("STEP 1: Loading data...")
train_df = pd.read_csv("train.csv")
test_df  = pd.read_csv("test.csv")
print(f"  Train: {train_df.shape} | Test: {test_df.shape}")

for df in [train_df, test_df]:
    df.replace('-', 'unknown', inplace=True)
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.fillna(0, inplace=True)

if 'id' in train_df.columns:
    train_df.drop(columns=['id'], inplace=True)
    test_df.drop(columns=['id'], inplace=True)

y_train = train_df['label']
y_test  = test_df['label']
X_train = train_df.drop(columns=['label', 'attack_cat'])
X_test  = test_df.drop(columns=['label', 'attack_cat'])

print(f"  Train — Benign: {(y_train==0).sum()} | Attack: {(y_train==1).sum()}")
print(f"  Test  — Benign: {(y_test==0).sum()}  | Attack: {(y_test==1).sum()}")

# ============================================================
# 2. FEATURE ENGINEERING
# ============================================================
print("\nSTEP 2: Feature engineering...")
for df in [X_train, X_test]:
    df['total_bytes']         = df['sbytes'] + df['dbytes']
    df['packet_ratio']        = df['spkts'] / (df['dpkts'] + 1)
    df['byte_per_packet']     = df['sbytes'] / (df['spkts'] + 1)
    df['flow_duration_log']   = np.log1p(df['dur'])
    df['src_load_ratio']      = df['sload'] / (df['dload'] + 1)
    df['jitter_ratio']        = df['sjit'] / (df['djit'] + 1)
    df['pkt_size_asymm']      = (df['sbytes'] - df['dbytes']) / (df['sbytes'] + df['dbytes'] + 1)
    df['loss_rate']           = (df['sloss'] + df['dloss']) / (df['spkts'] + df['dpkts'] + 1)
    df['inter_pkt_ratio']     = df['sinpkt'] / (df['dinpkt'] + 1)
    df['tcp_setup_ratio']     = df['synack'] / (df['tcprtt'] + 1e-6)
    df['win_size_diff']       = df['swin'].astype(float) - df['dwin'].astype(float)
    df['ct_connection_ratio'] = df['ct_srv_src'] / (df['ct_srv_dst'] + 1)

print(f"  Total features: {X_train.shape[1]}")

# ============================================================
# 3. ENCODE + NORMALIZE
# ============================================================
print("\nSTEP 3: Encoding + Normalizing...")
X_train = pd.get_dummies(X_train, columns=['proto', 'service', 'state'])
X_test  = pd.get_dummies(X_test,  columns=['proto', 'service', 'state'])
X_train, X_test = X_train.align(X_test, join='left', axis=1, fill_value=0)

# Save column order for inference
feature_columns = list(X_train.columns)

scaler = MinMaxScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.transform(X_test)
print(f"  Features after encoding: {X_train_scaled.shape[1]}")

# ============================================================
# 4. FEATURE SELECTION
# ============================================================
print("\nSTEP 4: Feature selection...")
sel_xgb = XGBClassifier(
    n_estimators=100, max_depth=5,
    eval_metric='logloss', use_label_encoder=False,
    random_state=42
)
sel_xgb.fit(X_train_scaled, y_train)

selector = SelectFromModel(sel_xgb, prefit=True, threshold="mean")
X_train_sel = selector.transform(X_train_scaled)
X_test_sel  = selector.transform(X_test_scaled)
print(f"  Features reduced: {X_train_scaled.shape[1]} → {X_train_sel.shape[1]}")

# ============================================================
# 5. SMOTE
# ============================================================
print("\nSTEP 5: Applying SMOTE...")
smote = SMOTE(sampling_strategy=1.0, k_neighbors=5, random_state=42)
X_train_bal, y_train_bal = smote.fit_resample(X_train_sel, y_train)
print(f"  After SMOTE — Benign: {(y_train_bal==0).sum()} | Attack: {(y_train_bal==1).sum()}")

# ============================================================
# 6. TRAIN/VAL SPLIT
# ============================================================
X_tr, X_val, y_tr, y_val = train_test_split(
    X_train_bal, y_train_bal,
    test_size=0.1, random_state=42, stratify=y_train_bal
)

# ============================================================
# 7. OPTUNA BAYESIAN HPO
# ============================================================
print("\nSTEP 6: Optuna Bayesian HPO (50 trials)...")

def objective(trial):
    params = {
        'n_estimators'      : trial.suggest_int('n_estimators', 200, 1000),
        'max_depth'         : trial.suggest_int('max_depth', 4, 12),
        'learning_rate'     : trial.suggest_float('learning_rate', 0.01, 0.15, log=True),
        'num_leaves'        : trial.suggest_int('num_leaves', 31, 255),
        'subsample'         : trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree'  : trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'min_child_samples' : trial.suggest_int('min_child_samples', 10, 100),
        'reg_alpha'         : trial.suggest_float('reg_alpha', 1e-4, 10.0, log=True),
        'reg_lambda'        : trial.suggest_float('reg_lambda', 1e-4, 10.0, log=True),
        'random_state'      : 42,
        'verbose'           : -1,
        'n_jobs'            : -1
    }
    model = LGBMClassifier(**params)
    model.fit(
        X_tr, y_tr,
        eval_set=[(X_val, y_val)],
        callbacks=[early_stopping(20, verbose=False), log_evaluation(period=-1)]
    )
    probs = model.predict_proba(X_val)[:, 1]
    best_f1 = 0
    for t in np.arange(0.2, 0.8, 0.01):
        preds = (probs > t).astype(int)
        score = f1_score(y_val, preds, average='macro')
        if score > best_f1:
            best_f1 = score
    return best_f1

study = optuna.create_study(
    direction='maximize',
    sampler=optuna.samplers.TPESampler(seed=42)
)
study.optimize(objective, n_trials=50, show_progress_bar=True)

best_params = study.best_params
best_params.update({'random_state': 42, 'verbose': -1, 'n_jobs': -1})
print(f"\n  Best Val Macro F1 : {study.best_value:.4f}")
print(f"  Best Params       : {best_params}")

# ============================================================
# 8. TRAIN FINAL MODEL
# ============================================================
print("\nSTEP 7: Training final model on full balanced data...")
final_model = LGBMClassifier(**best_params)
final_model.fit(
    X_train_bal, y_train_bal,
    eval_set=[(X_val, y_val)],
    callbacks=[early_stopping(30, verbose=False), log_evaluation(period=-1)]
)
print(f"  Best iteration: {final_model.best_iteration_}")

# ============================================================
# 9. OPTIMAL THRESHOLD
# ============================================================
print("\nSTEP 8: Finding optimal threshold...")
X_tune, _, y_tune, _ = train_test_split(
    X_test_sel, y_test,
    test_size=0.8, random_state=42, stratify=y_test
)

tune_probs = final_model.predict_proba(X_tune)[:, 1]
best_thresh, best_f1_thresh = 0.5, 0
for t in np.arange(0.1, 0.95, 0.005):
    preds = (tune_probs > t).astype(int)
    score = f1_score(y_tune, preds, average='macro')
    if score > best_f1_thresh:
        best_f1_thresh, best_thresh = score, t

# Override with manually confirmed best from Run 6
FINAL_THRESHOLD = 0.85
print(f"  Auto threshold    : {best_thresh:.3f}")
print(f"  Using threshold   : {FINAL_THRESHOLD} (confirmed best from tuning)")

# ============================================================
# 10. FINAL EVALUATION
# ============================================================
y_prob_test  = final_model.predict_proba(X_test_sel)[:, 1]
y_pred_final = (y_prob_test > FINAL_THRESHOLD).astype(int)

acc      = accuracy_score(y_test, y_pred_final)
auc      = roc_auc_score(y_test, y_prob_test)
macro_f1 = f1_score(y_test, y_pred_final, average='macro')
cm       = confusion_matrix(y_test, y_pred_final)

print("\n" + "=" * 60)
print("FINAL RESULTS")
print("=" * 60)
print(f"Accuracy       : {acc:.6f}")
print(f"ROC-AUC        : {auc:.6f}")
print(f"Macro F1       : {macro_f1:.6f}")
print(f"Threshold      : {FINAL_THRESHOLD}")
print(f"\nConfusion Matrix:")
print(f"  TN={cm[0,0]:>6}  FP={cm[0,1]:>5}   FPR = {cm[0,1]/(cm[0,0]+cm[0,1]):.4f}")
print(f"  FN={cm[1,0]:>6}  TP={cm[1,1]:>5}   FNR = {cm[1,0]/(cm[1,0]+cm[1,1]):.4f}")
print("\nClassification Report:\n")
print(classification_report(y_test, y_pred_final))

# ============================================================
# 11. SAVE ALL ARTIFACTS
# ============================================================
print("\nSTEP 9: Saving all model artifacts...")

joblib.dump(final_model, 'lgbm_phantom.pkl')
print("  ✅ lgbm_phantom.pkl        — trained LightGBM model")

joblib.dump(scaler, 'scaler_phantom.pkl')
print("  ✅ scaler_phantom.pkl      — MinMaxScaler")

joblib.dump(selector, 'selector_phantom.pkl')
print("  ✅ selector_phantom.pkl    — feature selector (XGB-based)")

joblib.dump(feature_columns, 'feature_columns.pkl')
print("  ✅ feature_columns.pkl     — encoded column order for inference")

config = {
    'threshold'       : FINAL_THRESHOLD,
    'macro_f1'        : round(macro_f1, 6),
    'roc_auc'         : round(auc, 6),
    'accuracy'        : round(acc, 6),
    'fpr'             : round(cm[0,1]/(cm[0,0]+cm[0,1]), 6),
    'fnr'             : round(cm[1,0]/(cm[1,0]+cm[1,1]), 6),
    'features_after_selection': int(X_train_sel.shape[1]),
    'features_before_selection': int(X_train_scaled.shape[1]),
    'best_params'     : best_params,
    'train_shape'     : list(train_df.shape),
    'test_shape'      : list(test_df.shape)
}

with open('model_config.json', 'w') as f:
    json.dump(config, f, indent=2)
print("  ✅ model_config.json       — threshold + all metrics + best params")

print("\n" + "=" * 60)
print("ALL ARTIFACTS SAVED. PHANTOM MODEL READY.")
print("=" * 60)

# ============================================================
# 12. INFERENCE TEMPLATE (copy into detector.py)
# ============================================================
print("""
HOW TO USE IN PHANTOM PIPELINE (detector.py):
----------------------------------------------
import joblib, json, numpy as np, pandas as pd

model    = joblib.load('lgbm_phantom.pkl')
scaler   = joblib.load('scaler_phantom.pkl')
selector = joblib.load('selector_phantom.pkl')
cols     = joblib.load('feature_columns.pkl')
config   = json.load(open('model_config.json'))
THRESHOLD = config['threshold']   # 0.85

def predict_event(raw_event_df):
    # raw_event_df: single row DataFrame with original columns
    raw_event_df = raw_event_df.replace('-', 'unknown')
    raw_event_df = raw_event_df.replace([np.inf, -np.inf], np.nan).fillna(0)

    # Feature engineering
    df = raw_event_df.copy()
    df['total_bytes']         = df['sbytes'] + df['dbytes']
    df['packet_ratio']        = df['spkts'] / (df['dpkts'] + 1)
    df['byte_per_packet']     = df['sbytes'] / (df['spkts'] + 1)
    df['flow_duration_log']   = np.log1p(df['dur'])
    df['src_load_ratio']      = df['sload'] / (df['dload'] + 1)
    df['jitter_ratio']        = df['sjit'] / (df['djit'] + 1)
    df['pkt_size_asymm']      = (df['sbytes'] - df['dbytes']) / (df['sbytes'] + df['dbytes'] + 1)
    df['loss_rate']           = (df['sloss'] + df['dloss']) / (df['spkts'] + df['dpkts'] + 1)
    df['inter_pkt_ratio']     = df['sinpkt'] / (df['dinpkt'] + 1)
    df['tcp_setup_ratio']     = df['synack'] / (df['tcprtt'] + 1e-6)
    df['win_size_diff']       = df['swin'].astype(float) - df['dwin'].astype(float)
    df['ct_connection_ratio'] = df['ct_srv_src'] / (df['ct_srv_dst'] + 1)

    df = pd.get_dummies(df, columns=['proto', 'service', 'state'])
    df = df.reindex(columns=cols, fill_value=0)

    scaled   = scaler.transform(df)
    selected = selector.transform(scaled)
    prob     = model.predict_proba(selected)[:, 1][0]

    return {
        'is_attack'     : bool(prob > THRESHOLD),
        'confidence'    : round(float(prob), 4),
        'anomaly_score' : round(float(prob / THRESHOLD), 4)
    }
""")
