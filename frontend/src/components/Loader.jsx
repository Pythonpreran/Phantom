import { motion } from "framer-motion";

const EARTH_URL =
    "https://customer-assets.emergentagent.com/job_39089e7b-866c-46b5-ad35-4282c1d0f834/artifacts/8bjevn7g_Gemini_Generated_Image_p3aelup3aelup3ae.png";

export default function Loader() {
    return (
        <motion.div
            data-testid="loader-screen"
            className="fixed inset-0 z-[100] flex flex-col items-center justify-start overflow-hidden bg-black"
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
        >
            {/* Background radial glow */}
            <motion.div
                className="absolute inset-0 pointer-events-none"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 2 }}
                style={{
                    background:
                        "radial-gradient(ellipse 80% 50% at 50% 90%, rgba(0, 255, 136, 0.15), transparent 70%)",
                }}
            />

            {/* PHANTOM text */}
            <motion.div
                className="relative z-20 w-full flex justify-center"
                initial={{ marginTop: "28vh" }}
                animate={{ marginTop: "20vh" }}
                transition={{ duration: 4.5, ease: [0.22, 1, 0.36, 1] }}
            >
                <motion.h1
                    layoutId="phantom-brand-text"
                    data-testid="loader-phantom-text"
                    className="font-display font-black tracking-[-0.04em] text-white select-none"
                    style={{
                        fontSize: "clamp(4rem, 12vw, 10rem)",
                        textShadow: "0 0 80px rgba(255,255,255,0.3)"
                    }}
                >
                    PHANTOM
                </motion.h1>
            </motion.div>

            {/* Status line */}
            <motion.div
                className="relative z-20 mt-6 flex items-center gap-3 font-mono text-[10px] uppercase tracking-[0.35em] text-[#00FF88]/80"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: [0, 1, 0.9, 0], y: 0 }}
                transition={{ duration: 4.5, times: [0, 0.2, 0.55, 0.9] }}
            >
                <span className="inline-block w-2 h-2 rounded-full bg-[#00FF88] animate-pulse" />
                Initializing secure perimeter
            </motion.div>

            {/* Earth image */}
            <motion.div
                className="absolute inset-x-0 pointer-events-none"
                style={{ top: "40vh", height: "100vh", overflow: "hidden" }}
                initial={{ opacity: 0, scale: 1.04, y: 30 }}
                animate={{ opacity: [0, 1, 1, 0.5], scale: 1, y: 0 }}
                transition={{ duration: 4.5, ease: "easeOut", times: [0, 0.35, 0.8, 1] }}
            >
                <img
                    src={EARTH_URL}
                    alt="Earth"
                    className="select-none block"
                    style={{
                        width: "100vw",
                        height: "auto",
                        maxWidth: "none",
                        maskImage: "linear-gradient(to bottom, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 80%)",
                        WebkitMaskImage: "linear-gradient(to bottom, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 80%)"
                    }}
                    draggable={false}
                />
            </motion.div>

            {/* Skip hint */}
            <motion.div
                data-testid="loader-skip-hint"
                className="absolute bottom-6 right-6 z-20 font-mono text-[10px] uppercase tracking-[0.3em] text-white/30"
                initial={{ opacity: 0 }}
                animate={{ opacity: [0, 0, 0.7] }}
                transition={{ duration: 4.5, times: [0, 0.5, 1] }}
            >
                click / scroll to skip
            </motion.div>

            {/* Top progress bar */}
            <motion.div
                className="absolute top-0 left-0 h-[2px] bg-gradient-to-r from-transparent via-[#00FF88] to-transparent z-20"
                initial={{ width: "0%" }}
                animate={{ width: "100%" }}
                transition={{ duration: 4.8, ease: "linear" }}
            />
        </motion.div>
    );
}
