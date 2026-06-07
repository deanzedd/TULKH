"""
Generate extremely hard test cases where CP-SAT struggles.
"""

import sys
import random
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

try:
    from .lns_solver import generate_test_case, write_case
except ImportError:
    from lns_solver import generate_test_case, write_case


ULTRA_HARD_CASES = [
    # filename, N, M, b, density, seed - lowers density = more constraints
    ("case_09_hardest.txt", 300, 30, 3, 0.05, 111),     # Rất hạn chế reviewer choices
    ("case_10_ultra.txt", 600, 60, 4, 0.04, 222),        # Lớn hơn, constraints hơn
    ("case_11_extreme.txt", 1200, 100, 4, 0.03, 333),    # Cực khó cho CP-SAT
]


def main():
    output_dir = Path(__file__).resolve().parent / "cases"
    output_dir.mkdir(parents=True, exist_ok=True)

    for filename, N, M, b, density, seed in ULTRA_HARD_CASES:
        print(f"Generating {filename}: N={N}, M={M}, b={b}, density={density} (HIGH CONSTRAINTS)")
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
