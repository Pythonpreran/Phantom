import { useEffect } from "react";
import Hero from "@/components/Hero";
import Features from "@/components/Features";
import WhyPhantom from "@/components/WhyPhantom";
import CanaryFlow from "@/components/CanaryFlow";
import HowItWorks from "@/components/HowItWorks";
import Demo from "@/components/Demo";
import Footer from "@/components/Footer";

export default function Landing() {
    /* Smooth-scroll when clicking an in‑page anchor */
    useEffect(() => {
        const handler = (e) => {
            const href = e.target.closest("a")?.getAttribute("href");
            if (href?.startsWith("#")) {
                e.preventDefault();
                document.getElementById(href.slice(1))?.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        };
        document.addEventListener("click", handler);
        return () => document.removeEventListener("click", handler);
    }, []);

    return (
        <div
            data-testid="landing-page"
            className="landing-root"
        >
            {/* ── Navbar ─────────────────────────────────── */}
            <header className="landing-nav">
                <div className="landing-container landing-nav-inner">
                    <a href="#top" className="nav-brand">
                        <span className="nav-brand-icon">
                            <span className="nav-brand-shield" />
                        </span>
                        PHANTOM
                    </a>

                    <nav className="nav-links">
                        <a href="#features">Features</a>
                        <a href="#why-phantom">Why PHANTOM</a>
                        <a href="#how-it-works">How it works</a>
                        <a href="#demo">Demo</a>
                    </nav>

                    <div className="nav-auth">
                        <a href="/login" className="nav-login">Login</a>
                        <a href="/login?mode=signup" className="nav-signup">Sign Up</a>
                    </div>
                </div>
            </header>

            {/* ── Sections ───────────────────────────────── */}
            <main>
                <Hero />
                <Features />
                <WhyPhantom />
                <CanaryFlow />
                <HowItWorks />
                <Demo />
            </main>

            <Footer />
        </div>
    );
}
