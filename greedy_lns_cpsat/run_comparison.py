"""
========================================================================
 RUN COMPARISON - Greedy vs LNS vs Google OR-Tools CP-SAT
========================================================================

File rieng de chay va in bang so sanh cho bai toan Balanced Paper
Assignment.

Cach chay:
  python .\TULKH\greedy_lns_cpsat\run_comparison.py input.txt
  python .\TULKH\greedy_lns_cpsat\run_comparison.py --benchmark
  python .\TULKH\greedy_lns_cpsat\run_comparison.py input.txt --lns-time-limit 3 --cpsat-time-limit 5

Bang ket qua gom:
  - MaxLoad: tai lon nhat cua reviewer.
  - ΔCP   : MaxLoad - MaxLoad(CP-SAT). So duong nghia la kem CP-SAT.
  - GainGreedy: Greedy MaxLoad - MaxLoad. So duong nghia la tot hon Greedy.
  - GapLB  : khoang cach so voi lower bound ceil(N*b/M).
  - Time(s), Mem(KB): thoi gian va bo nho peak do bang tracemalloc.
========================================================================
"""

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

try:
    from .lns_solver import (
        generate_test_case,
        lns_solve,
        lower_bound,
        parse_input,
        timed_call,
        validate_assignment,
    )
    from .excel_export import write_comparison_excel
except ImportError:
    from lns_solver import (
        generate_test_case,
        lns_solve,
        lower_bound,
        parse_input,
        timed_call,
        validate_assignment,
    )
    from excel_export import write_comparison_excel

from greedy_solver import greedy_assign
from local_search_solver import local_search_solve

try:
    from exact_ORTOOLS import exact_GG_ORTOI

    EXACT_ORTOOLS_AVAILABLE = True
    EXACT_ORTOOLS_IMPORT_ERROR = ""
except ImportError as exc:
    exact_GG_ORTOI = None
    EXACT_ORTOOLS_AVAILABLE = False
    EXACT_ORTOOLS_IMPORT_ERROR = str(exc)


def load_sample_cases():
    cases = []
    sample_path = (
        Path(__file__).resolve().parents[1]
        / "local_search"
        / "sa_vs_hc_case_sample.txt"
    )
    if sample_path.exists():
        N, M, b, L = parse_input(sample_path)
        cases.append(("Mau local-search", N, M, b, L, 2.0, 2.0))
    return cases


def default_benchmark_cases():
    cases = load_sample_cases()

    specs = [
        # name, N, M, b, density, seed, lns_time, cpsat_time
        ("Nho ngau nhien", 20, 10, 3, 0.35, 42, 2.0, 2.0),
        ("Vua thua", 100, 30, 3, 0.22, 123, 3.0, 3.0),
        ("Vua day", 200, 50, 3, 0.35, 456, 4.0, 4.0),
        ("Lon", 500, 100, 3, 0.16, 789, 6.0, 5.0),
        ("Stress", 1000, 200, 4, 0.10, 2024, 8.0, 5.0),
    ]

    for name, N, M, b, density, seed, lns_time, cpsat_time in specs:
        L = generate_test_case(N, M, b, density=density, seed=seed)
        cases.append((name, N, M, b, L, lns_time, cpsat_time))

    return cases


def run_greedy_measured(N, M, b, L):
    (assignment, max_load, loads, feasible), elapsed, peak_kb = timed_call(
        greedy_assign, N, M, b, L
    )
    status = "OK" if feasible else "INFEASIBLE_INPUT"
    return {
        "solver": "Greedy",
        "status": status,
        "assignment": assignment,
        "max_load": max_load,
        "loads": loads,
        "time_seconds": elapsed,
        "peak_memory_kb": peak_kb,
        "extra": {},
    }


def run_lns_measured(N, M, b, L, seed=42, time_limit_sec=None, max_iterations=None):
    (
        assignment,
        max_load,
        loads,
        stats,
    ), elapsed, peak_kb = timed_call(
        lns_solve,
        N,
        M,
        b,
        L,
        seed=seed,
        time_limit_sec=time_limit_sec,
        max_iterations=max_iterations,
    )

    return {
        "solver": "LNS",
        "status": stats.get("status", "OK"),
        "assignment": assignment,
        "max_load": max_load,
        "loads": loads,
        "time_seconds": elapsed,
        "peak_memory_kb": peak_kb,
        "extra": stats,
    }


def choose_local_search_iterations(N):
    if N <= 50:
        return 5000
    if N <= 300:
        return 10000
    if N <= 1000:
        return 15000
    return 20000


def run_local_search_measured(N, M, b, L, seed=42, max_iterations=None):
    if max_iterations is None:
        max_iterations = choose_local_search_iterations(N)

    (
        assignment,
        max_load,
        loads,
        history,
    ), elapsed, peak_kb = timed_call(
        local_search_solve,
        N,
        M,
        b,
        L,
        max_iterations=max_iterations,
        initial_temp=max(10.0, N * 0.1),
        cooling_rate=0.997,
        tabu_tenure=min(50, N),
        lns_frequency=max(20, max_iterations // 50),
        destroy_ratio=min(0.3, 10.0 / max(1, N)),
        seed=seed,
    )

    return {
        "solver": "LocalSearch",
        "status": "OK",
        "assignment": assignment,
        "max_load": max_load,
        "loads": loads,
        "time_seconds": elapsed,
        "peak_memory_kb": peak_kb,
        "extra": {
            "source": "local_search_solver.local_search_solve",
            "max_iterations": max_iterations,
            "accepted": history.get("accepted", 0),
            "rejected": history.get("rejected", 0),
            "improved": history.get("improved", 0),
        },
    }


def run_cpsat_measured(N, M, b, L, time_limit_sec=10.0, workers=4):
    def solve_with_exact_ortools():
        if not EXACT_ORTOOLS_AVAILABLE:
            return (
                None,
                -1,
                [0] * M,
                f"exact_ORTOOLS_IMPORT_ERROR: {EXACT_ORTOOLS_IMPORT_ERROR}",
            )

        assignment, max_load, loads, status = exact_GG_ORTOI(
            N, M, b, L, time_limit_sec=time_limit_sec
        )
        if assignment is None:
            return None, -1, [0] * M, status
        return assignment, max_load, loads, status

    (
        assignment,
        max_load,
        loads,
        status,
    ), elapsed, peak_kb = timed_call(solve_with_exact_ortools)

    return {
        "solver": "CP-SAT",
        "status": status,
        "assignment": assignment,
        "max_load": max_load,
        "loads": loads,
        "time_seconds": elapsed,
        "peak_memory_kb": peak_kb,
        "extra": {
            "source": "exact_ORTOOLS.exact_GG_ORTOI",
            "time_limit_sec": time_limit_sec,
            "workers_note": "exact_ORTOOLS.py uses 4 workers internally",
            "requested_workers": workers,
        },
    }


def result_row(result, lb, greedy_max=None, cpsat_max=None):
    max_load = result["max_load"]

    if max_load >= 0 and lb > 0:
        lb_gap = (max_load - lb) / lb * 100
        lb_gap_text = f"{lb_gap:6.2f}%"
    else:
        lb_gap_text = "   N/A "

    if max_load >= 0 and cpsat_max and cpsat_max > 0:
        delta_cp_text = f"{max_load - cpsat_max:+5d}"
    else:
        delta_cp_text = "  N/A"

    if greedy_max and greedy_max > 0 and max_load >= 0:
        gain_text = f"{greedy_max - max_load:+5d}"
    else:
        gain_text = "  N/A"

    return (
        f"{result['solver']:<12} "
        f"{result['status']:<18} "
        f"{max_load:>7} "
        f"{delta_cp_text:>7} "
        f"{gain_text:>11} "
        f"{lb_gap_text:>9} "
        f"{result['time_seconds']:>9.4f} "
        f"{result['peak_memory_kb']:>10.1f}"
    )


def print_comparison_table(case_name, N, M, b, results):
    lb = lower_bound(N, M, b)
    greedy_result = next((r for r in results if r["solver"] == "Greedy"), None)
    cpsat_result = next((r for r in results if r["solver"] == "CP-SAT"), None)

    greedy_max = greedy_result["max_load"] if greedy_result else None
    cpsat_max = (
        cpsat_result["max_load"]
        if cpsat_result and cpsat_result["max_load"] >= 0
        else None
    )

    print("\n" + "=" * 112)
    print(f"TEST: {case_name} | N={N}, M={M}, b={b}, LB={lb}")
    print("=" * 112)
    print(
        f"{'Solver':<12} {'Status':<18} {'MaxLoad':>7} "
        f"{'ΔCP':>7} {'GainGreedy':>11} {'GapLB':>9} "
        f"{'Time(s)':>9} {'Mem(KB)':>10}"
    )
    print("-" * 112)

    for result in results:
        print(result_row(result, lb, greedy_max=greedy_max, cpsat_max=cpsat_max))

    lns_result = next((r for r in results if r["solver"] == "LNS"), None)
    local_result = next((r for r in results if r["solver"] == "LocalSearch"), None)
    if greedy_result and lns_result and greedy_result["max_load"] >= 0:
        improvement = greedy_result["max_load"] - lns_result["max_load"]
        pct = improvement / greedy_result["max_load"] * 100 if greedy_result["max_load"] > 0 else 0
        print(
            f"\nNhan xet nhanh: LNS {'cai thien' if improvement > 0 else 'khong cai thien'} "
            f"so voi Greedy {improvement:+d} max_load ({pct:+.2f}%)."
        )

    if greedy_result and local_result and greedy_result["max_load"] >= 0:
        improvement = greedy_result["max_load"] - local_result["max_load"]
        pct = improvement / greedy_result["max_load"] * 100 if greedy_result["max_load"] > 0 else 0
        print(
            f"LocalSearch {'cai thien' if improvement > 0 else 'khong cai thien'} "
            f"so voi Greedy {improvement:+d} max_load ({pct:+.2f}%)."
        )

    if cpsat_result and lns_result and local_result and cpsat_result["max_load"] >= 0:
        lns_gap = lns_result["max_load"] - cpsat_result["max_load"]
        local_gap = local_result["max_load"] - cpsat_result["max_load"]
        greedy_gap = greedy_result["max_load"] - cpsat_result["max_load"]
        print(
            f"Chenh lech voi CP-SAT: Greedy {greedy_gap:+d}, "
            f"LNS {lns_gap:+d}, LocalSearch {local_gap:+d} max_load."
        )
        print(
            "Thoi gian: "
            f"Greedy={greedy_result['time_seconds']:.4f}s, "
            f"LNS={lns_result['time_seconds']:.4f}s, "
            f"LocalSearch={local_result['time_seconds']:.4f}s, "
            f"CP-SAT={cpsat_result['time_seconds']:.4f}s "
            "(CP-SAT lay tu exact_ORTOOLS.py)."
        )

    if cpsat_result and cpsat_result["status"] != "OPTIMAL":
        if cpsat_result["status"].startswith("exact_ORTOOLS_IMPORT_ERROR"):
            print("CP-SAT chua chay duoc qua exact_ORTOOLS.py. Kiem tra ortools/install path.")
        else:
            print("CP-SAT khong chung minh OPTIMAL trong time limit.")


def run_comparison(
    case_name,
    N,
    M,
    b,
    L,
    seed=42,
    lns_time_limit=None,
    lns_iterations=None,
    local_search_iterations=None,
    cpsat_time_limit=10.0,
    cpsat_workers=4,
    show_table=True,
):
    greedy_result = run_greedy_measured(N, M, b, L)
    lns_result = run_lns_measured(
        N,
        M,
        b,
        L,
        seed=seed,
        time_limit_sec=lns_time_limit,
        max_iterations=lns_iterations,
    )
    local_search_result = run_local_search_measured(
        N,
        M,
        b,
        L,
        seed=seed,
        max_iterations=local_search_iterations,
    )
    cpsat_result = run_cpsat_measured(
        N,
        M,
        b,
        L,
        time_limit_sec=cpsat_time_limit,
        workers=cpsat_workers,
    )

    results = [greedy_result, lns_result, local_search_result, cpsat_result]

    for result in results:
        if result["assignment"] is not None:
            ok, message = validate_assignment(N, b, L, result["assignment"])
            if not ok:
                result["status"] = f"INVALID: {message}"

    if show_table:
        print_comparison_table(case_name, N, M, b, results)

    return {
        "case_name": case_name,
        "N": N,
        "M": M,
        "b": b,
        "lower_bound": lower_bound(N, M, b),
        "results": [
            {
                key: value
                for key, value in result.items()
                if key not in ("assignment", "loads")
            }
            for result in results
        ],
    }


def run_benchmark(args):
    cases = default_benchmark_cases()
    summaries = []

    print("Greedy vs LNS vs Local Search vs Google OR-Tools CP-SAT")
    print("Balanced Paper Assignment")
    print("CP-SAT source: exact_ORTOOLS.exact_GG_ORTOI")
    if not EXACT_ORTOOLS_AVAILABLE:
        print(f"Luu y: khong import duoc exact_ORTOOLS.py: {EXACT_ORTOOLS_IMPORT_ERROR}")

    for case_name, N, M, b, L, lns_time, cpsat_time in cases:
        summary = run_comparison(
            case_name,
            N,
            M,
            b,
            L,
            seed=args.seed,
            lns_time_limit=args.lns_time_limit or lns_time,
            lns_iterations=args.lns_iterations,
            local_search_iterations=args.local_search_iterations,
            cpsat_time_limit=args.cpsat_time_limit or cpsat_time,
            cpsat_workers=args.cpsat_workers,
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

    return summaries


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Run comparison: Greedy vs LNS vs Local Search vs Google OR-Tools CP-SAT."
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        help="File input. Neu bo trong thi chay benchmark mac dinh.",
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Chay bo benchmark mac dinh.",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Giu tuong thich voi lns_solver.py; file nay compare mac dinh neu co input.",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--lns-time-limit", type=float, default=None)
    parser.add_argument("--lns-iterations", type=int, default=None)
    parser.add_argument(
        "--local-search-iterations",
        type=int,
        default=None,
        help="So iteration cho local_search_solver.py. Mac dinh tu chon theo N.",
    )
    parser.add_argument("--cpsat-time-limit", type=float, default=None)
    parser.add_argument("--cpsat-workers", type=int, default=4)
    parser.add_argument(
        "--output-json",
        default=None,
        help="Noi luu ket qua benchmark/compare dang JSON. Mac dinh khong luu.",
    )
    parser.add_argument(
        "--output-excel",
        default=None,
        help="Noi luu ket qua benchmark/compare dang .xlsx. Mac dinh khong luu.",
    )
    return parser


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.benchmark or not args.input_file:
        run_benchmark(args)
        return

    N, M, b, L = parse_input(args.input_file)
    summary = run_comparison(
        Path(args.input_file).name,
        N,
        M,
        b,
        L,
        seed=args.seed,
        lns_time_limit=args.lns_time_limit,
        lns_iterations=args.lns_iterations,
        local_search_iterations=args.local_search_iterations,
        cpsat_time_limit=args.cpsat_time_limit or 10.0,
        cpsat_workers=args.cpsat_workers,
        show_table=True,
    )

    if args.output_json:
        Path(args.output_json).write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\nDa luu ket qua vao {args.output_json}")

    if args.output_excel:
        path = write_comparison_excel(summary, args.output_excel)
        print(f"\nDa luu ket qua Excel vao {path}")


if __name__ == "__main__":
    main()
