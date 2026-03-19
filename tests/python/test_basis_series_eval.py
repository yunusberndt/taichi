import pytest
from tests import test_utils
from types import SimpleNamespace

import numpy as np
from numpy.polynomial import (
    chebval as np_chebval,
    fourierval as np_fourierval,
    hermval as np_hermval,
    lagval as np_lagval,
    legval as np_legval,
    polyval as np_polyval,
)

import taichi as ti
from taichi.math.polynomial import (
    lagval as ti_lagval,
    hermval as ti_hermval,
    chebval as ti_chebval,
    legval as ti_legval,
    polyval as ti_polyval,
    fourierval as ti_fourierval,
)


np_series_eval = SimpleNamespace(
    laguerre=np_lagval,
    hermite=np_hermval,
    legendre=np_legval,
    chebyshev=np_chebval,
    monomial=np_polyval,
    fourier=np_fourierval,
)

ti_series_eval = SimpleNamespace(
    laguerre=ti_lagval,
    hermite=ti_hermval,
    legendre=ti_legval,
    chebyshev=ti_chebval,
    monomial=ti_polyval,
    fourier=ti_fourierval,
)



def _test_basis_series_eval(dt, family, degree):
    tol = 1e-5 if dt == ti.f32 else 1e-12
    
    # Numpy logic to get expected values
    np_dt = np.float32 if dt == ti.f32 else np.float64

    x = np.linspace(-2.0, 2.0, 37, dtype=np_dt)
    coeffs = np.random.default_rng(1000 + degree).normal(size=degree + 1).astype(np_dt)
    np_basis_func = getattr(np_series_eval, family)
    expected = np_basis_func(x, coeffs).astype(np_dt)

    # Taichi logic to get actual values
    ti_x = ti.field(dt, shape=x.shape)
    ti_x.from_numpy(x)
    ti_coeffs = ti.field(dt, shape=coeffs.shape)
    ti_coeffs.from_numpy(coeffs)
    ti_basis_func = getattr(ti_series_eval, family)

    @ti.kernel
    def basis_test(ti_x: ti.template(), ti_coeffs: ti.template()):
        ti_basis_func(ti_x, ti_coeffs)

    basis_test(ti_x, ti_coeffs)
    actual = ti_x.to_numpy()

    # Compare expected and actual values
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

