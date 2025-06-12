"""
競馬予測システム - 特徴量エンジニアリング

このモジュールは競馬データの特徴量生成と前処理を行います。
過去成績、馬体情報、レース条件等から予測に有効な特徴量を生成します。

Author: Portfolio Demo
Date: 2024
"""

import pandas as pd
import numpy as np
import logging
from typing import Optional, Union

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    競馬データの特徴量エンジニアリングを行うクラス
    
    過去のレース成績、馬体情報、騎手・調教師データ等から
    機械学習モデルに適した特徴量を生成します。
    """
    
    def __init__(self):
        """特徴量エンジニアクラスを初期化"""
        logger.info("FeatureEngineerクラスを初期化しました")
        
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        全体的な特徴量生成のメインメソッド
        
        Args:
            df (pd.DataFrame): 入力データフレーム
            
        Returns:
            pd.DataFrame: 特徴量生成後のデータフレーム
        """
        logger.info("特徴量生成を開始します")
        
        # データのコピーを作成
        enhanced_df = df.copy()
        
        # 各種特徴量の生成
        enhanced_df = self._create_temporal_features(enhanced_df)
        enhanced_df = self._create_performance_features(enhanced_df)
        enhanced_df = self._create_physical_features(enhanced_df)
        enhanced_df = self._create_race_condition_features(enhanced_df)
        enhanced_df = self._create_interaction_features(enhanced_df)
        enhanced_df = self._standardize_numerical_features(enhanced_df)
        
        logger.info(f"特徴量生成完了: {enhanced_df.shape[1]} 特徴量")
        return enhanced_df
    
    def _create_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        時系列関連の特徴量を生成
        
        Args:
            df (pd.DataFrame): 入力データフレーム
            
        Returns:
            pd.DataFrame: 時系列特徴量追加後のデータフレーム
        """
        df_copy = df.copy()
        
        # 日付から月情報を抽出
        date_columns = ['race_date', 'last_race_date', 'second_last_race_date', 'third_last_race_date']
        for col in date_columns:
            if col in df_copy.columns:
                month_col = col.replace('_date', '_month')
                df_copy[month_col] = self._extract_month_from_date(df_copy[col])
        
        # 月と性別の組み合わせ特徴量
        if 'race_month' in df_copy.columns and 'gender' in df_copy.columns:
            df_copy['month_gender_combination'] = (
                df_copy['race_month'].astype(str) + '_' + df_copy['gender'].astype(str)
            )
        
        # 月と年齢の組み合わせ特徴量
        if 'race_month' in df_copy.columns and 'age' in df_copy.columns:
            df_copy['month_age_combination'] = df_copy['race_month'] + df_copy['age']
        
        return df_copy
    
    def _create_performance_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        過去成績関連の特徴量を生成
        
        Args:
            df (pd.DataFrame): 入力データフレーム
            
        Returns:
            pd.DataFrame: 成績特徴量追加後のデータフレーム
        """
        df_copy = df.copy()
        
        # 着順関連の特徴量
        position_features = [
            'last_race_position', 'second_last_position', 'third_last_position'
        ]
        
        # 着順の数値変換
        for col in position_features:
            if col in df_copy.columns:
                df_copy[col] = self._convert_position_to_numeric(df_copy[col])
        
        # 角順位と上がり順位の合成特徴量
        corner_uphill_features = [
            ('last_race_corner3', 'last_race_final_furlong_rank'),
            ('second_last_corner3', 'second_last_final_furlong_rank'),
            ('third_last_corner3', 'third_last_final_furlong_rank')
        ]
        
        for corner_col, uphill_col in corner_uphill_features:
            if corner_col in df_copy.columns and uphill_col in df_copy.columns:
                feature_name = f"{corner_col}_uphill_combined"
                df_copy[feature_name] = (
                    df_copy[corner_col].astype(float) * 0.8 + 
                    df_copy[uphill_col].astype(float)
                )
        
        # 人気と着順の乖離度（人気裏切り指数）
        if 'last_race_popularity' in df_copy.columns and 'last_race_position' in df_copy.columns:
            df_copy['popularity_performance_gap'] = (
                (df_copy['last_race_popularity'] - df_copy['last_race_position']) / 
                df_copy['last_race_field_size']
            )
        
        return df_copy
    
    def _create_physical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        馬体・騎手関連の特徴量を生成
        
        Args:
            df (pd.DataFrame): 入力データフレーム
            
        Returns:
            pd.DataFrame: 馬体特徴量追加後のデータフレーム
        """
        df_copy = df.copy()
        
        # 斤量体重比
        if 'weight_carried' in df_copy.columns and 'horse_weight' in df_copy.columns:
            df_copy['weight_burden_ratio'] = (
                df_copy['weight_carried'] / df_copy['horse_weight'] * 100
            )
        
        # 頭数変化
        if 'field_size' in df_copy.columns and 'last_race_field_size' in df_copy.columns:
            df_copy['field_size_change'] = (
                df_copy['field_size'] - df_copy['last_race_field_size']
            )
        
        # 距離変化
        if 'distance' in df_copy.columns and 'last_race_distance' in df_copy.columns:
            df_copy['distance_change'] = (
                df_copy['distance'].astype(float) - df_copy['last_race_distance'].astype(float)
            )
        
        return df_copy
    
    def _create_race_condition_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        レース条件関連の特徴量を生成
        
        Args:
            df (pd.DataFrame): 入力データフレーム
            
        Returns:
            pd.DataFrame: レース条件特徴量追加後のデータフレーム
        """
        df_copy = df.copy()
        
        # 競馬場と距離の組み合わせ
        if 'track_name' in df_copy.columns and 'distance' in df_copy.columns:
            df_copy['track_distance_combination'] = (
                df_copy['track_name'] + '_' + df_copy['distance'].astype(str)
            )
        
        # 競馬場と前走成績の組み合わせ
        track_performance_combinations = [
            ('track_name', 'last_race_corner3', 'track_last_corner3'),
            ('track_name', 'last_race_corner4', 'track_last_corner4'),
            ('track_name', 'last_race_final_furlong_rank', 'track_last_uphill')
        ]
        
        for track_col, perf_col, new_col in track_performance_combinations:
            if track_col in df_copy.columns and perf_col in df_copy.columns:
                df_copy[new_col] = (
                    df_copy[track_col] + '_' + df_copy[perf_col].astype(str)
                )
        
        # クラス名の組み合わせ
        if 'class_name' in df_copy.columns and 'last_race_class' in df_copy.columns:
            df_copy['class_progression'] = (
                df_copy['class_name'] + '_' + df_copy['last_race_class']
            )
        
        return df_copy
    
    def _create_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        相互作用特徴量を生成
        
        Args:
            df (pd.DataFrame): 入力データフレーム
            
        Returns:
            pd.DataFrame: 相互作用特徴量追加後のデータフレーム
        """
        df_copy = df.copy()
        
        # 競馬場と前走開催場の組み合わせ
        if 'track_name' in df_copy.columns and 'last_race_track' in df_copy.columns:
            df_copy['track_last_track_combination'] = (
                df_copy['track_name'] + '_' + df_copy['last_race_track']
            )
        
        return df_copy
    
    def _standardize_numerical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        数値特徴量の標準化（偏差値化）
        
        Args:
            df (pd.DataFrame): 入力データフレーム
            
        Returns:
            pd.DataFrame: 標準化後のデータフレーム
        """
        df_copy = df.copy()
        
        # 偏差値化対象の特徴量
        zscore_features = [
            'age', 'horse_weight', 'weight_burden_ratio',
            'last_race_corner3', 'last_race_corner4', 'last_race_final_furlong_rank',
            'last_race_time_difference', 'last_race_horse_weight',
            'second_last_corner3', 'second_last_corner4', 'second_last_final_furlong_rank',
            'second_last_time_difference', 'second_last_horse_weight',
            'third_last_corner3', 'third_last_corner4', 'third_last_final_furlong_rank',
            'third_last_time_difference', 'third_last_horse_weight'
        ]
        
        # 指数系特徴量
        index_features = [
            'leading_index_last', 'pace_index_last', 'uphill_index_last', 'speed_index_last',
            'leading_index_second', 'pace_index_second', 'uphill_index_second', 'speed_index_second',
            'leading_index_third', 'pace_index_third', 'uphill_index_third', 'speed_index_third'
        ]
        
        zscore_features.extend(index_features)
        
        # レース毎の偏差値計算（レースIDがある場合）
        if 'race_id' in df_copy.columns:
            df_copy = self._calculate_zscore_by_race(df_copy, zscore_features)
        else:
            # 全体での偏差値計算
            df_copy = self._calculate_global_zscore(df_copy, zscore_features)
        
        return df_copy
    
    def _calculate_zscore_by_race(self, df: pd.DataFrame, features: list) -> pd.DataFrame:
        """
        レース毎の偏差値を計算
        
        Args:
            df (pd.DataFrame): 入力データフレーム
            features (list): 偏差値化する特徴量リスト
            
        Returns:
            pd.DataFrame: 偏差値化後のデータフレーム
        """
        df_copy = df.copy()
        
        # 存在する特徴量のみフィルタリング
        existing_features = [f for f in features if f in df_copy.columns]
        
        if existing_features:
            # レース毎の平均と標準偏差
            race_means = df_copy.groupby('race_id')[existing_features].transform('mean')
            race_stds = df_copy.groupby('race_id')[existing_features].transform('std')
            
            # 偏差値計算 (平均50, 標準偏差10)
            df_copy[existing_features] = (
                (df_copy[existing_features] - race_means) / race_stds * 10 + 50
            )
            
            # NaN値の処理
            df_copy[existing_features] = df_copy[existing_features].fillna(50)
        
        return df_copy
    
    def _calculate_global_zscore(self, df: pd.DataFrame, features: list) -> pd.DataFrame:
        """
        全体での偏差値を計算
        
        Args:
            df (pd.DataFrame): 入力データフレーム
            features (list): 偏差値化する特徴量リスト
            
        Returns:
            pd.DataFrame: 偏差値化後のデータフレーム
        """
        df_copy = df.copy()
        
        # 存在する特徴量のみフィルタリング
        existing_features = [f for f in features if f in df_copy.columns]
        
        if existing_features:
            # 全体の平均と標準偏差
            global_means = df_copy[existing_features].mean()
            global_stds = df_copy[existing_features].std()
            
            # 偏差値計算
            df_copy[existing_features] = (
                (df_copy[existing_features] - global_means) / global_stds * 10 + 50
            )
            
            # NaN値の処理
            df_copy[existing_features] = df_copy[existing_features].fillna(50)
        
        return df_copy
    
    @staticmethod
    def _extract_month_from_date(date_series: pd.Series) -> pd.Series:
        """
        日付から月を抽出
        
        Args:
            date_series (pd.Series): 日付データ
            
        Returns:
            pd.Series: 月データ
        """
        return pd.to_datetime(date_series, errors='coerce').dt.month
    
    @staticmethod
    def _convert_position_to_numeric(position_series: pd.Series) -> pd.Series:
        """
        着順文字列を数値に変換
        
        Args:
            position_series (pd.Series): 着順データ
            
        Returns:
            pd.Series: 数値化された着順データ
        """
        # 全角数字を半角に変換
        converted_series = position_series.astype(str).str.translate(
            str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)})
        )
        
        # 数値に変換できない値（「外」「消」等）をNaNに
        return pd.to_numeric(converted_series, errors='coerce') 