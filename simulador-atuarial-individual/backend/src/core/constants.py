"""
Constantes centralizadas do sistema atuarial
Elimina números mágicos espalhados pelo código
"""

# Limites de idade e tempo
MIN_RETIREMENT_YEARS = 25  # Mínimo de anos de aposentadoria para projeção adequada
MAX_PROJECTION_MONTHS = 50 * 12  # Máximo de meses para projeções (50 anos)
MAX_AGE_LIMIT = 110  # Idade máxima considerada nas tábuas
MIN_AGE_LIMIT = 18   # Idade mínima para participação

# Limites de taxas
MAX_CONTRIBUTION_RATE = 50.0  # Taxa máxima de contribuição (50%)
MIN_DISCOUNT_RATE = 0.001     # Taxa mínima de desconto (0.1%)
MAX_DISCOUNT_RATE = 0.20      # Taxa máxima de desconto (20%)
MAX_ADMIN_FEE_RATE = 0.05     # Taxa máxima administrativa (5%)
MAX_LOADING_FEE_RATE = 0.30   # Taxa máxima de carregamento (30%)

# Defaults do sistema
DEFAULT_PROJECTION_DURATION = 15.0  # Anos padrão para duração de passivos
DEFAULT_BENEFIT_MONTHS_PER_YEAR = 13  # 13º salário padrão
DEFAULT_SALARY_MONTHS_PER_YEAR = 13   # 13º salário padrão

# Configurações de cálculo
FINANCIAL_PRECISION = 1e-8  # Precisão para cálculos financeiros
MAX_ITERATIONS_ROOT_FINDING = 100  # Máximo de iterações para busca de raízes
CONVERGENCE_TOLERANCE = 1e-6  # Tolerância para convergência

# Valores de validação
MIN_SALARY = 1000.0          # Salário mínimo aceito
MAX_SALARY = 1000000.0       # Salário máximo aceito
MIN_BENEFIT = 100.0          # Benefício mínimo aceito
MAX_BENEFIT = 500000.0       # Benefício máximo aceito

# Configurações de logging
LOG_DEBUG_ENGINE = "[ENGINE_DEBUG]"
LOG_RMBA_DEBUG = "[RMBA_DEBUG]"
LOG_RMBC_DEBUG = "[RMBC_DEBUG]"
LOG_AUDITORIA = "[AUDITORIA]"
LOG_FSOLVE = "[FSOLVE]"
LOG_SANIDADE = "[SANIDADE_ECONÔMICA]"

# Mensagens padronizadas
MSG_PERSON_RETIRED = "Pessoa já aposentada"
MSG_PERSON_ACTIVE = "Pessoa ativa"
MSG_EXTENDED_PROJECTION = "Período estendido para {} anos para análise adequada da aposentadoria"
MSG_RETIREMENT_PROJECTION = "Aposentado: projetando {:.0f} anos de benefícios"

# Configurações de sensibilidade
DEFAULT_SENSITIVITY_RANGE = 0.02  # ±2% para análises de sensibilidade
SENSITIVITY_STEPS = 5  # Número de steps para análise de sensibilidade