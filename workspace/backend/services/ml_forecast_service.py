"""Trained LSTM/GRU price forecasting (Phase 16).

Wraps the two Keras models produced by the recommendation-model workstream:

    Qantas_GRU_trained_model_oneday.h5    input (None, 90, 6) -> Dense(1)
    Qantas_LSTM_trained_model_fivedays.h5 input (None, 90, 6) -> Dense(5)

Both are stacked recurrent regressors (320 units -> dropout 0.2 -> 240 units ->
dropout 0.2 -> linear head) trained with Adam/MSE under Keras 2.6. They predict
*normalized closing prices*, not returns and not classes -- turning that output
into something a recommendation can use is this module's job.

Three things here differ deliberately from the original Django implementation,
because the original could not have worked as written:

  * **Input shape.** The original built ``(1, lookback, 1)`` windows of close
    prices only, with lookback 30 (GRU) / 60 (LSTM). Both checkpoints declare
    ``batch_input_shape [None, 90, 6]``. Feeding a 1-feature 30-step window to a
    6-feature 90-step model raises a shape error on every call, which the
    original swallowed in a bare ``except`` and returned the neutral 50.0 from.
    So every "trained model score" in the original output was the fallback
    constant, never a prediction. We build the real (90, 6) OHLCV+AdjClose
    window instead.

  * **Output meaning.** The original multiplied the raw network output by 100
    and called it a score. The output is a *min-max normalized price level*, so
    that number answers "where in the recent range does the model land?", not
    "how much will this gain?". A stock pinned at its 90-day high scores ~100
    whether or not it is predicted to rise. We invert the normalization back to
    rupees and score the implied **return versus the last close**.

  * **Degradation.** TensorFlow is not a dependency of this app (§2 pins no ML
    runtime, and the checkpoints are Keras 2.6 format which modern Keras 3 will
    not load). Everything below is import-guarded and falls back to a momentum
    estimator computed from our own cached price_history. The API always states
    which path produced a number -- see ``source`` in every payload.

Nothing here is stored. Predictions are computed on request, same principle as
§6 and §14.
"""

import math
import os
from datetime import date
from pathlib import Path

from models import PriceHistory

# Both checkpoints declare this input signature. Do not change without
# re-inspecting the .h5 -- it is read from the file, not chosen by us.
LOOKBACK = 90
N_FEATURES = 6

# yfinance's default frame is exactly these six columns, in this order. That the
# model wants 6 features is the tell that it was trained on a raw yf.download().
FEATURE_COLUMNS = ("Open", "High", "Low", "Close", "Adj Close", "Volume")
CLOSE_INDEX = 3

# The 1-day GRU is sharper but noisier; the 5-day LSTM carries more signal about
# direction. Same split the original used, kept for continuity.
WEIGHT_1DAY = 0.4
WEIGHT_5DAY = 0.6

# Return magnitude (in %) that saturates the score toward its bound. A predicted
# +3% move over the horizon is already a strong signal at equity scale, so the
# tanh is scaled to reach ~0.76 of full deflection there rather than needing an
# implausible +30% to move the needle.
RETURN_SCALE_PCT = 3.0

# The momentum fallback measures trend *acceleration* over months, which swings
# by tens of percent where a 1-day predicted return swings by ones. Reusing the
# 3% scale there pins almost every stock to 0 or 100 -- observed on real data
# before this constant existed -- so the fallback gets its own wider scale.
MOMENTUM_SCALE_PCT = 15.0

NEUTRAL_SCORE = 50.0

# Where to look for the checkpoints. The models live in the recommendation-model
# package at the repo root rather than being copied into workspace/ -- they are
# 20MB of binary and already tracked there. Override with MODEL_DIR.
_DEFAULT_MODEL_DIRS = (
    Path(__file__).resolve().parents[3] / "stock_recommendation_system" / "models",
    Path(__file__).resolve().parents[2] / "models",
)

GRU_FILENAME = "Qantas_GRU_trained_model_oneday.h5"
LSTM_FILENAME = "Qantas_LSTM_trained_model_fivedays.h5"

DISCLAIMER = (
    "Price predictions from a small recurrent network trained on a single "
    "airline stock's history. Treated as one weak signal among several, never "
    "as a forecast. Past price patterns do not predict future returns."
)


# --------------------------------------------------------------------------
# Model loading -- optional, cached, never fatal
# --------------------------------------------------------------------------

_state = {"loaded": False, "gru": None, "lstm": None, "reason": None, "detail": {}}


def _model_dir():
    override = os.environ.get("MODEL_DIR")
    if override:
        return Path(override)
    for candidate in _DEFAULT_MODEL_DIRS:
        if candidate.is_dir():
            return candidate
    return _DEFAULT_MODEL_DIRS[0]


def _load_models():
    """Resolve both checkpoints once. Any failure downgrades to the fallback.

    Inference runs through services/keras_h5_runtime -- a NumPy reimplementation
    of the forward pass -- rather than TensorFlow. TF publishes no wheels for
    this venv's Python 3.14, and TF >= 2.16 (Keras 3) refuses this HDF5 layout
    anyway, so the runtime reads the trained weights straight out of the file.
    Same weights, same arithmetic, no 500MB dependency.
    """
    if _state["loaded"]:
        return _state

    _state["loaded"] = True
    directory = _model_dir()

    try:
        from services import keras_h5_runtime
    except ImportError as exc:  # noqa: BLE001
        _state["reason"] = f"inference runtime unavailable: {exc}"
        return _state

    for key, filename in (("gru", GRU_FILENAME), ("lstm", LSTM_FILENAME)):
        path = directory / filename
        if not path.exists():
            _state["reason"] = f"Checkpoint not found: {path}"
            continue
        try:
            _state["detail"][key] = keras_h5_runtime.describe(str(path))
            _state[key] = str(path)
        except Exception as exc:  # noqa: BLE001 - report, never score 50 silently
            _state["reason"] = f"{filename} failed to load: {type(exc).__name__}: {exc}"

    if _state["gru"] is not None or _state["lstm"] is not None:
        _state["reason"] = None

    return _state


def model_status():
    """Which prediction path is live, for the UI to label honestly."""
    state = _load_models()
    available = state["gru"] is not None or state["lstm"] is not None
    return {
        "trained_models_available": available,
        "gru_1day_loaded": state["gru"] is not None,
        "lstm_5day_loaded": state["lstm"] is not None,
        "reason": state["reason"],
        "fallback": "momentum" if not available else None,
        "runtime": "numpy (keras_h5_runtime)",
        "model_dir": str(_model_dir()),
        "expected_input_shape": [LOOKBACK, N_FEATURES],
        "architecture": state["detail"],
        "disclaimer": DISCLAIMER,
    }


# --------------------------------------------------------------------------
# Feature windows
# --------------------------------------------------------------------------


def _fetch_ohlcv(symbol):
    """Fetch the (90, 6) OHLCV window the checkpoints expect.

    Live yfinance rather than our price_history cache, because the cache stores
    close only (§5.1) and these models want the full bar. Callers that cannot
    afford the network hop should use the momentum fallback instead.
    """
    try:
        import yfinance as yf
    except ImportError:
        return None

    try:
        frame = yf.download(
            symbol,
            period="6mo",
            interval="1d",
            progress=False,
            auto_adjust=False,
        )
    except Exception:  # noqa: BLE001 - yfinance is unofficial, treat as absent
        return None

    if frame is None or len(frame) < LOOKBACK:
        return None

    rows = []
    for column in FEATURE_COLUMNS:
        if column not in frame.columns:
            # auto_adjust=True drops "Adj Close"; fall back to Close so the
            # feature count still matches what the network declares.
            column = "Close" if "Close" in frame.columns else None
            if column is None:
                return None
        series = frame[column]
        if hasattr(series, "iloc") and getattr(series, "ndim", 1) > 1:
            series = series.iloc[:, 0]
        rows.append([float(v) for v in series.tail(LOOKBACK).tolist()])

    if any(len(r) < LOOKBACK for r in rows):
        return None

    # rows is feature-major; the network wants time-major (timesteps, features).
    return [[rows[f][t] for f in range(N_FEATURES)] for t in range(LOOKBACK)]


def _normalize(window):
    """Per-feature min-max over the window, plus the close scale to invert with.

    The training scaler was not shipped alongside the checkpoints, so this is a
    reconstruction of the standard per-window min-max these models are built
    with, not a recovery of the exact fit. Documented as a known limitation --
    it means absolute predictions carry more uncertainty than the network's own
    training error suggests.
    """
    mins = [min(row[f] for row in window) for f in range(N_FEATURES)]
    maxs = [max(row[f] for row in window) for f in range(N_FEATURES)]

    scaled = []
    for row in window:
        scaled_row = []
        for f in range(N_FEATURES):
            spread = maxs[f] - mins[f]
            scaled_row.append(0.5 if spread <= 0 else (row[f] - mins[f]) / spread)
        scaled.append(scaled_row)

    return scaled, mins[CLOSE_INDEX], maxs[CLOSE_INDEX]


def _denormalize_close(value, close_min, close_max):
    return value * (close_max - close_min) + close_min


def _score_from_return(return_pct, scale=RETURN_SCALE_PCT):
    """Map an expected return (%) onto 0-100, saturating smoothly.

    tanh rather than a linear clamp so that the difference between +1% and +2%
    still moves the score, while +40% (almost certainly a data artefact) cannot
    dominate the blend. `scale` sets how fast it saturates -- see
    MOMENTUM_SCALE_PCT for why the fallback needs a different one.
    """
    return NEUTRAL_SCORE * (1.0 + math.tanh(return_pct / scale))


# --------------------------------------------------------------------------
# Prediction
# --------------------------------------------------------------------------


def _predict_with_models(symbol):
    """Run both checkpoints over one symbol. Returns None if unusable."""
    state = _load_models()
    if state["gru"] is None and state["lstm"] is None:
        return None

    window = _fetch_ohlcv(symbol)
    if window is None:
        return None

    scaled, close_min, close_max = _normalize(window)
    if close_max <= close_min:
        return None

    last_close = window[-1][CLOSE_INDEX]
    if last_close <= 0:
        return None

    from services import keras_h5_runtime

    result = {"symbol": symbol, "last_close": round(last_close, 4)}

    if state["gru"] is not None:
        try:
            raw = keras_h5_runtime.predict(state["gru"], scaled)
            predicted = _denormalize_close(float(raw[0]), close_min, close_max)
            ret = (predicted / last_close - 1.0) * 100.0
            result["predicted_close_1day"] = round(predicted, 4)
            result["expected_return_1day_pct"] = round(ret, 4)
            result["score_1day"] = round(_score_from_return(ret), 2)
        except Exception:  # noqa: BLE001
            pass

    if state["lstm"] is not None:
        try:
            # Dense(5): one normalized close per day of the horizon, so the last
            # element is the 5-day-ahead level -- not a single scalar as the
            # original assumed when it indexed [0][0].
            raw = keras_h5_runtime.predict(state["lstm"], scaled)
            path = [_denormalize_close(float(v), close_min, close_max) for v in raw]
            predicted = path[-1]
            ret = (predicted / last_close - 1.0) * 100.0
            result["predicted_close_5day"] = round(predicted, 4)
            result["predicted_path_5day"] = [round(p, 4) for p in path]
            result["expected_return_5day_pct"] = round(ret, 4)
            result["score_5day"] = round(_score_from_return(ret), 2)
        except Exception:  # noqa: BLE001
            pass

    if "score_1day" not in result and "score_5day" not in result:
        return None

    result["source"] = "trained_model"
    return result


def _momentum_fallback(asset_id):
    """Trend estimate from our own cached closes when the networks are absent.

    Compares the most recent 30-day drift to the preceding 60-day drift, so a
    stock accelerating upward scores above one merely drifting up. Same shape of
    signal the original's _simple_forecast used, but reading price_history
    instead of re-downloading a year of prices per symbol.
    """
    rows = (
        PriceHistory.query.filter(PriceHistory.asset_id == asset_id)
        .order_by(PriceHistory.price_date.desc())
        .limit(91)
        .all()
    )
    if len(rows) < 61:
        return None

    closes = [float(r.close_price) for r in reversed(rows)]
    recent = closes[-30:]
    older = closes[-90:-30] if len(closes) >= 90 else closes[:-30]

    if not older or recent[0] <= 0 or older[0] <= 0:
        return None

    recent_trend = (recent[-1] - recent[0]) / recent[0] * 100.0
    older_trend = (older[-1] - older[0]) / older[0] * 100.0
    momentum = recent_trend - older_trend

    return {
        "source": "momentum_fallback",
        "last_close": round(closes[-1], 4),
        "recent_trend_pct": round(recent_trend, 4),
        "prior_trend_pct": round(older_trend, 4),
        "expected_return_1day_pct": None,
        "expected_return_5day_pct": None,
        "score_1day": None,
        "score_5day": None,
        "score": round(_score_from_return(momentum, MOMENTUM_SCALE_PCT), 2),
        "observations": len(closes),
    }


def forecast(symbol, asset_id=None):
    """Best available forward-looking score for one asset, 0-100.

    Always returns a dict with ``score`` and ``source`` so callers never have to
    guess whether a number came from the network or the fallback.
    """
    predicted = _predict_with_models(symbol)
    if predicted is not None:
        scores = [
            (predicted.get("score_1day"), WEIGHT_1DAY),
            (predicted.get("score_5day"), WEIGHT_5DAY),
        ]
        usable = [(s, w) for s, w in scores if s is not None]
        total_weight = sum(w for _, w in usable)
        predicted["score"] = round(sum(s * w for s, w in usable) / total_weight, 2)
        return predicted

    if asset_id is not None:
        fallback = _momentum_fallback(asset_id)
        if fallback is not None:
            return fallback

    return {
        "source": "unavailable",
        "score": NEUTRAL_SCORE,
        "score_1day": None,
        "score_5day": None,
        "note": "Not enough price history to form a view.",
    }


def forecast_many(assets):
    """Forecast a list of (symbol, asset_id) pairs, keyed by asset_id."""
    return {asset_id: forecast(symbol, asset_id) for symbol, asset_id in assets}
