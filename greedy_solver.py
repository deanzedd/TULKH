"""
========================================================================
 THUẬT TOÁN 1: GREEDY (Tham lam) - Balanced Paper Assignment
========================================================================
 Ý tưởng:
   Duyệt qua từng bài báo, chọn b reviewer có tải thấp nhất trong
   danh sách L(i) để phân công. Đây là chiến lược "min-load-first".
 
 Độ phức tạp:
   O(N * |L_max| * log(|L_max|)) với |L_max| là kích thước danh sách
   reviewer lớn nhất.
========================================================================
"""

import time
import tracemalloc
import random
import json
import sys


def greedy_assign(N, M, b, L):
    """
    Greedy solver cho bài toán Balanced Paper Assignment.
    
    Params:
        N (int): Số lượng bài báo (đánh số 0..N-1)
        M (int): Số lượng reviewer (đánh số 0..M-1)
        b (int): Số reviewer bắt buộc cho mỗi bài báo
        L (list[list[int]]): L[i] = danh sách reviewer sẵn sàng chấm bài i
    
    Returns:
        assignment (list[list[int]]): assignment[i] = danh sách reviewer được phân cho bài i
        max_load (int): Tải trọng tối đa
        loads (list[int]): loads[j] = tải của reviewer j
        feasible (bool): True nếu tìm được lời giải khả thi
    """
    loads = [0] * M  # Tải hiện tại của mỗi reviewer
    assignment = [[] for _ in range(N)]
    feasible = True

    for i in range(N):
        candidates = L[i]
        if len(candidates) < b:
            feasible = False
            # Vẫn cố gắng gán tối đa có thể
            sorted_candidates = sorted(candidates, key=lambda r: loads[r])
            for r in sorted_candidates:
                assignment[i].append(r)
                loads[r] += 1
            continue

        # Sắp xếp candidates theo tải tăng dần, chọn b reviewer có tải thấp nhất
        sorted_candidates = sorted(candidates, key=lambda r: loads[r])
        chosen = sorted_candidates[:b]
        assignment[i] = chosen
        for r in chosen:
            loads[r] += 1

    max_load = max(loads) if loads else 0
    return assignment, max_load, loads, feasible


def generate_test_case(N, M, b, density=0.3, seed=None):
    """
    Sinh test case ngẫu nhiên.
    
    Params:
        N: Số bài báo
        M: Số reviewer
        b: Số reviewer/bài
        density: Xác suất mỗi reviewer sẵn sàng chấm mỗi bài
        seed: Random seed
    
    Returns:
        L: Danh sách reviewer sẵn sàng cho mỗi bài
    """
    if seed is not None:
        random.seed(seed)
    
    L = []
    for i in range(N):
        willing = []
        for j in range(M):
            if random.random() < density:
                willing.append(j)
        # Đảm bảo ít nhất b reviewer sẵn sàng
        while len(willing) < b:
            r = random.randint(0, M - 1)
            if r not in willing:
                willing.append(r)
        L.append(willing)
    return L


def compute_statistics(loads):
    """Tính các chỉ số thống kê về phân bổ tải."""
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


def run_single_test(test_name, N, M, b, density, seed):
    """Chạy một test case và in kết quả."""
    print(f"\n{'='*60}")
    print(f" TEST: {test_name}")
    print(f" N={N}, M={M}, b={b}, density={density}, seed={seed}")
    print(f"{'='*60}")

    L = generate_test_case(N, M, b, density, seed)

    # Đo thời gian và bộ nhớ
    tracemalloc.start()
    start_time = time.perf_counter()

    assignment, max_load, loads, feasible = greedy_assign(N, M, b, L)

    end_time = time.perf_counter()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    elapsed = end_time - start_time
    stats = compute_statistics(loads)

    print(f" Khả thi: {'Có' if feasible else 'KHÔNG'}")
    print(f" Max Load (mục tiêu tối ưu): {max_load}")
    print(f" Min Load: {stats.get('min_load', 'N/A')}")
    print(f" Avg Load: {stats.get('avg_load', 'N/A')}")
    print(f" Std Dev:  {stats.get('std_dev', 'N/A')}")
    print(f" Thời gian: {elapsed:.6f} giây")
    print(f" Bộ nhớ peak: {peak / 1024:.2f} KB")

    # Kiểm tra ràng buộc
    for i in range(N):
        assert len(assignment[i]) == b or not feasible, \
            f"Bài {i} chỉ có {len(assignment[i])} reviewer (cần {b})"
        for r in assignment[i]:
            assert r in L[i], f"Reviewer {r} không trong L({i})"

    # In phân công chi tiết cho test nhỏ
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
        "feasible": feasible,
        "max_load": max_load,
        "time_seconds": round(elapsed, 6),
        "peak_memory_kb": round(peak / 1024, 2),
        **stats,
    }


def main():
    print("╔" + "═"*58 + "╗")
    print("║   THUẬT TOÁN GREEDY - Balanced Paper Assignment          ║")
    print("║   Chiến lược: Min-Load-First                             ║")
    print("╚" + "═"*58 + "╝")

    test_cases = [
        # (tên, N, M, b, density, seed)
        ("Nhỏ - Cơ bản",         5,   3, 2, 0.6,  42),
        ("Nhỏ - Thưa",           5,   3, 2, 0.3,  42),
        ("Trung bình",           20,  10, 3, 0.4,  42),
        ("Trung bình - Dày đặc", 20,  10, 3, 0.7,  42),
        ("Lớn",                 100,  30, 3, 0.3,  42),
        ("Lớn - Dày đặc",      100,  30, 3, 0.6,  42),
        ("Rất lớn",             500, 100, 3, 0.2,  42),
        ("Stress test",        1000, 200, 4, 0.15, 42),
        ("Cực lớn",            2000, 300, 3, 0.1,  42),
    ]

    results = []
    for test_name, N, M, b, density, seed in test_cases:
        result = run_single_test(test_name, N, M, b, density, seed)
        results.append(result)

    # Bảng tổng hợp
    print("\n\n" + "="*80)
    print(" BẢNG TỔNG HỢP KẾT QUẢ GREEDY")
    print("="*80)
    header = f"{'Test':<25} {'N':>5} {'M':>5} {'b':>2} {'MaxLoad':>8} {'AvgLoad':>8} {'StdDev':>7} {'Time(s)':>10} {'Mem(KB)':>10}"
    print(header)
    print("-" * len(header))
    for r in results:
        print(f"{r['test_name']:<25} {r['N']:>5} {r['M']:>5} {r['b']:>2} "
              f"{r['max_load']:>8} {r['avg_load']:>8} {r['std_dev']:>7} "
              f"{r['time_seconds']:>10.6f} {r['peak_memory_kb']:>10.2f}")

    # Xuất JSON
    with open("greedy_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n Kết quả đã lưu vào greedy_results.json")


if __name__ == "__main__":
    main()
