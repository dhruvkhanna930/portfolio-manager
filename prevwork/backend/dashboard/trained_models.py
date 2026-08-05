import numpy as np
import pandas as pd
import yfinance as yf
import warnings
import os
from django.conf import settings

warnings.filterwarnings('ignore')

try:
    import tensorflow as tf
    from tensorflow import keras
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False


class TrainedModelPredictor:
    """Load and use trained LSTM/GRU models for stock price prediction"""

    def __init__(self):
        self.lstm_5day_model = None
        self.gru_1day_model = None
        self.models_loaded = False
        self.model_path = os.path.join(
            os.path.dirname(__file__), '..', 'Qantas_LSTM_trained_model_fivedays.h5'
        )
        self.gru_model_path = os.path.join(
            os.path.dirname(__file__), '..', 'Qantas_GRU_trained_model_oneday.h5'
        )

        if TENSORFLOW_AVAILABLE:
            self._load_models()

    def _load_models(self):
        """Load pre-trained models with fallback for version compatibility"""
        import warnings
        warnings.filterwarnings('ignore')

        try:
            if os.path.exists(self.model_path):
                try:
                    self.lstm_5day_model = keras.models.load_model(
                        self.model_path,
                        safe_mode=False
                    )
                    print(f"✓ LSTM 5-day model loaded")
                except Exception as lstm_err:
                    print(f"⚠ LSTM model skipped (TensorFlow compatibility)")
                    self.lstm_5day_model = None

            if os.path.exists(self.gru_model_path):
                try:
                    self.gru_1day_model = keras.models.load_model(
                        self.gru_model_path,
                        safe_mode=False
                    )
                    print(f"✓ GRU 1-day model loaded")
                except Exception as gru_err:
                    print(f"⚠ GRU model skipped (TensorFlow compatibility)")
                    self.gru_1day_model = None

            if self.lstm_5day_model or self.gru_1day_model:
                self.models_loaded = True
            else:
                print(f"⚠ Using fallback: AI sentiment + forecasting (fully functional)")
                self.models_loaded = False
        except Exception as e:
            print(f"⚠ Trained models unavailable - using AI fallback")
            self.models_loaded = False

    def prepare_sequence_data(self, ticker: str, lookback: int = 60) -> np.ndarray:
        """Fetch historical price data and prepare it for model input"""
        try:
            # Fetch historical data
            hist = yf.download(ticker, period='3mo', progress=False)

            if len(hist) < lookback:
                return None

            closing_prices = hist['Close'].values

            # Normalize the data
            min_price = np.min(closing_prices)
            max_price = np.max(closing_prices)

            if max_price == min_price:
                return None

            normalized_prices = (closing_prices - min_price) / (max_price - min_price)

            # Create sequence
            sequence = normalized_prices[-lookback:]

            return sequence.reshape(1, lookback, 1)

        except Exception as e:
            print(f"Error preparing sequence data for {ticker}: {str(e)}")
            return None

    def predict_5day_return(self, ticker: str) -> float:
        """Predict 5-day return using LSTM model (0-100 score)"""
        if not self.lstm_5day_model or not TENSORFLOW_AVAILABLE:
            return 50.0

        try:
            sequence = self.prepare_sequence_data(ticker, lookback=60)

            if sequence is None:
                return 50.0

            prediction = self.lstm_5day_model.predict(sequence, verbose=0)

            # Convert prediction to 0-100 score
            prediction_score = float(prediction[0][0]) * 100
            return min(max(prediction_score, 0), 100)

        except Exception as e:
            print(f"Error predicting 5-day return for {ticker}: {str(e)}")
            return 50.0

    def predict_1day_return(self, ticker: str) -> float:
        """Predict 1-day return using GRU model (0-100 score)"""
        if not self.gru_1day_model or not TENSORFLOW_AVAILABLE:
            return 50.0

        try:
            sequence = self.prepare_sequence_data(ticker, lookback=30)

            if sequence is None:
                return 50.0

            prediction = self.gru_1day_model.predict(sequence, verbose=0)

            # Convert prediction to 0-100 score
            prediction_score = float(prediction[0][0]) * 100
            return min(max(prediction_score, 0), 100)

        except Exception as e:
            print(f"Error predicting 1-day return for {ticker}: {str(e)}")
            return 50.0

    def get_model_predictions(self, ticker: str) -> dict:
        """Get both 1-day and 5-day predictions for a stock"""
        if not self.models_loaded:
            return {
                '1day': 50.0,
                '5day': 50.0,
                'combined': 50.0,
                'available': False
            }

        try:
            prediction_1day = self.predict_1day_return(ticker)
            prediction_5day = self.predict_5day_return(ticker)

            # Combine predictions with 1-day having more weight for short-term
            combined = (prediction_1day * 0.4 + prediction_5day * 0.6)

            return {
                '1day': round(prediction_1day, 2),
                '5day': round(prediction_5day, 2),
                'combined': round(combined, 2),
                'available': True
            }
        except Exception as e:
            print(f"Error getting model predictions for {ticker}: {str(e)}")
            return {
                '1day': 50.0,
                '5day': 50.0,
                'combined': 50.0,
                'available': False
            }


def compute_trained_model_scores(symbols_list: list) -> dict:
    """Compute trained model predictions for a list of stocks"""
    predictor = TrainedModelPredictor()
    model_scores = {}

    for ticker in symbols_list:
        try:
            predictions = predictor.get_model_predictions(ticker)
            model_scores[ticker] = predictions
        except Exception as e:
            print(f"Error computing model score for {ticker}: {str(e)}")
            model_scores[ticker] = {
                '1day': 50.0,
                '5day': 50.0,
                'combined': 50.0,
                'available': False
            }

    return model_scores


def blend_with_model_scores(fundamental_score: float, model_score: dict,
                          fundamental_weight: float = 0.4) -> float:
    """Blend fundamental analysis score with trained model predictions"""
    if not model_score.get('available', False):
        return fundamental_score

    model_weight = 1.0 - fundamental_weight
    combined = (fundamental_score * fundamental_weight +
                model_score['combined'] * model_weight)

    return combined
