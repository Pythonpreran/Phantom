import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import Loader from "@/components/Loader";
import Landing from "@/components/Landing";

export default function Home() {
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const t = setTimeout(() => setLoading(false), 5000);
        return () => clearTimeout(t);
    }, []);

    // Skip loader on click or scroll
    useEffect(() => {
        if (!loading) return;
        const skip = () => setLoading(false);
        window.addEventListener("click", skip);
        window.addEventListener("wheel", skip, { passive: true });
        window.addEventListener("touchstart", skip, { passive: true });
        window.addEventListener("keydown", skip);
        return () => {
            window.removeEventListener("click", skip);
            window.removeEventListener("wheel", skip);
            window.removeEventListener("touchstart", skip);
            window.removeEventListener("keydown", skip);
        };
    }, [loading]);

    return (
        <div className="App">
            <div className="noise-overlay" />
            <AnimatePresence mode="wait">
                {loading ? (
                    <Loader key="loader" />
                ) : (
                    <motion.div
                        key="landing"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ duration: 0.8 }}
                    >
                        <Landing />
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
