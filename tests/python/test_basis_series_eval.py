import pytest

import numpy as np
from numpy.polynomial.chebyshev import chebval
from numpy.polynomial.hermite import hermval
from numpy.polynomial.laguerre import lagval
from numpy.polynomial.legendre import legval
from numpy.polynomial.polynomial import polyval
from tests.python.basis_functions_ref import fourier_evaluate
from types import SimpleNamespace

import taichi as ti
from tests import test_utils


series_eval = SimpleNamespace(
    laguerre=lagval,
    hermite=hermval,
    legendre=legval,
    chebyshev=chebval,
    monomial=polyval,
    fourier=fourier_evaluate,
)


def _taichi_series_eval(family, x, coeffs, dt):
    # TODO: Replace with your Taichi implementation call.
    # Example target signature:
    # return ti_basis.series_eval(family=family, x=x, coeffs=coeffs, dt=dt)
    raise NotImplementedError("Taichi basis series implementation is not wired yet.")


def _test_basis_series_eval(dt, family, degree):
    tol = 1e-5 if dt == ti.f32 else 1e-12
    np_dt = np.float32 if dt == ti.f32 else np.float64

    x = np.linspace(-2.0, 2.0, 37, dtype=np_dt)
    coeffs = np.random.default_rng(1000 + degree).normal(size=degree + 1).astype(np_dt)
    basis_func = getattr(series_eval, family)
    expected = basis_func(x, coeffs).astype(np_dt)

    try: # TODO: Remove this part once Taichi is wired.
        actual = _taichi_series_eval(family, x, coeffs, dt)
    except NotImplementedError as exc:
        pytest.skip(str(exc))

    np.testing.assert_allclose(np.asarray(actual, dtype=np_dt), expected, rtol=tol, atol=tol)


@pytest.mark.parametrize("family", ["laguerre", "hermite", "legendre", "chebyshev", "monomial", "fourier"])
@pytest.mark.parametrize("degree", [0, 1, 2, 4, 7, 10])
@test_utils.test(default_fp=ti.f32, fast_math=False)
def test_basis_series_eval_f32(family, degree):
    _test_basis_series_eval(ti.f32, family, degree)


@pytest.mark.parametrize("family", ["laguerre", "hermite", "legendre", "chebyshev", "monomial", "fourier"])
@pytest.mark.parametrize("degree", [0, 1, 2, 4, 7, 10])
@test_utils.test(require=ti.extension.data64, default_fp=ti.f64, fast_math=False)
def test_basis_series_eval_f64(family, degree):
    _test_basis_series_eval(ti.f64, family, degree)

