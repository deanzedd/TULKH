"""
========================================================================
 THUẬT TOÁN 2: EXACT SOLVER - Google OR-Tools (CP-SAT)
========================================================================
 Ý tưởng:
   Mô hình bài toán dưới dạng Integer Programming / Constraint 
   Programming và sử dụng Google OR-Tools CP-SAT solver để tìm 
   lời giải tối ưu toàn cục (optimal).
   
   Biến quyết định: x[i][j] ∈ {0, 1} - bài i có được gán cho reviewer j?
   
   Ràng buộc:
     - ∑_j x[i][j] = b  ∀i (mỗi bài có đúng b reviewer)
     - x[i][j] = 0 nếu j ∉ L(i) (chỉ gán reviewer sẵn sàng)
   
   Hàm mục tiêu: min(max_load) với max_load = max_j(∑_i x[i][j])
   
 Độ phức tạp:
   NP-hard trong trường hợp tổng quát, nhưng CP-SAT solver có thể
   giải được các instance vừa phải trong thời gian hợp lý.
========================================================================
"""

import time
import tracemalloc
import random
import json
import sys

try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False
    print("⚠ OR-Tools chưa được cài đặt. Chạy: pip install ortools", file=sys.stderr)
    print("  Đang sử dụng fallback ILP solver đơn giản...\n", file=sys.stderr)


# =====================================================================
#  HÀM ĐỌC / GHI THEO FORMAT ĐỀ BÀI
# =====================================================================
def parse_input(source=None):
    """
    Đọc input theo format:
      Dòng 1: N M b
      Dòng i+1 (i=1..N): k r1 r2 ... rk  (reviewer 1-indexed)

    Params:
        source: None = đọc từ stdin; str = đường dẫn file
    Returns:
        N, M, b, L  (L dùng 0-indexed nội bộ)
    """
    if source is None:
        lines = sys.stdin.read().split('\n')
    else:
        with open(source, encoding='utf-8') as f:
            lines = f.read().split('\n')

    lines = [l.strip() for l in lines if l.strip()]
    idx = 0
    N, M, b = map(int, lines[idx].split())
    idx += 1
    L = []
    for i in range(N):
        parts = list(map(int, lines[idx].split()))
        idx += 1
        k = parts[0]
        # 1-indexed → 0-indexed
        reviewers = [r - 1 for r in parts[1: k + 1]]
        L.append(reviewers)
    return N, M, b, L


def print_output(N, b, assignment):
    """
    In kết quả theo format:
      Dòng 1: N
      Dòng i+1: b r1 r2 ... rb  (reviewer 1-indexed)
    """
    print(N)
    for i in range(N):
        reviewers_1idx = [r + 1 for r in assignment[i]]
        print(b, *reviewers_1idx)



def exact_solve_ortools(N, M, b, L, time_limit_seconds=60):
    """
    Exact solver sử dụng Google OR-Tools CP-SAT.
    
    Params:
        N (int): Số bài báo
        M (int): Số reviewer
        b (int): Số reviewer/bài
        L (list[list[int]]): Danh sách reviewer sẵn sàng cho mỗi bài
        time_limit_seconds (int): Giới hạn thời gian
    
    Returns:
        assignment (list[list[int]]): Phân công
        max_load (int): Tải tối đa (tối ưu)
        loads (list[int]): Tải từng reviewer
        status_str (str): Trạng thái solver
    """
    if not ORTOOLS_AVAILABLE:
        return exact_solve_fallback(N, M, b, L, time_limit_seconds)

    model = cp_model.CpModel()

    # ----- Biến quyết định -----
    # x[i][j] = 1 nếu bài i được gán cho reviewer j
    x = {}
    for i in range(N):
        for j in L[i]:
            x[i, j] = model.NewBoolVar(f"x_{i}_{j}")

    # ----- Ràng buộc: mỗi bài có đúng b reviewer -----
    for i in range(N):
        model.Add(sum(x[i, j] for j in L[i]) == b)

    # ----- Biến mục tiêu: max_load -----
    max_load_var = model.NewIntVar(0, N * b, "max_load")
    
    # Tải của mỗi reviewer
    for j in range(M):
        papers_for_j = [i for i in range(N) if j in L[i]]
        if papers_for_j:
            load_j = sum(x[i, j] for i in papers_for_j)
            model.Add(load_j <= max_load_var)

    # ----- Hàm mục tiêu: minimize max_load -----
    model.Minimize(max_load_var)

    # ----- Giải -----
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    solver.parameters.num_search_workers = 4  # Đa luồng

    status = solver.Solve(model)
    status_str = solver.StatusName(status)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        assignment = [[] for _ in range(N)]
        loads = [0] * M
        
        for i in range(N):
            for j in L[i]:
                if solver.Value(x[i, j]) == 1:
                    assignment[i].append(j)
                    loads[j] += 1
        
        max_load = max(loads) if loads else 0
        return assignment, max_load, loads, status_str
    else:
        return [[] for _ in range(N)], -1, [0] * M, status_str


def exact_solve_fallback(N, M, b, L, time_limit_seconds=60):
    """
    Fallback solver đơn giản khi không có OR-Tools.
    Sử dụng phương pháp Binary Search + Flow-based check.
    """
    from collections import deque

    def can_achieve_max_load(target_max_load):
        """
        Kiểm tra xem có thể phân công sao cho max load <= target_max_load.
        Dùng thuật toán max-flow (BFS - Edmonds-Karp).
        
        Đồ thị luồng:
          Source -> Paper_i (capacity = b)
          Paper_i -> Reviewer_j nếu j ∈ L(i) (capacity = 1)
          Reviewer_j -> Sink (capacity = target_max_load)
        """
        # Nodes: 0=source, 1..N=papers, N+1..N+M=reviewers, N+M+1=sink
        source = 0
        sink = N + M + 1
        total_nodes = N + M + 2
        
        # Adjacency list + capacity
        graph = [dict() for _ in range(total_nodes)]
        
        def add_edge(u, v, cap):
            graph[u][v] = graph[u].get(v, 0) + cap
            if v not in graph[v]:
                graph[v][u] = 0

        # Source -> Papers
        for i in range(N):
            add_edge(source, i + 1, b)

        # Papers -> Reviewers
        for i in range(N):
            for j in L[i]:
                add_edge(i + 1, N + 1 + j, 1)

        # Reviewers -> Sink
        for j in range(M):
            add_edge(N + 1 + j, sink, target_max_load)

        # Edmonds-Karp max flow
        def bfs():
            parent = [-1] * total_nodes
            parent[source] = source
            queue = deque([source])
            while queue:
                u = queue.popleft()
                for v, cap in graph[u].items():
                    if parent[v] == -1 and cap > 0:
                        parent[v] = u
                        if v == sink:
                            return parent
                        queue.append(v)
            return None

        total_flow = 0
        while True:
            parent = bfs()
            if parent is None:
                break
            # Tìm bottleneck
            path_flow = float('inf')
            v = sink
            while v != source:
                u = parent[v]
                path_flow = min(path_flow, graph[u][v])
                v = u
            # Cập nhật
            v = sink
            while v != source:
                u = parent[v]
                graph[u][v] -= path_flow
                graph[v][u] = graph[v].get(u, 0) + path_flow
                v = u
            total_flow += path_flow

        return total_flow == N * b

    # Binary search trên max_load
    lo, hi = 1, N * b
    best_max_load = hi
    
    while lo <= hi:
        mid = (lo + hi) // 2
        if can_achieve_max_load(mid):
            best_max_load = mid
            hi = mid - 1
        else:
            lo = mid + 1

    # Tái dựng lời giải với best_max_load
    # Chạy lại flow và trích assignment
    from collections import deque as dq

    source = 0
    sink = N + M + 1
    total_nodes = N + M + 2
    graph = [dict() for _ in range(total_nodes)]

    def add_edge(u, v, cap):
        graph[u][v] = graph[u].get(v, 0) + cap
        if v not in graph[v]:
            graph[v][u] = 0

    for i in range(N):
        add_edge(source, i + 1, b)
    for i in range(N):
        for j in L[i]:
            add_edge(i + 1, N + 1 + j, 1)
    for j in range(M):
        add_edge(N + 1 + j, sink, best_max_load)

    def bfs():
        parent = [-1] * total_nodes
        parent[source] = source
        queue = dq([source])
        while queue:
            u = queue.popleft()
            for v, cap in graph[u].items():
                if parent[v] == -1 and cap > 0:
                    parent[v] = u
                    if v == sink:
                        return parent
                    queue.append(v)
        return None

    total_flow = 0
    while True:
        parent = bfs()
        if parent is None:
            break
        path_flow = float('inf')
        v = sink
        while v != source:
            u = parent[v]
            path_flow = min(path_flow, graph[u][v])
            v = u
        v = sink
        while v != source:
            u = parent[v]
            graph[u][v] -= path_flow
            graph[v][u] = graph[v].get(u, 0) + path_flow
            v = u
        total_flow += path_flow

    # Trích xuất assignment
    assignment = [[] for _ in range(N)]
    loads = [0] * M
    for i in range(N):
        for j in L[i]:
            # Nếu edge paper->reviewer đã dùng hết capacity (ban đầu = 1)
            remaining = graph[i + 1].get(N + 1 + j, 0)
            if remaining == 0:  # capacity đã dùng
                assignment[i].append(j)
                loads[j] += 1

    feasible = total_flow == N * b
    status_str = "OPTIMAL (fallback)" if feasible else "INFEASIBLE (fallback)"
    return assignment, best_max_load, loads, status_str


def generate_test_case(N, M, b, density=0.3, seed=None):
    """Sinh test case ngẫu nhiên."""
    if seed is not None:
        random.seed(seed)
    L = []
    for i in range(N):
        willing = []
        for j in range(M):
            if random.random() < density:
                willing.append(j)
        while len(willing) < b:
            r = random.randint(0, M - 1)
            if r not in willing:
                willing.append(r)
        L.append(willing)
    return L


def compute_statistics(loads):
    """Tính thống kê phân bổ tải."""
    if not loads:
        return {}
    avg = sum(loads) / len(loads)
    variance = sum((x - avg) ** 2 for x in loads) / len(loads)
    return {
        "max_load": max(loads),
        "min_load": min(loads),
        "avg_load": round(avg, 2),
        "std_dev": round(variance ** 0.5, 2),
        "total_assignments": sum(loads),
    }


def run_single_test(test_name, N, M, b, density, seed, time_limit=60):
    """Chạy một test case."""
    print(f"\n{'='*60}")
    print(f" TEST: {test_name}")
    print(f" N={N}, M={M}, b={b}, density={density}, seed={seed}")
    print(f"{'='*60}")

    L = generate_test_case(N, M, b, density, seed)

    tracemalloc.start()
    start_time = time.perf_counter()

    assignment, max_load, loads, status = exact_solve_ortools(
        N, M, b, L, time_limit_seconds=time_limit
    )

    end_time = time.perf_counter()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    elapsed = end_time - start_time
    stats = compute_statistics(loads)

    print(f" Trạng thái solver: {status}")
    print(f" Max Load (tối ưu): {max_load}")
    print(f" Min Load: {stats.get('min_load', 'N/A')}")
    print(f" Avg Load: {stats.get('avg_load', 'N/A')}")
    print(f" Std Dev:  {stats.get('std_dev', 'N/A')}")
    print(f" Thời gian: {elapsed:.6f} giây")
    print(f" Bộ nhớ peak: {peak / 1024:.2f} KB")

    # Kiểm tra tính đúng đắn
    if max_load >= 0:
        for i in range(N):
            if len(assignment[i]) != b:
                print(f" ⚠ Bài {i} chỉ có {len(assignment[i])} reviewer")
            for r in assignment[i]:
                assert r in L[i], f"Reviewer {r} không trong L({i})"

    if N <= 10:
        print("\n Phân công chi tiết:")
        for i in range(N):
            print(f"   Bài {i}: reviewers {assignment[i]}")
        print(f"\n Tải từng reviewer:")
        for j in range(M):
            bar = '█' * loads[j]
            print(f"   Reviewer {j}: {loads[j]:3d} | {bar}")

    return {
        "test_name": test_name,
        "N": N, "M": M, "b": b,
        "solver_status": status,
        "max_load": max_load,
        "time_seconds": round(elapsed, 6),
        "peak_memory_kb": round(peak / 1024, 2),
        **stats,
    }


def main():
    """
    Hai chế độ:
      1. python exact_solver.py <file>   -> đọc input từ file, in output theo format đề bài
      2. python exact_solver.py          -> chạy 9 test case ngẫu nhiên (batch benchmark)
    """
    # ── Chế độ 1: Đọc input từ file hoặc stdin ──────────────────────
    if len(sys.argv) >= 2:
        input_file = sys.argv[1]
        print(f"[Exact] Đọc input từ: {input_file}", file=sys.stderr)
        N, M, b, L = parse_input(input_file)

        tracemalloc.start()
        start_time = time.perf_counter()
        assignment, max_load, loads, status = exact_solve_ortools(N, M, b, L, time_limit_seconds=300)
        end_time = time.perf_counter()
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print(f"[Exact] Status = {status} | Max Load = {max_load}", file=sys.stderr)
        print(f"[Exact] Time = {end_time - start_time:.6f}s | Memory = {peak/1024:.2f} KB", file=sys.stderr)
        print_output(N, b, assignment)
        return

    # ── Chế độ 2: Batch benchmark với test case ngẫu nhiên ──────────
    print("╔" + "═"*58 + "╗")
    print("║   EXACT SOLVER - Google OR-Tools CP-SAT                 ║")
    print("║   Balanced Paper Assignment (Optimal Solution)          ║")
    print("╚" + "═"*58 + "╝")

    if ORTOOLS_AVAILABLE:
        print(" ✓ OR-Tools đã sẵn sàng")
    else:
        print(" ⚠ Đang dùng fallback solver (Binary Search + Max Flow)")

    test_cases = [
        # (tên, N, M, b, density, seed, time_limit)
        ("Nhỏ - Cơ bản",         5,   3, 2, 0.6,  42, 10),
        ("Nhỏ - Thưa",           5,   3, 2, 0.3,  42, 10),
        ("Trung bình",           20,  10, 3, 0.4,  42, 30),
        ("Trung bình - Dày đặc", 20,  10, 3, 0.7,  42, 30),
        ("Lớn",                 100,  30, 3, 0.3,  42, 60),
        ("Lớn - Dày đặc",      100,  30, 3, 0.6,  42, 60),
        ("Rất lớn",             500, 100, 3, 0.2,  42, 120),
        ("Stress test",        1000, 200, 4, 0.15, 42, 180),
        ("Cực lớn",            2000, 300, 3, 0.1,  42, 300),
    ]

    results = []
    for test_name, N, M, b, density, seed, tl in test_cases:
        result = run_single_test(test_name, N, M, b, density, seed, tl)
        results.append(result)

    print("\n\n" + "="*90)
    print(" BẢNG TỔNG HỢP KẾT QUẢ EXACT SOLVER")
    print("="*90)
    header = f"{'Test':<25} {'N':>5} {'M':>5} {'b':>2} {'Status':<12} {'MaxLoad':>8} {'Time(s)':>10} {'Mem(KB)':>10}"
    print(header)
    print("-" * len(header))
    for r in results:
        print(f"{r['test_name']:<25} {r['N']:>5} {r['M']:>5} {r['b']:>2} "
              f"{r['solver_status']:<12} {r['max_load']:>8} "
              f"{r['time_seconds']:>10.6f} {r['peak_memory_kb']:>10.2f}")

    with open("exact_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n Kết quả đã lưu vào exact_results.json")


if __name__ == "__main__":
    main()
