export const SPRING_DEFAULT = { type:"spring", stiffness:220, damping:26, mass:1 } as const;
export const SPRING_SNAPPY = { type:"spring", stiffness:320, damping:30, mass:.9 } as const;
export const HOVER_LIFT = { y:-3, boxShadow:"var(--shadow-lift)" } as const;
export const MODAL_OPEN = { hidden:{opacity:0,scale:.95}, visible:{opacity:1,scale:1,transition:SPRING_DEFAULT} } as const;
export const PAGE_TRANSITION = { hidden:{opacity:0,y:10}, visible:{opacity:1,y:0,transition:{duration:.2}} } as const;
export const STAGGER_CONTAINER = { hidden:{}, visible:{transition:{staggerChildren:.07}} } as const;
export const STAGGER_ITEM = { hidden:{opacity:0,y:12}, visible:{opacity:1,y:0,transition:SPRING_DEFAULT} } as const;
export const CHART_REVEAL = { hidden:{opacity:0,scaleY:0}, visible:{opacity:1,scaleY:1,transition:{duration:.5}} } as const;
