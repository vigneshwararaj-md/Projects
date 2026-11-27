"""
Demo: 3-class spiral classification.
1) Gradient-check the exact architecture we are about to train.
2) Train it with SGD / SGD+momentum / RMSProp / Adam and compare.
3) Save a decision-boundary plot (if matplotlib is installed).
"""
import numpy as np

from numpynet import (Adam, BatchNorm1D, Dense, ReLU, RMSProp, SGD, Sequential,
                      SoftmaxCrossEntropy, accuracy, fit, gradient_check)


def make_spiral(n_per_class=150, k=3, noise=0.25, rng=None):
    X = np.zeros((n_per_class * k, 2))
    y = np.zeros(n_per_class * k, dtype=int)
    for j in range(k):
        ix = slice(n_per_class * j, n_per_class * (j + 1))
        r = np.linspace(0.05, 1.0, n_per_class)
        t = np.linspace(j * 4, (j + 1) * 4, n_per_class) + rng.normal(size=n_per_class) * noise
        X[ix] = np.c_[r * np.sin(t), r * np.cos(t)]
        y[ix] = j
    return X, y


def build(seed):
    rng = np.random.default_rng(seed)
    return Sequential(
        Dense(2, 64, rng=rng), BatchNorm1D(64), ReLU(),
        Dense(64, 64, rng=rng), BatchNorm1D(64), ReLU(),
        Dense(64, 3, rng=rng),
    )


if __name__ == "__main__":
    rng = np.random.default_rng(42)
    X, y = make_spiral(rng=rng)
    perm = rng.permutation(len(X))
    X, y = X[perm], y[perm]
    split = int(0.8 * len(X))
    Xtr, ytr, Xva, yva = X[:split], y[:split], X[split:], y[split:]

    print("Gradient check on the demo architecture:")
    gradient_check(build(0), SoftmaxCrossEntropy(), Xtr[:16], ytr[:16], tol=1e-5)

    configs = {
        "SGD (lr=0.1)": lambda: SGD(0.1),
        "SGD + momentum": lambda: SGD(0.05, momentum=0.9, nesterov=True),
        "RMSProp": lambda: RMSProp(0.005),
        "Adam": lambda: Adam(0.01, weight_decay=1e-4),
    }
    models = {}
    print("\nTraining (150 epochs, batch 64):")
    print(f"{'optimizer':18s} {'train loss':>10s} {'train acc':>10s} {'val acc':>8s}")
    for name, make_opt in configs.items():
        model = build(0)
        hist = fit(model, SoftmaxCrossEntropy(), make_opt(), Xtr, ytr, epochs=150,
                   batch_size=64, X_val=Xva, y_val=yva, metric=accuracy,
                   rng=np.random.default_rng(0))
        models[name] = (model, hist)
        print(f"{name:18s} {hist['loss'][-1]:10.4f} {hist['metric'][-1]:10.3f} {hist['val_metric'][-1]:8.3f}")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(1, 2, figsize=(11, 4.5))
        for name, (_, h) in models.items():
            ax[0].plot(h["loss"], label=name)
        ax[0].set(xlabel="epoch", ylabel="training loss", yscale="log", title="Optimizer comparison")
        ax[0].legend()

        model = models["Adam"][0]
        xx, yy = np.meshgrid(np.linspace(-1.2, 1.2, 300), np.linspace(-1.2, 1.2, 300))
        pred = model.predict(np.c_[xx.ravel(), yy.ravel()]).argmax(axis=1).reshape(xx.shape)
        ax[1].contourf(xx, yy, pred, alpha=0.3, levels=[-0.5, 0.5, 1.5, 2.5])
        ax[1].scatter(Xva[:, 0], Xva[:, 1], c=yva, s=12, edgecolors="k", linewidths=0.3)
        ax[1].set(title="Adam decision boundary (validation points)")
        fig.tight_layout()
        fig.savefig("spiral_results.png", dpi=130)
        print("\nSaved spiral_results.png")
    except ImportError:
        print("\n(matplotlib not installed; skipping plot)")
