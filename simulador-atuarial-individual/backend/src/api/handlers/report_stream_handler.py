from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from pathlib import Path
import os
from typing import Dict, Callable, Any

from ...services.reports.models.report_models import ReportResponse, ReportRequest


class ReportStreamHandler:
    """Handler centralizado para streaming de relatórios"""

    @staticmethod
    def create_streaming_response(
        report_response: ReportResponse,
        request: ReportRequest,
        file_extension: str,
        media_type: str,
        content_type: str,
        report_type_prefix: str
    ) -> StreamingResponse:
        """
        Cria resposta de streaming padronizada para qualquer tipo de relatório

        Args:
            report_response: Resposta do gerador
            request: Request original
            file_extension: Extensão do arquivo (pdf, xlsx, csv)
            media_type: Media type para resposta
            content_type: Content-Type para headers
            report_type_prefix: Prefixo do nome do arquivo (relatorio_executivo, dados_simulacao, etc)
        """
        if not report_response.success:
            raise HTTPException(status_code=500, detail=report_response.message)

        # Verificar se arquivo foi criado
        file_path = Path(report_response.file_path)
        if not file_path.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Arquivo {file_extension.upper()} não foi gerado"
            )

        # Função geradora para streaming
        def iterfile():
            try:
                with open(file_path, mode="rb") as file_like:
                    yield from file_like
            finally:
                # Limpar arquivo temporário após download
                try:
                    if file_path.exists():
                        os.unlink(file_path)
                except Exception:
                    pass  # Falha na limpeza não deve quebrar o download

        # Determinar nome do arquivo baseado nos dados do participante
        participant_info = f"{request.state.age}anos_{request.state.gender}"
        plan_type = request.state.plan_type.lower()
        filename = f"{report_type_prefix}_{plan_type}_{participant_info}_{report_response.report_id[:8]}.{file_extension}"

        # Headers para download
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': content_type,
            'Content-Length': str(report_response.file_size)
        }

        return StreamingResponse(iterfile(), headers=headers, media_type=media_type)

    @classmethod
    def handle_pdf_response(
        cls,
        report_response: ReportResponse,
        request: ReportRequest,
        report_type: str = "executivo"
    ) -> StreamingResponse:
        """Handler específico para PDFs"""
        return cls.create_streaming_response(
            report_response=report_response,
            request=request,
            file_extension="pdf",
            media_type="application/pdf",
            content_type="application/pdf",
            report_type_prefix=f"relatorio_{report_type}"
        )

    @classmethod
    def handle_excel_response(
        cls,
        report_response: ReportResponse,
        request: ReportRequest
    ) -> StreamingResponse:
        """Handler específico para Excel"""
        return cls.create_streaming_response(
            report_response=report_response,
            request=request,
            file_extension="xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            report_type_prefix="dados_simulacao"
        )

    @classmethod
    def handle_csv_response(
        cls,
        report_response: ReportResponse,
        request: ReportRequest
    ) -> StreamingResponse:
        """Handler específico para CSV"""
        return cls.create_streaming_response(
            report_response=report_response,
            request=request,
            file_extension="csv",
            media_type="text/csv",
            content_type="text/csv; charset=utf-8",
            report_type_prefix="dados_simulacao"
        )

    @staticmethod
    def execute_with_error_handling(operation: Callable[[], ReportResponse]) -> ReportResponse:
        """Executa operação de geração com tratamento de erro padronizado"""
        try:
            return operation()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro interno ao gerar relatório: {str(e)}")