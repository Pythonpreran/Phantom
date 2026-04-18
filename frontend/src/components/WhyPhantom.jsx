import { motion } from "framer-motion";
import { X, Check } from "lucide-react";

const ease = [0.22, 1, 0.36, 1];

export default function WhyPhantom() {
    return (
        <section id="why-phantom" className="landing-section">
            <div className="landing-container">
                {/* Header */}
                <div className="section-header">
                    <motion.div
                        initial={{ opacity: 0, y: 16 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true, margin: "-80px" }}
                        className="section-tag"
                    >
                        // WHY PHANTOM
                    </motion.div>
                    <motion.h2
                        initial={{ opacity: 0, y: 16 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true, margin: "-80px" }}
                        transition={{ delay: 0.1, duration: 0.7, ease }}
                        className="section-title"
                    >
                        Legacy stacks alert.<br />
                        <span className="accent-green">PHANTOM decides.</span>
                    </motion.h2>
                </div>

                {/* Comparison cards */}
                <div className="why-grid">
                    {/* Legacy Card */}
                    <motion.div
                        initial={{ opacity: 0, x: -28 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true, margin: "-80px" }}
                        transition={{ duration: 0.7, ease }}
                        className="why-card why-card--legacy"
                    >
                        <div className="why-card-header">
                            <span className="section-tag" style={{ marginBottom: 0 }}>// TRADITIONAL SOC</span>
                            <span className="why-badge why-badge--legacy">LEGACY</span>
                        </div>
                        <h3 className="why-card-title why-card-title--legacy">Alerts without action</h3>
                        <ul className="why-list">
                            {[
                                "Alerts only — no action",
                                "No context or reasoning",
                                "Manual triage & response",
                                "Static rules, periodic updates",
                                "Isolated signal silos",
                            ].map((item, i) => (
                                <li key={i} className="why-list-item">
                                    <span className="why-icon why-icon--red">
                                        <X size={12} />
                                    </span>
                                    <span>{item}</span>
                                </li>
                            ))}
                        </ul>
                    </motion.div>

                    {/* Phantom Card */}
                    <motion.div
                        initial={{ opacity: 0, x: 28 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true, margin: "-80px" }}
                        transition={{ delay: 0.15, duration: 0.7, ease }}
                        className="why-card why-card--active"
                    >
                        <div className="why-card-header">
                            <span className="section-tag" style={{ marginBottom: 0, color: "#00FF88" }}>// PHANTOM</span>
                            <span className="why-badge why-badge--active">ACTIVE</span>
                        </div>
                        <h3 className="why-card-title">Decisions, not alerts</h3>
                        <ul className="why-list">
                            {[
                                "AI-driven intelligence loop",
                                "Context-aware decisioning",
                                "Autonomous response in ms",
                                "Self-evolving models",
                                "Fusion across every layer",
                            ].map((item, i) => (
                                <li key={i} className="why-list-item">
                                    <span className="why-icon why-icon--green">
                                        <Check size={12} />
                                    </span>
                                    <span>{item}</span>
                                </li>
                            ))}
                        </ul>
                    </motion.div>
                </div>
            </div>
        </section>
    );
}
