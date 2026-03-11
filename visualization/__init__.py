"""
Visualization and export functionality

Components:
    - ExcelExporter: Export results to formatted Excel files

Usage:
    from visualization import ExcelExporter
    
    exporter = ExcelExporter(lottery_config)
    
    # Export backtest results
    exporter.export_backtest_results(summaries, rankings, 'results.xlsx')
    
    # Export predictions
    exporter.export_recommendation(prediction, current_draw, 'prediction.xlsx')
"""

from .excel_exporter import ExcelExporter

__all__ = ['ExcelExporter']

__version__ = '1.0.0'
