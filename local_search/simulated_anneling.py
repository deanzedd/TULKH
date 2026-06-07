"""
========================================================================
 THUẬT TOÁN SIMULATED ANNEALING (SA) - Balanced Paper Assignment
========================================================================
 Ý tưởng:
   Như Hill Climbing nhưng chấp nhận move XẤU HƠN với xác suất
   exp(-Δ/T), trong đó T là "nhiệt độ" giảm dần theo thời gian.
   Điều này giúp SA thoát khỏi local optima.

 Operator: SWAP
   Chọn ngẫu nhiên paper i, thay ngẫu nhiên 1 reviewer trong
   assignment[i] bằng 1 reviewer khác trong L[i].

 Tham số mặc định:
   T_init   = max(5, N * 0.05)
   cooling  = 0.995
   T_min    = 0.01
   iters/T  = N moves mỗi nhiệt độ

 Tracking: best_solution riêng biệt (SA có thể rời xa best).

 Dừng: T < T_min hoặc vượt quá max_iterations hoặc time limit.
========================================================================
"""

import time
import tracemalloc
import sys
import math
import random
import statistics

# =====================================================================
#  HÀM ĐỌC / GHI (giữ nguyên như exact_ORTOOLS.py)
# =====================================================================
def input_data():
    """
    Đọc dữ liệu từ stdin (terminal), từng dòng một.
    Đọc dòng 1 lấy N, rồi đọc đúng N dòng tiếp theo.
    Chương trình tự động chạy ngay sau dòng cuối cùng - không cần Ctrl+Z.

    Format:
      Dòng 1: N M b
      Dòng i+1 (i=1..N): k r1 r2 ... rk  (reviewer 1-indexed)
    """
    first_line = sys.stdin.readline()
    N, M, b = map(int, first_line.strip().split())

    L = []
    for i in range(N):
        line = sys.stdin.readline()
        parts = list(map(int, line.strip().split()))
        k = parts[0]
        # 1-indexed -> 0-indexed
        reviewers = [p - 1 for p in parts[1:k+1]]
        L.append(reviewers)

    return N, M, b, L


def print_output(N, b, assignment):
    """In kết quả theo format đề bài (reviewer 1-indexed)."""
    print(N)
    for i in range(N):
        reviewer_1idx = [r + 1 for r in assignment[i]]
        print(b, *reviewer_1idx)


# =====================================================================
#  GREEDY KHỞI TẠO
# =====================================================================
def greedy_init(N, M, b, L):
    """
    Greedy min-load-first để tạo initial solution cho SA.
    Sắp xếp paper theo |L[i]| tăng dần.
    """
    loads = [0] * M
    assignment = [[] for _ in range(N)]
    feasible = True

    paper_order = sorted(range(N), key=lambda i: len(L[i]))

    for i in paper_order:
        candidates = L[i]
        if len(candidates) < b:
            feasible = False
            sorted_cands = sorted(candidates, key=lambda r: loads[r])
            for r in sorted_cands:
                assignment[i].append(r)
                loads[r] += 1
            continue

        sorted_cands = sorted(candidates, key=lambda r: loads[r])
        chosen = sorted_cands[:b]
        assignment[i] = chosen
        for r in chosen:
            loads[r] += 1

    max_load = max(loads) if loads else 0
    return assignment, max_load, loads, feasible


# =====================================================================
#  THUẬT TOÁN SIMULATED ANNEALING
# =====================================================================
def simulated_annealing(N, M, b, L,
                        T_init=None,
                        cooling=0.995,
                        T_min=0.01,
                        iters_per_temp=None,
                        max_iterations=500_000,
                        seed=42,
                        time_limit_sec=120.0):
    """
    Simulated Annealing solver cho bài toán Balanced Paper Assignment.

    Params:
        N (int): Số bài báo
        M (int): Số reviewer
        b (int): Số reviewer/bài
        L (list[list[int]]): Danh sách reviewer sẵn sàng cho mỗi bài
        T_init (float|None): Nhiệt độ khởi đầu. None = tự tính max(5, N*0.05)
        cooling (float): Hệ số làm lạnh (0 < cooling < 1)
        T_min (float): Nhiệt độ tối thiểu để dừng
        iters_per_temp (int|None): Số move mỗi mức nhiệt độ. None = N
        max_iterations (int): Tổng số move tối đa
        seed (int): Random seed
        time_limit_sec (float): Giới hạn thời gian (giây)

    Returns:
        assignment (list[list[int]]): Phân công tốt nhất
        max_load (int): Tải tối đa tốt nhất
        loads (list[int]): Tải từng reviewer
        stats (dict): Thống kê quá trình
    """
    rng = random.Random(seed)

    # Tham số nhiệt độ
    if T_init is None:
        T_init = max(5.0, N * 0.05)
    if iters_per_temp is None:
        iters_per_temp = max(N, 50)

    # ── Khởi tạo từ greedy ──────────────────────────────────────────
    assignment, cur_max_load, loads, _ = greedy_init(N, M, b, L)

    # Xây index ngược
    assign_set = [set(assignment[i]) for i in range(N)]
    reviewer_papers = [set() for _ in range(M)]
    for i in range(N):
        for r in assign_set[i]:
            reviewer_papers[r].add(i)

    # Các paper có ít nhất 1 reviewer thay thế (len(L[i]) > b)
    swappable_papers = [i for i in range(N) if len(L[i]) > b]

    # ── Tracking ─────────────────────────────────────────────────────
    best_max_load = cur_max_load
    best_assignment = [list(assignment[i]) for i in range(N)]
    time_to_best = 0.0
    convergence_iter = 0

    T = T_init
    total_moves = 0
    accepted_moves = 0
    improved_moves = 0
    worsening_accepted = 0
    start_time = time.perf_counter()

    convergence_history = []  # (iteration, best_max_load) mỗi 500 iter

    # ── Vòng lặp SA ──────────────────────────────────────────────────
    while T > T_min and total_moves < max_iterations:
        elapsed = time.perf_counter() - start_time
        if elapsed >= time_limit_sec:
            break

        for _ in range(iters_per_temp):
            if total_moves >= max_iterations:
                break
            elapsed = time.perf_counter() - start_time
            if elapsed >= time_limit_sec:
                break

            total_moves += 1

            # ── Chọn move ngẫu nhiên: SWAP ──────────────────────────
            # Chọn paper có thể swap (có reviewer dự phòng ngoài b)
            if swappable_papers:
                i = rng.choice(swappable_papers)
            else:
                i = rng.randrange(N)

            # Chọn reviewer đang trong assignment để bỏ (old_r)
            old_r = rng.choice(list(assign_set[i]))

            # Chọn reviewer thay thế ngoài assign_set[i]
            candidates_out = [r for r in L[i] if r not in assign_set[i]]
            if not candidates_out:
                continue  # Không có lựa chọn thay thế
            new_r = rng.choice(candidates_out)

            # ── Tính Δ (thay đổi max_load) ──────────────────────────
            # Sau swap: loads[old_r] -= 1, loads[new_r] += 1
            new_old_load = loads[old_r] - 1
            new_new_load = loads[new_r] + 1

            # Tính new max_load
            # Tối ưu: chỉ cần so sánh nếu old_r là người có max hoặc new_r vượt max
            old_max = cur_max_load

            if new_new_load > old_max:
                new_max = new_new_load
            elif loads[old_r] == old_max and new_old_load < old_max:
                # old_r hạ xuống từ đỉnh, cần tính lại max
                # Kiểm tra có reviewer nào khác còn ở old_max không
                # Tránh O(M) bằng cách đếm số reviewer ở đỉnh
                count_at_max = sum(1 for j in range(M)
                                   if loads[j] == old_max and j != old_r)
                if count_at_max > 0:
                    new_max = old_max
                else:
                    # old_r là reviewer duy nhất ở đỉnh, max giảm
                    # new_max = max(old_max - 1, new_new_load, second_max)
                    # Tính chính xác nhưng giới hạn chi phí
                    new_max = max(new_new_load, new_old_load,
                                  max((loads[j] for j in range(M) if j != old_r and j != new_r), default=0))
            else:
                new_max = old_max  # Không thay đổi max

            delta = new_max - old_max  # < 0 là tốt hơn, > 0 là xấu hơn

            # ── Quyết định chấp nhận move ────────────────────────────
            accept = False
            if delta <= 0:
                accept = True
                if delta < 0:
                    improved_moves += 1
            else:
                # Chấp nhận move xấu hơn với xác suất exp(-delta/T)
                prob = math.exp(-delta / T)
                if rng.random() < prob:
                    accept = True
                    worsening_accepted += 1

            if accept:
                # Thực hiện SWAP
                assign_set[i].discard(old_r)
                assign_set[i].add(new_r)
                assignment[i] = list(assign_set[i])

                loads[old_r] -= 1
                loads[new_r] += 1

                reviewer_papers[old_r].discard(i)
                reviewer_papers[new_r].add(i)

                # Tính lại max_load chính xác (đảm bảo không lệch)
                cur_max_load = max(loads)

                accepted_moves += 1

                # Cập nhật best
                if cur_max_load < best_max_load:
                    best_max_load = cur_max_load
                    best_assignment = [list(assignment[i]) for i in range(N)]
                    time_to_best = time.perf_counter() - start_time
                    convergence_iter = total_moves

            # Ghi convergence history mỗi 500 move
            if total_moves % 500 == 0:
                convergence_history.append((total_moves, best_max_load))

        # Làm lạnh nhiệt độ
        T *= cooling

    total_time = time.perf_counter() - start_time

    # Tính loads chính xác từ best_assignment
    best_loads = [0] * M
    for i in range(N):
        for r in best_assignment[i]:
            best_loads[r] += 1

    stats = {
        "T_init": T_init,
        "cooling": cooling,
        "T_min": T_min,
        "T_final": T,
        "total_moves": total_moves,
        "accepted_moves": accepted_moves,
        "improved_moves": improved_moves,
        "worsening_accepted": worsening_accepted,
        "acceptance_rate": accepted_moves / total_moves if total_moves > 0 else 0,
        "convergence_iter": convergence_iter,
        "time_to_best": time_to_best,
        "total_time": total_time,
        "convergence_history": convergence_history,
    }

    return best_assignment, best_max_load, best_loads, stats


# =====================================================================
#  SO SÁNH VỚI GREEDY VÀ EXACT SOLVER
# =====================================================================
def run_comparison(N, M, b, L, sa_result, sa_stats, time_limit_exact=30.0):
    """
    So sánh SA với Greedy và Exact (nếu có thể).
    In bảng so sánh đầy đủ theo các metric trong roadmap.
    """
    import sys as _sys

    sa_assign, sa_max_load, sa_loads, _ = sa_result

    # ── 1. Chạy Greedy ──────────────────────────────────────────────
    g_start = time.perf_counter()
    g_assign, g_max_load, g_loads, g_feasible = greedy_init(N, M, b, L)
    g_time = time.perf_counter() - g_start

    # ── 2. Chạy Exact (chỉ khi N nhỏ) ──────────────────────────────
    opt_max_load = None
    exact_time = None
    exact_status = "SKIPPED"

    if N <= 200:
        try:
            from ortools.sat.python import cp_model as _cp

            model = _cp.CpModel()
            x = {}
            for i in range(N):
                for j in L[i]:
                    x[i, j] = model.NewBoolVar(f"x_{i}_{j}")
            for i in range(N):
                model.Add(sum(x[i, j] for j in L[i]) == b)
            max_load_var = model.NewIntVar(0, N * b, "max_load")
            for j in range(M):
                papers_j = [i for i in range(N) if j in L[i]]
                if papers_j:
                    model.Add(sum(x[i, j] for i in papers_j) <= max_load_var)
            model.Minimize(max_load_var)

            solver = _cp.CpSolver()
            solver.parameters.max_time_in_seconds = time_limit_exact
            solver.parameters.num_search_workers = 4

            e_start = time.perf_counter()
            status = solver.Solve(model)
            exact_time = time.perf_counter() - e_start
            exact_status = solver.StatusName(status)

            if status in (_cp.OPTIMAL, _cp.FEASIBLE):
                opt_max_load = int(solver.ObjectiveValue())
        except ImportError:
            exact_status = "OR-TOOLS NOT INSTALLED"

    # ── 3. Lower Bound ───────────────────────────────────────────────
    LB = math.ceil(N * b / M)

    # ── 4. Tính Metrics ──────────────────────────────────────────────
    greedy_gap = (sa_max_load - g_max_load) / g_max_load * 100 if g_max_load > 0 else 0
    lb_gap     = (sa_max_load - LB) / LB * 100 if LB > 0 else 0
    opt_gap    = (sa_max_load - opt_max_load) / opt_max_load * 100 \
                 if opt_max_load is not None and opt_max_load > 0 else None

    g_lb_gap   = (g_max_load - LB) / LB * 100 if LB > 0 else 0

    # ── 5. In kết quả ────────────────────────────────────────────────
    sep = "=" * 70
    print(sep, file=_sys.stderr)
    print("  SIMULATED ANNEALING — KẾT QUẢ SO SÁNH", file=_sys.stderr)
    print(sep, file=_sys.stderr)
    print(f"  Instance  : N={N}, M={M}, b={b}", file=_sys.stderr)
    print(f"  LB (⌈N×b/M⌉) = {LB}", file=_sys.stderr)
    print(f"  SA Params : T_init={sa_stats['T_init']:.2f}, cooling={sa_stats['cooling']}, "
          f"T_min={sa_stats['T_min']}", file=_sys.stderr)
    print(sep, file=_sys.stderr)

    # Bảng max_load
    print(f"\n  {'Thuật toán':<20} {'max_load':>10} {'Thời gian':>12}", file=_sys.stderr)
    print(f"  {'-'*44}", file=_sys.stderr)
    print(f"  {'Greedy':<20} {g_max_load:>10} {g_time:>11.4f}s", file=_sys.stderr)
    print(f"  {'Simul. Annealing':<20} {sa_max_load:>10} {sa_stats['total_time']:>11.4f}s", file=_sys.stderr)
    if opt_max_load is not None:
        print(f"  {'Exact (OPT)':<20} {opt_max_load:>10} {exact_time:>11.4f}s  [{exact_status}]",
              file=_sys.stderr)
    else:
        print(f"  {'Exact':<20} {'N/A':>10}  [{exact_status}]", file=_sys.stderr)

    # Bảng chất lượng lời giải
    print(f"\n  3.1 CHẤT LƯỢNG LỜI GIẢI:", file=_sys.stderr)
    print(f"  {'Metric':<30} {'Greedy':>10} {'SA':>10}", file=_sys.stderr)
    print(f"  {'-'*52}", file=_sys.stderr)
    print(f"  {'LB Gap (LB=' + str(LB) + ')':<30} {g_lb_gap:>9.2f}% {lb_gap:>9.2f}%", file=_sys.stderr)
    print(f"  {'Greedy Gap':<30} {'(baseline)':>10} {greedy_gap:>9.2f}%", file=_sys.stderr)
    if opt_gap is not None:
        g_opt_gap = (g_max_load - opt_max_load) / opt_max_load * 100 if opt_max_load > 0 else 0
        opt_label = f'Optimality Gap (OPT={opt_max_load})'
        print(f"  {opt_label:<30} {g_opt_gap:>9.2f}% {opt_gap:>9.2f}%",
              file=_sys.stderr)

    # Bảng thời gian
    print(f"\n  3.2 THỜI GIAN:", file=_sys.stderr)
    print(f"  Wall-clock time    : {sa_stats['total_time']:.4f}s", file=_sys.stderr)
    print(f"  Time to best       : {sa_stats['time_to_best']:.4f}s", file=_sys.stderr)
    print(f"  T_final            : {sa_stats['T_final']:.4f}", file=_sys.stderr)
    print(f"  Total moves        : {sa_stats['total_moves']}", file=_sys.stderr)
    print(f"  Accepted moves     : {sa_stats['accepted_moves']} "
          f"({sa_stats['acceptance_rate']*100:.1f}%)", file=_sys.stderr)
    print(f"  Improved moves     : {sa_stats['improved_moves']}", file=_sys.stderr)
    print(f"  Worsening accepted : {sa_stats['worsening_accepted']}", file=_sys.stderr)
    print(f"  Convergence move   : {sa_stats['convergence_iter']}", file=_sys.stderr)

    print(f"\n  Cải thiện so với Greedy: {g_max_load - sa_max_load:+d} (Greedy Gap = {greedy_gap:.2f}%)",
          file=_sys.stderr)
    print(sep, file=_sys.stderr)


def run_robustness_test(N, M, b, L,
                        n_runs=10,
                        T_init=None,
                        cooling=0.995,
                        T_min=0.01,
                        max_iterations=500_000,
                        time_limit_sec=60.0):
    """
    3.3 Chạy SA n_runs lần với seed khác nhau, đo độ ổn định.
    """
    import sys as _sys
    seeds = [42, 123, 456, 789, 1000, 2024, 314, 271, 999, 100]
    results = []

    print(f"\n  3.3 ĐỘ ỔN ĐỊNH — Chạy {n_runs} lần (mỗi lần seed khác):", file=_sys.stderr)

    for run_idx in range(n_runs):
        seed = seeds[run_idx % len(seeds)]
        assignment, max_load, loads, stats = simulated_annealing(
            N, M, b, L,
            T_init=T_init,
            cooling=cooling,
            T_min=T_min,
            max_iterations=max_iterations,
            seed=seed,
            time_limit_sec=time_limit_sec
        )
        results.append(max_load)
        print(f"    Run {run_idx+1:2d} (seed={seed:4d}): max_load={max_load}  "
              f"time={stats['total_time']:.3f}s  "
              f"T_final={stats['T_final']:.4f}  "
              f"accept_rate={stats['acceptance_rate']*100:.1f}%", file=_sys.stderr)

    mean_val  = statistics.mean(results)
    std_val   = statistics.stdev(results) if len(results) > 1 else 0.0
    best_val  = min(results)
    worst_val = max(results)

    print(f"\n  {'Metric':<15} {'Giá trị':>10}", file=_sys.stderr)
    print(f"  {'-'*27}", file=_sys.stderr)
    print(f"  {'Mean':<15} {mean_val:>10.2f}", file=_sys.stderr)
    print(f"  {'Std Dev':<15} {std_val:>10.2f}", file=_sys.stderr)
    print(f"  {'Best of 10':<15} {best_val:>10}", file=_sys.stderr)
    print(f"  {'Worst of 10':<15} {worst_val:>10}", file=_sys.stderr)

    return results


# =====================================================================
#  MAIN
# =====================================================================
def main():
    N, M, b, L = input_data()

    # Tham số SA tự động theo kích thước bài toán
    T_init        = max(5.0, N * 0.05)
    cooling       = 0.995
    T_min         = 0.01
    max_iterations = max(500_000, N * 1000)
    time_limit    = 120.0

    tracemalloc.start()
    start_time = time.perf_counter()

    assignment, max_load, loads, stats = simulated_annealing(
        N, M, b, L,
        T_init=T_init,
        cooling=cooling,
        T_min=T_min,
        max_iterations=max_iterations,
        seed=42,
        time_limit_sec=time_limit
    )

    end_time = time.perf_counter()
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # ── In thông tin ra stderr ───────────────────────────────────────
    print(f"[SA] Max Load: {max_load} | Time: {end_time - start_time:.3f}s "
          f"| Mem: {peak_mem/1024:.1f} KB", file=sys.stderr)

    # ── So sánh với Greedy và Exact ─────────────────────────────────
    sa_result = (assignment, max_load, loads, stats)
    run_comparison(N, M, b, L, sa_result, stats, time_limit_exact=30.0)

    # ── Chạy robustness test ─────────────────────────────────────────
    run_robustness_test(
        N, M, b, L,
        n_runs=10,
        T_init=T_init,
        cooling=cooling,
        T_min=T_min,
        max_iterations=max_iterations,
        time_limit_sec=30.0
    )

    # ── In output chuẩn ra stdout ────────────────────────────────────
    print_output(N, b, assignment)


if __name__ == "__main__":
    main()
