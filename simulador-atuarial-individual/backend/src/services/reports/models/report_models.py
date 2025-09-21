"""
Modelos Pydantic para requests e responses do sistema de relatórios
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from ....models.participant import SimulatorState
from ....models.results import SimulatorResults


class ReportConfig(BaseModel):
    """Configurações para geração de relatórios"""
    company_name: str = "PrevLab"
    logo_url: Optional[str] = None
    include_charts: bool = True
    include_sensitivity: bool = True
    language: str = "pt"
    decimal_precision: int = 2
    chart_dpi: int = 300


class ReportRequest(BaseModel):
    """Request para geração de relatórios"""
    state: SimulatorState
    results: SimulatorResults
    config: Optional[ReportConfig] = None


class ReportResponse(BaseModel):
    """Response para geração de relatórios"""
    success: bool
    message: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    generation_time_ms: int
    report_id: str
    content_type: Optional[str] = None


class PreviewResponse(BaseModel):
    """Response para preview HTML de relatórios"""
    html_content: str
    css_content: Optional[str] = None
    charts: Dict[str, str] = {}  # chart_id -> base64_image
    generation_time_ms: int