import { motion } from "framer-motion";
import { ArrowRight, Play } from "lucide-react";
import { useNavigate } from "react-router-dom";

const EARTH_URL =
    "https://customer-assets.emergentagent.com/job_39089e7b-866c-46b5-ad35-4282c1d0f834/artifacts/8bjevn7g_Gemini_Generated_Image_p3aelup3aelup3ae.png";

/* Shared easing for all entrance anims */
const ease = [0.22, 1, 0.36, 1];
const up = (delay = 0) => ({
    initial: { opacity: 0, y: 28 },
    animate: { opacity: 1, y: 0 },
    transition: { delay, duration: 0.75, ease },
});

export default function Hero() {
    const navigate = useNavigate();

    const scrollTo = (id) => {
        const el = document.getElementById(id);
        if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    };

    return (
        <section
            id="top"
            data-testid="hero-section"
            className="hero-section"
        >
            {/* Cyber-grid background */}
            <div className="hero-grid-bg" />

            {/* Radial glows */}
            <div className="hero-radial-glow" />

            {/* Scanline */}
            <div className="hero-scanline-wrap">
                <motion.div
                    className="hero-scanline"
                    animate={{ top: ["0%", "100%"] }}
                    transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
                />
            </div>

            {/* Earth globe — bottom of hero, fades into black */}
            <motion.div
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6, duration: 1.4, ease }}
                style={{
                    position: "absolute",
                    bottom: 0,
                    left: 0,
                    right: 0,
                    height: "60%",
                    pointerEvents: "none",
                    zIndex: 2,
                    overflow: "hidden",
                }}
            >
                <img
                    src={EARTH_URL}
                    alt="Earth"
                    className="earth-fade"
                    draggable={false}
                    style={{
                        width: "100%",
                        height: "auto",
                        display: "block",
                        objectFit: "cover",
                        objectPosition: "top center",
                        userSelect: "none",
                    }}
                />
            </motion.div>

            {/* Content — sits above earth (z-index: 10) */}
            <div className="landing-container hero-content">
                {/* Badge */}
                <motion.div {...up(0.2)} className="hero-badge">
                    <span className="hero-badge-dot-wrap">
                        <span className="hero-badge-dot-ping" />
                        <span className="hero-badge-dot" />
                    </span>
                    System online — v4.0 Cortex
                </motion.div>

                {/* Main heading */}
                <motion.h1
                    layoutId="phantom-brand-text"
                    data-testid="hero-phantom-text"
                    className="hero-title"
                    initial={{ opacity: 0, scale: 0.96 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 1, delay: 0.1, ease }}
                >
                    PHANTOM
                </motion.h1>

                {/* Glowing underline */}
                <motion.div
                    initial={{ scaleX: 0, opacity: 0 }}
                    animate={{ scaleX: 1, opacity: 1 }}
                    transition={{ delay: 0.5, duration: 0.8, ease }}
                    className="hero-underline"
                />

                {/* Subtitle */}
                <motion.p {...up(0.5)} data-testid="hero-subtitle" className="hero-subtitle">
                    An AI-powered cybersecurity system that{" "}
                    <strong>detects</strong>,{" "}
                    <strong>explains</strong>, and{" "}
                    <strong>stops threats</strong> in
                    real time — while continuously evolving with every signal.
                </motion.p>

                {/* CTA */}
                <motion.div {...up(0.7)} className="hero-cta-row">
                    <button
                        data-testid="hero-get-started-btn"
                        onClick={() => navigate("/login")}
                        className="hero-btn-primary"
                    >
                        Login / Sign Up
                        <ArrowRight className="hero-btn-icon" />
                    </button>
                    <button
                        data-testid="hero-view-demo-btn"
                        onClick={() => scrollTo("demo")}
                        className="hero-btn-secondary"
                    >
                        <Play className="hero-btn-icon" />
                        View Demo
                    </button>
                </motion.div>

                {/* Stats */}
                <motion.div {...up(1.0)} className="hero-stats">
                    {[
                        { v: "< 12ms", l: "Detection latency" },
                        { v: "99.97%", l: "Threat recall" },
                        { v: "24/7", l: "Autonomous ops" },
                        { v: "SHAP", l: "Explainable AI" },
                    ].map((m) => (
                        <div key={m.l} className="hero-stat-card">
                            <div className="hero-stat-value">{m.v}</div>
                            <div className="hero-stat-label">{m.l}</div>
                        </div>
                    ))}
                </motion.div>
            </div>
        </section>
    );
}

