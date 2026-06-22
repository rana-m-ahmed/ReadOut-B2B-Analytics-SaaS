export const SPRING_DEFAULT = { type: "spring" as const, stiffness: 220, damping: 26, mass: 1 };
export const SPRING_SNAPPY = { type: "spring" as const, stiffness: 320, damping: 30, mass: 0.9 };

export const chartContainerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

export const chartItemVariants = {
  hidden: { opacity: 0, y: 10 },
  show: { opacity: 1, y: 0, transition: SPRING_DEFAULT },
};

export const hoverLift = {
  y: -3,
  boxShadow: "var(--shadow-lift)",
  transition: SPRING_SNAPPY,
};
