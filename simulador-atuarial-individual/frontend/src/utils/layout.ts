export const layoutClasses = {
  // Spacing
  spaceY: {
    sm: 'space-y-1.5',
    md: 'space-y-3',
    lg: 'space-y-6',
    xl: 'space-y-8'
  },
  
  spaceX: {
    sm: 'space-x-1.5',
    md: 'space-x-3',
    lg: 'space-x-6',
    xl: 'space-x-8'
  },

  // Flex layouts
  flexCenter: 'flex items-center justify-center',
  flexBetween: 'flex items-center justify-between',
  flexStart: 'flex items-center justify-start',
  flexEnd: 'flex items-center justify-end',
  flexCol: 'flex flex-col',
  flexRow: 'flex flex-row',

  // Gaps
  gap: {
    sm: 'gap-2',
    md: 'gap-3',
    lg: 'gap-4',
    xl: 'gap-6'
  },

  // Grid layouts
  grid: {
    cols1: 'grid grid-cols-1',
    cols2: 'grid grid-cols-1 md:grid-cols-2',
    cols3: 'grid grid-cols-1 md:grid-cols-3',
    cols4: 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4'
  },

  // Common containers
  container: {
    sm: 'max-w-sm mx-auto',
    md: 'max-w-md mx-auto', 
    lg: 'max-w-lg mx-auto',
    xl: 'max-w-xl mx-auto',
    '2xl': 'max-w-2xl mx-auto',
    '3xl': 'max-w-3xl mx-auto',
    '4xl': 'max-w-4xl mx-auto',
    '5xl': 'max-w-5xl mx-auto'
  }
};

export const combineClasses = (...classes: (string | undefined | null | false)[]): string => {
  return classes.filter(Boolean).join(' ');
};