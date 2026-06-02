import numpy as np


def _project_simplex(w, lo=None, hi=None):
    n = len(w)
    if lo is None:
        lo = np.zeros(n)
    if hi is None:
        hi = np.ones(n)
    w = np.clip(w, lo, hi)
    for _ in range(200):
        excess = w.sum() - 1.0
        if abs(excess) < 1e-12:
            break
        adj = excess / n
        w = np.clip(w - adj, lo, hi)
    return w


def _solve(obj_grad, n, bounds=None, max_iter=5000, lr=0.01):
    lo = np.array([b[0] for b in bounds]) if bounds else np.zeros(n)
    hi = np.array([b[1] for b in bounds]) if bounds else np.ones(n)
    w = np.ones(n) / n
    w = _project_simplex(w, lo, hi)
    best_w, best_val = w.copy(), obj_grad(w)[0]
    for i in range(max_iter):
        val, grad = obj_grad(w)
        step = lr / (1 + i * 0.001)
        w = w - step * grad
        w = _project_simplex(w, lo, hi)
        if val < best_val:
            best_val = val
            best_w = w.copy()
    return best_w, best_val


def optimize_max_sharpe(expected_returns, cov_matrix, bounds=None, risk_free_rate=0.0):
    n = len(expected_returns)
    if bounds is None:
        bounds = [(0, 0.10)] * n
    mu = np.array(expected_returns, dtype=float)
    C = np.array(cov_matrix, dtype=float)

    def obj_grad(w):
        port_ret = w @ mu - risk_free_rate
        port_vol = np.sqrt(max(w @ C @ w, 1e-20))
        neg_sharpe = -port_ret / port_vol
        d_ret = -mu / port_vol
        d_vol = port_ret / (port_vol ** 2) * (C @ w / port_vol)
        return neg_sharpe, d_ret + d_vol

    w, neg_s = _solve(obj_grad, n, bounds)
    return w, -neg_s


def optimize_min_variance(cov_matrix, bounds=None):
    n = cov_matrix.shape[0]
    if bounds is None:
        bounds = [(0, 0.10)] * n
    C = np.array(cov_matrix, dtype=float)

    def obj_grad(w):
        vol = np.sqrt(max(w @ C @ w, 1e-20))
        grad = C @ w / vol
        return vol, grad

    w, vol = _solve(obj_grad, n, bounds)
    return w, vol


def efficient_frontier(expected_returns, cov_matrix, n_points=20, bounds=None):
    n = len(expected_returns)
    if bounds is None:
        bounds = [(0, 0.10)] * n
    mu = np.array(expected_returns, dtype=float)
    C = np.array(cov_matrix, dtype=float)
    min_ret = mu.min()
    max_ret = mu.max()
    targets = np.linspace(min_ret, max_ret, n_points)

    frontier = []
    for target in targets:
        def obj_grad(w, t=target):
            vol = np.sqrt(max(w @ C @ w, 1e-20))
            ret_gap = w @ mu - t
            penalty = 100.0 * ret_gap ** 2
            grad_vol = C @ w / vol
            grad_pen = 200.0 * ret_gap * mu
            return vol + penalty, grad_vol + grad_pen

        w, _ = _solve(obj_grad, n, bounds)
        port_vol = np.sqrt(w @ C @ w)
        port_ret = w @ mu
        frontier.append({"return": port_ret, "volatility": port_vol, "weights": w})
    return frontier


def optimize_risk_parity(cov_matrix, bounds=None):
    n = cov_matrix.shape[0]
    if bounds is None:
        bounds = [(0.01, 0.30)] * n
    C = np.array(cov_matrix, dtype=float)

    def obj_grad(w):
        port_var = w @ C @ w
        port_vol = np.sqrt(max(port_var, 1e-20))
        marginal = C @ w
        risk_contrib = w * marginal / max(port_vol, 1e-10)
        target_rc = port_vol / n
        diff = risk_contrib - target_rc
        val = np.sum(diff ** 2)
        grad = 2 * diff * (marginal / port_vol + w * C / port_vol - np.outer(w * marginal, C @ w) / (port_vol ** 3)).sum(axis=1)
        return val, grad

    w, _ = _solve(obj_grad, n, bounds, max_iter=8000, lr=0.005)
    port_vol = np.sqrt(w @ C @ w)
    return w, port_vol


def optimize_target_return(expected_returns, cov_matrix, target_return, bounds=None):
    n = len(expected_returns)
    if bounds is None:
        bounds = [(0, 0.10)] * n
    mu = np.array(expected_returns, dtype=float)
    C = np.array(cov_matrix, dtype=float)

    def obj_grad(w):
        vol = np.sqrt(max(w @ C @ w, 1e-20))
        ret_gap = w @ mu - target_return
        penalty = 100.0 * ret_gap ** 2
        grad_vol = C @ w / vol
        grad_pen = 200.0 * ret_gap * mu
        return vol + penalty, grad_vol + grad_pen

    w, _ = _solve(obj_grad, n, bounds)
    port_vol = np.sqrt(w @ C @ w)
    return w, port_vol
