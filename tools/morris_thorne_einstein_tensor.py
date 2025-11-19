"""Symbolic Einstein tensor for the Morris-Thorne wormhole metric."""
from __future__ import annotations

import argparse
from typing import Tuple

import sympy as sp

CoordinateTuple = Tuple[sp.Symbol, ...]


def build_coordinates() -> CoordinateTuple:
    """Create the standard Morris-Thorne coordinate chart (t, r, theta, phi)."""
    t, r, theta, phi = sp.symbols("t r theta phi", real=True)
    return t, r, theta, phi


def resolve_profile(
    profile: sp.Expr | None,
    radius: sp.Symbol,
    *,
    default_name: str,
) -> sp.Expr:
    """Return the symbolic radial profile used inside the metric."""
    if profile is not None:
        return sp.sympify(profile)
    return sp.Function(default_name)(radius)


def morris_thorne_metric(
    redshift_profile: sp.Expr | None = None,
    shape_profile: sp.Expr | None = None,
) -> tuple[sp.Matrix, CoordinateTuple]:
    """Construct the Morris-Thorne metric tensor in Schwarzschild-like coordinates."""
    t, r, theta, phi = build_coordinates()
    redshift = resolve_profile(redshift_profile, r, default_name="Phi")
    shape = resolve_profile(shape_profile, r, default_name="b")

    g_tt = -sp.exp(2 * redshift)
    g_rr = 1 / (1 - shape / r)
    g_thth = r**2
    g_phph = r**2 * sp.sin(theta) ** 2
    metric = sp.diag(g_tt, g_rr, g_thth, g_phph)
    return metric, (t, r, theta, phi)


def christoffel_symbols(metric: sp.Matrix, coords: CoordinateTuple) -> list[list[list[sp.Expr]]]:
    """Compute the Christoffel symbols Γ^λ_{μν}."""
    dim = metric.shape[0]
    g_inv = metric.inv()
    gamma: list[list[list[sp.Expr]]] = [
        [[sp.Integer(0) for _ in range(dim)] for _ in range(dim)] for _ in range(dim)
    ]

    for lam in range(dim):
        for mu in range(dim):
            for nu in range(dim):
                term = sp.Integer(0)
                for sigma in range(dim):
                    term += g_inv[lam, sigma] * (
                        sp.diff(metric[sigma, mu], coords[nu])
                        + sp.diff(metric[sigma, nu], coords[mu])
                        - sp.diff(metric[mu, nu], coords[sigma])
                    )
                gamma[lam][mu][nu] = sp.simplify(sp.Rational(1, 2) * term)
    return gamma


def ricci_tensor(gamma: list[list[list[sp.Expr]]], coords: CoordinateTuple) -> sp.Matrix:
    """Compute the Ricci tensor R_{μν}."""
    dim = len(coords)
    ricci = sp.Matrix.zeros(dim)

    for mu in range(dim):
        for nu in range(dim):
            term = sp.Integer(0)
            for lam in range(dim):
                term += sp.diff(gamma[lam][mu][nu], coords[lam])
                term -= sp.diff(gamma[lam][mu][lam], coords[nu])
                for sigma in range(dim):
                    term += gamma[lam][mu][nu] * gamma[sigma][lam][sigma]
                    term -= gamma[sigma][mu][lam] * gamma[lam][nu][sigma]
            ricci[mu, nu] = sp.simplify(term)
    return ricci


def einstein_tensor(metric: sp.Matrix, coords: CoordinateTuple) -> sp.Matrix:
    """Return the Einstein tensor G_{μν} = R_{μν} - 1/2 g_{μν} R."""
    gamma = christoffel_symbols(metric, coords)
    ricci = ricci_tensor(gamma, coords)
    g_inv = metric.inv()
    scalar_curvature = sp.simplify(
        sum(g_inv[i, j] * ricci[i, j] for i in range(metric.shape[0]) for j in range(metric.shape[1]))
    )
    einstein = sp.Matrix.zeros(metric.shape[0])
    for mu in range(metric.shape[0]):
        for nu in range(metric.shape[1]):
            einstein[mu, nu] = sp.simplify(ricci[mu, nu] - sp.Rational(1, 2) * metric[mu, nu] * scalar_curvature)
    return einstein


def select_redshift(profile: str, radius: sp.Symbol) -> sp.Expr | None:
    """Map a CLI-friendly redshift profile name to a symbolic expression."""
    if profile == "zero":
        return sp.Integer(0)
    return None


def select_shape(profile: str, radius: sp.Symbol, throat_radius: float | None) -> sp.Expr | None:
    """Map a CLI-friendly shape function profile to an expression."""
    if profile == "ellis":
        if throat_radius is None:
            r0 = sp.symbols("r0", positive=True)
        else:
            r0 = sp.nsimplify(throat_radius)
        return r0**2 / radius
    return None


def pretty_print_tensor(tensor: sp.Matrix, coords: CoordinateTuple, label: str) -> None:
    """Display each non-zero component of the tensor."""
    print(f"\n{label} components:")
    for mu, coord_mu in enumerate(coords):
        for nu, coord_nu in enumerate(coords):
            component = sp.simplify(tensor[mu, nu])
            if component == 0:
                continue
            print(f"  {label}_{{{coord_mu}{coord_nu}}} = {component}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Compute the Einstein tensor for the Morris-Thorne wormhole metric. "
            "By default the computation keeps Φ(r) and b(r) symbolic."
        )
    )
    parser.add_argument(
        "--redshift",
        choices=["generic", "zero"],
        default="generic",
        help="Select a redshift function profile (Φ).",
    )
    parser.add_argument(
        "--shape",
        choices=["generic", "ellis"],
        default="generic",
        help="Select a wormhole shape function profile (b).",
    )
    parser.add_argument(
        "--throat-radius",
        type=float,
        default=None,
        help="Optional numeric throat radius r0 used for the Ellis profile.",
    )
    args = parser.parse_args()

    t, r, theta, phi = build_coordinates()
    redshift_expr = select_redshift(args.redshift, r)
    shape_expr = select_shape(args.shape, r, args.throat_radius)

    metric, coords = morris_thorne_metric(redshift_expr, shape_expr)
    tensor = einstein_tensor(metric, coords)

    print("Morris-Thorne wormhole metric g_{μν}:")
    sp.pprint(metric)
    pretty_print_tensor(tensor, coords, "G")


if __name__ == "__main__":
    main()
