"""
Constantes centralizadas do sistema atuarial
Elimina números mágicos espalhados pelo código
"""

# ============================================================
# CONSTANTES ATUARIAIS - LIMITES DE IDADE E TEMPO
# ============================================================

# Limites de idade básicos
MIN_AGE_LIMIT = 18   # Idade mínima para participação
MAX_AGE_LIMIT = 110  # Idade máxima considerada nas tábuas

# Limites de idade para projeções
MAX_RETIREMENT_AGE_PROJECTION = 95  # Idade máxima para aposentados em projeções
MAX_RETIREMENT_PROJECTION_YEARS = 30  # Anos máximos de projeção para já aposentados

# Limites de aposentadoria
MIN_RETIREMENT_YEARS = 25  # Mínimo de anos de aposentadoria para projeção adequada

# Limites de anuidades
MAX_ANNUITY_YEARS = 50  # Anos máximos para cálculo de anuidades vitalícias
MAX_ANNUITY_MONTHS = MAX_ANNUITY_YEARS * 12  # 600 meses
MAX_PROJECTION_MONTHS = MAX_ANNUITY_MONTHS  # Máximo de meses para projeções (compatibilidade)

# Períodos padrão CD
DEFAULT_PROGRAMMED_WITHDRAWAL_YEARS = 20  # Anos padrão para saque programado CD
DEFAULT_PROGRAMMED_WITHDRAWAL_MONTHS = DEFAULT_PROGRAMMED_WITHDRAWAL_YEARS * 12  # 240 meses

# ============================================================
# CONSTANTES ATUARIAIS - FATORES E TOLERÂNCIAS
# ============================================================

# Fatores de proteção contra erros numéricos
MIN_EFFECTIVE_RATE = -0.99  # Fator mínimo para taxas efetivas (evita divisão por zero)
MAX_EFFECTIVE_RATE = 10.0   # Fator máximo para taxas efetivas

# Probabilidades iniciais
INITIAL_SURVIVAL_PROBABILITY = 1.0  # Probabilidade inicial de sobrevivência (100%)

# Thresholds de viabilidade
ACHIEVABILITY_THRESHOLD = 0.95  # 95% - threshold para considerar objetivo alcançável
FEASIBILITY_TOLERANCE = 0.05    # 5% - tolerância para análise de viabilidade

# Limites para validação de parâmetros
MIN_ACHIEVABLE_RATIO = 0.80  # 80% - mínimo aceitável para relação objetivo/realizado
MAX_ACHIEVABLE_RATIO = 1.20  # 120% - máximo aceitável para relação objetivo/realizado

# ============================================================
# LIMITES DE TAXAS
# ============================================================

MAX_CONTRIBUTION_RATE = 50.0  # Taxa máxima de contribuição (50%)
MIN_DISCOUNT_RATE = 0.001     # Taxa mínima de desconto (0.1%)
MAX_DISCOUNT_RATE = 0.20      # Taxa máxima de desconto (20%)
MAX_ADMIN_FEE_RATE = 0.05     # Taxa máxima administrativa (5%)
MAX_LOADING_FEE_RATE = 0.30   # Taxa máxima de carregamento (30%)

# Defaults do sistema
DEFAULT_PROJECTION_DURATION = 15.0  # Anos padrão para duração de passivos

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

# Constantes de tempo
MONTHS_PER_YEAR = 12  # Meses por ano calendário (para conversões de tempo)