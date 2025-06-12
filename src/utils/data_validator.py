"""
競馬予測システム - データ検証ユーティリティ

このモジュールはデータの整合性チェックと前処理を行います。
不正なデータの除去、データ型の統一、欠損値の処理等を実施します。

Author: Portfolio Demo
Date: 2024
"""

import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Any

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataValidator:
    """
    競馬データの検証・清浄化を行うクラス
    
    データの整合性チェック、不正値の除去、
    データ型の統一などを実施します。
    """
    
    def __init__(self):
        """データ検証クラスを初期化"""
        logger.info("DataValidatorクラスを初期化しました")
    
    def validate_and_clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        データの検証と清浄化のメインメソッド
        
        Args:
            df (pd.DataFrame): 入力データフレーム
            
        Returns:
            pd.DataFrame: 清浄化されたデータフレーム
        """
        logger.info("データ検証・清浄化を開始します")
        
        cleaned_df = df.copy()
        
        # 各種検証・清浄化処理
        cleaned_df = self._remove_invalid_positions(cleaned_df)
        cleaned_df = self._standardize_data_types(cleaned_df)
        cleaned_df = self._handle_missing_values(cleaned_df)
        cleaned_df = self._remove_outliers(cleaned_df)
        
        logger.info(f"データ清浄化完了: {len(cleaned_df)} 行残存")
        return cleaned_df
    
    def _remove_invalid_positions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        不正な着順データを除去
        
        Args:
            df (pd.DataFrame): 入力データフレーム
            
        Returns:
            pd.DataFrame: 着順データ清浄化後のデータフレーム
        """
        df_copy = df.copy()
        
        # 着順の数値変換
        if 'finishing_position' in df_copy.columns:
            df_copy['finishing_position'] = pd.to_numeric(
                df_copy['finishing_position'], errors='coerce'
            )
            # 数値に変換できない行を除去
            df_copy = df_copy.dropna(subset=['finishing_position'])
            df_copy['finishing_position'] = df_copy['finishing_position'].astype(int)
        
        # 着順無加工列の「外」「消」を除去
        if 'raw_finishing_position' in df_copy.columns:
            invalid_positions = ['外', '消', 'DQ', 'DNS']
            df_copy = df_copy[~df_copy['raw_finishing_position'].isin(invalid_positions)]
        
        return df_copy
    
    def _standardize_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        データ型の統一
        
        Args:
            df (pd.DataFrame): 入力データフレーム
            
        Returns:
            pd.DataFrame: データ型統一後のデータフレーム
        """
        df_copy = df.copy()
        
        # 数値型に変換すべき列
        numeric_columns = [
            'age', 'horse_weight', 'weight_carried', 'distance',
            'field_size', 'popularity', 'odds',
            'last_race_distance', 'last_race_field_size',
            'second_last_distance', 'second_last_field_size',
            'third_last_distance', 'third_last_field_size'
        ]
        
        for col in numeric_columns:
            if col in df_copy.columns:
                df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
        
        # 文字列型に変換すべき列
        string_columns = [
            'horse_name', 'jockey_name', 'trainer_name',
            'track_name', 'race_class', 'track_condition',
            'weather', 'gender'
        ]
        
        for col in string_columns:
            if col in df_copy.columns:
                df_copy[col] = df_copy[col].astype(str)
        
        return df_copy
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        欠損値の処理
        
        Args:
            df (pd.DataFrame): 入力データフレーム
            
        Returns:
            pd.DataFrame: 欠損値処理後のデータフレーム
        """
        df_copy = df.copy()
        
        # 角順位・上がり順位の0値を空文字・18値に置換
        position_replacements = {
            'last_race_corner2': {'0': '', np.nan: 18},
            'last_race_corner3': {'0': '', np.nan: 18},
            'last_race_corner4': {'0': '', np.nan: 18},
            'last_race_final_furlong_rank': {'0': '', np.nan: 18},
            'second_last_corner2': {'0': '', np.nan: 18},
            'second_last_corner3': {'0': '', np.nan: 18},
            'second_last_corner4': {'0': '', np.nan: 18},
            'second_last_final_furlong_rank': {'0': '', np.nan: 18},
            'third_last_corner2': {'0': '', np.nan: 18},
            'third_last_corner3': {'0': '', np.nan: 18},
            'third_last_corner4': {'0': '', np.nan: 18},
            'third_last_final_furlong_rank': {'0': '', np.nan: 18}
        }
        
        df_copy = df_copy.replace(position_replacements)
        
        # 空文字列をNaNに変換
        df_copy = df_copy.replace('', np.nan)
        
        # 必須列の欠損値がある行を除去
        essential_columns = ['horse_name', 'track_name', 'distance']
        existing_essential = [col for col in essential_columns if col in df_copy.columns]
        if existing_essential:
            df_copy = df_copy.dropna(subset=existing_essential)
        
        return df_copy
    
    def _remove_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        外れ値の除去
        
        Args:
            df (pd.DataFrame): 入力データフレーム
            
        Returns:
            pd.DataFrame: 外れ値除去後のデータフレーム
        """
        df_copy = df.copy()
        
        # 馬体重の外れ値除去（300kg-700kg範囲外）
        if 'horse_weight' in df_copy.columns:
            df_copy = df_copy[
                (df_copy['horse_weight'] >= 300) & 
                (df_copy['horse_weight'] <= 700)
            ]
        
        # オッズの外れ値除去（1.0-999.9範囲外）
        if 'odds' in df_copy.columns:
            df_copy = df_copy[
                (df_copy['odds'] >= 1.0) & 
                (df_copy['odds'] <= 999.9)
            ]
        
        # 距離の外れ値除去（800m-4000m範囲外）
        if 'distance' in df_copy.columns:
            df_copy = df_copy[
                (df_copy['distance'] >= 800) & 
                (df_copy['distance'] <= 4000)
            ]
        
        return df_copy
    
    def validate_race_data(self, df: pd.DataFrame) -> bool:
        """
        レースデータの整合性をチェック
        
        Args:
            df (pd.DataFrame): チェック対象データフレーム
            
        Returns:
            bool: データが有効かどうか
        """
        validation_results = []
        
        # 必須列の存在チェック
        required_columns = ['horse_number', 'horse_name']
        for col in required_columns:
            if col not in df.columns:
                validation_results.append(f"必須列 '{col}' が存在しません")
        
        # 馬番の重複チェック
        if 'horse_number' in df.columns:
            if df['horse_number'].duplicated().any():
                validation_results.append("馬番に重複があります")
        
        # 頭数の整合性チェック
        if 'field_size' in df.columns and 'horse_number' in df.columns:
            max_horse_number = df['horse_number'].max()
            declared_field_size = df['field_size'].iloc[0] if len(df) > 0 else 0
            if max_horse_number != declared_field_size:
                validation_results.append(
                    f"頭数の不整合: 宣言{declared_field_size}, 実際{max_horse_number}"
                )
        
        if validation_results:
            for error in validation_results:
                logger.warning(f"データ検証エラー: {error}")
            return False
        
        logger.info("データ検証OK")
        return True
    
    def get_data_quality_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        データ品質レポートを生成
        
        Args:
            df (pd.DataFrame): 分析対象データフレーム
            
        Returns:
            Dict[str, Any]: データ品質レポート
        """
        report = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'missing_value_summary': {},
            'data_type_summary': {},
            'duplicate_rows': df.duplicated().sum()
        }
        
        # 欠損値サマリー
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            missing_rate = missing_count / len(df) * 100
            report['missing_value_summary'][col] = {
                'count': missing_count,
                'rate_percent': round(missing_rate, 2)
            }
        
        # データ型サマリー
        for col in df.columns:
            report['data_type_summary'][col] = str(df[col].dtype)
        
        logger.info(f"データ品質レポート生成完了: {report['total_rows']} 行")
        return report 