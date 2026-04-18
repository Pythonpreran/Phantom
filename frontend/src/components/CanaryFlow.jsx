import { motion } from "framer-motion";
import { Zap, Layers, GitBranch, AlertTriangle, Crosshair } from "lucide-react";

const ease = [0.22, 1, 0.36, 1];

const steps = [
    { id: "01", icon: Zap, title: "Trigger", desc: "DECOY INTERACTION" },
    { id: "02", icon: Layers, title: "Context", desc: "ENTITY + SESSION" },
    { id: "03", icon: GitBranch, title: "Pattern", desc: "TTP MATCH" },
    { id: "04", icon: AlertTriangle, title: "Risk", desc: "SCORE + SEVERITY" },
    { id: "05", icon: Crosshair, title: "Action", desc: "CONTAIN / DECEIVE" },
];

export default function CanaryFlow() {
    return (
        <section id="canary-flow" className="landing-section">
            <div className="landing-container">
                {/* Header */}
                <div className="section-header">
                    <motion.div
                        initial={{ opacity: 0, y: 16 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true, margin: "-80px" }}
                        className="section-tag"
                    >
                        // INTELLIGENT CANARY
                    </motion.div>
                    <motion.h2
                        initial={{ opacity: 0, y: 16 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true, margin: "-80px" }}
                        transition={{ delay: 0.1, duration: 0.7, ease }}
                        className="section-title"
                    >
                        Beyond canary tokens —{" "}
                        <span className="accent-green">intelligent threat signals.</span>
                    </motion.h2>
                    <motion.p
                        initial={{ opacity: 0, y: 16 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true, margin: "-80px" }}
                        transition={{ delay: 0.2, duration: 0.6 }}
                        className="section-desc"
                    >
                        Every decoy interaction becomes a rich behavioural story. PHANTOM transforms tripwires into reasoning primitives.
                    </motion.p>
                </div>

                {/* Flow steps */}
                <div className="canary-flow-wrap">
                    {/* Horizontal connector */}
                    <div className="canary-connector-bg" />
                    <motion.div
                        initial={{ scaleX: 0 }}
                        whileInView={{ scaleX: 1 }}
                        viewport={{ once: true, margin: "-80px" }}
                        transition={{ duration: 1.2, ease: "easeInOut", delay: 0.3 }}
                        className="canary-connector-active"
                    />

                    <div className="canary-steps">
                        {steps.map((step, i) => (
                            <motion.div
                                key={step.id}
                                initial={{ opacity: 0, y: 24 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true, margin: "-80px" }}
                                transition={{ delay: 0.3 + i * 0.12, duration: 0.6, ease }}
                                className="canary-step"
                            >
                                <div className="canary-node">
                                    <div className="canary-ring canary-ring--outer" />
                                    <div className="canary-ring canary-ring--inner" />
                                    <step.icon size={18} className="canary-node-icon" />
                                    <span className="canary-step-num">{step.id}</span>
                                </div>
                                <h4 className="canary-step-title">{step.title}</h4>
                                <p className="canary-step-desc">{step.desc}</p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </div>
        </section>
    );
}
