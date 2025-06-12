"""
競馬AI予測システム - メインパッケージ

機械学習を活用した競馬の着順予測システムです。
LightGBMベースのモデルにより高精度な予測を実現します。

Author: Portfolio Demo
Date: 2024
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Portfolio Demo"

# メインクラスのインポート
from .models.lightgbm_predictor import HorseRacingPredictor
from .data_processing.feature_engineering import FeatureEngineer
from .utils.data_validator import DataValidator
from .scrapers.data_collector import HorseRacingDataCollector, RaceScheduleCollector

__all__ = [
    'HorseRacingPredictor',
    'FeatureEngineer', 
    'DataValidator',
    'HorseRacingDataCollector',
    'RaceScheduleCollector'
] 