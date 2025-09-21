"""
Gerador de gráficos matplotlib para relatórios em PDF usando Strategy pattern.
"""
import matplotlib
matplotlib.use('Agg')  # Backend sem interface gráfica para PDFs

import matplotlib.pyplot as plt
from typing import Dict, Optional
from pathlib import Path

from .models.report_models import ReportConfig
from .chart_strategies import CHART_STRATEGIES, AbstractChartStrategy
from ...models.results import SimulatorResults


class ChartGenerator:
    """
    Classe para geração de gráficos usando Strategy pattern.
    Aplica SOLID principles:
    - Single Responsibility: Gerencia estratégias de chart, não implementa charts
    - Open/Closed: Aberto para extensão (novos charts) fechado para modificação
    - Dependency Inversion: Depende de abstrações (Strategy), não implementações
    """

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

        # Initialize chart strategies
        self._strategies: Dict[str, AbstractChartStrategy] = {}
        self._initialize_strategies()

    def _initialize_strategies(self) -> None:
        """Initialize all available chart strategies."""
        for strategy_name, strategy_class in CHART_STRATEGIES.items():
            self._strategies[strategy_name] = strategy_class(self.colors, self.dpi)

    def add_strategy(self, strategy: AbstractChartStrategy) -> None:
        """
        Add a new chart strategy (Open/Closed principle).

        Args:
            strategy: Chart strategy instance
        """
        self._strategies[strategy.chart_name] = strategy

    def get_available_charts(self) -> list[str]:
        """
        Get list of available chart types.

        Returns:
            List of chart strategy names
        """
        return list(self._strategies.keys())

    def generate_chart(self, chart_name: str, results: SimulatorResults) -> Optional[str]:
        """
        Generate a specific chart using Strategy pattern.

        Args:
            chart_name: Name of the chart strategy to use
            results: Simulation results data

        Returns:
            Base64 encoded chart or None if strategy not found
        """
        strategy = self._strategies.get(chart_name)
        if not strategy:
            import logging
            logging.warning(f"Chart strategy '{chart_name}' not found")
            return None

        try:
            return strategy.generate_chart(results)
        except Exception as e:
            import logging
            logging.error(f"Error generating chart '{chart_name}': {str(e)}")
            return None

    def generate_all_charts(self, results: SimulatorResults, chart_type: str = 'executive') -> Dict[str, str]:
        """
        Gerar todos os gráficos necessários usando Strategy pattern.

        Args:
            results: Simulation results data
            chart_type: Type of charts to generate ('executive' or 'technical')

        Returns:
            Dictionary mapping chart names to base64 encoded images
        """
        charts = {}

        # Define chart sets for different report types
        chart_sets = {
            'executive': [
                'reserve_evolution',
                'sensitivity_analysis',
                'cash_flow',
                'projections_summary'
            ],
            'technical': [
                'reserve_evolution',
                'sensitivity_analysis',
                'cash_flow',
                # Add technical-specific charts here when strategies are created
            ]
        }

        # Get charts for the requested type
        chart_names = chart_sets.get(chart_type, chart_sets['executive'])

        # Generate each chart using its strategy
        for chart_name in chart_names:
            chart_base64 = self.generate_chart(chart_name, results)
            if chart_base64:
                charts[chart_name] = chart_base64

        return charts