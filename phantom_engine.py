"""
╔══════════════════════════════════════════════════════════════════════╗
║  PHANTOM — Proactive Hybrid Anomaly & Threat Management Ops Net    ║
║  Full-Stack AI-Driven Cybersecurity Detection & Response Engine     ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import os
import time
import json
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════
#  STEP 1 — DATA HANDLING MODULE
# ═══════════════════════════════════════════════════════════════════

class DataHandler:
    """Loads, cleans, and prepares the UNSW-NB15 dataset."""

    @staticmethod
    def load_and_clean(filepath):
        """Load CSV, replace missing markers, drop irrelevant cols."""
        print(f"  [DATA] Loading {filepath}...")
        df = pd.read_csv(filepath, low_memory=False)
        # Replace dash-style missing values
        df.replace('-', 'unknown', inplace=True)
        df.replace(' ', 'unknown', inplace=True)
        # Drop ID column if present
        if 'id' in df.columns:
            df.drop('id', axis=1, inplace=True)
        # Strip whitespace from attack_cat
        if 'attack_cat' in df.columns:
            df['attack_cat'] = df['attack_cat'].astype(str).str.strip()
        print(f"  [DATA] Shape: {df.shape}  |  Columns: {len(df.columns)}")
        return df

    @staticmethod
    def separate_features_labels(df):
        """Split into features (X) and label (y)."""
        y = df['label'].astype(int)
        attack_cat = df['attack_cat'] if 'attack_cat' in df.columns else None
        X = df.drop(['label', 'attack_cat'], axis=1, errors='ignore')
        return X, y, attack_cat


# ═══════════════════════════════════════════════════════════════════
#  STEP 2 — FEATURE ENGINEERING MODULE
# ═══════════════════════════════════════════════════════════════════

class FeatureEngineer:
    """Creates behavioral features, one-hot encodes, aligns & scales."""

    CATEGORICAL_COLS = ['proto', 'service', 'state']

    @staticmethod
    def add_behavioral_features(df):
        """Add cross-layer behavioral signals (12 derived features from Optuna HPO pipeline)."""
        df = df.copy()
        # Ensure numeric types for arithmetic
        numeric_cols = ['sbytes', 'dbytes', 'spkts', 'dpkts', 'dur', 'sload',
                        'dload', 'sjit', 'djit', 'sloss', 'dloss', 'sinpkt',
                        'dinpkt', 'synack', 'tcprtt', 'swin', 'dwin',
                        'ct_srv_src', 'ct_srv_dst']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
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
        return df

    @staticmethod
    def encode_and_align(X_train, X_test):
        """One-hot encode categorical columns & align columns."""
        X_train = pd.get_dummies(X_train, columns=FeatureEngineer.CATEGORICAL_COLS, dtype=int)
        X_test = pd.get_dummies(X_test, columns=FeatureEngineer.CATEGORICAL_COLS, dtype=int)
        # Align columns — fill missing with 0
        X_train, X_test = X_train.align(X_test, join='left', axis=1, fill_value=0)
        return X_train, X_test

    @staticmethod
    def scale_features(X_train, X_test):
        """MinMax scale all numeric features."""
        # Coerce all columns to numeric
        X_train = X_train.apply(pd.to_numeric, errors='coerce').fillna(0)
        X_test = X_test.apply(pd.to_numeric, errors='coerce').fillna(0)

        scaler = MinMaxScaler()
        X_train_scaled = pd.DataFrame(
            scaler.fit_transform(X_train),
            columns=X_train.columns,
            index=X_train.index
        )
        X_test_scaled = pd.DataFrame(
            scaler.transform(X_test),
            columns=X_test.columns,
            index=X_test.index
        )
        return X_train_scaled, X_test_scaled, scaler


# ═══════════════════════════════════════════════════════════════════
#  STEP 3 — DETECTION ENGINE (Optuna-Tuned LightGBM)
# ═══════════════════════════════════════════════════════════════════

class DetectionEngine:
    """LightGBM-based primary threat detection engine (Optuna HPO tuned)."""

    OPTUNA_DIR = os.path.join(os.path.dirname(__file__), 'Optuna bayesian file')
    MODEL_PATH = os.path.join(OPTUNA_DIR, 'lgbm_phantom.pkl')
    SCALER_PATH = os.path.join(OPTUNA_DIR, 'scaler_phantom.pkl')
    SELECTOR_PATH = os.path.join(OPTUNA_DIR, 'selector_phantom.pkl')
    FEATURE_COLS_PATH = os.path.join(OPTUNA_DIR, 'feature_columns.pkl')
    CONFIG_PATH = os.path.join(OPTUNA_DIR, 'model_config.json')

    def __init__(self):
        self.model = None
        self.scaler = None
        self.selector = None
        self.feature_columns = None
        self.threshold = 0.85

    def train(self, X_train, y_train):
        """Training is done offline via hpo.py. This just loads the pre-trained model."""
        print("  [DETECT] Training is done offline via Optuna HPO (hpo.py).")
        print("  [DETECT] Loading pre-trained LightGBM model instead...")
        self.load()

    def predict(self, X_test, threshold=None):
        """Predict attack probabilities & apply threshold."""
        if threshold is None:
            threshold = self.threshold

        # Apply feature selection if selector is loaded
        if self.selector is not None:
            X_selected = self.selector.transform(X_test)
        else:
            X_selected = X_test

        probas = self.model.predict_proba(X_selected)[:, 1]
        preds = (probas > threshold).astype(int)
        return preds, probas

    def load(self):
        """Load the Optuna-tuned LightGBM model and pipeline artifacts."""
        if not os.path.exists(self.MODEL_PATH):
            print(f"  [DETECT] LightGBM model not found at {self.MODEL_PATH}")
            return False

        self.model = joblib.load(self.MODEL_PATH)
        print(f"  [DETECT] Loaded LightGBM model from {self.MODEL_PATH}")

        if os.path.exists(self.SELECTOR_PATH):
            self.selector = joblib.load(self.SELECTOR_PATH)
            print(f"  [DETECT] Loaded feature selector")

        if os.path.exists(self.FEATURE_COLS_PATH):
            self.feature_columns = joblib.load(self.FEATURE_COLS_PATH)
            print(f"  [DETECT] Loaded feature columns ({len(self.feature_columns)} features)")

        if os.path.exists(self.CONFIG_PATH):
            with open(self.CONFIG_PATH, 'r') as f:
                config = json.load(f)
            self.threshold = config.get('threshold', 0.85)
            print(f"  [DETECT] Threshold={self.threshold}, "
                  f"Macro-F1={config.get('macro_f1', 'N/A')}, "
                  f"ROC-AUC={config.get('roc_auc', 'N/A')}")

        return True


# ═══════════════════════════════════════════════════════════════════
#  STEP 4 — CORRELATION ENGINE
# ═══════════════════════════════════════════════════════════════════

class CorrelationEngine:
    """Groups consecutive attack detections into attack sessions."""

    @staticmethod
    def correlate(predictions, probabilities, attack_cats=None, min_group_size=3):
        """
        Group consecutive attack predictions into sessions.
        Returns list of dicts with group metadata.
        """
        groups = []
        current_group = []
        current_probas = []
        current_cats = []

        for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
            if pred == 1:
                current_group.append(i)
                current_probas.append(prob)
                if attack_cats is not None:
                    current_cats.append(str(attack_cats.iloc[i]))
            else:
                if len(current_group) >= min_group_size:
                    groups.append({
                        'group_id': len(groups) + 1,
                        'indices': current_group,
                        'size': len(current_group),
                        'probabilities': current_probas,
                        'attack_types': current_cats if current_cats else ['unknown']
                    })
                current_group = []
                current_probas = []
                current_cats = []

        # Final group
        if len(current_group) >= min_group_size:
            groups.append({
                'group_id': len(groups) + 1,
                'indices': current_group,
                'size': len(current_group),
                'probabilities': current_probas,
                'attack_types': current_cats if current_cats else ['unknown']
            })

        print(f"  [CORRELATE] Found {len(groups)} attack session(s) from {sum(predictions)} detections")
        return groups


# ═══════════════════════════════════════════════════════════════════
#  STEP 5 — DECISION ENGINE
# ═══════════════════════════════════════════════════════════════════

class DecisionEngine:
    """Assigns severity & interprets correlated attack groups."""

    @staticmethod
    def assess(groups):
        """Compute avg confidence, assign severity, classify attack type."""
        decisions = []
        for g in groups:
            avg_conf = np.mean(g['probabilities'])
            max_conf = np.max(g['probabilities'])
            unique_types = list(set(t for t in g['attack_types'] if t not in ['Normal', 'unknown', 'nan', '']))

            # Severity classification
            if avg_conf > 0.85:
                severity = 'CRITICAL'
            elif avg_conf > 0.75:
                severity = 'HIGH'
            else:
                severity = 'MEDIUM'

            # Attack interpretation
            if len(unique_types) > 1:
                interpretation = 'MULTI-STAGE ATTACK'
            elif len(unique_types) == 1:
                interpretation = f'SINGLE ATTACK: {unique_types[0]}'
            else:
                interpretation = 'UNKNOWN ATTACK PATTERN'

            decisions.append({
                **g,
                'avg_confidence': round(avg_conf, 4),
                'max_confidence': round(max_conf, 4),
                'severity': severity,
                'interpretation': interpretation,
                'unique_attack_types': unique_types
            })

        print(f"  [DECIDE] Assessed {len(decisions)} threat group(s)")
        return decisions


# ═══════════════════════════════════════════════════════════════════
#  STEP 6 — RESPONSE ENGINE
# ═══════════════════════════════════════════════════════════════════

class ResponseEngine:
    """Simulates automated defensive actions based on severity."""

    @staticmethod
    def respond(decisions):
        """Generate response actions for each threat group."""
        responses = []
        for d in decisions:
            if d['severity'] == 'CRITICAL':
                action = '🔴 BLOCK IP + ISOLATE SYSTEM — Immediate containment'
                action_code = 'BLOCK_AND_ISOLATE'
            elif d['severity'] == 'HIGH':
                action = '🟠 BLOCK IP — Network-level mitigation'
                action_code = 'BLOCK_IP'
            else:
                action = '🟡 MONITOR — Enhanced surveillance activated'
                action_code = 'MONITOR'

            responses.append({
                **d,
                'response_action': action,
                'action_code': action_code,
                'timestamp': datetime.now().isoformat()
            })

        return responses


# ═══════════════════════════════════════════════════════════════════
#  STEP 7 — EVALUATION MODULE
# ═══════════════════════════════════════════════════════════════════

class Evaluator:
    """Model evaluation with comprehensive metrics."""

    @staticmethod
    def evaluate(y_true, y_pred, y_proba=None):
        """Compute and print accuracy, classification report, confusion matrix."""
        acc = accuracy_score(y_true, y_pred)
        report = classification_report(y_true, y_pred, target_names=['Normal', 'Attack'], output_dict=True)
        cm = confusion_matrix(y_true, y_pred)
        report_text = classification_report(y_true, y_pred, target_names=['Normal', 'Attack'])

        return {
            'accuracy': acc,
            'report': report,
            'report_text': report_text,
            'confusion_matrix': cm.tolist(),
            'total_samples': len(y_true),
            'total_attacks_true': int(sum(y_true)),
            'total_attacks_pred': int(sum(y_pred))
        }


# ═══════════════════════════════════════════════════════════════════
#  SYNTHETIC LOG GENERATOR (for live dashboard streaming)
# ═══════════════════════════════════════════════════════════════════

class SyntheticLogGenerator:
    """Generates realistic synthetic network events for streaming."""

    PROTOS = ['tcp', 'udp', 'icmp', 'arp', 'ospf']
    SERVICES = ['http', 'ftp', 'ssh', 'dns', 'smtp', 'ssl', 'unknown', 'pop3', 'snmp', 'ftp-data']
    STATES = ['FIN', 'CON', 'INT', 'REQ', 'ACC', 'ECO', 'RST']
    ATTACK_CATS = ['Normal', 'Exploits', 'Fuzzers', 'DoS', 'Reconnaissance',
                   'Backdoor', 'Shellcode', 'Worms', 'Analysis', 'Generic']

    @staticmethod
    def generate_event(attack_probability=0.3):
        """Generate a single synthetic network event."""
        is_attack = np.random.random() < attack_probability

        if is_attack:
            attack_cat = np.random.choice(SyntheticLogGenerator.ATTACK_CATS[1:])
            dur = np.random.exponential(2.0)
            sbytes = int(np.random.exponential(5000))
            dbytes = int(np.random.exponential(3000))
            spkts = int(np.random.randint(2, 200))
            dpkts = int(np.random.randint(0, 100))
            rate = np.random.uniform(0.1, 500)
            sttl = int(np.random.choice([31, 62, 254]))
        else:
            attack_cat = 'Normal'
            dur = np.random.exponential(0.8)
            sbytes = int(np.random.exponential(800))
            dbytes = int(np.random.exponential(500))
            spkts = int(np.random.randint(2, 30))
            dpkts = int(np.random.randint(0, 20))
            rate = np.random.uniform(5, 100)
            sttl = int(np.random.choice([62, 254, 252]))

        event = {
            'timestamp': datetime.now().isoformat(),
            'dur': round(dur, 6),
            'proto': np.random.choice(SyntheticLogGenerator.PROTOS, p=[0.6, 0.25, 0.05, 0.05, 0.05]),
            'service': np.random.choice(SyntheticLogGenerator.SERVICES),
            'state': np.random.choice(SyntheticLogGenerator.STATES),
            'spkts': spkts,
            'dpkts': dpkts,
            'sbytes': sbytes,
            'dbytes': dbytes,
            'rate': round(rate, 4),
            'sttl': sttl,
            'dttl': int(np.random.choice([0, 29, 252, 254])),
            'sload': round(np.random.exponential(10000), 2),
            'dload': round(np.random.exponential(5000), 2),
            'sloss': int(np.random.randint(0, 20)),
            'dloss': int(np.random.randint(0, 15)),
            'sinpkt': round(np.random.exponential(100), 4),
            'dinpkt': round(np.random.exponential(80), 4),
            'sjit': round(np.random.exponential(3000), 4),
            'djit': round(np.random.exponential(200), 4),
            'swin': int(np.random.choice([0, 255])),
            'stcpb': int(np.random.randint(0, 2**31 - 1)),
            'dtcpb': int(np.random.randint(0, 2**31 - 1)),
            'dwin': int(np.random.choice([0, 255])),
            'tcprtt': round(np.random.exponential(0.1), 6),
            'synack': round(np.random.exponential(0.05), 6),
            'ackdat': round(np.random.exponential(0.05), 6),
            'smean': int(sbytes / max(spkts, 1)),
            'dmean': int(dbytes / max(dpkts, 1)),
            'trans_depth': int(np.random.choice([0, 1, 2, 3])),
            'response_body_len': int(np.random.exponential(500)),
            'ct_srv_src': int(np.random.randint(1, 30)),
            'ct_state_ttl': int(np.random.choice([0, 1, 2, 6])),
            'ct_dst_ltm': int(np.random.randint(1, 15)),
            'ct_src_dport_ltm': int(np.random.randint(1, 15)),
            'ct_dst_sport_ltm': int(np.random.randint(1, 5)),
            'ct_dst_src_ltm': int(np.random.randint(1, 40)),
            'is_ftp_login': 0,
            'ct_ftp_cmd': 0,
            'ct_flw_http_mthd': int(np.random.choice([0, 1])),
            'ct_src_ltm': int(np.random.randint(1, 15)),
            'ct_srv_dst': int(np.random.randint(1, 40)),
            'is_sm_ips_ports': 0,
            'attack_cat': attack_cat,
            'label': 1 if is_attack else 0,
            'total_bytes': sbytes + dbytes,
            'packet_ratio': round(spkts / (dpkts + 1), 4)
        }
        return event


# ═══════════════════════════════════════════════════════════════════
#  MAIN PIPELINE ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════

def run_phantom_pipeline(train_path='train.csv', test_path='test.csv', retrain=False):
    """
    Execute the full PHANTOM pipeline:
    Data → Feature Engineering → Detection → Correlation → Decision → Response
    """
    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║   P H A N T O M   —   Security Operations Pipeline            ║")
    print("║   Proactive Hybrid Anomaly & Threat Management Ops Network    ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()

    # ── Step 1: Data Handling ──
    print("━" * 60)
    print("  STEP 1 │ DATA HANDLING")
    print("━" * 60)
    train_df = DataHandler.load_and_clean(train_path)
    test_df = DataHandler.load_and_clean(test_path)

    X_train, y_train, _ = DataHandler.separate_features_labels(train_df)
    X_test, y_test, attack_cats_test = DataHandler.separate_features_labels(test_df)

    # ── Step 2: Feature Engineering ──
    print()
    print("━" * 60)
    print("  STEP 2 │ FEATURE ENGINEERING")
    print("━" * 60)
    X_train = FeatureEngineer.add_behavioral_features(X_train)
    X_test = FeatureEngineer.add_behavioral_features(X_test)
    print(f"  [FEAT] Added 12 behavioral features (HPO pipeline)")

    X_train, X_test = FeatureEngineer.encode_and_align(X_train, X_test)
    print(f"  [FEAT] One-hot encoded: proto, service, state")
    print(f"  [FEAT] Aligned columns: {X_train.shape[1]} features")

    X_train_s, X_test_s, scaler = FeatureEngineer.scale_features(X_train, X_test)
    print(f"  [FEAT] MinMaxScaler applied")

    # ── Step 3: Detection Engine ──
    print()
    print("━" * 60)
    print("  STEP 3 │ DETECTION ENGINE (LightGBM + Optuna HPO)")
    print("━" * 60)
    engine = DetectionEngine()

    if not retrain and engine.load():
        print("  [DETECT] Using pre-trained LightGBM model")
    else:
        engine.train(X_train_s, y_train)

    predictions, probabilities = engine.predict(X_test_s)
    print(f"  [DETECT] Predictions: {sum(predictions)} attacks / {len(predictions)} total")

    # ── Step 4: Correlation Engine ──
    print()
    print("━" * 60)
    print("  STEP 4 │ CORRELATION ENGINE")
    print("━" * 60)
    groups = CorrelationEngine.correlate(predictions, probabilities, attack_cats_test)

    # ── Step 5: Decision Engine ──
    print()
    print("━" * 60)
    print("  STEP 5 │ DECISION ENGINE")
    print("━" * 60)
    decisions = DecisionEngine.assess(groups)

    for d in decisions[:10]:  # Show first 10
        print(f"    Group #{d['group_id']}: {d['severity']:8s} | "
              f"Conf={d['avg_confidence']:.2%} | "
              f"Size={d['size']:4d} | "
              f"{d['interpretation']}")

    # ── Step 6: Response Engine ──
    print()
    print("━" * 60)
    print("  STEP 6 │ RESPONSE ENGINE")
    print("━" * 60)
    responses = ResponseEngine.respond(decisions)

    for r in responses[:10]:
        print(f"    Group #{r['group_id']}: {r['response_action']}")

    # ── Step 7: Evaluation ──
    print()
    print("━" * 60)
    print("  STEP 7 │ EVALUATION")
    print("━" * 60)
    metrics = Evaluator.evaluate(y_test, predictions)

    print(f"\n  ✅ ACCURACY: {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
    print(f"\n  Classification Report:")
    print(metrics['report_text'])
    print(f"  Confusion Matrix:")
    cm = np.array(metrics['confusion_matrix'])
    print(f"    TN={cm[0,0]:6d}  FP={cm[0,1]:6d}")
    print(f"    FN={cm[1,0]:6d}  TP={cm[1,1]:6d}")

    # ── Summary ──
    print()
    print("═" * 60)
    severity_counts = {}
    for r in responses:
        severity_counts[r['severity']] = severity_counts.get(r['severity'], 0) + 1
    print(f"  PHANTOM SUMMARY")
    print(f"  ├─ Total test samples:    {metrics['total_samples']:,}")
    print(f"  ├─ True attacks:          {metrics['total_attacks_true']:,}")
    print(f"  ├─ Predicted attacks:     {metrics['total_attacks_pred']:,}")
    print(f"  ├─ Accuracy:              {metrics['accuracy']*100:.2f}%")
    print(f"  ├─ Correlated groups:     {len(responses)}")
    for sev, cnt in sorted(severity_counts.items()):
        print(f"  │   └─ {sev}: {cnt}")
    print(f"  └─ Pipeline status:       ✅ OPERATIONAL")
    print("═" * 60)

    return {
        'metrics': metrics,
        'responses': responses,
        'predictions': predictions,
        'probabilities': probabilities,
        'scaler': scaler,
        'model': engine
    }


if __name__ == '__main__':
    base = os.path.dirname(os.path.abspath(__file__))
    run_phantom_pipeline(
        train_path=os.path.join(base, 'train.csv'),
        test_path=os.path.join(base, 'test.csv'),
        retrain=True
    )
