import { motion } from "framer-motion";
import { Terminal, Play, BookOpen } from "lucide-react";

const ease = [0.22, 1, 0.36, 1];

const logLines = [
    { time: "00:00.012", action: "trigger", detail: "canary.s3::decoy-bucket", color: "#00FF88" },
    { time: "00:00.034", action: "analyze", detail: "fusion::correlate(endpoint, identity)", color: "#8B9BB4" },
    { time: "00:00.088", action: "critical", detail: "model.v4.cortex::score=0.971", color: "#FF4F4F" },
    { time: "00:00.142", action: "explain", detail: "shap::top_features → [exfil_rate, anomalous_region]", color: "#00FF88" },
    { time: "00:00.214", action: "contain", detail: "playbook::ISO-EXFIL-07 engaged", color: "#8B9BB4" },
    { time: "00:00.267", action: "action", detail: "session.revoked + token.rotated", color: "#00FF88" },
    { time: "00:00.311", action: "evolve", detail: "learning::weights updated (+0.0042)", color: "#8B9BB4" },
];

export default function Demo() {
    return (
        <section id="demo" className="landing-section">
            <div className="landing-container">
                <div className="demo-grid">
                    {/* Left side text */}
                    <div className="demo-text">
                        <motion.div
                            initial={{ opacity: 0, y: 16 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true, margin: "-80px" }}
                            className="section-tag"
                            style={{ display: "flex", alignItems: "center", gap: "8px" }}
                        >
                            <Terminal size={14} />
                            // Live Demo
                        </motion.div>

                        <motion.h2
                            initial={{ opacity: 0, y: 16 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true, margin: "-80px" }}
                            transition={{ delay: 0.1, duration: 0.7, ease }}
                            className="section-title demo-title"
                        >
                            Watch PHANTOM contain a live exfiltration in{" "}
                            <span className="accent-green">267ms.</span>
                        </motion.h2>

                        <motion.p
                            initial={{ opacity: 0, y: 16 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true, margin: "-80px" }}
                            transition={{ delay: 0.2, duration: 0.6 }}
                            className="section-desc"
                        >
                            Real trace from the SOC console — trigger to containment, with the explanation baked in. No handoffs. No waiting rooms.
                        </motion.p>

                        <motion.div
                            initial={{ opacity: 0, y: 16 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true, margin: "-80px" }}
                            transition={{ delay: 0.3, duration: 0.6 }}
                            className="demo-btns"
                        >
                            <button className="demo-btn-play">
                                <Play size={14} style={{ fill: "black" }} />
                                Play walkthrough
                            </button>
                            <button className="demo-btn-docs">
                                <BookOpen size={14} />
                                Read the docs
                            </button>
                        </motion.div>
                    </div>

                    {/* Terminal window */}
                    <motion.div
                        initial={{ opacity: 0, x: 32 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true, margin: "-80px" }}
                        transition={{ delay: 0.3, duration: 0.8, ease }}
                        className="demo-terminal-wrap"
                    >
                        <div className="demo-terminal">
                            {/* Header */}
                            <div className="demo-terminal-header">
                                <div className="demo-dots">
                                    <span className="demo-dot demo-dot--red" />
                                    <span className="demo-dot demo-dot--yellow" />
                                    <span className="demo-dot demo-dot--green" />
                                </div>
                                <div className="demo-terminal-title">
                                    phantom.soc <span className="demo-sep">|</span>{" "}
                                    <span className="demo-trace">trace-0471</span>
                                </div>
                                <div className="demo-live-badge">
                                    <span className="demo-live-dot" />
                                    <span>LIVE</span>
                                </div>
                            </div>

                            {/* Body */}
                            <div className="demo-terminal-body">
                                {logLines.map((log, i) => (
                                    <motion.div
                                        key={i}
                                        initial={{ opacity: 0, x: -10 }}
                                        whileInView={{ opacity: 1, x: 0 }}
                                        viewport={{ once: true }}
                                        transition={{ delay: 0.4 + i * 0.12, duration: 0.45, ease }}
                                        className="demo-log-line"
                                    >
                                        <span className="demo-log-time">{log.time}</span>
                                        <span className="demo-log-action" style={{ color: log.color }}>{log.action}</span>
                                        <span className="demo-log-detail">{log.detail}</span>
                                    </motion.div>
                                ))}

                                {/* Result */}
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    whileInView={{ opacity: 1 }}
                                    viewport={{ once: true }}
                                    transition={{ delay: 1.5, duration: 0.5 }}
                                    className="demo-result"
                                >
                                    <div className="demo-result-header">
                                        <span className="demo-result-label">THREAT NEUTRALISED · 267ms</span>
                                        <span className="demo-result-shap">explainability: SHAP ✓</span>
                                    </div>
                                    <div className="demo-progress-track">
                                        <motion.div
                                            initial={{ width: "0%" }}
                                            whileInView={{ width: "100%" }}
                                            viewport={{ once: true }}
                                            transition={{ delay: 1.5, duration: 0.6, ease }}
                                            className="demo-progress-bar"
                                        />
                                    </div>
                                </motion.div>
                            </div>
                        </div>

                        {/* Glow effect */}
                        <div className="demo-terminal-glow" />
                    </motion.div>
                </div>
            </div>
        </section>
    );
}
