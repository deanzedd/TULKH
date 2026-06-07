"""
Generate fixed test cases for comparing Greedy, LNS, and CP-SAT.

Run:
  python .\TULKH\greedy_lns_cpsat\generate_comparison_cases.py

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


CASES = [
    # filename, N, M, b, density, seed
    ("case_01_small.txt", 30, 10, 2, 0.10, 5),
    ("case_02_medium.txt", 50, 15, 2, 0.10, 18),
    ("case_03_medium_b3.txt", 60, 15, 3, 0.15, 53),
    ("case_04_harder.txt", 60, 15, 3, 0.10, 21),
    ("case_05_large.txt", 100, 25, 3, 0.10, 37),
    # Larger cases to show LNS advantage
    ("case_06_xlarge.txt", 200, 50, 3, 0.08, 71),
    ("case_07_xxlarge.txt", 500, 100, 3, 0.06, 89),
    ("case_08_huge.txt", 1000, 200, 3, 0.05, 101),
    ("case_09_massive.txt", 1500, 250, 3, 0.04, 113),
    ("case_10_extreme.txt", 2000, 300, 3, 0.03, 127),
]


def main():
    output_dir = Path(__file__).resolve().parent / "cases"
    output_dir.mkdir(parents=True, exist_ok=True)

    for filename, N, M, b, density, seed in CASES:
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
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
