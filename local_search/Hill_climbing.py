"""
========================================================================
 THUẬT TOÁN HILL CLIMBING (HC) - Balanced Paper Assignment
========================================================================
 Ý tưởng:
   Bắt đầu từ lời giải greedy, liên tục thực hiện SWAP để cải thiện
   max_load. Tìm reviewer j* có tải cao nhất, thử thay bằng reviewer
   khác có tải thấp hơn trong cùng paper.

 Operator: SWAP
   - Tìm reviewer j* có load = max_load
   - Tìm paper i có j* trong assignment[i]
   - Thử thay j* bằng reviewer j' ∈ L[i] \ assignment[i]
     sao cho load[j'] < load[j*] - 1 (cải thiện được max_load)
   - Nếu tìm được: thực hiện và lặp lại

 Dừng: Khi không còn move nào cải thiện được max_load.

 Độ phức tạp mỗi bước: O(N × |L_max|)
========================================================================
"""

import time
import tracemalloc
import sys
import math
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
#  GREEDY KHỞI TẠO (dùng làm initial solution cho HC)
# =====================================================================
def greedy_init(N, M, b, L):
    """
    Greedy min-load-first để tạo initial solution cho HC.
    Sắp xếp paper theo |L[i]| tăng dần (ưu tiên paper khó hơn).
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
#  THUẬT TOÁN HILL CLIMBING
# =====================================================================
def hill_climbing(N, M, b, L, max_iterations=100_000, seed=None, time_limit_sec=60.0):
    """
    Hill Climbing solver cho bài toán Balanced Paper Assignment.

    Params:
        N (int): Số bài báo
        M (int): Số reviewer
        b (int): Số reviewer/bài
        L (list[list[int]]): Danh sách reviewer sẵn sàng cho mỗi bài
        max_iterations (int): Số vòng lặp tối đa
        seed (int|None): Random seed (không dùng trong HC thuần, giữ để đồng nhất API)
        time_limit_sec (float): Giới hạn thời gian (giây)

    Returns:
        assignment (list[list[int]]): Phân công tốt nhất
        max_load (int): Tải tối đa tốt nhất
        loads (list[int]): Tải từng reviewer
        stats (dict): Thống kê quá trình tìm kiếm
    """
    # ── Khởi tạo từ greedy ──────────────────────────────────────────
    assignment, max_load, loads, _ = greedy_init(N, M, b, L)

    # Xây index ngược: paper nào có reviewer j?
    # reviewer_papers[j] = set of paper indices
    reviewer_papers = [set() for _ in range(M)]
    for i in range(N):
        for r in assignment[i]:
            reviewer_papers[r].add(i)

    # Chuyển assignment thành set để tra cứu O(1)
    assign_set = [set(assignment[i]) for i in range(N)]

    # ── Tracking ────────────────────────────────────────────────────
    best_max_load = max_load
    best_assignment = [list(assignment[i]) for i in range(N)]
    time_to_best = 0.0
    iterations_done = 0
    improvements = 0
    convergence_iter = 0
    start_time = time.perf_counter()

    # ── Vòng lặp Hill Climbing ──────────────────────────────────────
    for iteration in range(max_iterations):
        elapsed = time.perf_counter() - start_time
        if elapsed >= time_limit_sec:
            break

        improved = False
        current_max = max_load

        # Tìm tất cả reviewer có tải = max_load (reviewer "nóng")
        hot_reviewers = [j for j in range(M) if loads[j] == current_max]

        for j_star in hot_reviewers:
            # Thử giảm tải của j_star bằng cách SWAP trong từng paper
            for i in list(reviewer_papers[j_star]):
                # Tìm reviewer thay thế j' ∈ L[i] \ assign_set[i]
                # Điều kiện cải thiện: loads[j'] < loads[j_star] - 1
                #   → sau swap: loads[j_star] giảm 1, loads[j'] tăng 1
                #   → max_load có thể giảm nếu j_star là reviewer duy nhất ở đỉnh
                best_swap_r = None
                best_swap_load = loads[j_star]  # muốn tìm j' có load < j_star - 1

                for r in L[i]:
                    if r in assign_set[i]:
                        continue  # r đã trong assignment[i]
                    # Sau swap: load[j_star] - 1, load[r] + 1
                    # new_max_load = max(max trừ j_star và r, load[j_star]-1, load[r]+1)
                    new_j_star_load = loads[j_star] - 1
                    new_r_load = loads[r] + 1

                    # max_load mới phải nhỏ hơn current_max
                    # → cần new_j_star_load < current_max (j_star không còn ở max)
                    # → cần new_r_load < current_max (r không vượt max)
                    if new_j_star_load < current_max and new_r_load < current_max:
                        # Cải thiện được max_load
                        if loads[r] < best_swap_load:
                            best_swap_load = loads[r]
                            best_swap_r = r

                if best_swap_r is not None:
                    # Thực hiện SWAP: thay j_star → best_swap_r trong paper i
                    r = best_swap_r

                    # Cập nhật assignment
                    assign_set[i].discard(j_star)
                    assign_set[i].add(r)
                    assignment[i] = list(assign_set[i])

                    # Cập nhật loads
                    loads[j_star] -= 1
                    loads[r] += 1

                    # Cập nhật reviewer_papers
                    reviewer_papers[j_star].discard(i)
                    reviewer_papers[r].add(i)

                    # Tính max_load mới
                    max_load = max(loads)
                    improvements += 1
                    improved = True

                    # Cập nhật best
                    if max_load < best_max_load:
                        best_max_load = max_load
                        best_assignment = [list(assignment[i]) for i in range(N)]
                        time_to_best = time.perf_counter() - start_time
                        convergence_iter = iteration

                    break  # Thoát vòng paper, tìm hot reviewer mới

            if improved:
                break  # Thoát vòng hot_reviewers, bắt đầu iteration mới

        iterations_done = iteration + 1

        # Dừng nếu không còn cải thiện được
        if not improved:
            break

    total_time = time.perf_counter() - start_time

    stats = {
        "iterations": iterations_done,
        "improvements": improvements,
        "convergence_iter": convergence_iter,
        "time_to_best": time_to_best,
        "total_time": total_time,
    }

    return best_assignment, best_max_load, [0] * M, stats


def hill_climbing_with_loads(N, M, b, L, max_iterations=100_000, seed=None, time_limit_sec=60.0):
    """
    Wrapper trả về loads chính xác cùng với assignment tốt nhất.
    """
    best_assignment, best_max_load, _, stats = hill_climbing(
        N, M, b, L, max_iterations, seed, time_limit_sec
    )

    # Tính lại loads từ best_assignment
    loads = [0] * M
    for i in range(N):
        for r in best_assignment[i]:
            loads[r] += 1

    return best_assignment, best_max_load, loads, stats


# =====================================================================
#  SO SÁNH VỚI GREEDY VÀ EXACT SOLVER
# =====================================================================
def run_comparison(N, M, b, L, hc_result, hc_stats, time_limit_exact=30.0):
    """
    So sánh HC với Greedy và Exact (nếu có thể).
    In bảng so sánh đầy đủ theo các metric trong roadmap.
    """
    import sys as _sys

    # ── 1. Chạy Greedy ──────────────────────────────────────────────
    g_start = time.perf_counter()
    g_assign, g_max_load, g_loads, g_feasible = greedy_init(N, M, b, L)
    g_time = time.perf_counter() - g_start

    # ── 2. Chạy Exact (chỉ khi N nhỏ để tránh timeout) ─────────────
    opt_max_load = None
    exact_time = None
    exact_status = "SKIPPED"

    if N <= 200:  # Chỉ chạy exact cho test nhỏ/trung bình
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

    # ── 3. Kết quả HC ────────────────────────────────────────────────
    hc_assign, hc_max_load, hc_loads, _ = hc_result

    # ── 4. Lower Bound ───────────────────────────────────────────────
    LB = math.ceil(N * b / M)

    # ── 5. Tính Metrics ──────────────────────────────────────────────
    greedy_gap = (hc_max_load - g_max_load) / g_max_load * 100 if g_max_load > 0 else 0
    lb_gap     = (hc_max_load - LB) / LB * 100 if LB > 0 else 0
    opt_gap    = (hc_max_load - opt_max_load) / opt_max_load * 100 \
                 if opt_max_load is not None and opt_max_load > 0 else None

    g_lb_gap   = (g_max_load - LB) / LB * 100 if LB > 0 else 0

    # ── 6. In kết quả ────────────────────────────────────────────────
    sep = "=" * 70
    print(sep, file=_sys.stderr)
    print("  HILL CLIMBING — KẾT QUẢ SO SÁNH", file=_sys.stderr)
    print(sep, file=_sys.stderr)
    print(f"  Instance  : N={N}, M={M}, b={b}", file=_sys.stderr)
    print(f"  LB (⌈N×b/M⌉) = {LB}", file=_sys.stderr)
    print(sep, file=_sys.stderr)

    # Bảng max_load
    print(f"\n  {'Thuật toán':<20} {'max_load':>10} {'Thời gian':>12}", file=_sys.stderr)
    print(f"  {'-'*44}", file=_sys.stderr)
    print(f"  {'Greedy':<20} {g_max_load:>10} {g_time:>11.4f}s", file=_sys.stderr)
    print(f"  {'Hill Climbing':<20} {hc_max_load:>10} {hc_stats['total_time']:>11.4f}s", file=_sys.stderr)
    if opt_max_load is not None:
        print(f"  {'Exact (OPT)':<20} {opt_max_load:>10} {exact_time:>11.4f}s  [{exact_status}]",
              file=_sys.stderr)
    else:
        print(f"  {'Exact':<20} {'N/A':>10}  [{exact_status}]", file=_sys.stderr)

    # Bảng chất lượng lời giải
    print(f"\n  3.1 CHẤT LƯỢNG LỜI GIẢI:", file=_sys.stderr)
    print(f"  {'Metric':<30} {'Greedy':>10} {'HC':>10}", file=_sys.stderr)
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
    print(f"  Wall-clock time : {hc_stats['total_time']:.4f}s", file=_sys.stderr)
    print(f"  Time to best    : {hc_stats['time_to_best']:.4f}s", file=_sys.stderr)
    print(f"  Iterations      : {hc_stats['iterations']}", file=_sys.stderr)
    print(f"  Improvements    : {hc_stats['improvements']}", file=_sys.stderr)
    print(f"  Convergence iter: {hc_stats['convergence_iter']}", file=_sys.stderr)

    print(f"\n  Cải thiện so với Greedy: {g_max_load - hc_max_load:+d} (Greedy Gap = {greedy_gap:.2f}%)",
          file=_sys.stderr)
    print(sep, file=_sys.stderr)


def run_robustness_test(N, M, b, L, n_runs=10, max_iterations=100_000, time_limit_sec=60.0):
    """
    3.3 Chạy HC 10 lần với seed khác nhau, đo độ ổn định.
    (HC là deterministic, nhưng giữ API đồng nhất với SA)
    """
    import sys as _sys
    seeds = [42, 123, 456, 789, 1000, 2024, 314, 271, 999, 100]
    results = []

    print(f"\n  3.3 ĐỘ ỔN ĐỊNH — Chạy {n_runs} lần:", file=_sys.stderr)

    for run_idx in range(n_runs):
        seed = seeds[run_idx % len(seeds)]
        assignment, max_load, loads, stats = hill_climbing_with_loads(
            N, M, b, L, max_iterations=max_iterations, seed=seed,
            time_limit_sec=time_limit_sec
        )
        results.append(max_load)
        print(f"    Run {run_idx+1:2d} (seed={seed:4d}): max_load={max_load}  time={stats['total_time']:.3f}s",
              file=_sys.stderr)

    mean_val = statistics.mean(results)
    std_val  = statistics.stdev(results) if len(results) > 1 else 0.0
    best_val = min(results)
    worst_val= max(results)

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

    tracemalloc.start()
    start_time = time.perf_counter()

    assignment, max_load, loads, stats = hill_climbing_with_loads(
        N, M, b, L,
        max_iterations=200_000,
        time_limit_sec=120.0
    )

    end_time = time.perf_counter()
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # ── In thông tin ra stderr ───────────────────────────────────────
    print(f"[HC] Max Load: {max_load} | Time: {end_time - start_time:.3f}s "
          f"| Mem: {peak_mem/1024:.1f} KB", file=sys.stderr)

    # ── So sánh với Greedy và Exact ─────────────────────────────────
    hc_result = (assignment, max_load, loads, stats)
    run_comparison(N, M, b, L, hc_result, stats, time_limit_exact=30.0)

    # ── Chạy robustness test ─────────────────────────────────────────
    run_robustness_test(N, M, b, L, n_runs=10, max_iterations=200_000, time_limit_sec=30.0)

    # ── In output chuẩn ra stdout ────────────────────────────────────
    print_output(N, b, assignment)


if __name__ == "__main__":
    main()
