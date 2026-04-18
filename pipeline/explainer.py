"""
PHANTOM Module 5  --  SHAP Explainer + Phi-3 LLM Playbook
========================================================
SHAP: Identifies which input features caused the anomaly.
Phi-3: Generates plain-English playbooks via Ollama (local, offline).
"""

import os
import traceback
import numpy as np
import torch

# Optional SHAP import (may not be available in all environments)
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("[Explainer] WARNING: SHAP not available. Using fallback feature attribution.")

# Optional Ollama import
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("[Explainer] WARNING: Ollama not available. Using template playbooks.")


FEATURE_NAMES = [
    # Network (0-10)
    "bytes_out", "bytes_in", "duration", "dst_port", "src_port",
    "tcp_flags", "protocol", "packet_rate", "conn_count",
    "dst_ip_hash", "src_ip_hash",
    # Application (11-20)
    "status_code", "payload_size", "method", "geo_country",
    "endpoint", "user_agent", "req_per_min", "auth_age",
    "session_hash", "role",
    # Endpoint (21-30)
    "cpu_pct", "mem_mb", "process_name", "parent_pid", "file_path",
    "registry_key", "child_proc_count", "net_connections", "file_writes",
    "user_hash",
    # Derived (31)
    "zone_trust",
]


class PhantomExplainer:
    """
    Produces human-readable explanations for anomaly detections.
    Part A: SHAP feature attribution (or fallback gradient-based)
    Part B: Phi-3 LLM playbook generation (or template fallback)
    """

    def __init__(self, models: dict = None, background_data: np.ndarray = None):
        """
        models: dict of {layer_name: SpecialistAutoencoder}
        background_data: numpy array of ~200 benign samples for SHAP baseline
        """
        self.models = models or {}
        self.explainers = {}
        self.ollama_model = "phi3"
        self._ollama_tested = False
        self._ollama_works = False

        # Initialize SHAP explainers if available
        if SHAP_AVAILABLE and background_data is not None and models:
            self._init_shap(background_data)

    def _init_shap(self, background_data: np.ndarray):
        """Build SHAP DeepExplainers for each model."""
        try:
            bg_tensor = torch.tensor(background_data[:200], dtype=torch.float32)
            for layer_name, model in self.models.items():
                model.eval()
                self.explainers[layer_name] = shap.DeepExplainer(model, bg_tensor)
            print(f"[Explainer] SHAP initialized for {list(self.explainers.keys())}")
        except Exception as e:
            print(f"[Explainer] SHAP init failed, using fallback: {e}")

    def explain_alert(self, event: dict, detection: dict) -> list:
        """
        Returns top-3 contributing features as [(feature_name, contribution_pct), ...].
        Uses SHAP if available, otherwise uses gradient-based attribution.
        """
        layer = event.get("layer", "")
        vec = event.get("normalized_vector")
        if vec is None:
            return [("unknown", 1.0)]

        # Try SHAP first
        if layer in self.explainers:
            try:
                x = torch.tensor([vec], dtype=torch.float32)
                shap_values = self.explainers[layer].shap_values(x)
                abs_vals = np.abs(shap_values[0][0]) if isinstance(shap_values, list) else np.abs(shap_values[0])
                total = abs_vals.sum()
                if total < 1e-8:
                    total = 1.0
                contributions = {
                    FEATURE_NAMES[i]: float(abs_vals[i] / total)
                    for i in range(min(len(FEATURE_NAMES), len(abs_vals)))
                }
                top_3 = sorted(contributions.items(), key=lambda x: x[1], reverse=True)[:3]
                return top_3
            except Exception:
                pass

        # Fallback: gradient-based feature attribution
        return self._gradient_attribution(event, detection)

    def _gradient_attribution(self, event: dict, detection: dict) -> list:
        """Fallback feature attribution using reconstruction error per dimension."""
        layer = event.get("layer", "")
        vec = event.get("normalized_vector")
        if vec is None or layer not in self.models:
            return [("unknown_feature", 1.0)]

        model = self.models[layer]
        x = torch.tensor([vec], dtype=torch.float32)

        with torch.no_grad():
            recon = model(x)
            per_dim_error = ((x - recon) ** 2).squeeze().numpy()

        total = per_dim_error.sum()
        if total < 1e-8:
            total = 1.0

        contributions = {
            FEATURE_NAMES[i]: float(per_dim_error[i] / total)
            for i in range(min(len(FEATURE_NAMES), len(per_dim_error)))
        }
        top_3 = sorted(contributions.items(), key=lambda x: x[1], reverse=True)[:3]
        return top_3

    def generate_playbook(self, alert_context: dict) -> str:
        """
        Generate a plain-English playbook for the SOC analyst.
        Uses Phi-3 via Ollama if available, otherwise uses templates.
        """
        # Test Ollama connectivity once
        if not self._ollama_tested:
            self._test_ollama()

        if self._ollama_works:
            return self._llm_playbook(alert_context)
        else:
            return self._template_playbook(alert_context)

    def _test_ollama(self):
        """Test if Ollama + Phi-3 is available."""
        self._ollama_tested = True
        if not OLLAMA_AVAILABLE:
            self._ollama_works = False
            return
        try:
            resp = ollama.chat(
                model=self.ollama_model,
                messages=[{"role": "user", "content": "Reply with OK"}],
            )
            if resp and resp.get("message", {}).get("content"):
                self._ollama_works = True
                print("[Explainer] Phi-3 via Ollama: ONLINE ✓")
            else:
                self._ollama_works = False
        except Exception:
            self._ollama_works = False
            print("[Explainer] Phi-3 unavailable  --  using template playbooks.")

    def _llm_playbook(self, ctx: dict) -> str:
        """Generate playbook via Phi-3."""
        shap_str = ", ".join(
            f"{feat} ({pct:.0%})" for feat, pct in ctx.get("shap_top3", [])
        )

        prompt = f"""You are a SOC analyst assistant. An AI security system raised an alert.

IP Address: {ctx.get('ip', 'unknown')}
User ID: {ctx.get('user_id', 'unknown')}
MITRE Technique: {ctx.get('mitre_id', '')}  --  {ctx.get('mitre_name', '')}
Kill Chain Stage: {ctx.get('stage', '')} ({ctx.get('stage_num', 0)}/5)
Layers triggered: {', '.join(ctx.get('layers_triggered', []))}
Network Zone: {ctx.get('zone', 'unknown')} (Trust: {ctx.get('zone_trust', 'unknown')})
Top contributing features: {shap_str}
Anomaly Score: {ctx.get('anomaly_score', 0):.2f}x above baseline
Severity: {ctx.get('severity', 'UNKNOWN')}

Write exactly:
1. A 2-sentence plain-English explanation of WHY this was flagged (no jargon)
2. A numbered 5-step remediation playbook for the SOC analyst
3. A one-line false-positive check the analyst should perform before acting

Be specific. Use the feature names and values above."""

        try:
            response = ollama.chat(
                model=self.ollama_model,
                messages=[{"role": "user", "content": prompt}],
            )
            return response["message"]["content"]
        except Exception as e:
            return self._template_playbook(ctx) + f"\n\n[LLM Error: {e}]"

    def _template_playbook(self, ctx: dict) -> str:
        """Fallback template-based playbook when Ollama is unavailable."""
        ip = ctx.get("ip", "unknown")
        user_id = ctx.get("user_id", "unknown")
        mitre_id = ctx.get("mitre_id", "")
        mitre_name = ctx.get("mitre_name", "")
        stage = ctx.get("stage", "UNKNOWN")
        severity = ctx.get("severity", "UNKNOWN")
        score = ctx.get("anomaly_score", 0)
        layers = ", ".join(ctx.get("layers_triggered", []))
        zone = ctx.get("zone", "unknown")
        shap_top3 = ctx.get("shap_top3", [])

        shap_str = ", ".join(f"{f} ({p:.0%})" for f, p in shap_top3) if shap_top3 else "N/A"

        templates = {
            "INITIAL_ACCESS": f"""⚠️ WHY FLAGGED:
Identity {user_id} at IP {ip} triggered {mitre_id} ({mitre_name}). Top anomaly signals: {shap_str}. Anomaly score {score:.1f}x above baseline across {layers}  --  consistent with brute-force credential attack.

📋 REMEDIATION PLAYBOOK:
1. Block IP {ip} at the perimeter firewall immediately
2. Reset all passwords for accounts targeted by this identity in the past 2 hours  
3. Check auth logs for any status 200 after repeated 401 sequences
4. Preserve all logs to /var/log/auth.log for forensic chain of custody
5. Scan for lateral movement originating from {ip} on internal subnets

🔍 FALSE POSITIVE CHECK:
Verify whether {ip} belongs to an automated test suite, load balancer, or CI/CD pipeline before blocking.""",

            "EXECUTION": f"""⚠️ WHY FLAGGED:
Identity {user_id} at IP {ip} spawned suspicious processes matching {mitre_id} ({mitre_name}). Anomaly signal driven by {shap_str}. Score: {score:.1f}x above baseline in zone {zone}.

📋 REMEDIATION PLAYBOOK:
1. Isolate the endpoint associated with {ip} from the network immediately
2. Capture memory dump and running process list before remediation
3. Identify the parent process chain that spawned the suspicious executable
4. Scan the endpoint for persistence mechanisms (registry, scheduled tasks)
5. Re-image the endpoint if compromise is confirmed

🔍 FALSE POSITIVE CHECK:
Verify if the process was launched by a legitimate admin script or IT deployment tool.""",

            "LATERAL_MOVEMENT": f"""⚠️ WHY FLAGGED:
Identity {user_id} at IP {ip} is probing internal targets across network zones ({zone}). {mitre_id} ({mitre_name}) detected with anomaly score {score:.1f}x. Key signals: {shap_str}.

📋 REMEDIATION PLAYBOOK:
1. Block all traffic from {ip} to internal subnets at the microsegmentation layer
2. Audit all authentication events from {user_id} across all systems
3. Check for credential dumping activity on the source endpoint
4. Review SMB/RDP/WinRM logs for successful connections from {ip}
5. Activate incident response protocol and notify the SOC lead

🔍 FALSE POSITIVE CHECK:
Confirm {user_id} is not an IT admin performing authorized maintenance across zones.""",

            "EXFILTRATION": f"""🚨 WHY FLAGGED:
Identity {user_id} at IP {ip} is exfiltrating data  --  {mitre_id} ({mitre_name}). Massive data transfer detected: {shap_str}. Severity: {severity}. Score: {score:.1f}x.

📋 REMEDIATION PLAYBOOK:
1. IMMEDIATELY sever network connection for {ip}
2. Identify and preserve all files accessed in the past 24 hours by {user_id}
3. Determine the external destination of the data transfer
4. Engage the legal team if PII/regulated data was involved
5. Initiate full forensic investigation and preserve evidence chain

🔍 FALSE POSITIVE CHECK:
Check if {user_id} was running an authorized backup, data migration, or cloud sync job.""",
        }

        # Default template
        default = f"""⚠️ WHY FLAGGED:
Identity {user_id} at IP {ip} triggered anomaly detection ({mitre_id}  --  {mitre_name}). Stage: {stage}. Key signals: {shap_str}. Anomaly score: {score:.1f}x above baseline.

📋 REMEDIATION PLAYBOOK:
1. Investigate all recent activity from {ip} and {user_id}
2. Check for indicators of compromise on the associated endpoint
3. Review network flows for suspicious external connections
4. Escalate to Tier 2 if attack progression continues
5. Document all findings for incident report

🔍 FALSE POSITIVE CHECK:
Verify if this activity matches any known scheduled tasks or authorized operations."""

        return templates.get(stage, default)
