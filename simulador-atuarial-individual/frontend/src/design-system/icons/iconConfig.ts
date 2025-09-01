import { 
  // Navegação
  User,
  Settings,
  FileText,
  BarChart3,
  TrendingUp,
  TrendingDown,
  
  // Status/Feedback
  CheckCircle,
  AlertTriangle,
  XCircle,
  Info,
  X,
  
  // Ações
  Download,
  Printer,
  Mail,
  ArrowRight,
  Sparkles,
  Eye,
  
  // Dados/Financeiro
  DollarSign,
  Coins,
  PieChart,
  Target,
  Scale,
  Calendar,
  Clock,
  
  // Interface/Controles
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
  Loader2,
  HelpCircle,
  
  // Específicos do domínio
  Cog,
  Lightbulb,
  FileSpreadsheet,
  File
} from 'lucide-react';

export type IconName = keyof typeof iconMap;

export const iconMap = {
  // Navegação
  'user': User,
  'settings': Settings,
  'file-text': FileText,
  'bar-chart': BarChart3,
  'trending-up': TrendingUp,
  'trending-down': TrendingDown,
  
  // Status/Feedback
  'check-circle': CheckCircle,
  'alert-triangle': AlertTriangle,
  'x-circle': XCircle,
  'info': Info,
  'close': X,
  
  // Ações
  'download': Download,
  'printer': Printer,
  'mail': Mail,
  'arrow-right': ArrowRight,
  'sparkles': Sparkles,
  'eye': Eye,
  
  // Dados/Financeiro
  'dollar-sign': DollarSign,
  'coins': Coins,
  'pie-chart': PieChart,
  'target': Target,
  'scale': Scale,
  'calendar': Calendar,
  'clock': Clock,
  
  // Interface/Controles
  'chevron-down': ChevronDown,
  'chevron-up': ChevronUp,
  'chevron-left': ChevronLeft,
  'chevron-right': ChevronRight,
  'loader': Loader2,
  'help-circle': HelpCircle,
  
  // Específicos do domínio
  'cog': Cog,
  'lightbulb': Lightbulb,
  'file-spreadsheet': FileSpreadsheet,
  'file': File
} as const;

export type IconSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

export const iconSizes: Record<IconSize, string> = {
  'xs': 'w-3 h-3',   // 12px
  'sm': 'w-4 h-4',   // 16px
  'md': 'w-5 h-5',   // 20px
  'lg': 'w-6 h-6',   // 24px
  'xl': 'w-8 h-8'    // 32px
} as const;

export type IconColor = 'primary' | 'success' | 'warning' | 'error' | 'neutral' | 'muted';

export const iconColors: Record<IconColor, string> = {
  'primary': 'text-blue-600',
  'success': 'text-green-600',
  'warning': 'text-yellow-600',
  'error': 'text-red-600',
  'neutral': 'text-gray-600',
  'muted': 'text-gray-400'
} as const;