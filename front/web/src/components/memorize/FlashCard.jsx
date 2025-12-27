import { motion, useMotionValue, useTransform } from "framer-motion";
import { useRef } from "react";

const cardStyle = {
  width: "320px",
  height: "420px",
  borderRadius: "16px",
  background: "white",
  boxShadow: "0 10px 30px rgba(0,0,0,0.15)",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  userSelect: "none",
  cursor: "grab"
};

export default function FlashCard({ children, onPass, onFail, onTap }) {
  const x = useMotionValue(0);
  const dragged = useRef(false);

  const rotate = useTransform(x, [-200, 200], [-15, 15]);

  function handleDragStart() {
    dragged.current = false;
  }

  function handleDrag(_, info) {
    if (Math.abs(info.offset.x) > 10) dragged.current = true;
  }

  function handleDragEnd(_, info) {
    if (info.offset.x > 120 && onPass) onPass();
    else if (info.offset.x < -120 && onFail) onFail();
  }

  function handleClick() {
    if (!dragged.current && onTap) onTap();
  }

  return (
    <motion.div
      drag="x"
      dragConstraints={{ left: 0, right: 0 }}
      style={{ x, rotate, ...cardStyle }}
      onDragStart={handleDragStart}
      onDrag={handleDrag}
      onDragEnd={handleDragEnd}
      onClick={handleClick}
      whileTap={{ scale: 1.05 }}
    >
      {children}
    </motion.div>
  );
}
