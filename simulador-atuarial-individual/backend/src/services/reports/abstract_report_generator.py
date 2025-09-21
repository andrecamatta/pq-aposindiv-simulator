"""
Base abstrata para todos os geradores de relatórios.
Aplica princípio DRY consolidando lógica comum de geração de relatórios.
"""
import uuid
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any

from .models.report_models import ReportConfig, ReportRequest, ReportResponse


class AbstractReportGenerator(ABC):
    """
    Classe base abstrata para geradores de relatórios.

    Consolida funcionalidades comuns:
    - Configuração e inicialização
    - Gestão de cache/diretórios
    - Medição de tempo de geração
    - Estrutura padrão de Response
    - Logging e tratamento de erros
    """

    def __init__(self, config: Optional[ReportConfig] = None, cache_dir: Optional[Path] = None):
        """
        Inicialização padrão para todos os geradores.

        Args:
            config: Configurações do relatório (opcional)
            cache_dir: Diretório de cache personalizado (opcional)
        """
        self.config = config or ReportConfig()
        self.cache_dir = cache_dir or Path(__file__).parent / "cache"

        # Garantir que diretório de cache existe
        self.cache_dir.mkdir(exist_ok=True)

        # Configurar logger específico para cada gerador
        self._setup_logging()

        # Hook para inicialização específica de cada gerador
        self._initialize_generator()

    def _setup_logging(self) -> None:
        """Configurar logging específico para o gerador."""
        import logging
        self.logger = logging.getLogger(self.__class__.__name__)

    def _initialize_generator(self) -> None:
        """
        Hook para inicialização específica de cada gerador.
        Pode ser sobrescrito por classes filhas.
        """
        pass

    def _generate_report_id(self) -> str:
        """Gerar ID único para o relatório."""
        return str(uuid.uuid4())

    def _measure_generation_time(self, start_time: float) -> int:
        """Calcular tempo de geração em milissegundos."""
        return int((time.time() - start_time) * 1000)

    def _create_success_response(
        self,
        report_id: str,
        generation_time_ms: int,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        content_type: Optional[str] = None,
        message: str = "Relatório gerado com sucesso"
    ) -> ReportResponse:
        """
        Criar response de sucesso padronizada.

        Args:
            report_id: ID único do relatório
            generation_time_ms: Tempo de geração em ms
            file_path: Caminho do arquivo gerado (opcional)
            file_size: Tamanho do arquivo em bytes (opcional)
            content_type: Tipo MIME do arquivo (opcional)
            message: Mensagem de sucesso personalizada

        Returns:
            ReportResponse configurado para sucesso
        """
        return ReportResponse(
            success=True,
            message=message,
            file_path=file_path,
            file_size=file_size,
            generation_time_ms=generation_time_ms,
            report_id=report_id,
            content_type=content_type
        )

    def _create_error_response(
        self,
        report_id: str,
        generation_time_ms: int,
        error_message: str
    ) -> ReportResponse:
        """
        Criar response de erro padronizada.

        Args:
            report_id: ID único do relatório
            generation_time_ms: Tempo decorrido até o erro
            error_message: Mensagem de erro detalhada

        Returns:
            ReportResponse configurado para erro
        """
        return ReportResponse(
            success=False,
            message=f"Erro na geração do relatório: {error_message}",
            file_path=None,
            file_size=None,
            generation_time_ms=generation_time_ms,
            report_id=report_id,
            content_type=None
        )

    def _validate_request(self, request: ReportRequest) -> None:
        """
        Validar request básico.
        Pode ser estendido por classes filhas.

        Args:
            request: Request a ser validado

        Raises:
            ValueError: Se request é inválido
        """
        if not request.state:
            raise ValueError("SimulatorState é obrigatório")

        if not request.results:
            raise ValueError("SimulatorResults é obrigatório")

    def _get_file_size(self, file_path: Path) -> Optional[int]:
        """
        Obter tamanho do arquivo gerado.

        Args:
            file_path: Caminho do arquivo

        Returns:
            Tamanho em bytes ou None se arquivo não existe
        """
        try:
            return file_path.stat().st_size if file_path.exists() else None
        except OSError:
            return None

    def generate_report(self, request: ReportRequest) -> ReportResponse:
        """
        Método principal público para geração de relatórios.
        Implementa template method pattern com estrutura comum.

        Args:
            request: Dados para geração do relatório

        Returns:
            ReportResponse com resultado da geração
        """
        start_time = time.time()
        report_id = self._generate_report_id()

        try:
            # Validação comum
            self._validate_request(request)

            # Log início da geração
            self.logger.info(f"Iniciando geração de relatório {report_id}")

            # Delegar geração específica para classe filha
            result = self._generate_specific_report(request, report_id)

            # Calcular tempo e log sucesso
            generation_time = self._measure_generation_time(start_time)
            self.logger.info(f"Relatório {report_id} gerado com sucesso em {generation_time}ms")

            return result

        except Exception as e:
            # Log erro e retornar response de erro
            generation_time = self._measure_generation_time(start_time)
            error_msg = str(e)

            self.logger.error(f"Erro na geração do relatório {report_id}: {error_msg}")

            return self._create_error_response(report_id, generation_time, error_msg)

    @abstractmethod
    def _generate_specific_report(self, request: ReportRequest, report_id: str) -> ReportResponse:
        """
        Método abstrato para geração específica do relatório.
        Deve ser implementado por cada classe filha.

        Args:
            request: Dados para geração
            report_id: ID único gerado

        Returns:
            ReportResponse com resultado da geração

        Raises:
            NotImplementedError: Se não implementado pela classe filha
        """
        raise NotImplementedError("Classe filha deve implementar _generate_specific_report")

    @property
    @abstractmethod
    def supported_formats(self) -> list[str]:
        """
        Lista de formatos suportados pelo gerador.
        Deve ser implementado por cada classe filha.

        Returns:
            Lista de formatos (ex: ['pdf', 'html'])
        """
        raise NotImplementedError("Classe filha deve implementar supported_formats")

    @property
    @abstractmethod
    def default_content_type(self) -> str:
        """
        Tipo MIME padrão para este gerador.
        Deve ser implementado por cada classe filha.

        Returns:
            String com tipo MIME (ex: 'application/pdf')
        """
        raise NotImplementedError("Classe filha deve implementar default_content_type")