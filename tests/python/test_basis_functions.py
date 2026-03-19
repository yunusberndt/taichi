import pytest

import numpy as np

import taichi as ti
from tests import test_utils
import tests.python.basis_functions_ref as basis_functions



def _taichi_basis_matrix(family, x, x_length, num_basis_functions, use_orth_weight, dt):
    # TODO: Replace with your Taichi implementation call.
    # Example target signature:
    # return ti_basis.basis_matrix(family=family, x=x, x_length=x_length, num_basis_functions=num_basis_functions, use_orth_weight=use_orth_weight, dt=dt)
    raise NotImplementedError("Taichi basis matrix implementation is not wired yet.")


def _test_basis_functions(dt, family, num_basis_functions, use_orth_weight):
    tol = 1e-5 if dt == ti.f32 else 1e-12
    np_dt = np.float32 if dt == ti.f32 else np.float64

    x = np.linspace(0.0, 0.999, 37, dtype=np_dt)
    x_length = x.shape[0]

    basis_func = getattr(basis_functions, family)
    expected = basis_func(x, x_length, num_basis_functions, use_orth_weight).astype(np_dt)

    try:  # TODO: Remove this part once Taichi is wired.
        actual = _taichi_basis_matrix(family, x, x_length, num_basis_functions, use_orth_weight, dt)
    except NotImplementedError as exc:
        pytest.skip(str(exc))

    actual = np.asarray(actual, dtype=np_dt)
    assert actual.shape == expected.shape
    np.testing.assert_allclose(actual, expected, rtol=tol, atol=tol)


@pytest.mark.parametrize(
    "family,use_orth_weight",
    [
        pytest.param("laguerre", False),
        pytest.param("laguerre", True),
        pytest.param("hermite", False),
        pytest.param("hermite", True),
        pytest.param("legendre", False),
        pytest.param("chebyshev", False),
        pytest.param("chebyshev", True),
        pytest.param("monomial", False),
        pytest.param("fourier", False),
    ],
)
@pytest.mark.parametrize("num_basis_functions", [1, 2, 4, 7, 10])
@test_utils.test(default_fp=ti.f32, fast_math=False)
def test_basis_functions_f32(family, use_orth_weight, num_basis_functions):
    _test_basis_functions(ti.f32, family, num_basis_functions, use_orth_weight)


@pytest.mark.parametrize(
    "family,use_orth_weight",
    [
        pytest.param("laguerre", False),
        pytest.param("laguerre", True),
        pytest.param("hermite", False),
        pytest.param("hermite", True),
        pytest.param("chebyshev", False),
        pytest.param("chebyshev", True),
        pytest.param("legendre", False),
        pytest.param("monomial", False),
        pytest.param("fourier", False),
    ],
)
@pytest.mark.parametrize("num_basis_functions", [1, 2, 4, 7, 10])
@test_utils.test(require=ti.extension.data64, default_fp=ti.f64, fast_math=False)
def test_basis_functions_f64(family, use_orth_weight, num_basis_functions):
    _test_basis_functions(ti.f64, family, num_basis_functions, use_orth_weight)
