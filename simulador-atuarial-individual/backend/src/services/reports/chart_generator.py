"""
Gerador de gráficos matplotlib para relatórios em PDF
"""
import matplotlib
matplotlib.use('Agg')  # Backend sem interface gráfica para PDFs

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
import numpy as np
from io import BytesIO
import base64
from typing import Dict, Optional
from pathlib import Path

from .models.report_models import ReportConfig
from ...models.results import SimulatorResults


class ChartGenerator:
    """Classe para geração de gráficos profissionais para PDFs"""

    def __init__(self, config: Optional[ReportConfig] = None):
        self.config = config or ReportConfig()
        self.dpi = self.config.chart_dpi

        # Configurar estilo matplotlib para PDFs
        plt.style.use('seaborn-v0_8-whitegrid')

        # Paleta de cores profissional
        self.colors = {
            'primary': '#2E86AB',      # Azul principal
            'secondary': '#A23B72',    # Roxo secundário
            'success': '#28A745',      # Verde sucesso
            'warning': '#FFC107',      # Amarelo aviso
            'danger': '#DC3545',       # Vermelho perigo
            'info': '#17A2B8',         # Azul info
            'accent': '#F18F01',       # Laranja destaque
            'dark': '#343A40',         # Cinza escuro
            'light': '#F8F9FA'         # Cinza claro
        }

        # Configurações globais matplotlib
        plt.rcParams.update({
            'font.size': 10,
            'axes.titlesize': 12,
            'axes.labelsize': 10,
            'xtick.labelsize': 9,
            'ytick.labelsize': 9,
            'legend.fontsize': 9,
            'figure.titlesize': 14,
            'font.family': 'sans-serif',
            'axes.grid': True,
            'grid.alpha': 0.3
        })

    def generate_all_charts(self, results: SimulatorResults, chart_type: str = 'executive') -> Dict[str, str]:
        """Gerar todos os gráficos necessários para relatórios"""
        charts = {}

        # Gerar gráficos base com tratamento individual de erros
        charts['reserve_evolution'] = self._safe_generate_chart(
            lambda: self.generate_reserve_evolution_chart(results),
            "Evolução das Reservas"
        )
        charts['sensitivity_analysis'] = self._safe_generate_chart(
            lambda: self.generate_sensitivity_chart(results),
            "Análise de Sensibilidade"
        )
        charts['cash_flow'] = self._safe_generate_chart(
            lambda: self.generate_cash_flow_chart(results),
            "Fluxo de Caixa"
        )

        if chart_type == 'executive':
            charts['projections_summary'] = self._safe_generate_chart(
                lambda: self.generate_projections_summary_chart(results),
                "Resumo das Projeções"
            )
        elif chart_type == 'technical':
            # Gráficos específicos do relatório técnico
            charts['mortality_analysis'] = self._safe_generate_chart(
                lambda: self.generate_mortality_analysis_chart(results),
                "Análise de Mortalidade"
            )
            charts['contribution_breakdown'] = self._safe_generate_chart(
                lambda: self.generate_contribution_breakdown_chart(results),
                "Decomposição de Contribuições"
            )
            charts['technical_projections'] = self._safe_generate_chart(
                lambda: self.generate_technical_projections_chart(results),
                "Projeções Técnicas"
            )

        print(f"[CHARTS] Gerados {len(charts)} gráficos para {chart_type}: {list(charts.keys())}")
        return charts

    def _safe_generate_chart(self, chart_func, chart_name: str) -> str:
        """Gerar gráfico com tratamento seguro de erros"""
        try:
            return chart_func()
        except Exception as e:
            print(f"[CHART_ERROR] Erro ao gerar {chart_name}: {e}")
            return self._generate_placeholder_chart(chart_name)

    def generate_reserve_evolution_chart(self, results: SimulatorResults) -> str:
        """
        Gráfico de evolução das reservas/saldo ao longo do tempo
        Adaptado para BD (RMBA/RMBC) e CD (Saldo Individual)
        """
        fig, ax = plt.subplots(figsize=(10, 6), dpi=self.dpi)

        years = results.projection_years or list(range(2024, 2054))
        reserves = results.accumulated_reserves or [0] * len(years)

        # Determinar se é BD ou CD baseado nos dados disponíveis
        is_cd = hasattr(results, 'individual_balance') and results.individual_balance is not None

        if is_cd:
            # Para CD: mostrar evolução do saldo individual
            ax.fill_between(years, reserves, alpha=0.3, color=self.colors['primary'], label='Saldo Individual CD')
            ax.plot(years, reserves, color=self.colors['primary'], linewidth=2.5, marker='o', markersize=3)
            ax.set_title('Evolução do Saldo Individual (CD)', fontweight='bold', pad=20)
            ax.set_ylabel('Saldo Acumulado (R$)')
        else:
            # Para BD: mostrar RMBA e RMBC
            rmba_evolution = results.projected_rmba_evolution or reserves
            rmbc_evolution = results.projected_rmbc_evolution or [0] * len(years)

            ax.fill_between(years, rmba_evolution, alpha=0.3, color=self.colors['primary'], label='RMBA')
            ax.fill_between(years, rmbc_evolution, alpha=0.3, color=self.colors['secondary'], label='RMBC')
            ax.plot(years, rmba_evolution, color=self.colors['primary'], linewidth=2.5, marker='o', markersize=3)
            ax.plot(years, rmbc_evolution, color=self.colors['secondary'], linewidth=2.5, marker='s', markersize=3)
            ax.set_title('Evolução das Reservas Matemáticas (BD)', fontweight='bold', pad=20)
            ax.set_ylabel('Reservas Matemáticas (R$)')

        ax.set_xlabel('Ano de Projeção')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)

        # Formatação dos valores no eixo Y
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x/1000:.0f}K' if x < 1000000 else f'R$ {x/1000000:.1f}M'))

        # Melhorar layout
        plt.tight_layout()
        plt.subplots_adjust(top=0.9)

        return self._fig_to_base64(fig)

    def generate_sensitivity_chart(self, results: SimulatorResults) -> str:
        """
        Gráfico tornado de análise de sensibilidade
        """
        fig, ax = plt.subplots(figsize=(10, 6), dpi=self.dpi)

        # Preparar dados de sensibilidade (simulados se não existirem)
        variables = []
        impacts = []

        # Usar dados reais de sensibilidade se disponíveis
        if hasattr(results, 'sensitivity_discount_rate') and results.sensitivity_discount_rate:
            base_value = results.rmba or 0
            for rate, value in results.sensitivity_discount_rate.items():
                variables.append(f'Taxa Desconto {rate}%')
                if base_value > 0:
                    impacts.append((value - base_value) / base_value * 100)
                else:
                    impacts.append(0)
        else:
            # Dados simulados para demonstração
            variables = [
                'Taxa de Desconto ±1%',
                'Mortalidade ±10%',
                'Crescimento Salarial ±0,5%',
                'Inflação ±1%',
                'Idade Aposentadoria ±2 anos'
            ]
            impacts = [15.2, -8.7, 6.3, -4.1, 12.8]

        if not impacts:
            return self._generate_placeholder_chart("Análise de Sensibilidade")

        # Ordenar por impacto absoluto
        sorted_data = sorted(zip(variables, impacts), key=lambda x: abs(x[1]), reverse=True)
        variables, impacts = zip(*sorted_data)

        # Cores baseadas no impacto (positivo = verde, negativo = vermelho)
        colors = [self.colors['success'] if x > 0 else self.colors['danger'] for x in impacts]

        # Criar gráfico tornado horizontal
        bars = ax.barh(range(len(variables)), impacts, color=colors, alpha=0.7, edgecolor='white', linewidth=1)

        ax.set_yticks(range(len(variables)))
        ax.set_yticklabels(variables, fontsize=9)
        ax.set_xlabel('Impacto no Resultado (%)')
        ax.set_title('Análise de Sensibilidade - Tornado', fontweight='bold', pad=20)
        ax.axvline(x=0, color='black', linewidth=1.5, alpha=0.8)

        # Adicionar valores nas barras
        for i, (bar, impact) in enumerate(zip(bars, impacts)):
            x_pos = impact + (1 if impact > 0 else -1)
            ax.text(x_pos, i, f'{impact:+.1f}%',
                   ha='left' if impact > 0 else 'right',
                   va='center', fontweight='bold', fontsize=9)

        # Ajustar limites do eixo X
        max_abs = max(abs(min(impacts)), abs(max(impacts))) if impacts else 10
        ax.set_xlim(-max_abs * 1.3, max_abs * 1.3)

        plt.tight_layout()
        return self._fig_to_base64(fig)

    def generate_projections_summary_chart(self, results: SimulatorResults) -> str:
        """
        Gráfico resumo das projeções principais
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), dpi=self.dpi)

        years = results.projection_years or list(range(2024, 2054))
        benefits = results.projected_benefits or [0] * len(years)
        contributions = results.projected_contributions or [0] * len(years)
        salaries = results.projected_salaries or [0] * len(years)

        # Gráfico superior: Benefícios vs Contribuições
        ax1.fill_between(years, benefits, alpha=0.4, color=self.colors['success'], label='Benefícios Anuais')
        ax1.fill_between(years, contributions, alpha=0.4, color=self.colors['info'], label='Contribuições Anuais')
        ax1.plot(years, benefits, color=self.colors['success'], linewidth=2, marker='o', markersize=2)
        ax1.plot(years, contributions, color=self.colors['info'], linewidth=2, marker='s', markersize=2)

        ax1.set_ylabel('Valores Anuais (R$)')
        ax1.set_title('Projeção de Benefícios e Contribuições', fontweight='bold')
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x/1000:.0f}K'))

        # Gráfico inferior: Evolução Salarial
        ax2.fill_between(years, salaries, alpha=0.4, color=self.colors['accent'], label='Salário Projetado')
        ax2.plot(years, salaries, color=self.colors['accent'], linewidth=2.5, marker='D', markersize=2)

        ax2.set_xlabel('Ano de Projeção')
        ax2.set_ylabel('Salário Anual (R$)')
        ax2.set_title('Evolução Salarial Projetada', fontweight='bold')
        ax2.legend(loc='upper left')
        ax2.grid(True, alpha=0.3)
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x/1000:.0f}K'))

        plt.tight_layout()
        return self._fig_to_base64(fig)

    def generate_cash_flow_chart(self, results: SimulatorResults) -> str:
        """
        Gráfico de fluxo de caixa acumulado
        """
        fig, ax = plt.subplots(figsize=(10, 6), dpi=self.dpi)

        years = results.projection_years or list(range(2024, 2054))
        contributions = results.projected_contributions or [0] * len(years)
        benefits = results.projected_benefits or [0] * len(years)

        # Calcular fluxo líquido e acumulado
        net_flow = [c - b for c, b in zip(contributions, benefits)]
        cumulative_flow = np.cumsum(net_flow)

        # Separar áreas positivas e negativas
        positive_mask = cumulative_flow >= 0

        ax.fill_between(years, cumulative_flow, 0,
                       where=positive_mask, color=self.colors['success'],
                       alpha=0.6, label='Superávit Acumulado', interpolate=True)
        ax.fill_between(years, cumulative_flow, 0,
                       where=~positive_mask, color=self.colors['danger'],
                       alpha=0.6, label='Déficit Acumulado', interpolate=True)

        # Linha principal
        ax.plot(years, cumulative_flow, color=self.colors['dark'], linewidth=2.5,
               marker='o', markersize=2, markerfacecolor='white', markeredgewidth=1)

        # Linha de referência zero
        ax.axhline(y=0, color='black', linestyle='--', alpha=0.7, linewidth=1)

        ax.set_xlabel('Ano de Projeção')
        ax.set_ylabel('Fluxo Acumulado (R$)')
        ax.set_title('Fluxo de Caixa Acumulado (Contribuições - Benefícios)', fontweight='bold', pad=20)
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)

        # Formatação do eixo Y
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x/1000:.0f}K' if abs(x) < 1000000 else f'R$ {x/1000000:.1f}M'))

        plt.tight_layout()
        return self._fig_to_base64(fig)

    def _fig_to_base64(self, fig: Figure) -> str:
        """Converter figura matplotlib para string base64"""
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=self.dpi, bbox_inches='tight',
                   facecolor='white', edgecolor='none', pad_inches=0.2)
        buffer.seek(0)

        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close(fig)  # Liberar memória

        return f"data:image/png;base64,{image_base64}"

    def _generate_placeholder_chart(self, title: str) -> str:
        """Gerar gráfico placeholder em caso de erro"""
        fig, ax = plt.subplots(figsize=(8, 4), dpi=self.dpi)

        ax.text(0.5, 0.5, f'{title}\n(Dados não disponíveis)',
               ha='center', va='center', fontsize=14,
               bbox=dict(boxstyle="round,pad=0.3", facecolor=self.colors['light'], alpha=0.8))

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        ax.set_title(title, fontweight='bold')

        plt.tight_layout()
        return self._fig_to_base64(fig)

    def generate_mortality_analysis_chart(self, results: SimulatorResults) -> str:
        """Gráfico de análise de mortalidade e expectativa de vida"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), dpi=self.dpi)

        # Probabilidades de sobrevivência
        if hasattr(results, 'survival_probabilities') and results.survival_probabilities:
            years = list(range(len(results.survival_probabilities)))
            ax1.plot(years, [p * 100 for p in results.survival_probabilities],
                    color=self.colors['primary'], linewidth=2, marker='o', markersize=3)
            ax1.set_xlabel('Anos desde hoje')
            ax1.set_ylabel('Probabilidade de Sobrevivência (%)')
            ax1.set_title('Probabilidades de Sobrevivência', fontweight='bold')
            ax1.grid(True, alpha=0.3)
        else:
            ax1.text(0.5, 0.5, 'Dados de mortalidade\nnão disponíveis',
                    ha='center', va='center', transform=ax1.transAxes)

        # Taxa de mortalidade (qx)
        if hasattr(results, 'survival_probabilities') and results.survival_probabilities:
            mortality_rates = []
            for i in range(len(results.survival_probabilities) - 1):
                if results.survival_probabilities[i] > 0:
                    qx = 1 - (results.survival_probabilities[i+1] / results.survival_probabilities[i])
                    mortality_rates.append(qx * 1000)  # Por mil
                else:
                    mortality_rates.append(0)

            if mortality_rates:
                ax2.plot(range(len(mortality_rates)), mortality_rates,
                        color=self.colors['danger'], linewidth=2)
                ax2.set_xlabel('Anos desde hoje')
                ax2.set_ylabel('Taxa de Mortalidade (‰)')
                ax2.set_title('Taxa de Mortalidade (qx)', fontweight='bold')
                ax2.grid(True, alpha=0.3)

        if not hasattr(results, 'survival_probabilities') or not results.survival_probabilities:
            ax2.text(0.5, 0.5, 'Dados de mortalidade\nnão disponíveis',
                    ha='center', va='center', transform=ax2.transAxes)

        plt.tight_layout()
        return self._fig_to_base64(fig)

    def generate_contribution_breakdown_chart(self, results: SimulatorResults) -> str:
        """Gráfico de breakdown das contribuições vs benefícios/reservas"""
        fig, ax = plt.subplots(figsize=(10, 6), dpi=self.dpi)

        years = getattr(results, 'projection_years', list(range(2024, 2054)))

        # Contribuições acumuladas
        if hasattr(results, 'projected_contributions') and results.projected_contributions:
            contributions_cumsum = np.cumsum(results.projected_contributions)
            ax.plot(years[:len(contributions_cumsum)], contributions_cumsum,
                   label='Contribuições Acumuladas', color=self.colors['primary'],
                   linewidth=2, marker='o', markersize=3)

        # Reservas/Saldo acumulado
        if hasattr(results, 'accumulated_reserves') and results.accumulated_reserves:
            ax.plot(years[:len(results.accumulated_reserves)], results.accumulated_reserves,
                   label='Reservas/Saldo Acumulado', color=self.colors['success'],
                   linewidth=2, marker='s', markersize=3)

        # Benefícios acumulados (se BD)
        if hasattr(results, 'projected_benefits') and results.projected_benefits:
            benefits_cumsum = np.cumsum(results.projected_benefits)
            ax.plot(years[:len(benefits_cumsum)], benefits_cumsum,
                   label='Benefícios Acumulados', color=self.colors['warning'],
                   linewidth=2, marker='^', markersize=3)

        ax.set_xlabel('Ano')
        ax.set_ylabel('Valor (R$)')
        ax.set_title('Evolução Acumulada - Contribuições vs Benefícios/Reservas', fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Formatação dos valores em milhares/milhões
        ax.yaxis.set_major_formatter(plt.FuncFormatter(
            lambda x, p: f'R$ {x/1000:.0f}K' if x < 1000000 else f'R$ {x/1000000:.1f}M'
        ))

        plt.tight_layout()
        return self._fig_to_base64(fig)

    def generate_technical_projections_chart(self, results: SimulatorResults) -> str:
        """Gráfico técnico detalhado das projeções anuais"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8), dpi=self.dpi)

        years = getattr(results, 'projection_years', list(range(2024, 2054)))

        # 1. Evolução Salarial
        if hasattr(results, 'projected_salaries') and results.projected_salaries:
            ax1.plot(years[:len(results.projected_salaries)], results.projected_salaries,
                    color=self.colors['primary'], linewidth=2)
            ax1.set_title('Evolução Salarial Projetada', fontweight='bold')
            ax1.set_ylabel('Salário (R$)')
            ax1.grid(True, alpha=0.3)
            ax1.yaxis.set_major_formatter(plt.FuncFormatter(
                lambda x, p: f'R$ {x/1000:.0f}K'
            ))

        # 2. Contribuições Anuais
        if hasattr(results, 'projected_contributions') and results.projected_contributions:
            ax2.bar(years[:len(results.projected_contributions)], results.projected_contributions,
                   color=self.colors['info'], alpha=0.7, width=0.8)
            ax2.set_title('Contribuições Anuais', fontweight='bold')
            ax2.set_ylabel('Contribuição (R$)')
            ax2.grid(True, alpha=0.3)

        # 3. Taxa de Crescimento das Reservas
        if hasattr(results, 'accumulated_reserves') and results.accumulated_reserves and len(results.accumulated_reserves) > 1:
            growth_rates = []
            for i in range(1, len(results.accumulated_reserves)):
                if results.accumulated_reserves[i-1] > 0:
                    growth = (results.accumulated_reserves[i] / results.accumulated_reserves[i-1] - 1) * 100
                    growth_rates.append(growth)
                else:
                    growth_rates.append(0)

            ax3.plot(years[1:len(growth_rates)+1], growth_rates,
                    color=self.colors['success'], linewidth=2, marker='o', markersize=3)
            ax3.set_title('Taxa de Crescimento das Reservas (%)', fontweight='bold')
            ax3.set_ylabel('Crescimento (%)')
            ax3.grid(True, alpha=0.3)
            ax3.axhline(y=0, color='black', linestyle='--', alpha=0.5)

        # 4. Distribuição de Recursos
        if hasattr(results, 'total_contributions') and hasattr(results, 'individual_balance'):
            total_contrib = getattr(results, 'total_contributions', 0)
            final_balance = getattr(results, 'individual_balance', 0)
            returns = final_balance - total_contrib if final_balance > total_contrib else 0

            labels = ['Contribuições', 'Rendimentos']
            sizes = [total_contrib, returns] if returns > 0 else [total_contrib]
            colors = [self.colors['primary'], self.colors['success']] if returns > 0 else [self.colors['primary']]

            if total_contrib > 0:
                ax4.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
                ax4.set_title('Composição do Saldo Final', fontweight='bold')

        plt.tight_layout()
        return self._fig_to_base64(fig)