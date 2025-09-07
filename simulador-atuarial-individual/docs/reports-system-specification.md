# Sistema de Relatórios - Especificação Técnica Detalhada

## Visão Geral

Este documento especifica a implementação completa do sistema de relatórios para o Simulador Atuarial Individual, incluindo geração de PDFs executivos e técnicos, exportação de dados e sistema de preview.

## 1. Dependências e Configuração

### 1.1 Dependências Python (Backend)

```bash
cd simulador-atuarial-individual/backend
uv add reportlab matplotlib jinja2 weasyprint pillow pandas openpyxl
```

**Dependências detalhadas:**
- `reportlab==4.0.7`: Geração robusta de PDFs com suporte completo a gráficos
- `matplotlib==3.8.2`: Geração de gráficos profissionais para relatórios  
- `jinja2==3.1.2`: Sistema de templates HTML flexível
- `weasyprint==61.2`: Conversão HTML para PDF de alta qualidade
- `pillow==10.1.0`: Manipulação e otimização de imagens
- `pandas==2.1.4`: Manipulação de dados para exports
- `openpyxl==3.1.2`: Geração de arquivos Excel

### 1.2 Estrutura de Diretórios

```
backend/src/services/reports/
├── __init__.py
├── report_generator.py          # Classe principal de coordenação
├── pdf_generator.py             # Lógica específica de geração de PDF
├── chart_generator.py           # Geração de gráficos e visualizações
├── data_exporter.py             # Export Excel/CSV
├── models/
│   ├── __init__.py
│   └── report_models.py         # Modelos Pydantic para requests/responses
├── templates/
│   ├── base_report.html         # Template base comum
│   ├── executive_report.html    # Template relatório executivo
│   ├── technical_report.html    # Template relatório técnico
│   └── components/
│       ├── header.html          # Header padrão
│       ├── kpi_cards.html       # Cards de indicadores
│       ├── charts.html          # Containers para gráficos
│       └── footer.html          # Footer padrão
├── static/
│   ├── styles.css              # Estilos CSS para PDFs
│   ├── logo.png               # Logo padrão da empresa
│   └── fonts/                 # Fontes personalizadas (se necessário)
└── cache/                     # Cache temporário de arquivos gerados
```

## 2. Modelos de Dados

### 2.1 Request Models (`models/report_models.py`)

```python
from pydantic import BaseModel
from typing import Optional, Literal
from ..models import SimulatorState, SimulatorResults

class ReportRequest(BaseModel):
    """Request base para geração de relatórios"""
    state: SimulatorState
    results: SimulatorResults
    report_config: Optional[dict] = None

class ReportConfig(BaseModel):
    """Configurações opcionais para relatórios"""
    company_name: str = "Simulador Atuarial"
    logo_url: Optional[str] = None
    include_charts: bool = True
    include_sensitivity: bool = True
    language: Literal["pt", "en"] = "pt"
    decimal_precision: int = 2

class ReportResponse(BaseModel):
    """Response padrão para geração de relatórios"""
    success: bool
    message: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    generation_time_ms: int
    report_id: str

class PreviewResponse(BaseModel):
    """Response para preview HTML"""
    html_content: str
    css_content: str
    charts: dict[str, str]  # chart_id -> base64_image
```

### 2.2 Enums e Constants

```python
from enum import Enum

class ReportType(Enum):
    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    DATA_EXPORT = "data_export"

class ExportFormat(Enum):
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    HTML = "html"

# Constantes de configuração
CHART_DPI = 300
PDF_PAGE_SIZE = "A4"
CACHE_DURATION_HOURS = 2
MAX_CACHE_FILES = 100
```

## 3. Classes Principais

### 3.1 ReportGenerator (`report_generator.py`)

```python
from pathlib import Path
from typing import Dict, Optional
import uuid
from datetime import datetime, timedelta

class ReportGenerator:
    """Classe principal para coordenar geração de relatórios"""
    
    def __init__(self, config: Optional[ReportConfig] = None):
        self.config = config or ReportConfig()
        self.template_dir = Path(__file__).parent / "templates"
        self.static_dir = Path(__file__).parent / "static"
        self.cache_dir = Path(__file__).parent / "cache"
        self.pdf_generator = PDFGenerator(self.config)
        self.chart_generator = ChartGenerator(self.config)
        self.data_exporter = DataExporter(self.config)
        
        # Criar diretórios se não existirem
        self.cache_dir.mkdir(exist_ok=True)
    
    async def generate_executive_report(
        self, 
        request: ReportRequest, 
        format: ExportFormat = ExportFormat.PDF
    ) -> ReportResponse:
        """Gerar relatório executivo"""
        
    async def generate_technical_report(
        self, 
        request: ReportRequest, 
        format: ExportFormat = ExportFormat.PDF
    ) -> ReportResponse:
        """Gerar relatório técnico"""
        
    async def generate_data_export(
        self, 
        request: ReportRequest, 
        format: ExportFormat
    ) -> ReportResponse:
        """Gerar export de dados (Excel/CSV)"""
        
    async def preview_report(
        self, 
        request: ReportRequest, 
        report_type: ReportType
    ) -> PreviewResponse:
        """Gerar preview HTML do relatório"""
        
    def _cleanup_cache(self):
        """Limpar arquivos antigos do cache"""
        cutoff = datetime.now() - timedelta(hours=CACHE_DURATION_HOURS)
        for file_path in self.cache_dir.iterdir():
            if file_path.stat().st_mtime < cutoff.timestamp():
                file_path.unlink()
```

### 3.2 PDFGenerator (`pdf_generator.py`)

```python
from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader
import base64
from io import BytesIO

class PDFGenerator:
    """Classe especializada em geração de PDFs"""
    
    def __init__(self, config: ReportConfig):
        self.config = config
        self.jinja_env = Environment(
            loader=FileSystemLoader(Path(__file__).parent / "templates")
        )
    
    def generate_executive_pdf(
        self, 
        state: SimulatorState, 
        results: SimulatorResults,
        charts: Dict[str, str]
    ) -> bytes:
        """
        Gerar PDF executivo (2-3 páginas)
        
        Estrutura:
        - Página 1: Capa + Resumo Executivo + KPIs principais
        - Página 2: Gráficos principais + Análise de cenários
        - Página 3: Recomendações + Conclusões
        """
        template = self.jinja_env.get_template("executive_report.html")
        
        context = {
            "config": self.config,
            "state": state,
            "results": results,
            "charts": charts,
            "generation_date": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "kpis": self._extract_executive_kpis(results),
            "recommendations": self._generate_recommendations(state, results)
        }
        
        html_content = template.render(**context)
        return self._html_to_pdf(html_content)
    
    def generate_technical_pdf(
        self, 
        state: SimulatorState, 
        results: SimulatorResults,
        charts: Dict[str, str]
    ) -> bytes:
        """
        Gerar PDF técnico (6-10 páginas)
        
        Estrutura:
        - Página 1: Capa com dados do participante
        - Página 2: Índice + Resumo executivo
        - Página 3: Premissas atuariais detalhadas
        - Página 4: Metodologia e base técnica
        - Página 5-6: Projeções e fluxos detalhados
        - Página 7: Análise de sensibilidade completa
        - Página 8: Cenários alternativos
        - Página 9: Validações e testes
        - Página 10: Anexos técnicos
        """
        template = self.jinja_env.get_template("technical_report.html")
        
        context = {
            "config": self.config,
            "state": state,
            "results": results,
            "charts": charts,
            "generation_date": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "technical_details": self._extract_technical_details(results),
            "validation_results": self._validate_calculations(results),
            "methodology": self._get_methodology_details(state)
        }
        
        html_content = template.render(**context)
        return self._html_to_pdf(html_content)
    
    def _html_to_pdf(self, html_content: str) -> bytes:
        """Converter HTML para PDF usando WeasyPrint"""
        css_file = Path(__file__).parent / "static" / "styles.css"
        
        html_doc = HTML(string=html_content)
        css_doc = CSS(filename=str(css_file))
        
        pdf_bytes = html_doc.write_pdf(stylesheets=[css_doc])
        return pdf_bytes
    
    def _extract_executive_kpis(self, results: SimulatorResults) -> dict:
        """Extrair KPIs principais para relatório executivo"""
        return {
            "rmba": results.rmba,
            "rmbc": results.rmbc,
            "superavit": results.deficit_surplus,
            "superavit_percentage": results.deficit_surplus_percentage,
            "replacement_ratio": results.replacement_ratio,
            "funding_ratio": results.funding_ratio or 0,
            "required_contribution": results.required_contribution_rate,
            "total_contributions": results.total_contributions,
            "total_benefits": results.total_benefits
        }
    
    def _generate_recommendations(self, state: SimulatorState, results: SimulatorResults) -> list:
        """Gerar recomendações automáticas baseadas nos resultados"""
        recommendations = []
        
        if results.deficit_surplus_percentage < -5:
            recommendations.append({
                "type": "warning",
                "title": "Déficit Identificado",
                "description": f"O plano apresenta déficit de {abs(results.deficit_surplus_percentage):.1f}%. Recomenda-se revisar contribuições ou benefícios."
            })
        
        if results.replacement_ratio < state.target_replacement_rate * 0.9:
            recommendations.append({
                "type": "info",
                "title": "Taxa de Reposição Baixa",
                "description": f"A taxa de reposição atual ({results.replacement_ratio:.1f}%) está abaixo do objetivo. Considere aumentar contribuições."
            })
        
        if state.retirement_age < 62:
            recommendations.append({
                "type": "suggestion",
                "title": "Otimização da Idade de Aposentadoria",
                "description": "Postergar a aposentadoria em 2-3 anos pode melhorar significativamente os resultados."
            })
        
        return recommendations
```

### 3.3 ChartGenerator (`chart_generator.py`)

```python
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
import numpy as np
from io import BytesIO
import base64

class ChartGenerator:
    """Classe para geração de gráficos e visualizações"""
    
    def __init__(self, config: ReportConfig):
        self.config = config
        self.dpi = CHART_DPI
        
        # Configurar estilo matplotlib
        plt.style.use('seaborn-v0_8-whitegrid')
        self.colors = {
            'primary': '#2E86AB',
            'secondary': '#A23B72', 
            'success': '#F18F01',
            'warning': '#C73E1D',
            'info': '#7209B7'
        }
    
    def generate_all_charts(self, results: SimulatorResults) -> Dict[str, str]:
        """Gerar todos os gráficos necessários para os relatórios"""
        charts = {}
        
        charts['reserve_evolution'] = self.generate_reserve_evolution_chart(results)
        charts['sensitivity_tornado'] = self.generate_sensitivity_chart(results)
        charts['projections'] = self.generate_projections_chart(results)
        charts['cash_flow'] = self.generate_cash_flow_chart(results)
        charts['scenarios'] = self.generate_scenarios_chart(results)
        
        return charts
    
    def generate_reserve_evolution_chart(self, results: SimulatorResults) -> str:
        """
        Gráfico de evolução das reservas matemáticas (RMBA vs RMBC)
        Mostra a evolução ao longo dos anos de projeção
        """
        fig, ax = plt.subplots(figsize=(12, 6), dpi=self.dpi)
        
        years = results.projection_years
        rmba_evolution = results.projected_rmba_evolution
        accumulated_reserves = results.accumulated_reserves
        
        ax.plot(years, rmba_evolution, 
               label='RMBA', color=self.colors['primary'], linewidth=2)
        ax.plot(years, accumulated_reserves, 
               label='RMBC', color=self.colors['secondary'], linewidth=2)
        
        ax.set_xlabel('Ano')
        ax.set_ylabel('Valor (R$)')
        ax.set_title('Evolução das Reservas Matemáticas')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Formatação dos valores no eixo Y
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x/1000:.0f}K'))
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def generate_sensitivity_chart(self, results: SimulatorResults) -> str:
        """
        Gráfico tornado de análise de sensibilidade
        Mostra impacto das variáveis nos resultados
        """
        fig, ax = plt.subplots(figsize=(10, 8), dpi=self.dpi)
        
        # Preparar dados de sensibilidade
        variables = []
        impacts = []
        
        if results.sensitivity_discount_rate:
            base_value = list(results.sensitivity_discount_rate.values())[len(results.sensitivity_discount_rate)//2]
            for rate, value in results.sensitivity_discount_rate.items():
                variables.append(f'Taxa Desc. {rate}%')
                impacts.append((value - base_value) / base_value * 100)
        
        # Ordenar por impacto absoluto
        sorted_data = sorted(zip(variables, impacts), key=lambda x: abs(x[1]), reverse=True)
        variables, impacts = zip(*sorted_data)
        
        # Criar gráfico tornado
        colors = [self.colors['success'] if x > 0 else self.colors['warning'] for x in impacts]
        bars = ax.barh(range(len(variables)), impacts, color=colors, alpha=0.7)
        
        ax.set_yticks(range(len(variables)))
        ax.set_yticklabels(variables)
        ax.set_xlabel('Impacto (%)')
        ax.set_title('Análise de Sensibilidade')
        ax.axvline(x=0, color='black', linewidth=0.8)
        
        # Adicionar valores nas barras
        for i, (bar, impact) in enumerate(zip(bars, impacts)):
            ax.text(impact + (0.5 if impact > 0 else -0.5), i, 
                   f'{impact:.1f}%', ha='left' if impact > 0 else 'right', 
                   va='center')
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def generate_projections_chart(self, results: SimulatorResults) -> str:
        """
        Gráfico de projeções (benefícios vs contribuições)
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), dpi=self.dpi)
        
        years = results.projection_years
        benefits = results.projected_benefits
        contributions = results.projected_contributions
        salaries = results.projected_salaries
        
        # Gráfico superior: Benefícios e Contribuições
        ax1.fill_between(years, benefits, alpha=0.3, color=self.colors['primary'], label='Benefícios')
        ax1.fill_between(years, contributions, alpha=0.3, color=self.colors['secondary'], label='Contribuições')
        ax1.plot(years, benefits, color=self.colors['primary'], linewidth=2)
        ax1.plot(years, contributions, color=self.colors['secondary'], linewidth=2)
        
        ax1.set_ylabel('Valor Anual (R$)')
        ax1.set_title('Projeção de Benefícios e Contribuições')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Gráfico inferior: Evolução Salarial
        ax2.plot(years, salaries, color=self.colors['success'], linewidth=2, label='Salário Projetado')
        ax2.set_xlabel('Ano')
        ax2.set_ylabel('Salário (R$)')
        ax2.set_title('Evolução Salarial')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def generate_cash_flow_chart(self, results: SimulatorResults) -> str:
        """
        Gráfico de fluxo de caixa acumulado
        """
        fig, ax = plt.subplots(figsize=(12, 6), dpi=self.dpi)
        
        years = results.projection_years
        contributions = results.projected_contributions
        benefits = results.projected_benefits
        
        # Calcular fluxo acumulado
        net_flow = [c - b for c, b in zip(contributions, benefits)]
        cumulative_flow = np.cumsum(net_flow)
        
        # Gráfico de área com cores condicionais
        positive_mask = cumulative_flow >= 0
        ax.fill_between(years, cumulative_flow, 0, 
                       where=positive_mask, color=self.colors['success'], 
                       alpha=0.6, label='Superávit Acumulado')
        ax.fill_between(years, cumulative_flow, 0, 
                       where=~positive_mask, color=self.colors['warning'], 
                       alpha=0.6, label='Déficit Acumulado')
        
        ax.plot(years, cumulative_flow, color='black', linewidth=2)
        ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        ax.set_xlabel('Ano')
        ax.set_ylabel('Fluxo Acumulado (R$)')
        ax.set_title('Fluxo de Caixa Acumulado')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def generate_scenarios_chart(self, results: SimulatorResults) -> str:
        """
        Gráfico de cenários (melhor caso, base, pior caso)
        """
        fig, ax = plt.subplots(figsize=(10, 6), dpi=self.dpi)
        
        scenarios = ['Pior Caso', 'Caso Base', 'Melhor Caso']
        rmba_values = [
            results.worst_case_scenario.get('rmba', results.rmba * 0.8),
            results.rmba,
            results.best_case_scenario.get('rmba', results.rmba * 1.2)
        ]
        
        bars = ax.bar(scenarios, rmba_values, 
                     color=[self.colors['warning'], self.colors['info'], self.colors['success']], 
                     alpha=0.7)
        
        # Adicionar valores nas barras
        for bar, value in zip(bars, rmba_values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + value*0.01,
                   f'R$ {value:,.0f}', ha='center', va='bottom', fontweight='bold')
        
        ax.set_ylabel('RMBA (R$)')
        ax.set_title('Análise de Cenários')
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x/1000:.0f}K'))
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _fig_to_base64(self, fig: Figure) -> str:
        """Converter figura matplotlib para string base64"""
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=self.dpi, bbox_inches='tight')
        buffer.seek(0)
        
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close(fig)  # Liberar memória
        
        return f"data:image/png;base64,{image_base64}"
```

### 3.4 DataExporter (`data_exporter.py`)

```python
import pandas as pd
from pathlib import Path
import csv
from typing import Dict, Any

class DataExporter:
    """Classe para exportação de dados (Excel/CSV)"""
    
    def __init__(self, config: ReportConfig):
        self.config = config
    
    def export_to_excel(
        self, 
        state: SimulatorState, 
        results: SimulatorResults
    ) -> bytes:
        """Exportar dados completos para Excel"""
        
        # Criar múltiplas abas
        with pd.ExcelWriter(BytesIO(), engine='openpyxl') as writer:
            
            # Aba 1: Resumo Executivo
            summary_data = self._prepare_summary_data(state, results)
            pd.DataFrame([summary_data]).to_excel(
                writer, sheet_name='Resumo Executivo', index=False
            )
            
            # Aba 2: Premissas
            assumptions_data = self._prepare_assumptions_data(state)
            pd.DataFrame([assumptions_data]).to_excel(
                writer, sheet_name='Premissas', index=False
            )
            
            # Aba 3: Projeções Anuais
            projections_df = self._prepare_projections_data(results)
            projections_df.to_excel(
                writer, sheet_name='Projeções Anuais', index=False
            )
            
            # Aba 4: Análise de Sensibilidade
            sensitivity_df = self._prepare_sensitivity_data(results)
            sensitivity_df.to_excel(
                writer, sheet_name='Sensibilidade', index=False
            )
            
            # Aba 5: Cenários
            scenarios_df = self._prepare_scenarios_data(results)
            scenarios_df.to_excel(
                writer, sheet_name='Cenários', index=False
            )
        
        return writer.book
    
    def export_to_csv(
        self, 
        state: SimulatorState, 
        results: SimulatorResults
    ) -> bytes:
        """Exportar projeções principais para CSV"""
        
        projections_df = self._prepare_projections_data(results)
        
        output = BytesIO()
        projections_df.to_csv(output, index=False, encoding='utf-8-sig')
        
        return output.getvalue()
    
    def _prepare_summary_data(self, state: SimulatorState, results: SimulatorResults) -> Dict[str, Any]:
        """Preparar dados do resumo executivo"""
        return {
            'Data_Calculo': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'Idade_Participante': state.age,
            'Genero': state.gender,
            'Salario_Atual': state.salary,
            'Idade_Aposentadoria': state.retirement_age,
            'Taxa_Contribuicao': f"{state.contribution_rate}%",
            'RMBA': results.rmba,
            'RMBC': results.rmbc,
            'Superavit_Deficit': results.deficit_surplus,
            'Superavit_Percentual': f"{results.deficit_surplus_percentage:.2f}%",
            'Taxa_Reposicao': f"{results.replacement_ratio:.2f}%",
            'Taxa_Contribuicao_Necessaria': f"{results.required_contribution_rate:.2f}%",
            'Total_Contribuicoes': results.total_contributions,
            'Total_Beneficios': results.total_benefits,
            'Tabua_Mortalidade': state.mortality_table,
            'Taxa_Desconto': f"{state.discount_rate*100:.2f}%",
            'Crescimento_Salarial': f"{state.salary_growth_real*100:.2f}%"
        }
    
    def _prepare_projections_data(self, results: SimulatorResults) -> pd.DataFrame:
        """Preparar dados das projeções anuais"""
        return pd.DataFrame({
            'Ano': results.projection_years,
            'Salario_Projetado': results.projected_salaries,
            'Contribuicao_Anual': results.projected_contributions,
            'Beneficio_Anual': results.projected_benefits,
            'Reserva_Acumulada': results.accumulated_reserves,
            'Probabilidade_Sobrevivencia': results.survival_probabilities,
            'VPA_Beneficios': results.projected_vpa_benefits,
            'VPA_Contribuicoes': results.projected_vpa_contributions,
            'RMBA_Evolucao': results.projected_rmba_evolution
        })
```

## 4. Templates HTML

### 4.1 Template Base (`templates/base_report.html`)

```html
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link href="{{ url_for('static', filename='styles.css') }}" rel="stylesheet">
    <style>
        @page {
            size: A4;
            margin: 2cm 1.5cm;
            @top-center { content: "{{ config.company_name }}"; }
            @bottom-center { content: "Página " counter(page) " de " counter(pages); }
        }
        
        body {
            font-family: 'Arial', sans-serif;
            line-height: 1.4;
            color: #333;
        }
        
        .page-break { page-break-after: always; }
        .no-break { page-break-inside: avoid; }
        
        .header {
            border-bottom: 2px solid #2E86AB;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .kpi-card {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            background: #f8f9fa;
        }
        
        .chart-container {
            text-align: center;
            margin: 20px 0;
        }
        
        .chart-container img {
            max-width: 100%;
            height: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        
        .recommendation {
            margin: 15px 0;
            padding: 15px;
            border-radius: 5px;
        }
        
        .recommendation.warning {
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
        }
        
        .recommendation.info {
            background-color: #d1ecf1;
            border-left: 4px solid #17a2b8;
        }
        
        .recommendation.success {
            background-color: #d4edda;
            border-left: 4px solid #28a745;
        }
    </style>
</head>
<body>
    {% include 'components/header.html' %}
    
    <main>
        {% block content %}{% endblock %}
    </main>
    
    {% include 'components/footer.html' %}
</body>
</html>
```

### 4.2 Template Relatório Executivo (`templates/executive_report.html`)

```html
{% extends "base_report.html" %}

{% block content %}
<!-- Página 1: Resumo Executivo -->
<div class="executive-summary">
    <h1>Relatório Executivo - Simulação Atuarial Individual</h1>
    
    <div class="participant-info">
        <h2>Dados do Participante</h2>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div>
                <p><strong>Idade:</strong> {{ state.age }} anos</p>
                <p><strong>Gênero:</strong> {{ 'Masculino' if state.gender == 'M' else 'Feminino' }}</p>
                <p><strong>Salário Atual:</strong> R$ {{ "{:,.2f}".format(state.salary) }}</p>
                <p><strong>Idade de Aposentadoria:</strong> {{ state.retirement_age }} anos</p>
            </div>
            <div>
                <p><strong>Taxa de Contribuição:</strong> {{ state.contribution_rate }}%</p>
                <p><strong>Tábua de Mortalidade:</strong> {{ state.mortality_table }}</p>
                <p><strong>Taxa de Desconto:</strong> {{ (state.discount_rate * 100)|round(2) }}%</p>
                <p><strong>Data do Cálculo:</strong> {{ generation_date }}</p>
            </div>
        </div>
    </div>
    
    <div class="kpi-section">
        <h2>Indicadores Principais</h2>
        <div class="kpi-grid">
            <div class="kpi-card">
                <h3>RMBA</h3>
                <p class="kpi-value">R$ {{ "{:,.0f}".format(kpis.rmba) }}</p>
                <small>Reserva Matemática de Benefícios a Conceder</small>
            </div>
            <div class="kpi-card">
                <h3>RMBC</h3>
                <p class="kpi-value">R$ {{ "{:,.0f}".format(kpis.rmbc) }}</p>
                <small>Reserva Matemática de Benefícios Concedidos</small>
            </div>
            <div class="kpi-card">
                <h3>Superávit/Déficit</h3>
                <p class="kpi-value {{ 'positive' if kpis.superavit > 0 else 'negative' }}">
                    {{ "{:.1f}".format(kpis.superavit_percentage) }}%
                </p>
                <small>R$ {{ "{:,.0f}".format(kpis.superavit) }}</small>
            </div>
            <div class="kpi-card">
                <h3>Taxa de Reposição</h3>
                <p class="kpi-value">{{ "{:.1f}".format(kpis.replacement_ratio) }}%</p>
                <small>Percentual do salário coberto</small>
            </div>
        </div>
    </div>
    
    {% if charts.reserve_evolution %}
    <div class="chart-container no-break">
        <h3>Evolução das Reservas Matemáticas</h3>
        <img src="{{ charts.reserve_evolution }}" alt="Evolução das Reservas">
    </div>
    {% endif %}
</div>

<div class="page-break"></div>

<!-- Página 2: Análise e Cenários -->
<div class="analysis-section">
    <h2>Análise de Sensibilidade</h2>
    
    {% if charts.sensitivity_tornado %}
    <div class="chart-container">
        <img src="{{ charts.sensitivity_tornado }}" alt="Análise de Sensibilidade">
    </div>
    {% endif %}
    
    <h2>Projeções Financeiras</h2>
    
    {% if charts.projections %}
    <div class="chart-container">
        <img src="{{ charts.projections }}" alt="Projeções Financeiras">
    </div>
    {% endif %}
    
    <div class="scenarios-summary">
        <h3>Resumo de Cenários</h3>
        <table>
            <thead>
                <tr>
                    <th>Cenário</th>
                    <th>RMBA (R$)</th>
                    <th>Superávit (%)</th>
                    <th>Taxa Reposição (%)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Pior Caso</td>
                    <td>{{ "{:,.0f}".format(results.worst_case_scenario.get('rmba', kpis.rmba * 0.8)) }}</td>
                    <td>{{ "{:.1f}".format(results.worst_case_scenario.get('superavit_pct', kpis.superavit_percentage - 10)) }}</td>
                    <td>{{ "{:.1f}".format(results.worst_case_scenario.get('replacement_ratio', kpis.replacement_ratio - 15)) }}</td>
                </tr>
                <tr style="background-color: #e3f2fd;">
                    <td><strong>Caso Base</strong></td>
                    <td><strong>{{ "{:,.0f}".format(kpis.rmba) }}</strong></td>
                    <td><strong>{{ "{:.1f}".format(kpis.superavit_percentage) }}</strong></td>
                    <td><strong>{{ "{:.1f}".format(kpis.replacement_ratio) }}</strong></td>
                </tr>
                <tr>
                    <td>Melhor Caso</td>
                    <td>{{ "{:,.0f}".format(results.best_case_scenario.get('rmba', kpis.rmba * 1.2)) }}</td>
                    <td>{{ "{:.1f}".format(results.best_case_scenario.get('superavit_pct', kpis.superavit_percentage + 10)) }}</td>
                    <td>{{ "{:.1f}".format(results.best_case_scenario.get('replacement_ratio', kpis.replacement_ratio + 15)) }}</td>
                </tr>
            </tbody>
        </table>
    </div>
</div>

<div class="page-break"></div>

<!-- Página 3: Recomendações -->
<div class="recommendations-section">
    <h2>Recomendações e Conclusões</h2>
    
    {% for recommendation in recommendations %}
    <div class="recommendation {{ recommendation.type }}">
        <h4>{{ recommendation.title }}</h4>
        <p>{{ recommendation.description }}</p>
    </div>
    {% endfor %}
    
    <div class="conclusion">
        <h3>Conclusão Executiva</h3>
        <p>
            {% if kpis.superavit_percentage > 5 %}
            O plano apresenta situação superavitária com {{ "{:.1f}".format(kpis.superavit_percentage) }}% 
            de superávit, indicando sustentabilidade das contribuições atuais.
            {% elif kpis.superavit_percentage < -5 %}
            O plano apresenta déficit de {{ "{:.1f}".format(abs(kpis.superavit_percentage)) }}%, 
            requerendo ajustes nos parâmetros para garantir sustentabilidade.
            {% else %}
            O plano apresenta equilíbrio atuarial, com pequena variação de 
            {{ "{:.1f}".format(kpis.superavit_percentage) }}%.
            {% endif %}
        </p>
        
        <p>
            A taxa de contribuição necessária para o equilíbrio atuarial é de 
            {{ "{:.2f}".format(kpis.required_contribution) }}%, comparada aos 
            {{ state.contribution_rate }}% atualmente estabelecidos.
        </p>
        
        <p>
            Com os parâmetros atuais, o participante terá uma taxa de reposição de 
            {{ "{:.1f}".format(kpis.replacement_ratio) }}% na aposentadoria.
        </p>
    </div>
    
    <div class="technical-note" style="margin-top: 40px; padding: 20px; background-color: #f8f9fa; border-left: 4px solid #6c757d;">
        <h4>Nota Técnica</h4>
        <p>
            Este relatório foi gerado com base nas premissas atuariais informadas e na 
            tábua de mortalidade {{ state.mortality_table }}. Os resultados são válidos 
            para as condições especificadas e devem ser revisados periodicamente.
        </p>
        <p>
            <strong>Tempo de processamento:</strong> {{ results.computation_time_ms }}ms<br>
            <strong>Método de cálculo:</strong> {{ state.calculation_method }}<br>
            <strong>Gerado em:</strong> {{ generation_date }}
        </p>
    </div>
</div>
{% endblock %}
```

## 5. API Endpoints

### 5.1 Reports Router (`api/reports_router.py`)

```python
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from typing import Optional
import uuid
import asyncio
from pathlib import Path
import os

from ..services.reports.report_generator import ReportGenerator
from ..services.reports.models.report_models import (
    ReportRequest, ReportResponse, PreviewResponse, 
    ReportType, ExportFormat, ReportConfig
)

router = APIRouter(prefix="/reports", tags=["reports"])

# Instância global do gerador
report_generator = ReportGenerator()

@router.post("/executive-pdf", response_class=StreamingResponse)
async def generate_executive_pdf(request: ReportRequest):
    """
    Gerar relatório executivo em PDF
    
    Retorna um stream do arquivo PDF para download direto
    """
    try:
        report_response = await report_generator.generate_executive_report(
            request, ExportFormat.PDF
        )
        
        if not report_response.success:
            raise HTTPException(status_code=500, detail=report_response.message)
        
        # Ler arquivo gerado
        file_path = Path(report_response.file_path)
        
        def iterfile():
            with open(file_path, mode="rb") as file_like:
                yield from file_like
        
        # Headers para download
        headers = {
            'Content-Disposition': f'attachment; filename="relatorio_executivo_{request.state.calculation_id or "sim"}.pdf"',
            'Content-Type': 'application/pdf'
        }
        
        return StreamingResponse(iterfile(), headers=headers)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar relatório: {str(e)}")

@router.post("/technical-pdf", response_class=StreamingResponse)
async def generate_technical_pdf(request: ReportRequest):
    """
    Gerar relatório técnico em PDF
    """
    try:
        report_response = await report_generator.generate_technical_report(
            request, ExportFormat.PDF
        )
        
        if not report_response.success:
            raise HTTPException(status_code=500, detail=report_response.message)
        
        file_path = Path(report_response.file_path)
        
        def iterfile():
            with open(file_path, mode="rb") as file_like:
                yield from file_like
        
        headers = {
            'Content-Disposition': f'attachment; filename="relatorio_tecnico_{request.state.calculation_id or "sim"}.pdf"',
            'Content-Type': 'application/pdf'
        }
        
        return StreamingResponse(iterfile(), headers=headers)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar relatório: {str(e)}")

@router.post("/data-excel", response_class=StreamingResponse)
async def export_data_excel(request: ReportRequest):
    """
    Exportar dados completos em Excel
    """
    try:
        report_response = await report_generator.generate_data_export(
            request, ExportFormat.EXCEL
        )
        
        if not report_response.success:
            raise HTTPException(status_code=500, detail=report_response.message)
        
        file_path = Path(report_response.file_path)
        
        def iterfile():
            with open(file_path, mode="rb") as file_like:
                yield from file_like
        
        headers = {
            'Content-Disposition': f'attachment; filename="dados_simulacao_{request.state.calculation_id or "sim"}.xlsx"',
            'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        
        return StreamingResponse(iterfile(), headers=headers)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao exportar dados: {str(e)}")

@router.post("/data-csv", response_class=StreamingResponse)
async def export_data_csv(request: ReportRequest):
    """
    Exportar projeções em CSV
    """
    try:
        report_response = await report_generator.generate_data_export(
            request, ExportFormat.CSV
        )
        
        if not report_response.success:
            raise HTTPException(status_code=500, detail=report_response.message)
        
        file_path = Path(report_response.file_path)
        
        def iterfile():
            with open(file_path, mode="rb") as file_like:
                yield from file_like
        
        headers = {
            'Content-Disposition': f'attachment; filename="projecoes_{request.state.calculation_id or "sim"}.csv"',
            'Content-Type': 'text/csv'
        }
        
        return StreamingResponse(iterfile(), headers=headers)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao exportar CSV: {str(e)}")

@router.post("/preview-executive")
async def preview_executive_report(request: ReportRequest) -> PreviewResponse:
    """
    Gerar preview HTML do relatório executivo
    """
    try:
        preview = await report_generator.preview_report(request, ReportType.EXECUTIVE)
        return preview
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar preview: {str(e)}")

@router.post("/preview-technical")
async def preview_technical_report(request: ReportRequest) -> PreviewResponse:
    """
    Gerar preview HTML do relatório técnico
    """
    try:
        preview = await report_generator.preview_report(request, ReportType.TECHNICAL)
        return preview
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar preview: {str(e)}")

@router.get("/health")
async def reports_health_check():
    """Health check do sistema de relatórios"""
    return {
        "status": "healthy",
        "service": "reports",
        "cache_files": len(list(report_generator.cache_dir.iterdir())),
        "version": "1.0.0"
    }

@router.delete("/cache/cleanup")
async def cleanup_cache():
    """Limpar cache de relatórios manualmente"""
    try:
        report_generator._cleanup_cache()
        remaining_files = len(list(report_generator.cache_dir.iterdir()))
        return {
            "success": True,
            "message": "Cache limpo com sucesso",
            "remaining_files": remaining_files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao limpar cache: {str(e)}")
```

## 6. Integração com Main API

### 6.1 Atualizar `main.py`

```python
# Adicionar import
from .api.reports_router import router as reports_router

# Adicionar após as outras rotas
app.include_router(reports_router)
```

## 7. Instalação e Configuração

### 7.1 Script de Instalação (`scripts/install_reports.py`)

```python
#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path

def install_dependencies():
    """Instalar todas as dependências necessárias"""
    dependencies = [
        "reportlab==4.0.7",
        "matplotlib==3.8.2", 
        "jinja2==3.1.2",
        "weasyprint==61.2",
        "pillow==10.1.0",
        "pandas==2.1.4",
        "openpyxl==3.1.2"
    ]
    
    for dep in dependencies:
        print(f"Instalando {dep}...")
        subprocess.run([sys.executable, "-m", "uv", "add", dep], check=True)

def setup_directories():
    """Criar estrutura de diretórios necessária"""
    base_dir = Path(__file__).parent.parent / "src" / "services" / "reports"
    
    directories = [
        base_dir,
        base_dir / "templates" / "components",
        base_dir / "static" / "fonts", 
        base_dir / "cache",
        base_dir / "models"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Diretório criado: {directory}")

if __name__ == "__main__":
    print("Configurando sistema de relatórios...")
    
    try:
        install_dependencies()
        setup_directories()
        print("✅ Sistema de relatórios configurado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro na configuração: {e}")
        sys.exit(1)
```

## 8. Testes

### 8.1 Testes Unitários (`tests/test_reports.py`)

```python
import pytest
from pathlib import Path
import tempfile
from unittest.mock import Mock

from src.services.reports.report_generator import ReportGenerator
from src.services.reports.models.report_models import ReportRequest, ReportConfig
from src.models import SimulatorState, SimulatorResults

@pytest.fixture
def mock_state():
    """Estado mockado para testes"""
    return SimulatorState(
        age=35,
        gender="M",
        salary=10000.0,
        plan_type="BD",
        initial_balance=0.0,
        benefit_target_mode="VALUE",
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

@pytest.fixture  
def mock_results():
    """Resultados mockados para testes"""
    return SimulatorResults(
        rmba=450000.0,
        rmbc=380000.0,
        normal_cost=25000.0,
        deficit_surplus=70000.0,
        deficit_surplus_percentage=15.5,
        required_contribution_rate=8.5,
        projection_years=list(range(2024, 2054)),
        projected_salaries=[10000 * (1.02 ** i) for i in range(30)],
        projected_benefits=[6000 * (1.02 ** i) for i in range(30)],
        projected_contributions=[1000 * (1.02 ** i) for i in range(30)],
        survival_probabilities=[0.99 - (i * 0.01) for i in range(30)],
        accumulated_reserves=[10000 * i for i in range(30)],
        projected_vpa_benefits=[5000 * i for i in range(30)],
        projected_vpa_contributions=[800 * i for i in range(30)],
        projected_rmba_evolution=[400000 + (i * 1000) for i in range(30)],
        total_contributions=240000.0,
        total_benefits=180000.0,
        replacement_ratio=60.0,
        target_replacement_ratio=60.0,
        sustainable_replacement_ratio=58.5,
        sensitivity_discount_rate={4: 480000, 5: 450000, 6: 420000, 7: 390000},
        sensitivity_mortality={"base": 450000, "aggravated": 470000},
        sensitivity_retirement_age={60: 520000, 65: 450000, 70: 380000},
        sensitivity_salary_growth={1: 430000, 2: 450000, 3: 470000},
        sensitivity_inflation={2: 440000, 3: 450000, 4: 460000},
        actuarial_present_value_benefits=420000.0,
        actuarial_present_value_salary=280000.0,
        service_cost_breakdown={"normal_cost": 25000, "interest": 15000},
        liability_duration=12.5,
        convexity=156.7,
        best_case_scenario={"rmba": 540000, "superavit_pct": 25.0, "replacement_ratio": 75.0},
        worst_case_scenario={"rmba": 360000, "superavit_pct": 5.0, "replacement_ratio": 45.0},
        confidence_intervals={"rmba": [400000, 500000], "replacement_ratio": [55.0, 65.0]},
        calculation_timestamp="2024-01-15T10:30:00",
        computation_time_ms=1250,
        actuarial_method_details={"method": "PUC", "iterations": 100},
        assumptions_validation={"discount_rate": True, "mortality": True}
    )

class TestReportGenerator:
    """Testes para a classe ReportGenerator"""
    
    def test_init(self):
        """Testar inicialização do gerador"""
        config = ReportConfig(company_name="Teste Corp")
        generator = ReportGenerator(config)
        
        assert generator.config.company_name == "Teste Corp"
        assert generator.template_dir.exists()
        assert generator.cache_dir.exists()
    
    @pytest.mark.asyncio
    async def test_generate_executive_report(self, mock_state, mock_results):
        """Testar geração do relatório executivo"""
        config = ReportConfig()
        generator = ReportGenerator(config)
        
        request = ReportRequest(state=mock_state, results=mock_results)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            generator.cache_dir = Path(temp_dir)
            
            response = await generator.generate_executive_report(request)
            
            assert response.success == True
            assert response.file_path is not None
            assert Path(response.file_path).exists()
            assert response.generation_time_ms > 0
    
    @pytest.mark.asyncio  
    async def test_generate_technical_report(self, mock_state, mock_results):
        """Testar geração do relatório técnico"""
        config = ReportConfig()
        generator = ReportGenerator(config)
        
        request = ReportRequest(state=mock_state, results=mock_results)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            generator.cache_dir = Path(temp_dir)
            
            response = await generator.generate_technical_report(request)
            
            assert response.success == True
            assert response.file_path is not None
            assert Path(response.file_path).exists()
    
    def test_cleanup_cache(self):
        """Testar limpeza do cache"""
        config = ReportConfig()
        generator = ReportGenerator(config)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            generator.cache_dir = Path(temp_dir)
            
            # Criar arquivos de teste
            old_file = generator.cache_dir / "old_report.pdf"
            old_file.touch()
            
            # Modificar timestamp para ser antigo
            import os
            import time
            old_timestamp = time.time() - (3 * 3600)  # 3 horas atrás
            os.utime(old_file, (old_timestamp, old_timestamp))
            
            generator._cleanup_cache()
            
            assert not old_file.exists()

class TestChartGenerator:
    """Testes para geração de gráficos"""
    
    def test_generate_reserve_evolution_chart(self, mock_results):
        """Testar geração do gráfico de evolução de reservas"""
        from src.services.reports.chart_generator import ChartGenerator
        
        config = ReportConfig()
        generator = ChartGenerator(config)
        
        chart_data = generator.generate_reserve_evolution_chart(mock_results)
        
        assert chart_data.startswith("data:image/png;base64,")
        assert len(chart_data) > 1000  # Assumindo que imagem tem tamanho razoável
    
    def test_generate_all_charts(self, mock_results):
        """Testar geração de todos os gráficos"""
        from src.services.reports.chart_generator import ChartGenerator
        
        config = ReportConfig()
        generator = ChartGenerator(config)
        
        charts = generator.generate_all_charts(mock_results)
        
        expected_charts = [
            'reserve_evolution', 'sensitivity_tornado', 'projections', 
            'cash_flow', 'scenarios'
        ]
        
        for chart_name in expected_charts:
            assert chart_name in charts
            assert charts[chart_name].startswith("data:image/png;base64,")

class TestDataExporter:
    """Testes para exportação de dados"""
    
    def test_export_to_excel(self, mock_state, mock_results):
        """Testar export para Excel"""
        from src.services.reports.data_exporter import DataExporter
        
        config = ReportConfig()
        exporter = DataExporter(config)
        
        excel_data = exporter.export_to_excel(mock_state, mock_results)
        
        assert len(excel_data) > 1000  # Arquivo deve ter tamanho razoável
        
    def test_export_to_csv(self, mock_state, mock_results):
        """Testar export para CSV"""
        from src.services.reports.data_exporter import DataExporter
        
        config = ReportConfig()
        exporter = DataExporter(config)
        
        csv_data = exporter.export_to_csv(mock_state, mock_results)
        csv_content = csv_data.decode('utf-8-sig')
        
        assert "Ano" in csv_content
        assert "Salario_Projetado" in csv_content
        assert len(csv_content.split('\n')) > 30  # Deve ter pelo menos 30 linhas
```

## 9. Cronograma de Implementação

### Fase 1 - Implementação Base (2-3 dias)

**Dia 1:**
- [ ] Executar script de instalação de dependências  
- [ ] Criar estrutura de diretórios
- [ ] Implementar classes base (ReportGenerator, PDFGenerator)
- [ ] Criar templates HTML básicos

**Dia 2:**
- [ ] Implementar ChartGenerator completo
- [ ] Finalizar template do relatório executivo
- [ ] Implementar geração de PDF executivo
- [ ] Criar endpoints básicos da API

**Dia 3:**
- [ ] Implementar template do relatório técnico
- [ ] Finalizar DataExporter (Excel/CSV)
- [ ] Implementar sistema de cache
- [ ] Criar testes unitários básicos

### Critérios de Aceite

- [ ] PDFs executivo e técnico são gerados corretamente
- [ ] Gráficos são incluídos nos relatórios com qualidade adequada
- [ ] Exports Excel/CSV contêm todos os dados necessários  
- [ ] API endpoints funcionam via REST
- [ ] Sistema de cache funciona corretamente
- [ ] Testes unitários passam com ≥80% coverage
- [ ] Documentação está completa e atualizada

### Métricas de Qualidade

- **Performance**: Geração de relatório executivo em ≤5s
- **Tamanho**: PDF executivo ≤2MB, técnico ≤5MB  
- **Qualidade**: Gráficos em 300 DPI mínimo
- **Compatibilidade**: PDFs compatíveis com Adobe Reader/navegadores
- **Robustez**: Sistema lida com dados faltantes graciosamente

---

**Total estimado: 20-24 horas de desenvolvimento**

Esta especificação fornece uma base sólida para implementar um sistema completo de relatórios profissionais para o simulador atuarial.