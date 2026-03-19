"""
Math polynomial module.
"""
from taichi.lang.kernel_impl import func
from taichi.types import template
from taichi.lang.ops import (cos, sin)

@func
def lagval(x_field: template(), c_field: template()):
    """
    Evaluate a Laguerre series in-place on a 1D Taichi array.

    For coefficients ``c_field`` of length ``n + 1``, this computes

    .. math::
        p(x) = \\sum_{k=0}^{n} c_k L_k(x)

    for every element in ``x_field`` and writes the result back into
    ``x_field``.

    This function is intended to be called inside a Taichi kernel,
    much like other math functions in Taichi's math module.
    The evaluation uses Clenshaw recursion, and closely 
    follows the numpy lagval implementation.

    Parameters
    ----------
    x_field : template
        1D mutable container (for example ``ti.ndarray`` or templated field)
        containing the input ``x`` values. Updated in-place.
    c_field : template
        1D coefficient container where ``c_field[k]`` is the coefficient
        of :math:`L_k(x)`.

    Returns
    -------
    template
        The same container as ``x_field`` after in-place update.
    """

    c_len = c_field.shape[0]

    if c_len == 1:
        for j in range(x_field.shape[0]):
            x_field[j] = c_field[0]
    elif c_len == 2:
        for j in range(x_field.shape[0]):
            x_field[j] = c_field[0] + c_field[1]*(1 - x_field[j])
    else:
        for j in range(x_field.shape[0]):
            nd = c_len
            c0 = c_field[c_len-2]
            c1 = c_field[c_len-1]
            for i in range(3, c_len + 1):
                tmp = c0
                nd = nd - 1
                c0 = c_field[c_len-i] - (c1*(nd - 1))/nd
                c1 = tmp + (c1*((2*nd - 1) - x_field[j]))/nd
            x_field[j] = c0 + c1*(1 - x_field[j])

    return x_field


@func
def hermval(x_field: template(), c_field: template()):
    """
    Evaluate an Hermite series in-place on a 1D Taichi array.

    For coefficients ``c_field`` of length ``n + 1``, this computes

    .. math::
        p(x) = \\sum_{k=0}^{n} c_k H_k(x)

    for every element in ``x_field`` and writes the result back into
    ``x_field``.

    This function is intended to be called inside a Taichi kernel,
    much like other math functions in Taichi's math module.
    The evaluation uses Clenshaw recursion, and closely 
    follows the numpy hermval implementation.

    Parameters
    ----------
    x_field : template
        1D mutable container (for example ``ti.ndarray`` or templated field)
        containing the input ``x`` values. Updated in-place.
    c_field : template
        1D coefficient container where ``c_field[k]`` is the coefficient
        of :math:`H_k(x)`.

    Returns
    -------
    template
        The same container as ``x_field`` after in-place update.

    """
    c_len = c_field.shape[0]
    if c_len == 1:
        for j in range(x_field.shape[0]):
            x_field[j] = c_field[0]
    elif c_len == 2:
        for j in range(x_field.shape[0]):
            x_field[j] = c_field[0] + c_field[1]*x_field[j]*2
    else:
        for j in range(x_field.shape[0]):
            nd = c_len
            c0 = c_field[c_len-2]
            c1 = c_field[c_len-1]
            for i in range(3, c_len + 1):
                tmp = c0
                nd = nd - 1
                c0 = c_field[c_len-i] - c1*(2*(nd - 1))
                c1 = tmp + c1*x_field[j]*2
            x_field[j] = c0 + c1*x_field[j]*2
    return x_field


@func
def chebval(x_field: template(), c_field: template()):
    """
    Evaluate a Chebyshev series in-place on a 1D Taichi array.

    For coefficients ``c_field`` of length ``n + 1``, this computes

    .. math:: p(x) = \\sum_{k=0}^{n} c_k T_k(x)

    for every element in ``x_field`` and writes the result back into
    ``x_field``.

    This function is intended to be called inside a Taichi kernel,
    much like other math functions in Taichi's math module.
    The evaluation uses Clenshaw recursion, and closely 
    follows the numpy chebval implementation.

    Parameters
    ----------
    x_field : template
        1D mutable container (for example ``ti.ndarray`` or templated field)
        containing the input ``x`` values. Updated in-place.
    c_field : template
        1D coefficient container where ``c_field[k]`` is the coefficient
        of :math:`T_k(x)`.

    Returns
    -------
    template
        The same container as ``x_field`` after in-place update.

    """
    c_len = c_field.shape[0]

    if c_len == 1:
        for j in range(x_field.shape[0]):
            x_field[j] = c_field[0]
    elif c_len == 2:
        for j in range(x_field.shape[0]):
            x_field[j] = c_field[0] + c_field[1]*x_field[j]
    else:
        for j in range(x_field.shape[0]):
            c0 = c_field[c_len-2]
            c1 = c_field[c_len-1]
            for i in range(3, c_len + 1):
                tmp = c0
                c0 = c_field[c_len-i] - c1
                c1 = tmp + c1*2*x_field[j]
            x_field[j] = c0 + c1*x_field[j]
    return x_field


@func
def legval(x_field: template(), c_field: template()):
    """
    Evaluate a Legendre series in-place on a 1D Taichi array.

    For coefficients ``c_field`` of length ``n + 1``, this computes

    .. math:: p(x) = \\sum_{k=0}^{n} c_k P_k(x)

    for every element in ``x_field`` and writes the result back into
    ``x_field``.

    This function is intended to be called inside a Taichi kernel,
    much like other math functions in Taichi's math module.
    The evaluation uses Clenshaw recursion, and closely 
    follows the numpy legval implementation.

    Parameters
    ----------
    x_field : template
        1D mutable container (for example ``ti.ndarray`` or templated field)
        containing the input ``x`` values. Updated in-place.
    c_field : template
        1D coefficient container where ``c_field[k]`` is the coefficient
        of :math:`P_k(x)`.

    Returns
    -------
    template
        The same container as ``x_field`` after in-place update.

    """
    c_len = c_field.shape[0]

    if c_len == 1:
        for j in range(x_field.shape[0]):
            x_field[j] = c_field[0]
    elif c_len == 2:
        for j in range(x_field.shape[0]):
            x_field[j] = c_field[0] + c_field[1]*x_field[j]
    else:
        for j in range(x_field.shape[0]):
            nd = c_len
            c0 = c_field[c_len-2]
            c1 = c_field[c_len-1]
            for i in range(3, c_len + 1):
                tmp = c0
                nd = nd - 1
                c0 = c_field[c_len-i] - (c1*(nd - 1))/nd
                c1 = tmp + (c1*x_field[j]*(2*nd - 1))/nd
            x_field[j] = c0 + c1*x_field[j]

    return x_field


@func
def polyval(x_field: template(), c_field: template()):
    """
    Evaluate a power series in-place on a 1D Taichi array.

    For coefficients ``c_field`` of length ``n + 1``, this computes

    .. math:: p(x) = \\sum_{k=0}^{n} c_k x^k

    for every element in ``x_field`` and writes the result back into
    ``x_field``.

    This function is intended to be called inside a Taichi kernel,
    much like other math functions in Taichi's math module.
    The evaluation uses Horner's method, and closely 
    follows the numpy polyval implementation.

    Parameters
    ----------
    x_field : template
        1D mutable container (for example ``ti.ndarray`` or templated field)
        containing the input ``x`` values. Updated in-place.
    c_field : template
        1D coefficient container where ``c_field[k]`` is the coefficient
        of :math:`x^k`.

    Returns
    -------
    template
        The same container as ``x_field`` after in-place update.

    """

    c_len = c_field.shape[0]

    for j in range(x_field.shape[0]):
        c0 = c_field[c_len-1]
        for i in range(2, c_len + 1):
            c0 = c_field[c_len-i] + c0*x_field[j]
        x_field[j] = c0
    
    return x_field


@func
def fourierval(x_field: template(), c_field: template()):
    """
    Evaluate a Fourier series in-place on a 1D Taichi array.

    Coefficients are interpreted in the order:
    ``[c0, cos(1*x), sin(1*x), cos(2*x), sin(2*x), ...]``.
    For every element in ``x_field``, this computes the Fourier series value
    and writes it back into ``x_field``.

    Parameters
    ----------
    x_field : template
        1D mutable container (for example ``ti.ndarray`` or templated field)
        containing the input ``x`` values. Updated in-place.
    c_field : template
        1D coefficient container in interleaved cosine/sine order.

    Returns
    -------
    template
        The same container as ``x_field`` after in-place update.
    """
    
    c_len = c_field.shape[0]

    if c_len == 1:
        for j in range(x_field.shape[0]):
            x_field[j] = 0.5 * c_field[0]
    else:
        k_max = c_len // 2
        for j in range(x_field.shape[0]):
            cx = cos(x_field[j])
            sx = sin(x_field[j])

            bc1 = 0.0
            bc2 = 0.0
            bs1 = 0.0
            bs2 = 0.0

            for k in range(k_max):
                ia = 2 * (k_max-k)

                ak = c_field[ia-1] if (ia - 1) < c_len else 0.0
                bk = c_field[ia] if ia < c_len else 0.0

                bc0 = ak + 2.0 * cx * bc1 - bc2
                bs0 = bk + 2.0 * cx * bs1 - bs2

                bc2 = bc1
                bc1 = bc0
                bs2 = bs1
                bs1 = bs0

            x_field[j] = 0.5 * c_field[0] + (bc1 * cx - bc2) + bs1 * sx

    return x_field


__all__ = ["lagval", "hermval", "chebval", "legval", "polyval", "fourierval"]
