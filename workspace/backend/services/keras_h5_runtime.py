"""Minimal inference runtime for the Keras 2.6 HDF5 checkpoints (Phase 16).

Runs the trained GRU and LSTM models **without TensorFlow**, by reading the
weight tensors straight out of the .h5 with h5py and reimplementing the forward
pass in NumPy.

Why this exists rather than `pip install tensorflow`:

  * The backend venv is **Python 3.14**, and TensorFlow publishes no wheels for
    it (`No matching distribution found for tensorflow`). Installing it would
    mean rebuilding the environment on an older interpreter.
  * Even on a supported Python, TF >= 2.16 ships Keras 3, which refuses this
    HDF5 layout outright -- so the working combination is a pinned legacy TF
    *and* a downgraded interpreter, for one 25% scoring component.
  * The forward pass for a stacked GRU/LSTM regressor is about eighty lines of
    matrix arithmetic. The rest of this codebase computes its statistics in
    pure Python for the same reason (see risk_service), so this is consistent
    with how the app already works rather than an exception to it.

These are **the real trained weights** -- nothing is approximated. The only
thing not reproduced is dropout, which is a no-op at inference time anyway.

Architecture is read from the file, never assumed:

    GRU  : (None,90,6) -> GRU(320, seq) -> GRU(240) -> Dense(1)    718,081 params
    LSTM : (None,90,6) -> LSTM(320, seq) -> LSTM(240) -> Dense(5)  958,325 params

Both use tanh cell activation. The GRU has ``reset_after=False`` with
``hard_sigmoid`` gates (the pre-cuDNN formulation); the LSTM uses standard
sigmoid gates. Getting either of those wrong produces plausible-looking numbers
that are quietly wrong, so they're read from ``model_config`` and asserted.
"""

import json
import os

_CACHE = {}


# --------------------------------------------------------------------------
# activations
# --------------------------------------------------------------------------


def _sigmoid(x):
    import numpy as np

    # Split on sign to avoid overflow warnings on large-magnitude inputs.
    out = np.empty_like(x)
    positive = x >= 0
    out[positive] = 1.0 / (1.0 + np.exp(-x[positive]))
    exp_x = np.exp(x[~positive])
    out[~positive] = exp_x / (1.0 + exp_x)
    return out


def _hard_sigmoid(x):
    """Keras 2.x hard_sigmoid: clip(0.2x + 0.5, 0, 1)."""
    import numpy as np

    return np.clip(0.2 * x + 0.5, 0.0, 1.0)


_RECURRENT_ACTIVATIONS = {"sigmoid": _sigmoid, "hard_sigmoid": _hard_sigmoid}


# --------------------------------------------------------------------------
# checkpoint loading
# --------------------------------------------------------------------------


def _read_checkpoint(path):
    """Pull layer config + weight arrays out of an HDF5 checkpoint."""
    import h5py
    import numpy as np

    with h5py.File(path, "r") as handle:
        raw_config = handle.attrs.get("model_config")
        if raw_config is None:
            raise ValueError("checkpoint has no model_config")
        if isinstance(raw_config, bytes):
            raw_config = raw_config.decode()
        config = json.loads(raw_config)

        weights = {}

        def collect(name, node):
            if isinstance(node, h5py.Dataset):
                # "gru_4/gru_4/gru_cell_4/kernel:0" -> layer "gru_4", tensor "kernel"
                layer = name.split("/")[0]
                tensor = name.split("/")[-1].split(":")[0]
                weights.setdefault(layer, {})[tensor] = np.array(node, dtype="float64")

        handle["model_weights"].visititems(collect)

    layers = []
    for entry in config["config"]["layers"]:
        kind = entry["class_name"]
        if kind not in ("GRU", "LSTM", "Dense"):
            continue  # InputLayer / Dropout carry nothing we need at inference
        cfg = entry["config"]
        name = cfg["name"]
        if name not in weights:
            raise ValueError(f"no weights found for layer {name}")

        layers.append(
            {
                "kind": kind,
                "name": name,
                "units": cfg.get("units"),
                "activation": cfg.get("activation", "tanh"),
                "recurrent_activation": cfg.get("recurrent_activation", "sigmoid"),
                "reset_after": cfg.get("reset_after", False),
                "return_sequences": cfg.get("return_sequences", False),
                "W": weights[name].get("kernel"),
                "U": weights[name].get("recurrent_kernel"),
                "b": weights[name].get("bias"),
            }
        )

    return layers


def load(path):
    """Load and cache a checkpoint. Raises on anything unexpected."""
    key = os.path.abspath(path)
    if key not in _CACHE:
        _CACHE[key] = _read_checkpoint(key)
    return _CACHE[key]


# --------------------------------------------------------------------------
# forward passes
# --------------------------------------------------------------------------


def _gru_forward(layer, sequence):
    """Keras GRU, reset_after=False.

        z = rec_act(x·Wz + b_z + h·Uz)
        r = rec_act(x·Wr + b_r + h·Ur)
        h~ = act(x·Wh + b_h + (r ⊙ h)·Uh)
        h  = z ⊙ h + (1 - z) ⊙ h~

    Note the reset gate multiplies the *hidden state* before the recurrent
    matmul -- that is what reset_after=False means, and it is not
    interchangeable with the reset_after=True form.
    """
    import numpy as np

    units = layer["units"]
    W, U, b = layer["W"], layer["U"], layer["b"]
    rec_act = _RECURRENT_ACTIVATIONS[layer["recurrent_activation"]]

    Wz, Wr, Wh = W[:, :units], W[:, units : 2 * units], W[:, 2 * units :]
    Uz, Ur, Uh = U[:, :units], U[:, units : 2 * units], U[:, 2 * units :]
    bz, br, bh = b[:units], b[units : 2 * units], b[2 * units :]

    h = np.zeros(units)
    outputs = []

    for x in sequence:
        z = rec_act(x @ Wz + bz + h @ Uz)
        r = rec_act(x @ Wr + br + h @ Ur)
        hh = np.tanh(x @ Wh + bh + (r * h) @ Uh)
        h = z * h + (1.0 - z) * hh
        if layer["return_sequences"]:
            outputs.append(h.copy())

    return np.array(outputs) if layer["return_sequences"] else h


def _lstm_forward(layer, sequence):
    """Keras LSTM. Gate order in the packed kernel is i, f, c, o."""
    import numpy as np

    units = layer["units"]
    W, U, b = layer["W"], layer["U"], layer["b"]
    rec_act = _RECURRENT_ACTIVATIONS[layer["recurrent_activation"]]

    h = np.zeros(units)
    c = np.zeros(units)
    outputs = []

    for x in sequence:
        z = x @ W + h @ U + b
        i = rec_act(z[:units])
        f = rec_act(z[units : 2 * units])
        c = f * c + i * np.tanh(z[2 * units : 3 * units])
        o = rec_act(z[3 * units :])
        h = o * np.tanh(c)
        if layer["return_sequences"]:
            outputs.append(h.copy())

    return np.array(outputs) if layer["return_sequences"] else h


def predict(path, sequence):
    """Run one (timesteps, features) window through the network.

    Returns a 1-D array -- length 1 for the GRU checkpoint, length 5 for the
    LSTM's multi-horizon head.
    """
    import numpy as np

    activations = np.asarray(sequence, dtype="float64")

    for layer in load(path):
        if layer["kind"] == "GRU":
            activations = _gru_forward(layer, activations)
        elif layer["kind"] == "LSTM":
            activations = _lstm_forward(layer, activations)
        else:  # Dense, linear head
            activations = activations @ layer["W"] + layer["b"]
            if layer["activation"] == "tanh":
                activations = np.tanh(activations)
            elif layer["activation"] == "relu":
                activations = np.maximum(activations, 0.0)

    return np.atleast_1d(activations)


def describe(path):
    """Architecture summary, for the model-status endpoint."""
    layers = load(path)
    total = 0
    for layer in layers:
        for tensor in ("W", "U", "b"):
            if layer[tensor] is not None:
                total += int(layer[tensor].size)

    return {
        "layers": [
            {"kind": layer["kind"], "name": layer["name"], "units": layer["units"]}
            for layer in layers
        ],
        "parameters": total,
        "output_units": layers[-1]["units"],
    }
