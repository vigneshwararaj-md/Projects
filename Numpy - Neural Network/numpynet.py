"""
numpynet: a small neural network library in pure NumPy.

Contents
    Layers       Dense, ReLU, LeakyReLU, Tanh, Sigmoid, Dropout, BatchNorm1D
    Losses       MSE, BCEWithLogits, SoftmaxCrossEntropy
    Optimizers   SGD (momentum / Nesterov), RMSProp, Adam (decoupled weight decay)
    Model        Sequential (+ save/load), fit(), accuracy()
    Verification gradient_check() (centred finite differences)

Conventions
    * Data is a 2-D array of shape (batch, features), float64.
    * Losses return the MEAN over the batch, so the loss gradient already
      carries the 1/N factor. Layers therefore SUM over the batch in backward.
    * Every layer caches what it needs in forward() and consumes it in backward().
"""
from __future__ import annotations

import numpy as np


# ----------------------------------------------------------------------------
# Layers
# ----------------------------------------------------------------------------
class Layer:
    """Base class. `params`/`grads` are dicts of same-shaped arrays updated in place."""

    def __init__(self):
        self.params: dict[str, np.ndarray] = {}
        self.grads: dict[str, np.ndarray] = {}
        self.buffers: dict[str, np.ndarray] = {}  # non-trainable state (saved, not optimised)

    def forward(self, x, training=True):
        raise NotImplementedError

    def backward(self, grad):
        raise NotImplementedError


class Dense(Layer):
    """y = x @ W + b.   dW = x^T g,  db = sum(g),  dx = g W^T."""

    def __init__(self, n_in, n_out, init="he", rng=None):
        super().__init__()
        rng = rng if rng is not None else np.random.default_rng()
        if init == "he":  # suited to ReLU
            std = np.sqrt(2.0 / n_in)
        elif init == "xavier":  # suited to tanh / sigmoid
            std = np.sqrt(2.0 / (n_in + n_out))
        else:
            raise ValueError(f"unknown init '{init}'")
        self.params = {"W": rng.normal(0.0, std, (n_in, n_out)), "b": np.zeros(n_out)}
        self.grads = {k: np.zeros_like(v) for k, v in self.params.items()}

    def forward(self, x, training=True):
        self.x = x
        return x @ self.params["W"] + self.params["b"]

    def backward(self, grad):
        self.grads["W"][...] = self.x.T @ grad
        self.grads["b"][...] = grad.sum(axis=0)
        return grad @ self.params["W"].T


class ReLU(Layer):
    def forward(self, x, training=True):
        self.mask = x > 0
        return x * self.mask

    def backward(self, grad):
        return grad * self.mask


class LeakyReLU(Layer):
    def __init__(self, alpha=0.01):
        super().__init__()
        self.alpha = alpha

    def forward(self, x, training=True):
        self.pos = x > 0
        return np.where(self.pos, x, self.alpha * x)

    def backward(self, grad):
        return grad * np.where(self.pos, 1.0, self.alpha)


class Tanh(Layer):
    def forward(self, x, training=True):
        self.out = np.tanh(x)
        return self.out

    def backward(self, grad):
        return grad * (1.0 - self.out ** 2)


def _sigmoid(z):
    """Numerically stable sigmoid (never exponentiates a large positive number)."""
    out = np.empty_like(z, dtype=float)
    pos = z >= 0
    out[pos] = 1.0 / (1.0 + np.exp(-z[pos]))
    ez = np.exp(z[~pos])
    out[~pos] = ez / (1.0 + ez)
    return out


class Sigmoid(Layer):
    def forward(self, x, training=True):
        self.out = _sigmoid(x)
        return self.out

    def backward(self, grad):
        return grad * self.out * (1.0 - self.out)


class Dropout(Layer):
    """Inverted dropout: scale at train time so inference is a no-op."""

    def __init__(self, p=0.5, rng=None):
        super().__init__()
        self.p = p
        self.rng = rng if rng is not None else np.random.default_rng()

    def forward(self, x, training=True):
        if not training or self.p == 0.0:
            self.mask = None
            return x
        self.mask = (self.rng.random(x.shape) >= self.p) / (1.0 - self.p)
        return x * self.mask

    def backward(self, grad):
        return grad if self.mask is None else grad * self.mask


class BatchNorm1D(Layer):
    """
    Batch normalisation over the batch axis.
        xhat = (x - mu) / sqrt(var + eps),   y = gamma * xhat + beta
    Backward (derived through mu and var):
        dx = (inv_std / N) * (N*dxhat - sum(dxhat) - xhat * sum(dxhat * xhat))
    """

    def __init__(self, n_features, momentum=0.9, eps=1e-5):
        super().__init__()
        self.momentum, self.eps = momentum, eps
        self.params = {"gamma": np.ones(n_features), "beta": np.zeros(n_features)}
        self.grads = {k: np.zeros_like(v) for k, v in self.params.items()}
        self.buffers = {"running_mean": np.zeros(n_features), "running_var": np.ones(n_features)}

    def forward(self, x, training=True):
        self.training = training
        if training:
            mu, var = x.mean(axis=0), x.var(axis=0)
            m = self.momentum
            self.buffers["running_mean"][...] = m * self.buffers["running_mean"] + (1 - m) * mu
            self.buffers["running_var"][...] = m * self.buffers["running_var"] + (1 - m) * var
        else:
            mu, var = self.buffers["running_mean"], self.buffers["running_var"]
        self.inv_std = 1.0 / np.sqrt(var + self.eps)
        self.xhat = (x - mu) * self.inv_std
        return self.params["gamma"] * self.xhat + self.params["beta"]

    def backward(self, grad):
        self.grads["gamma"][...] = (grad * self.xhat).sum(axis=0)
        self.grads["beta"][...] = grad.sum(axis=0)
        dxhat = grad * self.params["gamma"]
        if not self.training:  # statistics are constants in eval mode
            return dxhat * self.inv_std
        n = grad.shape[0]
        return (self.inv_std / n) * (
            n * dxhat - dxhat.sum(axis=0) - self.xhat * (dxhat * self.xhat).sum(axis=0)
        )


# ----------------------------------------------------------------------------
# Losses  (forward -> scalar mean loss, backward -> d loss / d prediction)
# ----------------------------------------------------------------------------
class MSE:
    def forward(self, pred, target):
        self.diff = pred - target
        return float(np.mean(self.diff ** 2))

    def backward(self):
        return 2.0 * self.diff / self.diff.size


class BCEWithLogits:
    """Binary cross-entropy on raw logits (stable form, no log(0))."""

    def forward(self, logits, target):
        self.logits, self.target = logits, target
        loss = np.maximum(logits, 0) - logits * target + np.log1p(np.exp(-np.abs(logits)))
        return float(loss.mean())

    def backward(self):
        return (_sigmoid(self.logits) - self.target) / self.logits.size


class SoftmaxCrossEntropy:
    """Fused softmax + cross-entropy on logits with integer class labels.
    The fused gradient is simply (softmax - onehot) / N."""

    def forward(self, logits, y):
        z = logits - logits.max(axis=1, keepdims=True)  # shift for stability
        log_probs = z - np.log(np.exp(z).sum(axis=1, keepdims=True))
        self.probs = np.exp(log_probs)
        self.y = y.astype(int)
        return float(-log_probs[np.arange(len(self.y)), self.y].mean())

    def backward(self):
        grad = self.probs.copy()
        grad[np.arange(len(self.y)), self.y] -= 1.0
        return grad / len(self.y)


# ----------------------------------------------------------------------------
# Optimizers. `params` is a list of (array, grad, decay_flag); updates are in place.
# ----------------------------------------------------------------------------
class Optimizer:
    def __init__(self, lr, weight_decay=0.0):
        self.lr, self.weight_decay = lr, weight_decay
        self.state: dict[int, dict] = {}
        self.t = 0

    def step(self, params):
        self.t += 1
        for i, (p, g, decay) in enumerate(params):
            self._update(self.state.setdefault(i, {}), p, g, decay and self.weight_decay > 0)


class SGD(Optimizer):
    """SGD with optional (Nesterov) momentum and coupled L2 weight decay."""

    def __init__(self, lr=0.01, momentum=0.0, nesterov=False, weight_decay=0.0):
        super().__init__(lr, weight_decay)
        self.momentum, self.nesterov = momentum, nesterov

    def _update(self, s, p, g, decay):
        if decay:
            g = g + self.weight_decay * p
        if self.momentum == 0.0:
            p -= self.lr * g
            return
        buf = s.setdefault("buf", np.zeros_like(p))
        buf *= self.momentum
        buf += g
        p -= self.lr * (g + self.momentum * buf if self.nesterov else buf)


class RMSProp(Optimizer):
    def __init__(self, lr=1e-3, rho=0.9, eps=1e-8, weight_decay=0.0):
        super().__init__(lr, weight_decay)
        self.rho, self.eps = rho, eps

    def _update(self, s, p, g, decay):
        if decay:
            g = g + self.weight_decay * p
        sq = s.setdefault("sq", np.zeros_like(p))
        sq *= self.rho
        sq += (1 - self.rho) * g * g
        p -= self.lr * g / (np.sqrt(sq) + self.eps)


class Adam(Optimizer):
    """Adam with bias correction. weight_decay is DECOUPLED (AdamW)."""

    def __init__(self, lr=1e-3, beta1=0.9, beta2=0.999, eps=1e-8, weight_decay=0.0):
        super().__init__(lr, weight_decay)
        self.b1, self.b2, self.eps = beta1, beta2, eps

    def _update(self, s, p, g, decay):
        m = s.setdefault("m", np.zeros_like(p))
        v = s.setdefault("v", np.zeros_like(p))
        m *= self.b1
        m += (1 - self.b1) * g
        v *= self.b2
        v += (1 - self.b2) * g * g
        m_hat = m / (1 - self.b1 ** self.t)
        v_hat = v / (1 - self.b2 ** self.t)
        if decay:
            p -= self.lr * self.weight_decay * p
        p -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)


# ----------------------------------------------------------------------------
# Model
# ----------------------------------------------------------------------------
class Sequential:
    def __init__(self, *layers):
        self.layers = list(layers)

    def forward(self, x, training=True):
        for layer in self.layers:
            x = layer.forward(x, training)
        return x

    def backward(self, grad):
        for layer in reversed(self.layers):
            grad = layer.backward(grad)
        return grad

    def predict(self, x):
        return self.forward(x, training=False)

    def parameters(self):
        """List of (param, grad, apply_weight_decay). Only weight matrices are decayed."""
        out = []
        for layer in self.layers:
            for name, p in layer.params.items():
                out.append((p, layer.grads[name], name == "W"))
        return out

    def state_dict(self):
        sd = {}
        for i, layer in enumerate(self.layers):
            for name, a in {**layer.params, **layer.buffers}.items():
                sd[f"{i}.{name}"] = a
        return sd

    def save(self, path):
        np.savez(path, **self.state_dict())

    def load(self, path):
        data = np.load(path)
        for key, a in self.state_dict().items():
            a[...] = data[key]


def accuracy(logits, y):
    return float((logits.argmax(axis=1) == y).mean())


def fit(model, loss_fn, optimizer, X, y, epochs=100, batch_size=32,
        X_val=None, y_val=None, metric=None, rng=None, log_every=0):
    """Mini-batch training loop. Returns a history dict of per-epoch values."""
    rng = rng if rng is not None else np.random.default_rng()
    n = len(X)
    hist = {"loss": [], "val_loss": [], "metric": [], "val_metric": []}
    for epoch in range(1, epochs + 1):
        order = rng.permutation(n)
        total = 0.0
        for start in range(0, n, batch_size):
            idx = order[start:start + batch_size]
            out = model.forward(X[idx], training=True)
            total += loss_fn.forward(out, y[idx]) * len(idx)
            model.backward(loss_fn.backward())
            optimizer.step(model.parameters())
        hist["loss"].append(total / n)
        if metric:
            hist["metric"].append(metric(model.predict(X), y))
        if X_val is not None:
            pv = model.predict(X_val)
            hist["val_loss"].append(loss_fn.forward(pv, y_val))
            if metric:
                hist["val_metric"].append(metric(pv, y_val))
        if log_every and (epoch % log_every == 0 or epoch == 1):
            msg = f"epoch {epoch:4d}  loss {hist['loss'][-1]:.4f}"
            if metric:
                msg += f"  metric {hist['metric'][-1]:.3f}"
            if X_val is not None:
                msg += f"  val_loss {hist['val_loss'][-1]:.4f}"
                if metric:
                    msg += f"  val_metric {hist['val_metric'][-1]:.3f}"
            print(msg)
    return hist


# ----------------------------------------------------------------------------
# Gradient check
# ----------------------------------------------------------------------------
def gradient_check(model, loss_fn, x, y, eps=1e-5, tol=1e-6, atol=1e-8,
                   samples_per_param=20, rng=None, verbose=True):
    """
    Compare analytic gradients from backprop with centred finite differences:
        dL/dw ~ (L(w+eps) - L(w-eps)) / (2*eps)
    Uses relative error |a-n| / (|a|+|n|). If BOTH |a| and |n| are below `atol` they count as zero:
    some true gradients are exactly 0 (e.g. the bias of a Dense layer feeding a
    BatchNorm, whose mean-subtraction cancels it), and there the two estimates are
    just float noise (~1e-11) whose relative error is meaningless.
    Returns the worst error found.

    Notes: run in float64; avoid Dropout (stochastic loss); ReLU kinks can give
    rare false alarms when a pre-activation sits within eps of 0.
    """
    rng = rng if rng is not None else np.random.default_rng(0)

    def loss():
        return loss_fn.forward(model.forward(x, training=True), y)

    loss()
    model.backward(loss_fn.backward())
    analytic = [g.copy() for _, g, _ in model.parameters()]

    worst = 0.0
    for k, (p, _, _) in enumerate(model.parameters()):
        flat = p.reshape(-1)  # view: writes go straight into the parameter
        picks = rng.choice(flat.size, size=min(samples_per_param, flat.size), replace=False)
        errs = []
        for j in picks:
            orig = flat[j]
            flat[j] = orig + eps
            lp = loss()
            flat[j] = orig - eps
            lm = loss()
            flat[j] = orig
            num = (lp - lm) / (2 * eps)
            ana = analytic[k].reshape(-1)[j]
            both_zero = abs(ana) < atol and abs(num) < atol
            errs.append(0.0 if both_zero else abs(ana - num) / (abs(ana) + abs(num)))
        worst = max(worst, max(errs))
        if verbose:
            print(f"  param {k} shape {str(p.shape):10s} max rel err {max(errs):.2e}")
    if verbose:
        print(f"  => worst {worst:.2e}  [{'PASS' if worst < tol else 'FAIL'}]")
    return worst
