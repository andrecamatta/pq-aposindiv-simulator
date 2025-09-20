"""
Gerador de PDFs para relatórios executivos usando WeasyPrint
"""
import uuid
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from io import BytesIO

from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader
import tempfile

from .models.report_models import ReportConfig, ReportRequest, ReportResponse
from .chart_generator import ChartGenerator
from ...models.participant import SimulatorState
from ...models.results import SimulatorResults


class PDFGenerator:
    """Classe principal para geração de PDFs executivos"""

    def __init__(self, config: Optional[ReportConfig] = None):
        self.config = config or ReportConfig()
        self.templates_dir = Path(__file__).parent / "templates"
        self.static_dir = Path(__file__).parent / "static"
        self.cache_dir = Path(__file__).parent / "cache"

        # Garantir que diretórios existem
        self.cache_dir.mkdir(exist_ok=True)

        # Configurar Jinja2
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True
        )

        # Registrar filtros customizados
        self._register_template_filters()

        # Inicializar gerador de gráficos
        self.chart_generator = ChartGenerator(self.config)

    def generate_executive_pdf(self, request: ReportRequest) -> ReportResponse:
        """
        Gerar PDF do relatório executivo
        """
        start_time = time.time()
        report_id = str(uuid.uuid4())

        try:
            # Gerar gráficos
            charts = self.chart_generator.generate_all_charts(request.results)

            # Renderizar HTML
            html_content = self._render_executive_template(
                request.state, request.results, charts
            )

            # Gerar PDF
            pdf_bytes = self._html_to_pdf(html_content)

            # Salvar arquivo no cache
            file_path = self.cache_dir / f"executive_report_{report_id}.pdf"
            with open(file_path, 'wb') as f:
                f.write(pdf_bytes)

            generation_time = int((time.time() - start_time) * 1000)

            return ReportResponse(
                success=True,
                message="Relatório executivo gerado com sucesso",
                file_path=str(file_path),
                file_size=len(pdf_bytes),
                generation_time_ms=generation_time,
                report_id=report_id,
                content_type="application/pdf"
            )

        except Exception as e:
            generation_time = int((time.time() - start_time) * 1000)
            return ReportResponse(
                success=False,
                message=f"Erro ao gerar relatório: {str(e)}",
                generation_time_ms=generation_time,
                report_id=report_id
            )

    def generate_technical_pdf(self, request: ReportRequest) -> ReportResponse:
        """
        Gerar PDF do relatório técnico atuarial
        """
        start_time = time.time()
        report_id = str(uuid.uuid4())

        try:
            # Gerar gráficos técnicos
            charts = self.chart_generator.generate_all_charts(request.results, chart_type='technical')

            # Renderizar HTML
            html_content = self._render_technical_template(
                request.state, request.results, charts, report_id
            )

            # Gerar PDF
            pdf_bytes = self._html_to_pdf(html_content)

            # Salvar arquivo no cache
            file_path = self.cache_dir / f"technical_report_{report_id}.pdf"
            with open(file_path, 'wb') as f:
                f.write(pdf_bytes)

            generation_time = int((time.time() - start_time) * 1000)

            return ReportResponse(
                success=True,
                message="Relatório técnico gerado com sucesso",
                file_path=str(file_path),
                file_size=len(pdf_bytes),
                generation_time_ms=generation_time,
                report_id=report_id,
                content_type="application/pdf"
            )

        except Exception as e:
            generation_time = int((time.time() - start_time) * 1000)
            return ReportResponse(
                success=False,
                message=f"Erro ao gerar relatório técnico: {str(e)}",
                generation_time_ms=generation_time,
                report_id=report_id
            )

    def _render_executive_template(
        self,
        state: SimulatorState,
        results: SimulatorResults,
        charts: Dict[str, str]
    ) -> str:
        """Renderizar template HTML do relatório executivo"""

        # Extrair KPIs principais
        kpis = self._extract_kpis(state, results)

        # Gerar recomendações
        recommendations = self._generate_recommendations(state, results)

        # Análise de situação
        situation = self._analyze_situation(state, results)

        # Contexto para o template
        context = {
            'config': self.config,
            'state': state,
            'results': results,
            'charts': charts,
            'kpis': kpis,
            'recommendations': recommendations,
            'situation': situation,
            'generation_date': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'is_cd': state.plan_type == 'CD',
            'is_bd': state.plan_type == 'BD'
        }

        template = self.jinja_env.get_template('executive_report.html')
        return template.render(**context)

    def _html_to_pdf(self, html_content: str) -> bytes:
        """Converter HTML para PDF usando WeasyPrint"""
        css_file = self.static_dir / "styles.css"

        # HTML documento
        html_doc = HTML(string=html_content, base_url=str(self.static_dir))

        # CSS stylesheet
        stylesheets = []
        if css_file.exists():
            stylesheets.append(CSS(filename=str(css_file)))

        # Gerar PDF
        pdf_bytes = html_doc.write_pdf(stylesheets=stylesheets)
        return pdf_bytes

    def _extract_kpis(self, state: SimulatorState, results: SimulatorResults) -> Dict:
        """Extrair KPIs principais baseado no tipo de plano"""

        if state.plan_type == 'CD':
            return {
                'saldo_final': getattr(results, 'individual_balance', 0) or 0,
                'renda_mensal': getattr(results, 'monthly_income_cd', 0) or 0,
                'rendimento_total': getattr(results, 'accumulated_return', 0) or 0,
                'taxa_reposicao': results.replacement_ratio or 0,
                'taxa_reposicao_meta': state.target_replacement_rate or 70,
                'modalidade_conversao': state.cd_conversion_mode or 'ACTUARIAL',
                'duracao_beneficios': getattr(results, 'benefit_duration_years', 0) or 0
            }
        else:
            return {
                'rmba': results.rmba or 0,
                'rmbc': results.rmbc or 0,
                'deficit_surplus': results.deficit_surplus or 0,
                'deficit_surplus_pct': getattr(results, 'deficit_surplus_percentage', 0) or 0,
                'taxa_reposicao': results.replacement_ratio or 0,
                'taxa_reposicao_meta': results.target_replacement_ratio or 0,
                'taxa_reposicao_sustentavel': getattr(results, 'sustainable_replacement_ratio', 0) or 0,
                'contribuicao_necessaria': results.required_contribution_rate or 0,
                'contribuicao_atual': state.contribution_rate or 0
            }

    def _analyze_situation(self, state: SimulatorState, results: SimulatorResults) -> Dict:
        """Analisar situação geral do plano"""

        if state.plan_type == 'CD':
            replacement_ratio = results.replacement_ratio or 0
            target_rate = state.target_replacement_rate or 70
            adequacy_ratio = replacement_ratio / target_rate if target_rate > 0 else 0

            if adequacy_ratio >= 1.1:
                return {
                    'status': 'Excelente',
                    'color': 'success',
                    'description': 'Renda projetada supera significativamente a meta de aposentadoria'
                }
            elif adequacy_ratio >= 0.9:
                return {
                    'status': 'Adequada',
                    'color': 'info',
                    'description': 'Renda projetada atende à meta estabelecida'
                }
            elif adequacy_ratio >= 0.7:
                return {
                    'status': 'Atenção',
                    'color': 'warning',
                    'description': 'Renda projetada abaixo da meta, requer monitoramento'
                }
            else:
                return {
                    'status': 'Crítica',
                    'color': 'danger',
                    'description': 'Renda projetada muito abaixo da meta, ação necessária'
                }
        else:
            deficit_surplus = results.deficit_surplus or 0

            if deficit_surplus > 100000:
                return {
                    'status': 'Superavitário',
                    'color': 'success',
                    'description': 'Plano com reservas suficientes e folga financeira'
                }
            elif deficit_surplus >= 0:
                return {
                    'status': 'Equilibrado',
                    'color': 'info',
                    'description': 'Reservas adequadas às obrigações atuariais'
                }
            elif deficit_surplus > -100000:
                return {
                    'status': 'Atenção',
                    'color': 'warning',
                    'description': 'Pequeno déficit atuarial, monitoramento necessário'
                }
            else:
                return {
                    'status': 'Crítico',
                    'color': 'danger',
                    'description': 'Déficit significativo, ação imediata necessária'
                }

    def _generate_recommendations(self, state: SimulatorState, results: SimulatorResults) -> list:
        """Gerar recomendações automáticas baseadas nos resultados"""
        recommendations = []

        if state.plan_type == 'CD':
            # Recomendações para CD
            replacement_ratio = results.replacement_ratio or 0
            target_rate = state.target_replacement_rate or 70

            if replacement_ratio < target_rate * 0.8:
                recommendations.append({
                    'type': 'warning',
                    'title': 'Taxa de Reposição Insuficiente',
                    'description': f'Taxa atual ({replacement_ratio:.1f}%) muito abaixo da meta ({target_rate:.1f}%). Considere aumentar a contribuição ou revisar a estratégia de investimento.'
                })

            if state.cd_conversion_mode == 'ACTUARIAL_EQUIVALENT':
                recommendations.append({
                    'type': 'info',
                    'title': 'Equivalência Atuarial Selecionada',
                    'description': 'Modalidade escolhida oferece flexibilidade com recálculo anual do benefício, proporcionando proteção contra longevidade.'
                })

            if replacement_ratio > target_rate * 1.2:
                recommendations.append({
                    'type': 'success',
                    'title': 'Meta Superada',
                    'description': f'Taxa de reposição ({replacement_ratio:.1f}%) supera a meta. Considere otimizar contribuições ou aumentar benefício alvo.'
                })

        else:
            # Recomendações para BD
            deficit_surplus = results.deficit_surplus or 0

            if deficit_surplus < -50000:
                recommendations.append({
                    'type': 'warning',
                    'title': 'Déficit Atuarial Identificado',
                    'description': f'Déficit de R$ {abs(deficit_surplus):,.0f}. Revisar contribuições ou benefícios para equilibrar o plano.'
                })

            required_rate = results.required_contribution_rate or 0
            current_rate = state.contribution_rate or 0

            if required_rate > current_rate * 1.2:
                recommendations.append({
                    'type': 'warning',
                    'title': 'Contribuição Insuficiente',
                    'description': f'Taxa necessária ({required_rate:.1f}%) supera a atual ({current_rate:.1f}%). Ajuste gradual recomendado.'
                })

        # Recomendações gerais
        years_to_retirement = state.retirement_age - state.age
        if years_to_retirement < 10:
            recommendations.append({
                'type': 'info',
                'title': 'Próximo à Aposentadoria',
                'description': 'Considere estratégias mais conservadoras e revisão periódica das premissas.'
            })

        if not recommendations:
            recommendations.append({
                'type': 'success',
                'title': 'Situação Adequada',
                'description': 'Os parâmetros atuais apresentam resultados satisfatórios. Mantenha acompanhamento periódico.'
            })

        return recommendations

    def _register_template_filters(self):
        """Registrar filtros customizados para os templates"""

        def format_currency(value, precision=0):
            """Filtro para formatação de moeda brasileira"""
            try:
                if value is None:
                    return "R$ 0,00"

                if precision == 0:
                    return f"R$ {value:,.0f}".replace(',', '.')
                else:
                    formatted = f"R$ {value:,.{precision}f}"
                    return formatted.replace(',', '_').replace('.', ',').replace('_', '.')
            except:
                return "R$ 0,00"

        def format_percentage(value, precision=1):
            """Filtro para formatação de percentual"""
            try:
                if value is None:
                    return "0,0%"
                return f"{value:.{precision}f}%".replace('.', ',')
            except:
                return "0,0%"

        def format_date_br(value):
            """Filtro para formatação de data brasileira"""
            if isinstance(value, str):
                return value
            return value.strftime('%d/%m/%Y') if value else ""

        def safe_default(value, default="N/A"):
            """Filtro para valores seguros com fallback"""
            if value is None or value == "":
                return default
            return value

        def safe_length(value):
            """Filtro para obter tamanho seguro de listas"""
            try:
                if value is None:
                    return 0
                return len(value)
            except:
                return 0

        # Registrar filtros
        self.jinja_env.filters['currency'] = format_currency
        self.jinja_env.filters['percentage'] = format_percentage
        self.jinja_env.filters['date_br'] = format_date_br
        self.jinja_env.filters['safe_default'] = safe_default
        self.jinja_env.filters['safe_length'] = safe_length

    def _render_technical_template(
        self,
        state: SimulatorState,
        results: SimulatorResults,
        charts: Dict[str, str],
        report_id: str
    ) -> str:
        """Renderizar template HTML do relatório técnico"""

        # Validar e sanitizar dados
        validated_results = self._validate_results_data(results)

        print(f"[TECHNICAL_REPORT] Validando dados: projections={len(validated_results.projection_years or [])}, charts={len(charts)}")

        # Extrair KPIs principais
        kpis = self._extract_kpis(state, validated_results)

        # Gerar recomendações técnicas específicas
        recommendations = self._generate_technical_recommendations(state, validated_results)

        # Análise de situação técnica
        situation = self._analyze_situation(state, validated_results)

        # Contexto para o template técnico
        context = {
            'config': self.config,
            'state': state,
            'results': validated_results,
            'charts': charts,
            'kpis': kpis,
            'recommendations': recommendations,
            'situation': situation,
            'generation_date': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'is_cd': state.plan_type == 'CD',
            'is_bd': state.plan_type == 'BD',
            'report_id': report_id
        }

        template = self.jinja_env.get_template('technical_report.html')
        return template.render(**context)

    def _validate_results_data(self, results: SimulatorResults) -> SimulatorResults:
        """Validar e garantir que todos os campos necessários estão preenchidos"""
        # Criar cópia dos resultados para não modificar o original
        validated_data = results.dict()

        # Validar vetores de projeção - garantir que tenham tamanho mínimo
        if not validated_data.get('projection_years') or len(validated_data['projection_years']) == 0:
            print("[VALIDATION] Criando vetores de projeção padrão")
            # Criar vetores padrão baseados em 30 anos
            years_count = 30
            current_year = datetime.now().year
            validated_data['projection_years'] = list(range(current_year, current_year + years_count))
            validated_data['projected_salaries'] = [0.0] * years_count
            validated_data['projected_benefits'] = [0.0] * years_count
            validated_data['projected_contributions'] = [0.0] * years_count
            validated_data['survival_probabilities'] = [1.0] * years_count
            validated_data['accumulated_reserves'] = [0.0] * years_count
            validated_data['projected_vpa_benefits'] = [0.0] * years_count
            validated_data['projected_vpa_contributions'] = [0.0] * years_count
            validated_data['projected_rmba_evolution'] = [0.0] * years_count
            validated_data['projected_rmbc_evolution'] = [0.0] * years_count

        # Garantir que campos opcionais tenham valores padrão
        if validated_data.get('computation_time_ms') is None:
            validated_data['computation_time_ms'] = 0.0

        # Garantir que campos de CD tenham valores padrão
        if validated_data.get('individual_balance') is None:
            validated_data['individual_balance'] = 0.0
        if validated_data.get('total_contributions') is None:
            validated_data['total_contributions'] = 0.0

        print(f"[VALIDATION] Dados validados: projections={len(validated_data['projection_years'])}")

        # Retornar novo objeto SimulatorResults com dados validados
        return SimulatorResults(**validated_data)

    def _generate_technical_recommendations(self, state: SimulatorState, results: SimulatorResults) -> list:
        """Gerar recomendações técnicas específicas mais detalhadas"""
        recommendations = []

        if state.plan_type == 'CD':
            # Recomendações técnicas para CD
            replacement_ratio = results.replacement_ratio or 0
            target_rate = state.target_replacement_rate or 70

            if replacement_ratio < target_rate * 0.6:
                recommendations.append({
                    'type': 'critical',
                    'title': 'Inadequação Severa da Taxa de Reposição',
                    'description': f'Taxa atual ({replacement_ratio:.1f}%) significativamente abaixo da meta ({target_rate:.1f}%). Requer revisão urgente da estratégia de contribuição e/ou alocação de investimentos. Considere: aumentar contribuição em 2-3 p.p., revisar perfil de risco, implementar aportes extraordinários.'
                })
            elif replacement_ratio < target_rate * 0.8:
                recommendations.append({
                    'type': 'warning',
                    'title': 'Taxa de Reposição Insuficiente',
                    'description': f'Taxa atual ({replacement_ratio:.1f}%) abaixo da meta ({target_rate:.1f}%). Implementar plano de recuperação: aumentar contribuição gradualmente, otimizar alocação de ativos, estabelecer metas intermediárias de acompanhamento.'
                })

            # Análise da modalidade CD
            if state.cd_conversion_mode == 'ACTUARIAL_EQUIVALENT':
                recommendations.append({
                    'type': 'info',
                    'title': 'Equivalência Atuarial - Vantagens e Riscos',
                    'description': 'Modalidade escolhida oferece proteção contra risco de longevidade e inflação, mas expõe a variabilidade anual dos benefícios. Recomenda-se educação financeira sobre volatilidade e planejamento complementar.'
                })
            else:
                recommendations.append({
                    'type': 'info',
                    'title': 'Consideração sobre Modalidade de Conversão',
                    'description': 'Modalidade atual pode não proteger adequadamente contra risco de longevidade. Considere migração para equivalência atuarial para maior sustentabilidade dos benefícios.'
                })

            # Análise de contribuição
            if state.contribution_rate < 8:
                recommendations.append({
                    'type': 'warning',
                    'title': 'Taxa de Contribuição Abaixo do Recomendado',
                    'description': f'Taxa atual ({state.contribution_rate:.1f}%) pode ser insuficiente. Estudos indicam necessidade mínima de 8-12% para adequação previdenciária. Avaliar viabilidade de aumento gradual.'
                })

        else:
            # Recomendações técnicas para BD
            deficit_surplus = results.deficit_surplus or 0
            required_rate = results.required_contribution_rate or 0
            current_rate = state.contribution_rate or 0

            if deficit_surplus < -200000:
                recommendations.append({
                    'type': 'critical',
                    'title': 'Déficit Atuarial Significativo',
                    'description': f'Déficit de R$ {abs(deficit_surplus):,.0f} representa risco de sustentabilidade. Implementar imediatamente: plano de equacionamento com prazo definido, revisão de premissas atuariais, análise de estresse dos investimentos.'
                })
            elif deficit_surplus < -50000:
                recommendations.append({
                    'type': 'warning',
                    'title': 'Déficit Atuarial Moderado',
                    'description': f'Déficit de R$ {abs(deficit_surplus):,.0f} requer monitoramento ativo. Estabelecer plano de equacionamento gradual, revisar estratégia de investimentos, considerar ajustes paramétricos.'
                })

            if required_rate > current_rate * 1.5:
                recommendations.append({
                    'type': 'critical',
                    'title': 'Desequilíbrio Atuarial na Contribuição',
                    'description': f'Taxa necessária ({required_rate:.1f}%) muito superior à atual ({current_rate:.1f}%). Revisar urgentemente: benefícios prometidos, idade de aposentadoria, período de contribuição, ou implementar contribuição extraordinária.'
                })
            elif required_rate > current_rate * 1.2:
                recommendations.append({
                    'type': 'warning',
                    'title': 'Ajuste Contributivo Necessário',
                    'description': f'Taxa necessária ({required_rate:.1f}%) superior à atual ({current_rate:.1f}%). Planejar aumento gradual da contribuição ou revisar parâmetros do plano.'
                })

        # Recomendações gerais técnicas
        years_to_retirement = state.retirement_age - state.age

        if years_to_retirement < 5:
            recommendations.append({
                'type': 'info',
                'title': 'Proximidade da Aposentadoria - Gestão de Riscos',
                'description': 'Com aposentadoria próxima, adotar estratégia conservadora: reduzir exposição a risco, garantir liquidez, revisar premissas de longevidade, planejar transição para fase de benefícios.'
            })
        elif years_to_retirement < 15:
            recommendations.append({
                'type': 'info',
                'title': 'Fase Pré-Aposentadoria - Ajustes Finais',
                'description': 'Período crítico para ajustes finais: intensificar acompanhamento atuarial, otimizar contribuições remanescentes, validar estratégia de conversão em renda.'
            })

        # Recomendações metodológicas
        if state.discount_rate > 0.08:
            recommendations.append({
                'type': 'warning',
                'title': 'Taxa de Desconto Elevada',
                'description': f'Taxa de {(state.discount_rate * 100):.1f}% pode ser otimista. Recomendam-se testes de sensibilidade e eventual revisão para taxa mais conservadora (4-6% real).'
            })
        elif state.discount_rate < 0.03:
            recommendations.append({
                'type': 'info',
                'title': 'Taxa de Desconto Conservadora',
                'description': f'Taxa de {(state.discount_rate * 100):.1f}% é conservadora, mas pode subestimar capacidade de crescimento. Considerar análise de cenários alternativos.'
            })

        if not recommendations:
            recommendations.append({
                'type': 'success',
                'title': 'Situação Técnica Adequada',
                'description': 'Os parâmetros atuariais e resultados estão dentro de faixas aceitáveis. Manter acompanhamento periódico e reavaliação anual das premissas conforme evolução do cenário econômico.'
            })

        return recommendations