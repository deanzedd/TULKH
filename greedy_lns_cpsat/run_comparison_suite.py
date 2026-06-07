"""
Run the curated Greedy-vs-LNS-vs-LocalSearch-vs-CP-SAT comparison suite.

Run from TULKH:
  python greedy_lns_cpsat\run_comparison_suite.py

Run from project root:
  python .\TULKH\greedy_lns_cpsat\run_comparison_suite.py
"""

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

try:
    from .lns_solver import parse_input
    from .run_comparison import run_comparison
    from .excel_export import write_comparison_excel
except ImportError:
    from lns_solver import parse_input
    from run_comparison import run_comparison
    from excel_export import write_comparison_excel


CASE_SETTINGS = [
    ("case_01_small.txt", 1.0, 5.0),
    ("case_02_medium.txt", 1.5, 5.0),
    ("case_03_medium_b3.txt", 2.0, 5.0),
    ("case_04_harder.txt", 3.0, 8.0),
    ("case_05_large.txt", 3.0, 8.0),
    # Larger cases: LNS advantage becomes clear
    ("case_06_xlarge.txt", 4.0, 10.0),
    ("case_07_xxlarge.txt", 5.0, 15.0),
    ("case_08_huge.txt", 7.0, 20.0),
    ("case_09_massive.txt", 10.0, 30.0),
    ("case_10_extreme.txt", 15.0, 60.0),
]


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Run curated test cases comparing Greedy, LNS, Local Search, and CP-SAT."
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--lns-time-scale", type=float, default=1.0)
    parser.add_argument(
        "--local-search-iterations",
        type=int,
        default=None,
        help="So iteration cho local_search_solver.py. Mac dinh tu chon theo N.",
    )
    parser.add_argument("--cpsat-time-scale", type=float, default=1.0)
    parser.add_argument(
        "--cases-dir",
        default=None,
        help="Folder chua cac file case_*.txt. Mac dinh dung greedy_lns_cpsat/cases.",
    )
    parser.add_argument(
        "--output-json",
        default=None,
        help="Noi luu ket qua JSON. Mac dinh chi in bang.",
    )
    parser.add_argument(
        "--output-excel",
        default=None,
        help="Noi luu ket qua .xlsx. Mac dinh chi in bang.",
    )
    return parser


def main():
    args = build_arg_parser().parse_args()
    root_dir = Path(__file__).resolve().parent
    cases_dir = (
        Path(args.cases_dir)
        if args.cases_dir
        else root_dir / "cases"
    )

    summaries = []
    for filename, lns_time, cpsat_time in CASE_SETTINGS:
        path = cases_dir / filename
        N, M, b, L = parse_input(path)
        summary = run_comparison(
            filename,
            N,
            M,
            b,
            L,
            seed=args.seed,
            lns_time_limit=lns_time * args.lns_time_scale,
            local_search_iterations=args.local_search_iterations,
            cpsat_time_limit=cpsat_time * args.cpsat_time_scale,
            show_table=True,
        )
        summaries.append(summary)

    if args.output_json:
        Path(args.output_json).write_text(
            json.dumps(summaries, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\nDa luu ket qua vao {args.output_json}")

    if args.output_excel:
        path = write_comparison_excel(summaries, args.output_excel)
        print(f"\nDa luu ket qua Excel vao {path}")


if __name__ == "__main__":
    main()
