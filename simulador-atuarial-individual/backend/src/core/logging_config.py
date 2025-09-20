"""
Configuração de logging estruturado para o sistema atuarial
Substitui os print() espalhados pelo código
"""
import logging
import sys
from typing import Optional
from .constants import (
    LOG_DEBUG_ENGINE, LOG_RMBA_DEBUG, LOG_RMBC_DEBUG,
    LOG_AUDITORIA, LOG_FSOLVE, LOG_SANIDADE
)


class ActuarialFormatter(logging.Formatter):
    """Formatter customizado para logs atuariais"""

    def format(self, record):
        # Adicionar prefixos baseados no contexto
        if hasattr(record, 'actuarial_context'):
            record.msg = f"{record.actuarial_context} {record.msg}"

        return super().format(record)


def get_actuarial_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Cria logger configurado para componentes atuariais

    Args:
        name: Nome do logger (ex: 'actuarial.engine', 'actuarial.rmba')
        level: Nível de log (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)

    # Evitar duplicar handlers
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Formato estruturado
    formatter = ActuarialFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    # Evitar propagação para root logger
    logger.propagate = False

    return logger


class ActuarialLoggerMixin:
    """Mixin para adicionar logging estruturado a classes atuariais"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_actuarial_logger(self.__class__.__module__ + '.' + self.__class__.__name__)

    def log_engine_debug(self, message: str, **kwargs):
        """Log de debug do engine"""
        self.logger.debug(message, extra={'actuarial_context': LOG_DEBUG_ENGINE, **kwargs})

    def log_rmba_debug(self, message: str, **kwargs):
        """Log de debug RMBA"""
        self.logger.debug(message, extra={'actuarial_context': LOG_RMBA_DEBUG, **kwargs})

    def log_rmbc_debug(self, message: str, **kwargs):
        """Log de debug RMBC"""
        self.logger.debug(message, extra={'actuarial_context': LOG_RMBC_DEBUG, **kwargs})

    def log_auditoria(self, message: str, **kwargs):
        """Log de auditoria"""
        self.logger.info(message, extra={'actuarial_context': LOG_AUDITORIA, **kwargs})

    def log_fsolve(self, message: str, **kwargs):
        """Log de busca de raízes"""
        self.logger.warning(message, extra={'actuarial_context': LOG_FSOLVE, **kwargs})

    def log_sanidade(self, message: str, **kwargs):
        """Log de sanidade econômica"""
        self.logger.warning(message, extra={'actuarial_context': LOG_SANIDADE, **kwargs})

    def log_info(self, message: str, **kwargs):
        """Log de informação geral"""
        self.logger.info(message, **kwargs)

    def log_warning(self, message: str, **kwargs):
        """Log de aviso"""
        self.logger.warning(message, **kwargs)

    def log_error(self, message: str, **kwargs):
        """Log de erro"""
        self.logger.error(message, **kwargs)


def configure_actuarial_logging(level: str = "INFO"):
    """
    Configuração global do logging atuarial

    Args:
        level: Nível de log ("DEBUG", "INFO", "WARNING", "ERROR")
    """
    log_level = getattr(logging, level.upper())

    # Configurar logger raiz para componentes atuariais
    actuarial_logger = logging.getLogger('actuarial')
    actuarial_logger.setLevel(log_level)

    # Desabilitar logs de bibliotecas externas em desenvolvimento
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('fastapi').setLevel(logging.WARNING)


# Função de conveniência para migração gradual dos print()
def replace_print_with_log(logger: logging.Logger, message: str, level: str = "INFO"):
    """
    Função temporária para facilitar migração de print() para logging

    Args:
        logger: Logger a usar
        message: Mensagem a logar
        level: Nível do log
    """
    log_level = getattr(logging, level.upper())
    logger.log(log_level, message)