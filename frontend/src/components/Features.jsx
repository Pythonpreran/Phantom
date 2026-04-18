import { motion } from "framer-motion";
import { Brain, Target, Shield, Zap, Eye, Activity } from "lucide-react";

const features = [
    {
        title: "Multi-layer AI Detection",
        desc: "Stacked neural classifiers correlate signals across network, endpoint, and identity to catch what single models miss.",
        icon: Brain,
    },
    {
        title: "Intelligent Canary System",
        desc: "Adaptive decoys that learn attacker behavior and emit rich, contextualised signals — not noisy alerts.",
        icon: Target,
    },
    {
        title: "Autonomous Threat Containment",
        desc: "Auto-isolate, revoke, and reroute in milliseconds with policy-bound actions — humans stay in the loop, not on the line.",
        icon: Shield,
    },
    {
        title: "Self-Evolving Security",
        desc: "Every incident trains the fusion engine. PHANTOM hardens itself after each encounter — no manual tuning.",
        icon: Zap,
    },
    {
        title: "Explainable AI (SHAP + Playbooks)",
        desc: "Every decision ships with a readable explanation, feature attribution, and the playbook that fired.",
        icon: Eye,
    },
    {
        title: "Real-time SOC Dashboard",
        desc: "A live operational view of the kill chain — threats, containment actions, and model drift in one surface.",
        icon: Activity,
    },
];

const cardVariant = {
    hidden: { opacity: 0, y: 32 },
    show: (i) => ({
        opacity: 1,
        y: 0,
        transition: { delay: 0.15 + i * 0.08, duration: 0.6, ease: [0.22, 1, 0.36, 1] },
    }),
};

export default function Features() {
    return (
        <section id="features" className="landing-section">
            <div className="landing-container">
                {/* Header */}
                <div className="section-header">
                    <motion.div
                        initial={{ opacity: 0, y: 16 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true, margin: "-80px" }}
                        className="section-tag"
                    >
                        // CAPABILITIES
                    </motion.div>
                    <motion.h2
                        initial={{ opacity: 0, y: 16 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true, margin: "-80px" }}
                        transition={{ delay: 0.1, duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
                        className="section-title"
                    >
                        Built for threats that{" "}
                        <span className="accent-green">don't announce themselves.</span>
                    </motion.h2>
                    <motion.p
                        initial={{ opacity: 0, y: 16 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true, margin: "-80px" }}
                        transition={{ delay: 0.2, duration: 0.6 }}
                        className="section-desc"
                    >
                        Six coordinated systems working as one cognitive perimeter.
                    </motion.p>
                </div>

                {/* Grid */}
                <div className="features-grid">
                    {features.map((feature, i) => (
                        <motion.div
                            key={i}
                            custom={i}
                            variants={cardVariant}
                            initial="hidden"
                            whileInView="show"
                            viewport={{ once: true, margin: "-40px" }}
                            className="feature-card"
                        >
                            <span className="feature-index">0{i + 1}</span>
                            <div className="feature-icon-wrap">
                                <feature.icon className="feature-icon" />
                            </div>
                            <h3 className="feature-card-title">{feature.title}</h3>
                            <p className="feature-card-desc">{feature.desc}</p>
                        </motion.div>
                    ))}
                </div>
            </div>
        </section>
    );
}
