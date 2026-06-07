"""
========================================================================
 LARGE NEIGHBORHOOD SEARCH (LNS) - Balanced Paper Assignment
========================================================================

Bai toan:
  - Co N bai bao, M reviewer.
  - Moi bai i chi duoc gan reviewer trong L[i].
  - Moi bai phai co dung b reviewer.
  - Muc tieu: minimize max_load, trong do max_load la tai lon nhat
    cua mot reviewer bat ky.

Y tuong LNS:
  1. Khoi tao bang Greedy min-load-first.
  2. Lap lai:
       DESTROY: chon mot nhom paper, uu tien cac paper dang lam reviewer
                tai cao bi "nong".
       REPAIR : gan lai nhom paper do bang greedy theo tai hien tai,
                them nhieu nhe de da dang loi giai.
       POLISH : thu vai move cuc bo de ha reviewer dang co max_load.
       ACCEPT : giu loi giai tot hon/equal, thinh thoang chap nhan loi
                giai xau hon mot chut de thoat vung ket.

File nay tap trung vao thuat toan LNS. Phan so sanh chi tiet nam trong
run_comparison.py, nhung CLI cu van duoc giu de tien chay.

File nay co 3 che do chay:
  1. python .\TULKH\greedy_lns_cpsat\lns_solver.py input.txt
     -> chay rieng LNS, in assignment dung format de bai.

  2. python .\TULKH\greedy_lns_cpsat\lns_solver.py input.txt --compare
     -> goi sang run_comparison.py de so sanh Greedy, LNS, CP-SAT.

  3. python .\TULKH\greedy_lns_cpsat\lns_solver.py --benchmark
     -> goi sang run_comparison.py de chay bo benchmark.
========================================================================
"""

import argparse
import json
import math
import random
import sys
import time
import tracemalloc
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

try:
    from ortools.sat.python import cp_model

    CPSAT_AVAILABLE = True
except ImportError:
    cp_model = None
    CPSAT_AVAILABLE = False


# =====================================================================
#  INPUT / OUTPUT
# =====================================================================
def parse_input(source=None):
    """
    Doc input theo format:
      Dong 1: N M b
      Dong i+1: k r1 r2 ... rk, reviewer 1-indexed.

    Ham nay bo qua dong trong va comment bat dau bang '#', de doc duoc
    cac file testcase co ghi chu.
    """
    if source is None:
        raw_text = sys.stdin.read()
    else:
        raw_text = Path(source).read_text(encoding="utf-8")

    lines = []
    for line in raw_text.splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            lines.append(line)

    if not lines:
        raise ValueError("Input rong.")

    N, M, b = map(int, lines[0].split())
    if len(lines) < N + 1:
        raise ValueError(f"Input thieu dong: can {N} dong paper, hien co {len(lines) - 1}.")

    L = []
    for i in range(N):
        parts = list(map(int, lines[i + 1].split()))
        k = parts[0]
        reviewers = [r - 1 for r in parts[1 : k + 1]]
        L.append(reviewers)

    return N, M, b, L


def print_output(N, b, assignment):
    """In assignment theo format de bai, reviewer 1-indexed."""
    print(N)
    for i in range(N):
        reviewers_1idx = [r + 1 for r in assignment[i]]
        print(b, *reviewers_1idx)


def write_case(path, N, M, b, L):
    lines = [f"{N} {M} {b}"]
    for reviewers in L:
        one_based = [str(r + 1) for r in reviewers]
        lines.append(" ".join([str(len(reviewers))] + one_based))
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


# =====================================================================
#  CAC HAM CHUNG
# =====================================================================
def check_instance_feasible(N, M, b, L):
    if b < 0 or N < 0 or M < 0:
        return False
    if b == 0:
        return True
    if M == 0:
        return False
    return all(len(L[i]) >= b for i in range(N))


def compute_loads(assignment, M):
    loads = [0] * M
    for reviewers in assignment:
        for r in reviewers:
            loads[r] += 1
    return loads


def compute_statistics(loads):
    if not loads:
        return {
            "min_load": 0,
            "max_load": 0,
            "avg_load": 0.0,
            "std_dev": 0.0,
            "sum_sq": 0,
        }

    avg = sum(loads) / len(loads)
    variance = sum((load - avg) ** 2 for load in loads) / len(loads)
    return {
        "min_load": min(loads),
        "max_load": max(loads),
        "avg_load": round(avg, 3),
        "std_dev": round(math.sqrt(variance), 3),
        "sum_sq": sum(load * load for load in loads),
    }


def lower_bound(N, M, b):
    if M == 0:
        return 0
    return math.ceil(N * b / M)


def objective(loads):
    """
    Muc tieu: minimize max_load.
    """
    if not loads:
        return 0
    return max(loads)


def validate_assignment(N, b, L, assignment):
    if len(assignment) != N:
        return False, f"Assignment co {len(assignment)} paper, can {N}."

    for i in range(N):
        if len(assignment[i]) != b:
            return False, f"Bai {i + 1} co {len(assignment[i])} reviewer, can {b}."
        if len(set(assignment[i])) != len(assignment[i]):
            return False, f"Bai {i + 1} bi trung reviewer."
        allowed = set(L[i])
        for r in assignment[i]:
            if r not in allowed:
                return False, f"Reviewer {r + 1} khong nam trong L[{i + 1}]."
    return True, "OK"


def timed_call(fn, *args, **kwargs):
    tracemalloc.start()
    start_time = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed = time.perf_counter() - start_time
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, elapsed, peak / 1024


# =====================================================================
#  GREEDY BASELINE
# =====================================================================
def greedy_assign(N, M, b, L):
    """
    Baseline greedy:
      - Xu ly paper it lua chon truoc.
      - Moi paper chon b reviewer co load thap nhat trong L[i].
    """
    loads = [0] * M
    assignment = [[] for _ in range(N)]

    if not check_instance_feasible(N, M, b, L):
        return assignment, -1, loads, False

    paper_order = sorted(range(N), key=lambda i: (len(L[i]), i))
    for i in paper_order:
        candidates = sorted(L[i], key=lambda r: (loads[r], r))
        chosen = candidates[:b]
        assignment[i] = list(chosen)
        for r in chosen:
            loads[r] += 1

    return assignment, max(loads) if loads else 0, loads, True


# =====================================================================
#  GOOGLE OR-TOOLS CP-SAT
# =====================================================================
def cpsat_solve(N, M, b, L, time_limit_sec=10.0, workers=4):
    """
    Exact solver bang Google OR-Tools CP-SAT.
    Neu dat status OPTIMAL thi max_load la OPT de tinh gap cho LNS/Greedy.
    """
    if not CPSAT_AVAILABLE:
        return None, -1, [0] * M, "CP-SAT_NOT_INSTALLED"

    if not check_instance_feasible(N, M, b, L):
        return None, -1, [0] * M, "INFEASIBLE_INPUT"

    model = cp_model.CpModel()
    x = {}

    for i in range(N):
        for r in L[i]:
            x[i, r] = model.NewBoolVar(f"x_{i}_{r}")

    for i in range(N):
        model.Add(sum(x[i, r] for r in L[i]) == b)

    load_vars = []
    for r in range(M):
        load_r = model.NewIntVar(0, N, f"load_{r}")
        papers_for_r = [i for i in range(N) if r in L[i]]
        if papers_for_r:
            model.Add(load_r == sum(x[i, r] for i in papers_for_r))
        else:
            model.Add(load_r == 0)
        load_vars.append(load_r)

    lb = lower_bound(N, M, b)
    max_load_var = model.NewIntVar(lb, N * b, "max_load")
    model.AddMaxEquality(max_load_var, load_vars)
    model.Minimize(max_load_var)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit_sec)
    solver.parameters.num_search_workers = int(workers)

    status = solver.Solve(model)
    status_str = solver.StatusName(status)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, -1, [0] * M, status_str

    assignment = [[] for _ in range(N)]
    loads = [0] * M
    for i in range(N):
        for r in L[i]:
            if solver.Value(x[i, r]) == 1:
                assignment[i].append(r)
                loads[r] += 1

    return assignment, max(loads) if loads else 0, loads, status_str


# =====================================================================
#  LNS CORE
# =====================================================================
def choose_lns_parameters(N):
    """
    Bo tham so mac dinh can bang giua chat luong va thoi gian.

    Truc giac:
      - destroy qua nho: de ket o local optimum.
      - destroy qua lon: gan nhu restart, cham va mat loi giai tot.
      - voi test vua/lon, pha khoang 1-4% so paper moi vong la kha on.
    """
    sqrt_n = max(1, int(math.sqrt(max(1, N))))

    if N <= 50:
        max_iterations = 2500
        time_limit_sec = 2.0
    elif N <= 200:
        max_iterations = 4500
        time_limit_sec = 4.0
    elif N <= 1000:
        max_iterations = 7000
        time_limit_sec = 7.0
    else:
        max_iterations = 9000
        time_limit_sec = 10.0

    destroy_min = max(1, min(N, sqrt_n // 2))
    destroy_max = max(destroy_min, min(N, max(8, 2 * sqrt_n, int(0.04 * N))))

    return {
        "max_iterations": max_iterations,
        "time_limit_sec": time_limit_sec,
        "destroy_min": destroy_min,
        "destroy_max": destroy_max,
        "heavy_bias": 0.70,
        "repair_noise": 0.10,
        "polish_steps": 8 if N <= 300 else 4,
        "restart_after": max(800, max_iterations // 4),
    }


def choose_destroy_size(rng, destroy_min, destroy_max, stale_iterations, restart_after):
    if destroy_min >= destroy_max:
        return destroy_min

    # Khi lau khong cai thien, tang kich thuoc destroy de nhay xa hon.
    if stale_iterations >= restart_after // 2:
        lo = (destroy_min + destroy_max) // 2
        return rng.randint(lo, destroy_max)

    return rng.randint(destroy_min, destroy_max)


def select_destroy_papers(assignment, loads, L, k, rng, heavy_bias):
    """
    Chon paper de destroy.
    Uu tien paper dang gan reviewer tai cao, vi chung co kha nang la nut that
    cua max_load. Phan con lai random de giu da dang.
    """
    N = len(assignment)
    if k >= N:
        return list(range(N))

    max_load = max(loads) if loads else 0
    hot_threshold = max_load if max_load <= 1 else max_load - 1
    hot_reviewers = {r for r, load in enumerate(loads) if load >= hot_threshold}

    scored = []
    for i in range(N):
        hot_count = sum(1 for r in assignment[i] if r in hot_reviewers)
        if hot_count > 0:
            # Paper co nhieu alternative hon de repair linh hoat hon.
            scored.append((-hot_count, -len(L[i]), rng.random(), i))

    scored.sort()
    selected = []
    selected_set = set()
    target_hot = min(k, int(round(k * heavy_bias)))

    for _, _, _, i in scored:
        if len(selected) >= target_hot:
            break
        selected.append(i)
        selected_set.add(i)

    while len(selected) < k:
        i = rng.randrange(N)
        if i not in selected_set:
            selected.append(i)
            selected_set.add(i)

    return selected


def destroy_assignment(assignment, loads, papers):
    for i in papers:
        for r in assignment[i]:
            loads[r] -= 1
        assignment[i] = []


def repair_assignment(assignment, loads, b, L, papers, rng, repair_noise):
    """
    Repair greedy:
      - Paper it candidate duoc gan truoc.
      - Moi paper lay b reviewer co load thap nhat.
      - Nhieu nhe chi pha tie/gap rat nho, khong lam mat tinh min-load.
    """
    repair_order = sorted(papers, key=lambda i: (len(L[i]), rng.random()))

    for i in repair_order:
        if len(L[i]) < b:
            return False

        scored = []
        for r in L[i]:
            noisy_load = loads[r] + rng.random() * repair_noise
            scored.append((noisy_load, loads[r], r))

        scored.sort()
        chosen = [r for _, _, r in scored[:b]]
        assignment[i] = chosen
        for r in chosen:
            loads[r] += 1

    return True


def polish_hot_reviewers(assignment, loads, L, max_steps):
    """
    Buoc repair cuc bo: neu reviewer dang o max_load co the chuyen mot paper
    sang reviewer nhe hon ma khong lam tang max_load, thuc hien move do.
    """
    if max_steps <= 0 or not loads:
        return 0

    N = len(assignment)
    moves = 0

    while moves < max_steps:
        current_max = max(loads)
        hot_reviewers = [r for r, load in enumerate(loads) if load == current_max]
        improved = False

        for hot in hot_reviewers:
            # Paper co nhieu lua chon hon thu truoc vi de thay reviewer hon.
            papers = [i for i in range(N) if hot in assignment[i]]
            papers.sort(key=lambda i: -len(L[i]))

            for i in papers:
                assigned = set(assignment[i])
                candidates = [
                    r
                    for r in L[i]
                    if r not in assigned and loads[r] + 1 < current_max
                ]
                if not candidates:
                    continue

                new_r = min(candidates, key=lambda r: loads[r])
                assignment[i].remove(hot)
                assignment[i].append(new_r)
                loads[hot] -= 1
                loads[new_r] += 1

                moves += 1
                improved = True
                break

            if improved:
                break

        if not improved:
            break

    return moves


def score_delta(new_obj, old_obj, total_assignments):
    return new_obj - old_obj


def lns_solve(
    N,
    M,
    b,
    L,
    max_iterations=None,
    time_limit_sec=None,
    destroy_min=None,
    destroy_max=None,
    heavy_bias=None,
    repair_noise=None,
    polish_steps=None,
    restart_after=None,
    seed=42,
):
    """
    Chay LNS va tra ve:
      best_assignment, best_max_load, best_loads, stats
    """
    if not check_instance_feasible(N, M, b, L):
        return [[] for _ in range(N)], -1, [0] * M, {
            "status": "INFEASIBLE_INPUT",
            "iterations": 0,
            "accepted": 0,
            "rejected": 0,
            "best_updates": 0,
            "time_to_best": 0.0,
        }

    params = choose_lns_parameters(N)
    max_iterations = params["max_iterations"] if max_iterations is None else max_iterations
    time_limit_sec = params["time_limit_sec"] if time_limit_sec is None else time_limit_sec
    destroy_min = params["destroy_min"] if destroy_min is None else destroy_min
    destroy_max = params["destroy_max"] if destroy_max is None else destroy_max
    heavy_bias = params["heavy_bias"] if heavy_bias is None else heavy_bias
    repair_noise = params["repair_noise"] if repair_noise is None else repair_noise
    polish_steps = params["polish_steps"] if polish_steps is None else polish_steps
    restart_after = params["restart_after"] if restart_after is None else restart_after

    destroy_min = max(1, min(N, destroy_min))
    destroy_max = max(destroy_min, min(N, destroy_max))

    rng = random.Random(seed)
    assignment, _, loads, feasible = greedy_assign(N, M, b, L)
    if not feasible:
        return assignment, -1, loads, {"status": "INFEASIBLE_INPUT"}

    current_obj = objective(loads)
    best_assignment = [list(reviewers) for reviewers in assignment]
    best_loads = list(loads)
    best_obj = current_obj

    start_time = time.perf_counter()
    time_to_best = 0.0
    last_best_iteration = 0

    stats = {
        "status": "OK",
        "initial_max_load": current_obj,
        "iterations": 0,
        "accepted": 0,
        "rejected": 0,
        "best_updates": 0,
        "destroyed_total": 0,
        "polish_moves": 0,
        "resets_to_best": 0,
        "time_to_best": 0.0,
        "best_iteration": 0,
        "destroy_min": destroy_min,
        "destroy_max": destroy_max,
        "heavy_bias": heavy_bias,
        "repair_noise": repair_noise,
    }

    total_assignments = N * b
    initial_temperature = 1.25

    for iteration in range(1, max_iterations + 1):
        elapsed = time.perf_counter() - start_time
        if elapsed >= time_limit_sec:
            break

        stale = iteration - last_best_iteration

        # Neu di qua lau khong cai thien, dua current ve best roi tiep tuc
        # pha neighborhood lon hon.
        if stale >= restart_after:
            assignment = [list(reviewers) for reviewers in best_assignment]
            loads = list(best_loads)
            current_obj = best_obj
            last_best_iteration = iteration
            stats["resets_to_best"] += 1
            stale = 0

        old_assignment = [list(reviewers) for reviewers in assignment]
        old_loads = list(loads)
        old_obj = current_obj

        k = choose_destroy_size(rng, destroy_min, destroy_max, stale, restart_after)
        papers = select_destroy_papers(assignment, loads, L, k, rng, heavy_bias)

        destroy_assignment(assignment, loads, papers)
        repaired = repair_assignment(assignment, loads, b, L, papers, rng, repair_noise)

        if repaired:
            stats["polish_moves"] += polish_hot_reviewers(
                assignment, loads, L, polish_steps
            )

        if not repaired:
            assignment = old_assignment
            loads = old_loads
            current_obj = old_obj
            stats["rejected"] += 1
            continue

        new_obj = objective(loads)

        accept = False
        if new_obj <= old_obj:
            accept = True
        else:
            progress = iteration / max(1, max_iterations)
            temperature = max(0.05, initial_temperature * (1.0 - progress))
            delta = score_delta(new_obj, old_obj, total_assignments)
            if delta <= 0:
                accept = True
            else:
                accept = rng.random() < math.exp(-delta / temperature)

        if accept:
            current_obj = new_obj
            stats["accepted"] += 1
            stats["destroyed_total"] += len(papers)

            if new_obj < best_obj:
                best_obj = new_obj
                best_assignment = [list(reviewers) for reviewers in assignment]
                best_loads = list(loads)
                time_to_best = time.perf_counter() - start_time
                last_best_iteration = iteration
                stats["best_updates"] += 1
                stats["time_to_best"] = time_to_best
                stats["best_iteration"] = iteration
        else:
            assignment = old_assignment
            loads = old_loads
            current_obj = old_obj
            stats["rejected"] += 1

        stats["iterations"] = iteration

    stats["total_time"] = time.perf_counter() - start_time
    stats["final_current_max_load"] = current_obj
    stats["best_max_load"] = best_obj

    return best_assignment, best_obj, best_loads, stats


# =====================================================================
#  TEST CASE GENERATOR
# =====================================================================
def generate_test_case(N, M, b, density=0.3, seed=42, min_extra_choice=1):
    """
    Sinh test ngau nhien. Dam bao moi paper co it nhat b reviewer,
    thuong la b+1 neu M cho phep de LNS co khong gian repair.
    """
    rng = random.Random(seed)
    L = []
    min_choices = min(M, b + min_extra_choice)

    for _ in range(N):
        reviewers = [r for r in range(M) if rng.random() < density]
        while len(reviewers) < min_choices:
            r = rng.randrange(M)
            if r not in reviewers:
                reviewers.append(r)
        rng.shuffle(reviewers)
        L.append(reviewers)

    return L


# =====================================================================
#  CLI
# =====================================================================
def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="LNS solver and comparison runner for Balanced Paper Assignment."
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        help="File input. Neu bo trong thi chay benchmark mac dinh.",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="So sanh Greedy, LNS va CP-SAT tren input_file.",
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Chay bo benchmark mac dinh.",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--lns-time-limit", type=float, default=None)
    parser.add_argument("--lns-iterations", type=int, default=None)
    parser.add_argument("--cpsat-time-limit", type=float, default=None)
    parser.add_argument("--cpsat-workers", type=int, default=4)
    parser.add_argument(
        "--output-json",
        default=None,
        help="Noi luu ket qua benchmark/compare dang JSON. Mac dinh khong luu.",
    )
    return parser


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.benchmark or not args.input_file:
        from run_comparison import run_benchmark

        run_benchmark(args)
        return

    N, M, b, L = parse_input(args.input_file)

    if args.compare:
        from run_comparison import run_comparison

        summary = run_comparison(
            Path(args.input_file).name,
            N,
            M,
            b,
            L,
            seed=args.seed,
            lns_time_limit=args.lns_time_limit,
            lns_iterations=args.lns_iterations,
            cpsat_time_limit=args.cpsat_time_limit or 10.0,
            cpsat_workers=args.cpsat_workers,
            show_table=True,
        )
        if args.output_json:
            Path(args.output_json).write_text(
                json.dumps(summary, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        return

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
        seed=args.seed,
        time_limit_sec=args.lns_time_limit,
        max_iterations=args.lns_iterations,
    )

    print(
        f"[LNS] Max Load = {max_load} | "
        f"Iterations = {stats.get('iterations', 0)} | "
        f"Best at iter = {stats.get('best_iteration', 0)}",
        file=sys.stderr,
    )
    print(f"[LNS] Time = {elapsed:.6f}s | Memory = {peak_kb:.2f} KB", file=sys.stderr)
    print_output(N, b, assignment)


if __name__ == "__main__":
    main()
