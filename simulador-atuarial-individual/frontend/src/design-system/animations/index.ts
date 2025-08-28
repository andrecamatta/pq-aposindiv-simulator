// S-Tier Animation System
// Professional micro-interactions for enhanced UX

export const animations = {
  // Entrance animations
  fadeIn: "animate-fade-in",
  slideIn: "animate-slide-in",
  
  // Loading animations
  spin: "animate-spin",
  pulse: "animate-pulse",
  pulseSubtle: "animate-pulse-subtle",
  
  // Interaction feedback
  bounceSubtle: "animate-bounce-subtle",
  
  // Progress animations
  shrink: "animate-shrink",
  
  // Transition classes
  transition: {
    default: "transition-all duration-150 ease-in-out",
    fast: "transition-all duration-100 ease-in-out", 
    slow: "transition-all duration-300 ease-in-out",
    colors: "transition-colors duration-150 ease-in-out",
    transform: "transition-transform duration-150 ease-in-out",
    opacity: "transition-opacity duration-150 ease-in-out",
  },
  
  // Hover effects
  hover: {
    scale: "hover:scale-105 transform transition-transform duration-150",
    lift: "hover:-translate-y-0.5 transform transition-transform duration-150",
    glow: "hover:shadow-lg transition-shadow duration-150",
    brighten: "hover:brightness-110 transition-all duration-150",
  },
  
  // Focus states for accessibility
  focus: {
    ring: "focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2",
    visible: "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2",
  },
};

// Utility function to combine animation classes
export const combineAnimations = (...classes: string[]): string => {
  return classes.filter(Boolean).join(" ");
};

// Predefined interaction patterns
export const interactionPatterns = {
  button: combineAnimations(
    animations.transition.default,
    animations.hover.scale,
    animations.focus.visible
  ),
  card: combineAnimations(
    animations.transition.default,
    animations.hover.lift,
    animations.hover.glow
  ),
  input: combineAnimations(
    animations.transition.colors,
    animations.focus.ring
  ),
  tooltip: combineAnimations(
    animations.fadeIn,
    animations.transition.default
  ),
};