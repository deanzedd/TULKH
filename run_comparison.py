"""
========================================================================
 RUN COMPARISON - Greedy vs Hill Climbing vs LNS vs Google OR-Tools CP-SAT
========================================================================

Chay so sanh 4 thuat toan cho bai toan Balanced Paper Assignment.

Cach chay:
  python run_comparison.py testcase.txt
  python run_comparison.py --benchmark
  python run_comparison.py testcase.txt --hc-time-limit 2 --lns-time-limit 3 --cpsat-time-limit 5

File input co the chua mot testcase hoac nhieu testcase ngan cach boi
comment dang "# Test 01: ...".
========================================================================
"""

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from greedy_solver import greedy_assign

try:
    from greedy_lns_cpsat.lns_solver import (
        generate_test_case,
        lns_solve,
        lower_bound,
        timed_call,
        validate_assignment,
    )
except ModuleNotFoundError:
    from lns.lns_solver import (
        generate_test_case,
        lns_solve,
        lower_bound,
        timed_call,
        validate_assignment,
    )

try:
    from greedy_lns_cpsat.excel_export import write_comparison_excel
except ModuleNotFoundError:
    try:
        from lns.excel_export import write_comparison_excel
    except ImportError as exc:
        write_comparison_excel = None
        EXCEL_EXPORT_AVAILABLE = False
        EXCEL_EXPORT_IMPORT_ERROR = str(exc)
    else:
        EXCEL_EXPORT_AVAILABLE = True
        EXCEL_EXPORT_IMPORT_ERROR = ""
except ImportError as exc:
    write_comparison_excel = None
    EXCEL_EXPORT_AVAILABLE = False
    EXCEL_EXPORT_IMPORT_ERROR = str(exc)
else:
    EXCEL_EXPORT_AVAILABLE = True
    EXCEL_EXPORT_IMPORT_ERROR = ""

try:
    from local_search.Hill_climbing import hill_climbing_with_loads

    HILL_CLIMBING_AVAILABLE = True
    HILL_CLIMBING_IMPORT_ERROR = ""
except ImportError as exc:
    hill_climbing_with_loads = None
    HILL_CLIMBING_AVAILABLE = False
    HILL_CLIMBING_IMPORT_ERROR = str(exc)

try:
    from exact_ORTOOLS import exact_GG_ORTOI

    EXACT_ORTOOLS_AVAILABLE = True
    EXACT_ORTOOLS_IMPORT_ERROR = ""
except ImportError as exc:
    exact_GG_ORTOI = None
    EXACT_ORTOOLS_AVAILABLE = False
    EXACT_ORTOOLS_IMPORT_ERROR = str(exc)


def parse_input_cases(source):
    """
    Doc mot hoac nhieu testcase tu file txt.

    Ho tro:
      1. Mot testcase:
           N M b
           k r1 r2 ...
      2. Nhieu testcase:
           # Test 01: Ten test
           N M b
           k r1 r2 ...

    Tra ve list tuple: (case_name, N, M, b, L).
    Reviewer trong L duoc chuyen tu 1-indexed sang 0-indexed.
    """
    path = Path(source)
    raw_lines = path.read_text(encoding="utf-8").splitlines()
    cases = []
    pending_name = None
    index = 0

    def clean_data_line(line):
        return line.split("#", 1)[0].strip()

    def is_case_marker(line):
        return line.lower().startswith("test-case")

    while index < len(raw_lines):
        original_line = raw_lines[index].strip()
        data_line = clean_data_line(raw_lines[index])

        if is_case_marker(original_line):
            pending_name = original_line.rstrip(":")
            index += 1
            continue

        if not data_line:
            if original_line.startswith("#"):
                label = original_line.lstrip("#").strip()
                if label:
                    pending_name = label
            index += 1
            continue

        header = data_line.split()
        if len(header) != 3:
            raise ValueError(
                f"Dong {index + 1}: header testcase phai co dang 'N M b', gap: {data_line}"
            )

        N, M, b = map(int, header)
        L = []
        index += 1

        for paper_idx in range(N):
            while index < len(raw_lines) and not clean_data_line(raw_lines[index]):
                index += 1

            if index >= len(raw_lines):
                raise ValueError(
                    f"Testcase {len(cases) + 1} thieu dong paper: can {N}, moi co {paper_idx}."
                )

            parts = list(map(int, clean_data_line(raw_lines[index]).split()))
            k = parts[0]
            reviewers = [r - 1 for r in parts[1 : k + 1]]
            if len(reviewers) != k:
                raise ValueError(
                    f"Dong {index + 1}: khai bao k={k} nhung chi co {len(reviewers)} reviewer."
                )
            L.append(reviewers)
            index += 1

        case_name = pending_name or path.name
        if len(cases) > 0 and case_name == path.name:
            case_name = f"{path.name} #{len(cases) + 1}"
        cases.append((case_name, N, M, b, L))
        pending_name = None

    if not cases:
        raise ValueError("Input rong.")

    return cases


def parse_output_cases(source):
    """
    Doc mot hoac nhieu output theo format:
      Test-case 1:
      N
      b r1 r2 ...
      ...

    Tra ve list tuple: (case_name, assignment).
    Reviewer duoc chuyen tu 1-indexed sang 0-indexed.
    """
    path = Path(source)
    raw_lines = path.read_text(encoding="utf-8").splitlines()
    cases = []
    pending_name = None
    index = 0

    def clean_data_line(line):
        return line.split("#", 1)[0].strip()

    def is_case_marker(line):
        return line.strip().lower().startswith("test-case")

    while index < len(raw_lines):
        original_line = raw_lines[index].strip()
        data_line = clean_data_line(raw_lines[index])

        if is_case_marker(original_line):
            pending_name = original_line.rstrip(":")
            index += 1
            continue

        if not data_line:
            index += 1
            continue

        parts = data_line.split()
        if len(parts) != 1:
            raise ValueError(
                f"Dong {index + 1}: header output phai la mot so N, gap: {data_line}"
            )

        N = int(parts[0])
        assignment = []
        index += 1

        for paper_idx in range(N):
            while index < len(raw_lines) and not clean_data_line(raw_lines[index]):
                index += 1

            if index >= len(raw_lines):
                raise ValueError(
                    f"Output testcase {len(cases) + 1} thieu dong paper: can {N}, moi co {paper_idx}."
                )

            row = list(map(int, clean_data_line(raw_lines[index]).split()))
            k = row[0]
            reviewers = [r - 1 for r in row[1 : k + 1]]
            if len(reviewers) != k:
                raise ValueError(
                    f"Dong {index + 1}: khai bao k={k} nhung chi co {len(reviewers)} reviewer."
                )
            assignment.append(reviewers)
            index += 1

        case_name = pending_name or path.name
        if len(cases) > 0 and case_name == path.name:
            case_name = f"{path.name} #{len(cases) + 1}"
        cases.append((case_name, assignment))
        pending_name = None

    if not cases:
        raise ValueError("Output rong.")

    return cases


def compute_loads_from_assignment(assignment, M):
    loads = [0] * M
    for reviewers in assignment:
        for reviewer in reviewers:
            if 0 <= reviewer < M:
                loads[reviewer] += 1
    return loads


def build_reference_result(N, M, b, L, assignment, solver_name="HUSTack"):
    loads = compute_loads_from_assignment(assignment, M)
    max_load = max(loads) if loads else 0
    ok, message = validate_assignment(N, b, L, assignment)
    return {
        "solver": solver_name,
        "status": "OK" if ok else f"INVALID: {message}",
        "assignment": assignment,
        "max_load": max_load,
        "loads": loads,
        "time_seconds": 0.0,
        "peak_memory_kb": 0.0,
        "extra": {
            "source": "reference output",
        },
    }


def default_benchmark_cases():
    cases = []
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
    return {
        "solver": "Greedy",
        "status": "OK" if feasible else "INFEASIBLE_INPUT",
        "assignment": assignment,
        "max_load": max_load,
        "loads": loads,
        "time_seconds": elapsed,
        "peak_memory_kb": peak_kb,
        "extra": {},
    }


def run_hill_climbing_measured(
    N,
    M,
    b,
    L,
    seed=42,
    time_limit_sec=5.0,
    max_iterations=100_000,
):
    def solve_with_hill_climbing():
        if not HILL_CLIMBING_AVAILABLE:
            return (
                None,
                -1,
                [0] * M,
                {
                    "status": f"HILL_CLIMBING_IMPORT_ERROR: {HILL_CLIMBING_IMPORT_ERROR}",
                    "source": "local_search/Hill_climbing.py",
                },
            )

        assignment, max_load, loads, stats = hill_climbing_with_loads(
            N,
            M,
            b,
            L,
            max_iterations=max_iterations,
            seed=seed,
            time_limit_sec=time_limit_sec,
        )
        stats = dict(stats)
        stats["status"] = "OK"
        stats["source"] = "local_search/Hill_climbing.py"
        stats["time_limit_sec"] = time_limit_sec
        stats["max_iterations"] = max_iterations
        return assignment, max_load, loads, stats

    (
        assignment,
        max_load,
        loads,
        stats,
    ), elapsed, peak_kb = timed_call(solve_with_hill_climbing)

    return {
        "solver": "HillClimb",
        "status": stats.get("status", "OK"),
        "assignment": assignment,
        "max_load": max_load,
        "loads": loads,
        "time_seconds": elapsed,
        "peak_memory_kb": peak_kb,
        "extra": stats,
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
        f"{result['solver']:<10} "
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
    hc_result = next((r for r in results if r["solver"] == "HillClimb"), None)
    lns_result = next((r for r in results if r["solver"] == "LNS"), None)
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
        f"{'Solver':<10} {'Status':<18} {'MaxLoad':>7} "
        f"{'DeltaCP':>7} {'GainGreedy':>11} {'GapLB':>9} "
        f"{'Time(s)':>9} {'Mem(KB)':>10}"
    )
    print("-" * 112)

    for result in results:
        print(result_row(result, lb, greedy_max=greedy_max, cpsat_max=cpsat_max))

    if greedy_result and hc_result and greedy_result["max_load"] >= 0:
        improvement = greedy_result["max_load"] - hc_result["max_load"]
        pct = improvement / greedy_result["max_load"] * 100 if greedy_result["max_load"] > 0 else 0
        print(
            f"\nNhan xet nhanh: Hill Climbing {'cai thien' if improvement > 0 else 'khong cai thien'} "
            f"so voi Greedy {improvement:+d} max_load ({pct:+.2f}%)."
        )

    if greedy_result and lns_result and greedy_result["max_load"] >= 0:
        improvement = greedy_result["max_load"] - lns_result["max_load"]
        pct = improvement / greedy_result["max_load"] * 100 if greedy_result["max_load"] > 0 else 0
        print(
            f"Nhan xet nhanh: LNS {'cai thien' if improvement > 0 else 'khong cai thien'} "
            f"so voi Greedy {improvement:+d} max_load ({pct:+.2f}%)."
        )

    if cpsat_result and lns_result and cpsat_result["max_load"] >= 0:
        greedy_gap = greedy_result["max_load"] - cpsat_result["max_load"]
        hc_gap = (
            hc_result["max_load"] - cpsat_result["max_load"]
            if hc_result and hc_result["max_load"] >= 0
            else None
        )
        lns_gap = lns_result["max_load"] - cpsat_result["max_load"]
        hc_gap_text = f", HillClimb {hc_gap:+d}" if hc_gap is not None else ""
        print(
            f"Chenh lech voi CP-SAT: Greedy {greedy_gap:+d}, "
            f"LNS {lns_gap:+d}{hc_gap_text} max_load."
        )
        hc_time_text = (
            f"HillClimb={hc_result['time_seconds']:.4f}s, "
            if hc_result
            else ""
        )
        print(
            "Thoi gian: "
            f"Greedy={greedy_result['time_seconds']:.4f}s, "
            f"{hc_time_text}"
            f"LNS={lns_result['time_seconds']:.4f}s, "
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
    hc_time_limit=None,
    hc_iterations=None,
    lns_time_limit=None,
    lns_iterations=None,
    cpsat_time_limit=10.0,
    cpsat_workers=4,
    reference_assignment=None,
    reference_name="HUSTack",
    show_table=True,
):
    results = []
    if reference_assignment is not None:
        results.append(
            build_reference_result(
                N,
                M,
                b,
                L,
                reference_assignment,
                solver_name=reference_name,
            )
        )

    greedy_result = run_greedy_measured(N, M, b, L)
    hill_climbing_result = run_hill_climbing_measured(
        N,
        M,
        b,
        L,
        seed=seed,
        time_limit_sec=hc_time_limit if hc_time_limit is not None else 5.0,
        max_iterations=hc_iterations if hc_iterations is not None else 100_000,
    )
    lns_result = run_lns_measured(
        N,
        M,
        b,
        L,
        seed=seed,
        time_limit_sec=lns_time_limit,
        max_iterations=lns_iterations,
    )
    cpsat_result = run_cpsat_measured(
        N,
        M,
        b,
        L,
        time_limit_sec=cpsat_time_limit,
        workers=cpsat_workers,
    )

    results.extend([greedy_result, hill_climbing_result, lns_result, cpsat_result])

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

    print("Greedy vs Hill Climbing vs LNS vs Google OR-Tools CP-SAT")
    print("Balanced Paper Assignment")
    print("Hill Climbing source: local_search/Hill_climbing.py")
    print("CP-SAT source: exact_ORTOOLS.exact_GG_ORTOI")
    if not HILL_CLIMBING_AVAILABLE:
        print(f"Luu y: khong import duoc Hill_climbing.py: {HILL_CLIMBING_IMPORT_ERROR}")
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
            hc_time_limit=args.hc_time_limit or lns_time,
            hc_iterations=args.hc_iterations,
            lns_time_limit=args.lns_time_limit or lns_time,
            lns_iterations=args.lns_iterations,
            cpsat_time_limit=args.cpsat_time_limit or cpsat_time,
            cpsat_workers=args.cpsat_workers,
            show_table=True,
        )
        summaries.append(summary)

    return summaries


def write_outputs(result_data, args):
    if args.output_json:
        Path(args.output_json).write_text(
            json.dumps(result_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\nDa luu ket qua vao {args.output_json}")

    if args.output_excel:
        if not EXCEL_EXPORT_AVAILABLE:
            print(f"\nKhong luu duoc Excel: {EXCEL_EXPORT_IMPORT_ERROR}")
            return
        path = write_comparison_excel(result_data, args.output_excel)
        print(f"\nDa luu ket qua Excel vao {path}")


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Run comparison: Greedy vs Hill Climbing vs LNS vs Google OR-Tools CP-SAT."
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
    parser.add_argument("--hc-time-limit", type=float, default=None)
    parser.add_argument("--hc-iterations", type=int, default=None)
    parser.add_argument("--lns-time-limit", type=float, default=None)
    parser.add_argument("--lns-iterations", type=int, default=None)
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
    parser.add_argument(
        "--reference-output",
        default=None,
        help="File output tham chieu, vi du Output_hustack.txt, de validate va so sanh max_load.",
    )
    return parser


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.benchmark or not args.input_file:
        summaries = run_benchmark(args)
        write_outputs(summaries, args)
        return

    cases = parse_input_cases(args.input_file)
    if len(cases) > 1:
        print(f"Phat hien {len(cases)} testcase trong {args.input_file}.")

    reference_cases = None
    if args.reference_output:
        reference_cases = parse_output_cases(args.reference_output)
        if len(reference_cases) != len(cases):
            raise ValueError(
                f"So testcase input ({len(cases)}) khac output tham chieu ({len(reference_cases)})."
            )
        print(f"Phat hien {len(reference_cases)} output tham chieu trong {args.reference_output}.")

    summaries = []
    for case_index, (case_name, N, M, b, L) in enumerate(cases):
        reference_assignment = (
            reference_cases[case_index][1]
            if reference_cases is not None
            else None
        )
        summary = run_comparison(
            case_name,
            N,
            M,
            b,
            L,
            seed=args.seed,
            hc_time_limit=args.hc_time_limit,
            hc_iterations=args.hc_iterations,
            lns_time_limit=args.lns_time_limit,
            lns_iterations=args.lns_iterations,
            cpsat_time_limit=args.cpsat_time_limit or 10.0,
            cpsat_workers=args.cpsat_workers,
            reference_assignment=reference_assignment,
            reference_name="HUSTack",
            show_table=True,
        )
        summaries.append(summary)

    output_data = summaries[0] if len(summaries) == 1 else summaries
    write_outputs(output_data, args)


if __name__ == "__main__":
    main()
