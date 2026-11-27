"""Run with:  python test_numpynet.py   (or: pytest -q)"""
import numpy as np

from numpynet import (Adam, BatchNorm1D, BCEWithLogits, Dense, Dropout, LeakyReLU,
                      MSE, ReLU, RMSProp, SGD, Sequential, Sigmoid, SoftmaxCrossEntropy,
                      Tanh, accuracy, fit, gradient_check)

N, D, H, C = 8, 4, 5, 3


def build(act, batchnorm=False, seed=0):
    rng = np.random.default_rng(seed)
    layers = [Dense(D, H, rng=rng)]
    if batchnorm:
        layers.append(BatchNorm1D(H))
    layers += [act(), Dense(H, H, rng=rng), act(), Dense(H, C, rng=rng)]
    return Sequential(*layers)


def data(seed=1):
    rng = np.random.default_rng(seed)
    return rng.normal(size=(N, D)), rng.integers(0, C, N), rng.normal(size=(N, C))


def test_softmax_ce_all_activations():
    x, y, _ = data()
    for act in (Tanh, Sigmoid, ReLU, lambda: LeakyReLU(0.1)):
        assert gradient_check(build(act), SoftmaxCrossEntropy(), x, y, tol=1e-5, verbose=False) < 1e-5


def test_mse():
    x, _, t = data()
    assert gradient_check(build(Tanh), MSE(), x, t, verbose=False) < 1e-6


def test_bce_with_logits():
    x, _, _ = data()
    t = (np.random.default_rng(3).random((N, C)) > 0.5).astype(float)
    assert gradient_check(build(Tanh), BCEWithLogits(), x, t, verbose=False) < 1e-6


def test_batchnorm_gradients():
    x, y, _ = data()
    assert gradient_check(build(Tanh, batchnorm=True), SoftmaxCrossEntropy(), x, y, verbose=False) < 1e-6


def test_dropout_behaviour():
    d = Dropout(0.5, rng=np.random.default_rng(0))
    x = np.ones((2000, 10))
    assert np.array_equal(d.forward(x, training=False), x)  # identity at inference
    assert abs(d.forward(x, training=True).mean() - 1.0) < 0.05  # expectation preserved


def test_gradient_check_catches_a_bug():
    """A checker that never fails is worthless: sabotage a backward pass."""
    x, y, _ = data()
    model = build(Tanh)
    model.layers[1].backward = lambda g: g  # wrong: ignores the tanh derivative
    assert gradient_check(model, SoftmaxCrossEntropy(), x, y, verbose=False) > 1e-3


def test_optimizers_converge_on_quadratic():
    target = np.array([3.0, -2.0, 0.5])
    for opt in (SGD(0.1), SGD(0.05, momentum=0.9), SGD(0.05, momentum=0.9, nesterov=True),
                RMSProp(0.01), Adam(0.1)):
        w, g = np.zeros(3), np.zeros(3)
        for _ in range(1000):
            g[...] = 2 * (w - target)
            opt.step([(w, g, False)])
        assert np.abs(w - target).max() < 0.05, type(opt).__name__


def test_learns_xor_and_roundtrips_weights(tmp_path="/tmp"):
    rng = np.random.default_rng(0)
    X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], float)
    y = np.array([0, 1, 1, 0])
    model = Sequential(Dense(2, 8, init="xavier", rng=rng), Tanh(), Dense(8, 2, init="xavier", rng=rng))
    fit(model, SoftmaxCrossEntropy(), Adam(0.05), X, y, epochs=300, batch_size=4, rng=rng)
    assert accuracy(model.predict(X), y) == 1.0

    path = f"{tmp_path}/xor.npz"
    model.save(path)
    clone = Sequential(Dense(2, 8, rng=rng), Tanh(), Dense(8, 2, rng=rng))
    clone.load(path)
    assert np.allclose(clone.predict(X), model.predict(X))


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS  {t.__name__}")
    print(f"\n{len(tests)}/{len(tests)} tests passed")
