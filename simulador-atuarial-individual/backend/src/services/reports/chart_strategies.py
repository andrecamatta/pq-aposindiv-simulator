"""
Strategy pattern implementation for chart generation.
Applies SOLID principles by separating chart generation concerns.
"""
import matplotlib.pyplot as plt
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from io import BytesIO
import base64

from ...models.results import SimulatorResults


class AbstractChartStrategy(ABC):
    """
    Abstract base class for chart generation strategies.

    Implements Strategy pattern following SOLID principles:
    - Single Responsibility: Each strategy handles one chart type
    - Open/Closed: Easy to add new chart types without modifying existing code
    - Interface Segregation: Clients depend only on methods they use
    """

    def __init__(self, colors: Dict[str, str], dpi: int = 300):
        """
        Initialize strategy with common configuration.

        Args:
            colors: Color palette for charts
            dpi: Chart resolution
        """
        self.colors = colors
        self.dpi = dpi

    @abstractmethod
    def generate_chart(self, results: SimulatorResults) -> str:
        """
        Generate specific chart as base64 encoded string.

        Args:
            results: Simulation results data

        Returns:
            Base64 encoded chart image
        """
        raise NotImplementedError("Strategy must implement generate_chart method")

    @property
    @abstractmethod
    def chart_name(self) -> str:
        """
        Unique identifier for this chart type.

        Returns:
            Chart name/identifier
        """
        raise NotImplementedError("Strategy must implement chart_name property")

    @property
    @abstractmethod
    def chart_title(self) -> str:
        """
        Human-readable title for this chart.

        Returns:
            Chart display title
        """
        raise NotImplementedError("Strategy must implement chart_title property")

    def _create_figure(self, figsize: tuple = (10, 6)) -> tuple:
        """
        Create matplotlib figure with common styling.

        Args:
            figsize: Figure dimensions (width, height)

        Returns:
            Tuple of (figure, axes)
        """
        fig, ax = plt.subplots(figsize=figsize, dpi=self.dpi)

        # Apply common styling
        ax.grid(True, alpha=0.3)
        ax.set_facecolor('#FAFAFA')

        return fig, ax

    def _figure_to_base64(self, fig) -> str:
        """
        Convert matplotlib figure to base64 data URI string for WeasyPrint.

        Args:
            fig: Matplotlib figure

        Returns:
            Data URI formatted string (data:image/png;base64,...)
        """
        buffer = BytesIO()
        fig.savefig(buffer, format='png', bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        buffer.seek(0)

        img_base64 = base64.b64encode(buffer.read()).decode()
        plt.close(fig)
        buffer.close()

        return f"data:image/png;base64,{img_base64}"

    def _format_currency_axis(self, ax, axis: str = 'y') -> None:
        """
        Format axis to display currency values in Brazilian format.

        Args:
            ax: Matplotlib axes
            axis: Which axis to format ('x' or 'y')
        """
        import matplotlib.ticker as ticker

        def currency_formatter(x, pos):
            if abs(x) >= 1e6:
                return f'R$ {x/1e6:.1f}M'.replace('.', ',')
            elif abs(x) >= 1e3:
                return f'R$ {x/1e3:.0f}K'
            else:
                return f'R$ {x:.0f}'

        if axis == 'y':
            ax.yaxis.set_major_formatter(ticker.FuncFormatter(currency_formatter))
        else:
            ax.xaxis.set_major_formatter(ticker.FuncFormatter(currency_formatter))


class ReserveEvolutionStrategy(AbstractChartStrategy):
    """Strategy for generating reserve evolution charts."""

    @property
    def chart_name(self) -> str:
        return "reserve_evolution"

    @property
    def chart_title(self) -> str:
        return "Evolução das Reservas Atuariais"

    def generate_chart(self, results: SimulatorResults) -> str:
        """Generate reserve evolution chart."""
        import logging
        fig, ax = self._create_figure(figsize=(12, 6))

        # Log available data for debugging
        logging.info(f"[RESERVE_CHART] projection_years: {len(results.projection_years or [])}, accumulated_reserves: {len(results.accumulated_reserves or [])}")

        # Check if we have sufficient data - be less restrictive
        if (not results.projection_years or not results.accumulated_reserves or
            len(results.projection_years) == 0 or len(results.accumulated_reserves) == 0 or
            len(results.projection_years) != len(results.accumulated_reserves)):
            # Log why we're showing empty chart
            logging.warning(f"[RESERVE_CHART] Insufficient data - proj_years: {len(results.projection_years or [])}, reserves: {len(results.accumulated_reserves or [])}")
            # Empty chart with message
            ax.text(0.5, 0.5, 'Dados de projeção não disponíveis',
                   ha='center', va='center', transform=ax.transAxes, fontsize=14)
            ax.set_title(self.chart_title, fontsize=16, fontweight='bold', pad=20)
            return self._figure_to_base64(fig)

        # Extract data from projection fields
        years = results.projection_years
        reserves = results.accumulated_reserves
        logging.info(f"[RESERVE_CHART] Generating chart with {len(years)} data points")

        # Plot reserve evolution
        ax.plot(years, reserves, linewidth=3, color=self.colors['primary'],
               marker='o', markersize=4, label='Reservas Atuariais')

        # Styling
        ax.set_title(self.chart_title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Ano', fontsize=12)
        ax.set_ylabel('Reservas (R$)', fontsize=12)

        self._format_currency_axis(ax, 'y')
        ax.legend(loc='upper left')

        # Add trend information
        if len(reserves) > 1:
            trend = "crescente" if reserves[-1] > reserves[0] else "decrescente"
            ax.text(0.02, 0.98, f'Tendência: {trend}', transform=ax.transAxes,
                   fontsize=10, va='top', bbox=dict(boxstyle='round',
                   facecolor='white', alpha=0.8))

        return self._figure_to_base64(fig)


class SensitivityAnalysisStrategy(AbstractChartStrategy):
    """Strategy for generating sensitivity analysis charts."""

    @property
    def chart_name(self) -> str:
        return "sensitivity_analysis"

    @property
    def chart_title(self) -> str:
        return "Análise de Sensibilidade"

    def generate_chart(self, results: SimulatorResults) -> str:
        """Generate sensitivity analysis chart."""
        fig, ax = self._create_figure(figsize=(10, 8))

        if not hasattr(results, 'sensitivity_analysis') or not results.sensitivity_analysis:
            # Empty chart with message
            ax.text(0.5, 0.5, 'Análise de sensibilidade não disponível',
                   ha='center', va='center', transform=ax.transAxes, fontsize=14)
            ax.set_title(self.chart_title, fontsize=16, fontweight='bold', pad=20)
            return self._figure_to_base64(fig)

        # Create sample sensitivity data (replace with actual data when available)
        scenarios = ['Conservador', 'Base', 'Otimista']
        variables = ['Taxa de Desconto', 'Crescimento Salarial', 'Mortalidade']

        # Sample impact data
        impact_data = np.array([
            [-15, -5, 5],    # Taxa de Desconto
            [-8, 0, 8],      # Crescimento Salarial
            [-12, 0, 12]     # Mortalidade
        ])

        # Create heatmap
        im = ax.imshow(impact_data, cmap='RdYlGn', aspect='auto', vmin=-20, vmax=20)

        # Set ticks and labels
        ax.set_xticks(np.arange(len(scenarios)))
        ax.set_yticks(np.arange(len(variables)))
        ax.set_xticklabels(scenarios)
        ax.set_yticklabels(variables)

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label('Impacto (%)', rotation=270, labelpad=15)

        # Add text annotations
        for i in range(len(variables)):
            for j in range(len(scenarios)):
                text = ax.text(j, i, f'{impact_data[i, j]:+.0f}%',
                             ha="center", va="center", color="black", fontweight='bold')

        ax.set_title(self.chart_title, fontsize=16, fontweight='bold', pad=20)

        return self._figure_to_base64(fig)


class CashFlowStrategy(AbstractChartStrategy):
    """Strategy for generating cash flow charts."""

    @property
    def chart_name(self) -> str:
        return "cash_flow"

    @property
    def chart_title(self) -> str:
        return "Fluxo de Caixa Projetado"

    def generate_chart(self, results: SimulatorResults) -> str:
        """Generate cash flow chart."""
        import logging
        fig, ax = self._create_figure(figsize=(12, 6))

        # Log available data for debugging
        logging.info(f"[CASH_FLOW_CHART] projection_years: {len(results.projection_years or [])}, projected_contributions: {len(results.projected_contributions or [])}, projected_benefits: {len(results.projected_benefits or [])}")

        # Check if we have sufficient data - be less restrictive
        if (not results.projection_years or not results.projected_contributions or
            len(results.projection_years) == 0 or len(results.projected_contributions) == 0):
            # Log why we're showing empty chart
            logging.warning(f"[CASH_FLOW_CHART] Insufficient data - proj_years: {len(results.projection_years or [])}, contributions: {len(results.projected_contributions or [])}")
            # Empty chart with message
            ax.text(0.5, 0.5, 'Dados de fluxo de caixa não disponíveis',
                   ha='center', va='center', transform=ax.transAxes, fontsize=14)
            ax.set_title(self.chart_title, fontsize=16, fontweight='bold', pad=20)
            return self._figure_to_base64(fig)

        # Extract data from projection fields
        years = results.projection_years
        contributions = results.projected_contributions
        benefits = [-b for b in results.projected_benefits] if results.projected_benefits else [0] * len(years)  # Negative for cash outflow
        logging.info(f"[CASH_FLOW_CHART] Generating chart with {len(years)} data points")

        # Create stacked bar chart
        width = 0.6
        ax.bar(years, contributions, width, label='Contribuições',
              color=self.colors['success'], alpha=0.8)
        ax.bar(years, benefits, width, label='Benefícios',
              color=self.colors['danger'], alpha=0.8)

        # Add net cash flow line
        net_flow = [c + b for c, b in zip(contributions, benefits)]
        ax.plot(years, net_flow, linewidth=2, color=self.colors['dark'],
               marker='o', markersize=4, label='Fluxo Líquido')

        # Add zero line
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)

        # Styling
        ax.set_title(self.chart_title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Ano', fontsize=12)
        ax.set_ylabel('Fluxo de Caixa (R$)', fontsize=12)

        self._format_currency_axis(ax, 'y')
        ax.legend(loc='upper right')

        return self._figure_to_base64(fig)


class ProjectionsSummaryStrategy(AbstractChartStrategy):
    """Strategy for generating projections summary charts."""

    @property
    def chart_name(self) -> str:
        return "projections_summary"

    @property
    def chart_title(self) -> str:
        return "Resumo das Projeções"

    def generate_chart(self, results: SimulatorResults) -> str:
        """Generate projections summary chart."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=self.dpi)

        # Left chart: Key metrics pie chart
        metrics = ['RMBA', 'RMBC', 'Custo Normal']
        values = [
            abs(results.rmba or 0),
            abs(results.rmbc or 0),
            abs(results.normal_cost or 0)
        ]

        # Filter out zero values
        non_zero = [(m, v) for m, v in zip(metrics, values) if v > 0]
        if non_zero:
            metrics, values = zip(*non_zero)
            colors = [self.colors['primary'], self.colors['secondary'], self.colors['info']][:len(values)]

            ax1.pie(values, labels=metrics, autopct='%1.1f%%', startangle=90, colors=colors)
            ax1.set_title('Distribuição dos Resultados', fontsize=14, fontweight='bold')
        else:
            ax1.text(0.5, 0.5, 'Dados não disponíveis', ha='center', va='center',
                    transform=ax1.transAxes, fontsize=12)
            ax1.set_title('Distribuição dos Resultados', fontsize=14, fontweight='bold')

        # Right chart: Balance indicator
        balance = results.deficit_surplus or 0

        if balance > 0:
            color = self.colors['success']
            label = f'Superávit\nR$ {abs(balance):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        elif balance < 0:
            color = self.colors['danger']
            label = f'Déficit\nR$ {abs(balance):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        else:
            color = self.colors['info']
            label = 'Equilíbrio\nR$ 0,00'

        # Create gauge-like visualization
        ax2.pie([abs(balance), 100000 - abs(balance)], colors=[color, '#f0f0f0'],
               startangle=90, counterclock=False, wedgeprops=dict(width=0.3))

        ax2.text(0, 0, label, ha='center', va='center', fontsize=12, fontweight='bold')
        ax2.set_title('Situação Atuarial', fontsize=14, fontweight='bold')

        fig.suptitle(self.chart_title, fontsize=16, fontweight='bold')
        plt.tight_layout()

        return self._figure_to_base64(fig)


# Strategy registry for easy chart type management
CHART_STRATEGIES = {
    'reserve_evolution': ReserveEvolutionStrategy,
    'sensitivity_analysis': SensitivityAnalysisStrategy,
    'cash_flow': CashFlowStrategy,
    'projections_summary': ProjectionsSummaryStrategy,
}