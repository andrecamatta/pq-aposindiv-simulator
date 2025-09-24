"""
Router para endpoints de geração de relatórios em PDF
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pathlib import Path
import os
import uuid
from typing import Optional

from ..services.reports.pdf_generator import PDFGenerator
from ..services.reports.excel_generator import ExcelGenerator
from ..services.reports.models.report_models import ReportRequest, ReportResponse, ReportConfig
from .handlers.report_stream_handler import ReportStreamHandler


router = APIRouter(prefix="/reports", tags=["reports"])

# Instâncias globais dos geradores
pdf_generator = PDFGenerator()
excel_generator = ExcelGenerator(pdf_generator.cache_dir)


@router.post("/executive-pdf", response_class=StreamingResponse)
async def generate_executive_pdf(request: ReportRequest):
    """
    Gerar relatório executivo em PDF

    Retorna um stream do arquivo PDF para download direto
    """
    report_response = ReportStreamHandler.execute_with_error_handling(
        lambda: pdf_generator.generate_executive_pdf(request)
    )
    return ReportStreamHandler.handle_pdf_response(report_response, request, "executivo")


@router.post("/technical-pdf", response_class=StreamingResponse)
async def generate_technical_pdf(request: ReportRequest):
    """
    Gerar relatório técnico em PDF

    Retorna um stream do arquivo PDF para download direto
    """
    report_response = ReportStreamHandler.execute_with_error_handling(
        lambda: pdf_generator.generate_technical_pdf(request)
    )
    return ReportStreamHandler.handle_pdf_response(report_response, request, "tecnico")


@router.post("/data-excel", response_class=StreamingResponse)
async def generate_data_excel(request: ReportRequest):
    """
    Gerar planilha Excel com dados estruturados

    Retorna um stream do arquivo Excel para download direto
    """
    report_response = ReportStreamHandler.execute_with_error_handling(
        lambda: excel_generator.generate_excel(request)
    )
    return ReportStreamHandler.handle_excel_response(report_response, request)


@router.post("/data-csv", response_class=StreamingResponse)
async def generate_data_csv(request: ReportRequest):
    """
    Gerar arquivo CSV com dados estruturados

    Retorna um stream do arquivo CSV para download direto
    """
    report_response = ReportStreamHandler.execute_with_error_handling(
        lambda: excel_generator.generate_csv(request)
    )
    return ReportStreamHandler.handle_csv_response(report_response, request)


@router.post("/preview-executive")
async def preview_executive_html(request: ReportRequest):
    """
    Gerar preview HTML do relatório executivo (sem conversão para PDF)

    Útil para debugging ou preview antes do download
    """
    try:
        # Usar o gerador de PDF para renderizar apenas o HTML
        charts = pdf_generator.chart_generator.generate_all_charts(request.results)

        html_content = pdf_generator._render_executive_template(
            request.state, request.results, charts
        )

        return {
            "success": True,
            "html_content": html_content,
            "charts_count": len(charts),
            "report_type": "executive"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar preview: {str(e)}")


@router.post("/preview-technical")
async def preview_technical_html(request: ReportRequest):
    """
    Gerar preview HTML do relatório técnico (sem conversão para PDF)

    Útil para debugging ou preview antes do download
    """
    try:
        # Usar o gerador de PDF para renderizar apenas o HTML
        charts = pdf_generator.chart_generator.generate_all_charts(request.results, chart_type='technical')

        html_content = pdf_generator._render_technical_template(
            request.state, request.results, charts
        )

        return {
            "success": True,
            "html_content": html_content,
            "charts_count": len(charts),
            "report_type": "technical"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar preview: {str(e)}")


@router.get("/health")
async def reports_health_check():
    """Health check do sistema de relatórios"""
    try:
        # Verificar se dependências estão funcionando
        import weasyprint
        import matplotlib
        import jinja2

        # Verificar diretórios
        cache_dir = pdf_generator.cache_dir
        templates_dir = pdf_generator.templates_dir

        cache_files_count = len(list(cache_dir.iterdir())) if cache_dir.exists() else 0

        return {
            "status": "healthy",
            "service": "reports",
            "dependencies": {
                "weasyprint": weasyprint.__version__,
                "matplotlib": matplotlib.__version__,
                "jinja2": jinja2.__version__
            },
            "directories": {
                "cache_exists": cache_dir.exists(),
                "templates_exists": templates_dir.exists(),
                "cache_files": cache_files_count
            },
            "config": {
                "company_name": pdf_generator.config.company_name,
                "include_charts": pdf_generator.config.include_charts,
                "chart_dpi": pdf_generator.config.chart_dpi
            }
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "reports",
            "error": str(e)
        }


@router.delete("/cache/cleanup")
async def cleanup_cache():
    """
    Limpar cache de relatórios manualmente

    Remove arquivos PDF temporários antigos
    """
    try:
        cache_dir = pdf_generator.cache_dir
        if not cache_dir.exists():
            return {
                "success": True,
                "message": "Diretório de cache não existe",
                "files_removed": 0
            }

        files_removed = 0
        for file_path in cache_dir.iterdir():
            if file_path.is_file() and file_path.suffix == '.pdf':
                try:
                    file_path.unlink()
                    files_removed += 1
                except Exception:
                    continue

        remaining_files = len(list(cache_dir.iterdir()))

        return {
            "success": True,
            "message": "Cache limpo com sucesso",
            "files_removed": files_removed,
            "remaining_files": remaining_files
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao limpar cache: {str(e)}")


@router.post("/test-generation")
async def test_pdf_generation():
    """
    Endpoint de teste para verificar se a geração de PDF está funcionando

    Gera um PDF de teste com dados fictícios
    """
    try:
        from ..models.participant import SimulatorState, PlanType, Gender, BenefitTargetMode
        from ..models.results import SimulatorResults

        # Criar estado de teste
        test_state = SimulatorState(
            age=35,
            gender=Gender.MALE,
            salary=10000.0,
            plan_type=PlanType.BD,
            initial_balance=0.0,
            benefit_target_mode=BenefitTargetMode.VALUE,
            target_benefit=6000.0,
            accrual_rate=5.0,
            retirement_age=65,
            contribution_rate=10.0,
            mortality_table="BR_EMS_2021",
            mortality_aggravation=0.0,
            discount_rate=0.06,
            salary_growth_real=0.02,
            benefit_indexation="none",
            contribution_indexation="salary",
            use_ettj=False,
            admin_fee_rate=0.01,
            loading_fee_rate=0.0,
            payment_timing="postecipado",
            salary_months_per_year=13,
            benefit_months_per_year=13,
            projection_years=30,
            calculation_method="PUC"
        )

        # Usar endpoint de cálculo real para obter resultados válidos
        from ..core.actuarial_engine import ActuarialEngine
        engine = ActuarialEngine()
        test_results = engine.calculate_individual_simulation(test_state)

        # Criar request de teste
        test_request = ReportRequest(
            state=test_state,
            results=test_results
        )

        # Gerar PDF de teste
        report_response = pdf_generator.generate_executive_pdf(test_request)

        return {
            "success": report_response.success,
            "message": "PDF de teste gerado com sucesso" if report_response.success else report_response.message,
            "file_size": report_response.file_size,
            "generation_time_ms": report_response.generation_time_ms,
            "report_id": report_response.report_id
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Erro no teste: {str(e)}",
            "error_type": type(e).__name__
        }