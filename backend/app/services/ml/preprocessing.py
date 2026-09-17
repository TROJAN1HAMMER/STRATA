"""
Leakage-Safe Preprocessing Pipeline for STRATA ML Models.
Strictly fitted on the TRAIN split only.
"""
from typing import Dict, List, Optional, Union
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from backend.app.services.ml.features import FEATURE_ALLOWLIST, validate_feature_dataframe


class MLPreprocessor:
    """
    Leakage-safe preprocessor encapsulating missing value imputation and feature scaling.
    Must be fitted exclusively on the training split.
    """

    def __init__(
        self,
        feature_names: Optional[List[str]] = None,
        scale: bool = True,
    ):
        self.feature_names: List[str] = feature_names or list(FEATURE_ALLOWLIST)
        self.scale: bool = scale
        self.imputer: SimpleImputer = SimpleImputer(strategy="median")
        self.scaler: StandardScaler = StandardScaler()
        self.is_fitted: bool = False

    def fit(self, X_train: pd.DataFrame) -> "MLPreprocessor":
        """
        Fits imputer and scaler strictly on training DataFrame.
        """
        validate_feature_dataframe(X_train, is_training=True)
        X_sub = X_train[self.feature_names].to_numpy(dtype=np.float64)

        # 1. Fit imputer
        imputed = self.imputer.fit_transform(X_sub)


        # 2. Fit scaler if enabled
        if self.scale:
            self.scaler.fit(imputed)

        self.is_fitted = True
        return self

    def transform(self, X: Union[pd.DataFrame, Dict[str, float], List[Dict[str, float]]]) -> np.ndarray:
        """
        Transforms features using pre-fitted parameters.
        """
        if not self.is_fitted:
            raise RuntimeError("MLPreprocessor must be fitted on training data before calling transform().")

        if isinstance(X, dict):
            # Single feature dict
            df_in = pd.DataFrame([X])
        elif isinstance(X, list):
            df_in = pd.DataFrame(X)
        elif isinstance(X, pd.DataFrame):
            df_in = X
        else:
            raise ValueError(f"Unsupported input type for transformation: {type(X)}")

        # Ensure all required features are present
        for col in self.feature_names:
            if col not in df_in.columns:
                raise ValueError(f"Input data missing feature: {col}")

        X_sub = df_in[self.feature_names].to_numpy(dtype=np.float64)

        # Apply imputer
        imputed = self.imputer.transform(X_sub)

        # Apply scaler if enabled
        if self.scale:
            return self.scaler.transform(imputed)
        return imputed

    def fit_transform(self, X_train: pd.DataFrame) -> np.ndarray:
        return self.fit(X_train).transform(X_train)
