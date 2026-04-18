export default function Footer() {
    return (
        <footer className="landing-footer">
            <div className="footer-glow" />

            <div className="landing-container footer-grid">
                <div className="footer-brand-col">
                    <div className="footer-brand">PHANTOM</div>
                    <p className="footer-tagline">
                        An autonomous, self-evolving AI cybersecurity system. Cognitive perimeter for modern threat landscapes.
                    </p>
                </div>

                <div className="footer-link-col">
                    <h4 className="footer-col-title">// Product</h4>
                    <ul className="footer-links">
                        <li><a href="#features">Features</a></li>
                        <li><a href="#how-it-works">How it works</a></li>
                        <li><a href="#demo">Demo</a></li>
                    </ul>
                </div>

                <div className="footer-link-col">
                    <h4 className="footer-col-title">// Company</h4>
                    <ul className="footer-links">
                        <li><a href="#about">About</a></li>
                        <li><a href="#contact">Contact</a></li>
                        <li><a href="#careers">Careers</a></li>
                    </ul>
                </div>
            </div>

            <div className="landing-container footer-bottom">
                <p className="footer-copy">© 2026 PHANTOM AI · All rights reserved</p>
                <div className="footer-status">
                    <span className="footer-status-dot" />
                    <span>Systems Operational</span>
                </div>
            </div>
        </footer>
    );
}
