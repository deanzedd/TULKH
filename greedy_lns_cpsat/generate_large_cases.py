"""
Generate large test cases for comparing Greedy, LNS, and CP-SAT.

Run:
  python .\TULKH\greedy_lns_cpsat\generate_large_cases.py

Output folder:
  greedy_lns_cpsat/cases/
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

try:
    from .lns_solver import generate_test_case, write_case
except ImportError:
    from lns_solver import generate_test_case, write_case


LARGE_CASES = [
    # filename, N, M, b, density, seed
    ("case_06_xlarge.txt", 200, 50, 3, 0.10, 42),
    ("case_07_xxlarge.txt", 500, 100, 3, 0.08, 99),
    ("case_08_huge.txt", 1000, 200, 3, 0.06, 123),
]


def main():
    output_dir = Path(__file__).resolve().parent / "cases"
    output_dir.mkdir(parents=True, exist_ok=True)

    for filename, N, M, b, density, seed in LARGE_CASES:
        print(f"Generating {filename}: N={N}, M={M}, b={b}, density={density}")
        L = generate_test_case(
            N,
            M,
            b,
            density=density,
            seed=seed,
            min_extra_choice=1,
        )
        path = output_dir / filename
        write_case(path, N, M, b, L)
        print(f"  ✓ wrote {path}")
        print(f"  File size: {path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
