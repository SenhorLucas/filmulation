"""Invert the negative "scan" map: scanned-negative RGB -> negative CMY density.

The forward scan (``FilmSim._density_cmy_to_rgb`` in negative mode) builds a
spectral transmission density that is *linear* in the CMY density vector
(``compute_density_spectral``), turns it into light via ``10**(-D)`` and
integrates against the CMF/illuminant to XYZ. That composition,

    D(lambda)  = density_cmy . dye(lambda) + base(lambda)
    T(lambda)  = 10**(-D(lambda))
    XYZ_j      = sum_lambda weights[lambda, j] * T(lambda)

is a smooth, monotone 3->3 map with a closed-form Jacobian, so it inverts
cleanly with a vectorized Newton-Raphson. This module owns that math; the
pipeline wiring lives in ``filmulation.model.process``.
"""

import numpy as np

LN10 = np.log(10.0)


def forward_density_to_xyz(density_cmy, dye, base, weights):
    """Map CMY density to XYZ, mirroring the negative-mode scan's spectral step.

    Parameters
    ----------
    density_cmy : ndarray, shape (..., 3)
        CMY density vectors.
    dye : ndarray, shape (L, 3)
        Per-wavelength dye densities of the three CMY layers
        (``profile.data.dye_density[:, 0:3]``).
    base : ndarray, shape (L,)
        Per-wavelength base/min density already scaled by
        ``dye_density_min_factor``.
    weights : ndarray, shape (L, 3)
        ``illuminant[lambda] * CMFS[lambda, j] / normalization``.

    Returns
    -------
    ndarray, shape (..., 3)
        XYZ tristimulus values.
    """
    D = density_cmy @ dye.T + base          # (..., L)
    T = 10.0 ** (-D)                        # (..., L)
    return T @ weights                      # (..., 3)


def invert_density_cmy_from_xyz(xyz_target, dye, base, weights,
                                x0=None, n_iter=12, damping=1.0,
                                density_clip=(-0.5, 8.0), tol=1e-7):
    """Recover CMY density from target XYZ via vectorized Newton-Raphson.

    The Jacobian of :func:`forward_density_to_xyz` is

        J[n, j, c] = d XYZ_j / d density_c
                   = -ln(10) * sum_lambda weights[lambda, j] * T[n, lambda] * dye[lambda, c]

    Newton over all points at once: ``m <- m - damping * solve(J, forward(m) - xyz)``,
    clamping density each step. Targets outside the realizable negative gamut
    converge to a clamped least-residual density rather than diverging.

    Parameters
    ----------
    xyz_target : ndarray, shape (..., 3)
        Target XYZ to invert.
    dye, base, weights : ndarray
        Same as :func:`forward_density_to_xyz`.
    x0 : ndarray, optional
        Initial density guess (same shape as ``xyz_target``). Defaults to zeros.
    n_iter : int
        Maximum Newton iterations.
    damping : float
        Step size multiplier (``< 1`` for extra stability near the gamut edge).
    density_clip : (float, float)
        Min/max density clamp applied after each step; guards the ill-conditioned
        near-black region where ``T -> 0``.
    tol : float
        Stop early once the max absolute XYZ residual drops below this.

    Returns
    -------
    ndarray, shape (..., 3)
        Recovered CMY density, same leading shape as ``xyz_target``.
    """
    shape = xyz_target.shape
    xyz = np.asarray(xyz_target, dtype=float).reshape(-1, 3)
    dye = np.asarray(dye, dtype=float)
    base = np.asarray(base, dtype=float)
    weights = np.asarray(weights, dtype=float)

    m = np.zeros_like(xyz) if x0 is None else np.asarray(x0, dtype=float).reshape(-1, 3).copy()
    for _ in range(n_iter):
        D = m @ dye.T + base                              # (N, L)
        T = 10.0 ** (-D)                                  # (N, L)
        residual = T @ weights - xyz                      # (N, 3)
        if np.nanmax(np.abs(residual)) < tol:
            break
        # J[n, j, c] = -ln10 * sum_l weights[l, j] * T[n, l] * dye[l, c]
        J = -LN10 * np.einsum('lj,nl,lc->njc', weights, T, dye)
        step = np.linalg.solve(J, residual[..., None])[..., 0]  # (N, 3)
        m = m - damping * step
        np.clip(m, density_clip[0], density_clip[1], out=m)
    return m.reshape(shape)
