import { motion } from "framer-motion";
import { Database, BrainCircuit, Network, Target, ShieldAlert, RefreshCw } from "lucide-react";

const ease = [0.22, 1, 0.36, 1];

const pipelineSteps = [
    { num: "01", title: "Data Ingestion", desc: "Universal intake from syslog, network, identity, and cloud flows.", icon: Database },
    { num: "02", title: "AI Detection", desc: "Stacked anomaly models evaluate stateful behavioral patterns.", icon: BrainCircuit },
    { num: "03", title: "Fusion Engine", desc: "Cross-correlates layer signals into high-confidence threat contexts.", icon: Network },
    { num: "04", title: "Canary Intelligence", desc: "Integrates telemetry from active decoys and honeytokens.", icon: Target },
    { num: "05", title: "Autonomous Response", desc: "Playbook-bound execution across API layers in real-time.", icon: ShieldAlert },
    { num: "06", title: "Learning Loop", desc: "Every response feeds the models; weights continuously update.", icon: RefreshCw },
];

export default function HowItWorks() {
    return (
        <section id="how-it-works" className="landing-section">
            <div className="landing-container">
                {/* Header */}
                <div className="section-header">
                    <motion.div
                        initial={{ opacity: 0, y: 16 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true, margin: "-80px" }}
                        className="section-tag"
                    >
                        // PIPELINE
                    </motion.div>
                    <motion.h2
                        initial={{ opacity: 0, y: 16 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true, margin: "-80px" }}
                        transition={{ delay: 0.1, duration: 0.7, ease }}
                        className="section-title"
                    >
                        How PHANTOM thinks.
                    </motion.h2>
                    <motion.p
                        initial={{ opacity: 0, y: 16 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true, margin: "-80px" }}
                        transition={{ delay: 0.2, duration: 0.6 }}
                        className="section-desc"
                    >
                        A zero-trust processing pipeline. From intake to action in milliseconds.
                    </motion.p>
                </div>

                {/* Pipeline */}
                <div className="pipeline-wrap">
                    {/* Vertical connector */}
                    <div className="pipeline-line-bg" />
                    <motion.div
                        initial={{ height: "0%" }}
                        whileInView={{ height: "100%" }}
                        viewport={{ once: true, margin: "-80px" }}
                        transition={{ duration: 1.5, ease: "anticipate", delay: 0.4 }}
                        className="pipeline-line-active"
                    />

                    <div className="pipeline-steps">
                        {pipelineSteps.map((step, i) => (
                            <motion.div
                                key={step.num}
                                initial={{ opacity: 0, x: -28 }}
                                whileInView={{ opacity: 1, x: 0 }}
                                viewport={{ once: true, margin: "-60px" }}
                                transition={{ delay: 0.15 + i * 0.12, duration: 0.6, ease }}
                                className="pipeline-step"
                            >
                                <div className="pipeline-icon-wrap">
                                    <span className="pipeline-step-num">{step.num}</span>
                                    <step.icon size={20} className="pipeline-icon" />
                                </div>
                                <div className="pipeline-step-text">
                                    <h3 className="pipeline-step-title">{step.title}</h3>
                                    <p className="pipeline-step-desc">{step.desc}</p>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </div>
        </section>
    );
}
