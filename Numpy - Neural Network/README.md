# numpynet

A small neural network library in pure NumPy (about 400 lines, no autograd). Backprop is derived and implemented by hand for every layer, then verified numerically.

## Run

```bash
pip install numpy matplotlib   # matplotlib optional (plots only)
python test_numpynet.py        # 8 tests: gradient checks, optimizers, XOR, save/load
python demo_spiral.py          # gradient check + optimizer comparison + plot
```

## What's inside

| Area | Implemented |
|---|---|
| Layers | Dense (He/Xavier init), ReLU, LeakyReLU, Tanh, Sigmoid, Dropout (inverted), BatchNorm1D |
| Losses | MSE, BCEWithLogits, SoftmaxCrossEntropy (fused, log-sum-exp stable) |
| Optimizers | SGD (momentum, Nesterov), RMSProp, Adam / AdamW (bias correction, decoupled weight decay) |
| Tooling | `Sequential`, `fit()` mini-batch loop, `save`/`load`, `gradient_check()` |

## Usage

```python
from numpynet import *

model = Sequential(Dense(2, 64), BatchNorm1D(64), ReLU(), Dense(64, 3))
loss  = SoftmaxCrossEntropy()
opt   = Adam(lr=1e-2, weight_decay=1e-4)

gradient_check(model, loss, X[:16], y[:16])          # verify backprop first
fit(model, loss, opt, X, y, epochs=100, batch_size=64, metric=accuracy, log_every=10)
```

## Design notes (worth being able to explain)

- **Loss returns the batch mean**, so the 1/N lives in the loss gradient and layers just sum over the batch.
- **Softmax + cross-entropy are fused**: the gradient collapses to `(softmax - onehot) / N`, and the forward pass uses the max-shift trick to avoid overflow.
- **BatchNorm backward** is derived through both the batch mean and variance: `dx = inv_std/N * (N*dxhat - sum(dxhat) - xhat*sum(dxhat*xhat))`. Eval mode uses running statistics.
- **Gradient check** uses centred differences `(L(w+e) - L(w-e)) / 2e` in float64 and relative error. One subtle case: the bias of a Dense layer feeding a BatchNorm has a true gradient of exactly 0, because BN's mean subtraction cancels it, so only a tiny absolute tolerance is applied when both estimates are ~0.
- **The checker is itself tested**: `test_gradient_check_catches_a_bug` sabotages a backward pass and asserts the check fails.
- Limitations: no conv/RNN layers, no GPU, Dropout cannot be gradient-checked (stochastic loss).

## Ideas to extend (good for a write-up)

Conv2D via im2col, LayerNorm, learning-rate schedules, gradient clipping, MNIST benchmark, and an ablation of optimizers/initialisation.
