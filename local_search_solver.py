"""
========================================================================
 THUẬT TOÁN 3: SIMULATED ANNEALING + TABU SEARCH + LNS
========================================================================
 Ý tưởng:
   Kết hợp 3 kỹ thuật Local Search mạnh:
   
   1. Simulated Annealing (SA): Chấp nhận lời giải xấu hơn với xác suất
      giảm dần theo nhiệt độ, giúp thoát local optima.
      
   2. Tabu Search: Lưu danh sách các move gần đây (tabu list) để tránh
      quay lại trạng thái cũ, khám phá không gian tìm kiếm hiệu quả.
      
   3. Large Neighborhood Search (LNS): Phá hủy và tái xây dựng một phần
      lời giải, cho phép nhảy xa trong không gian tìm kiếm.
   
   Các Toán tử (Operators):
     - SWAP: Hoán đổi reviewer giữa 2 bài báo
     - MOVE: Chuyển bài từ reviewer tải cao sang reviewer tải thấp
     - DESTROY-REPAIR (LNS): Xóa phân công của k bài, tái phân greedy
   
 Độ phức tạp:
   O(iterations * N * M) cho mỗi lần chạy, nhưng thường hội tụ nhanh
   hơn nhiều nhờ các toán tử thông minh.
========================================================================
"""

import time
import tracemalloc
import random
import math
import json
import copy
import sys
from collections import deque


def initial_greedy(N, M, b, L):
    """Tạo lời giải khởi tạo bằng greedy min-load."""
    loads = [0] * M
    assignment = [[] for _ in range(N)]
    
    for i in range(N):
        sorted_candidates = sorted(L[i], key=lambda r: loads[r])
        chosen = sorted_candidates[:b]
        assignment[i] = list(chosen)
        for r in chosen:
            loads[r] += 1
    
    return assignment, loads


def compute_max_load(loads):
    """Tính max load."""
    return max(loads) if loads else 0


def compute_objective(loads):
    """
    Hàm mục tiêu mở rộng: ưu tiên giảm max_load, 
    sau đó giảm tổng bình phương tải (để cân bằng).
    """
    max_l = max(loads) if loads else 0
    sum_sq = sum(l * l for l in loads)
    return (max_l, sum_sq)


# =====================================================================
#  TOÁN TỬ 1: SWAP - Hoán đổi reviewer giữa 2 bài
# =====================================================================
def operator_swap(assignment, loads, N, M, b, L):
    """
    Chọn bài có reviewer tải cao nhất, thử swap với bài khác
    để giảm max load.
    """
    max_load = max(loads)
    # Tìm reviewer có tải = max_load
    heavy_reviewers = [j for j in range(M) if loads[j] == max_load]
    
    if not heavy_reviewers:
        return False

    r_heavy = random.choice(heavy_reviewers)
    
    # Tìm các bài được gán cho r_heavy
    papers_of_heavy = [i for i in range(N) if r_heavy in assignment[i]]
    
    if not papers_of_heavy:
        return False
    
    paper_i = random.choice(papers_of_heavy)
    
    # Thử swap r_heavy ra khỏi paper_i, thay bằng reviewer nhẹ hơn
    for r_light in L[paper_i]:
        if r_light not in assignment[paper_i] and loads[r_light] < loads[r_heavy] - 1:
            # Thực hiện swap
            assignment[paper_i].remove(r_heavy)
            assignment[paper_i].append(r_light)
            loads[r_heavy] -= 1
            loads[r_light] += 1
            return True
    
    return False


# =====================================================================
#  TOÁN TỬ 2: MOVE - Chuyển bài từ reviewer nặng sang nhẹ
# =====================================================================
def operator_move(assignment, loads, N, M, b, L):
    """
    Di chuyển một bài từ reviewer tải cao nhất sang reviewer tải 
    thấp nhất (nếu khả thi trong L[i]).
    """
    max_load = max(loads)
    min_load = min(loads)
    
    if max_load - min_load <= 1:
        return False  # Đã khá cân bằng
    
    heavy_reviewers = [j for j in range(M) if loads[j] == max_load]
    light_reviewers = set(j for j in range(M) if loads[j] <= min_load + 1)
    
    r_heavy = random.choice(heavy_reviewers)
    papers_of_heavy = [i for i in range(N) if r_heavy in assignment[i]]
    
    random.shuffle(papers_of_heavy)
    
    for paper_i in papers_of_heavy:
        eligible_light = [r for r in L[paper_i] 
                         if r in light_reviewers and r not in assignment[paper_i]]
        if eligible_light:
            r_light = min(eligible_light, key=lambda r: loads[r])
            assignment[paper_i].remove(r_heavy)
            assignment[paper_i].append(r_light)
            loads[r_heavy] -= 1
            loads[r_light] += 1
            return True
    
    return False


# =====================================================================
#  TOÁN TỬ 3: DESTROY-REPAIR (LNS)
# =====================================================================
def operator_lns(assignment, loads, N, M, b, L, destroy_ratio=0.2):
    """
    Large Neighborhood Search:
    1. DESTROY: Xóa phân công của một tỷ lệ bài ngẫu nhiên
    2. REPAIR: Tái phân công bằng greedy min-load
    """
    k = max(1, int(N * destroy_ratio))
    papers_to_destroy = random.sample(range(N), k)
    
    # Lưu trạng thái cũ
    old_assignment = [list(assignment[i]) for i in papers_to_destroy]
    old_loads = list(loads)
    
    # DESTROY
    for i in papers_to_destroy:
        for r in assignment[i]:
            loads[r] -= 1
        assignment[i] = []
    
    # REPAIR (greedy min-load)
    for i in papers_to_destroy:
        sorted_candidates = sorted(L[i], key=lambda r: loads[r])
        chosen = sorted_candidates[:b]
        assignment[i] = list(chosen)
        for r in chosen:
            loads[r] += 1
    
    # Kiểm tra có cải thiện không
    new_obj = compute_objective(loads)
    old_obj = compute_objective(old_loads)
    
    if new_obj <= old_obj:
        return True  # Chấp nhận cải thiện
    else:
        # Khôi phục (sẽ được xử lý bởi SA acceptance)
        # Trả về True và để SA quyết định
        return True


# =====================================================================
#  MAIN SOLVER: Simulated Annealing + Tabu + LNS
# =====================================================================
def local_search_solve(N, M, b, L, max_iterations=10000, 
                       initial_temp=10.0, cooling_rate=0.995,
                       tabu_tenure=20, lns_frequency=50,
                       destroy_ratio=0.2, seed=None):
    """
    Solver kết hợp SA + Tabu Search + LNS.
    
    Params:
        N, M, b, L: Tham số bài toán
        max_iterations: Số vòng lặp tối đa
        initial_temp: Nhiệt độ ban đầu (SA)
        cooling_rate: Tốc độ giảm nhiệt (SA)
        tabu_tenure: Độ dài tabu list
        lns_frequency: Mỗi bao nhiêu iteration thì chạy LNS
        destroy_ratio: Tỷ lệ phá hủy trong LNS
    
    Returns:
        best_assignment, best_max_load, best_loads, history
    """
    if seed is not None:
        random.seed(seed)

    # Khởi tạo
    assignment, loads = initial_greedy(N, M, b, L)
    best_assignment = [list(a) for a in assignment]
    best_loads = list(loads)
    best_obj = compute_objective(loads)
    best_max_load = compute_max_load(loads)
    
    # Tabu list: lưu các move gần đây (paper, old_reviewer, new_reviewer)
    tabu_list = deque(maxlen=tabu_tenure)
    
    # SA parameters
    temperature = initial_temp
    
    # History tracking
    history = {
        "iterations": [],
        "max_loads": [],
        "temperatures": [],
        "accepted": 0,
        "rejected": 0,
        "improved": 0,
        "operator_stats": {
            "swap": {"tried": 0, "success": 0},
            "move": {"tried": 0, "success": 0},
            "lns": {"tried": 0, "success": 0},
        }
    }

    for iteration in range(max_iterations):
        # Lưu trạng thái hiện tại
        prev_assignment = [list(a) for a in assignment]
        prev_loads = list(loads)
        prev_obj = compute_objective(loads)
        
        # Chọn toán tử
        if iteration > 0 and iteration % lns_frequency == 0:
            # LNS phá hủy-sửa chữa
            op_name = "lns"
            history["operator_stats"]["lns"]["tried"] += 1
            success = operator_lns(assignment, loads, N, M, b, L, destroy_ratio)
        else:
            # Chọn ngẫu nhiên giữa SWAP và MOVE (ưu tiên SWAP)
            if random.random() < 0.6:
                op_name = "swap"
                history["operator_stats"]["swap"]["tried"] += 1
                success = operator_swap(assignment, loads, N, M, b, L)
            else:
                op_name = "move"
                history["operator_stats"]["move"]["tried"] += 1
                success = operator_move(assignment, loads, N, M, b, L)
        
        if not success:
            continue
        
        new_obj = compute_objective(loads)
        
        # Kiểm tra tabu
        # (Đơn giản hóa: chỉ dùng max_load làm state key)
        state_key = tuple(sorted(loads))
        is_tabu = state_key in tabu_list
        
        # Quyết định chấp nhận (SA + Tabu)
        delta = new_obj[0] - prev_obj[0]  # So sánh max_load
        
        accept = False
        if delta < 0:
            # Cải thiện → luôn chấp nhận (bỏ qua tabu nếu aspiration)
            accept = True
            history["improved"] += 1
            history["operator_stats"][op_name]["success"] += 1
        elif delta == 0 and new_obj[1] < prev_obj[1]:
            # Max load giữ nguyên nhưng cân bằng hơn
            accept = not is_tabu
            if accept:
                history["operator_stats"][op_name]["success"] += 1
        elif temperature > 0.01:
            # SA: chấp nhận xấu hơn với xác suất
            prob = math.exp(-delta / temperature) if delta > 0 else 1.0
            if random.random() < prob and not is_tabu:
                accept = True
        
        if accept:
            history["accepted"] += 1
            tabu_list.append(state_key)
            
            # Cập nhật best
            if new_obj < best_obj:
                best_assignment = [list(a) for a in assignment]
                best_loads = list(loads)
                best_obj = new_obj
                best_max_load = compute_max_load(loads)
        else:
            # Khôi phục
            history["rejected"] += 1
            for i in range(N):
                assignment[i] = prev_assignment[i]
            for j in range(M):
                loads[j] = prev_loads[j]
        
        # Giảm nhiệt
        temperature *= cooling_rate
        
        # Ghi lịch sử (mỗi 100 iterations)
        if iteration % 100 == 0:
            history["iterations"].append(iteration)
            history["max_loads"].append(compute_max_load(loads))
            history["temperatures"].append(round(temperature, 4))

    return best_assignment, best_max_load, best_loads, history


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
    """Tính thống kê."""
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


def run_single_test(test_name, N, M, b, density, seed, max_iter=5000):
    """Chạy một test case."""
    print(f"\n{'='*60}")
    print(f" TEST: {test_name}")
    print(f" N={N}, M={M}, b={b}, density={density}, seed={seed}")
    print(f"{'='*60}")

    L = generate_test_case(N, M, b, density, seed)

    # Greedy ban đầu để so sánh
    greedy_assign, greedy_loads = initial_greedy(N, M, b, L)
    greedy_max = compute_max_load(greedy_loads)

    tracemalloc.start()
    start_time = time.perf_counter()

    best_assignment, best_max_load, best_loads, history = local_search_solve(
        N, M, b, L, 
        max_iterations=max_iter,
        initial_temp=max(10.0, N * 0.1),
        cooling_rate=0.997,
        tabu_tenure=min(50, N),
        lns_frequency=max(20, max_iter // 50),
        destroy_ratio=min(0.3, 10.0 / N),
        seed=seed + 1000
    )

    end_time = time.perf_counter()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    elapsed = end_time - start_time
    stats = compute_statistics(best_loads)
    improvement = greedy_max - best_max_load

    print(f" Greedy Max Load:    {greedy_max}")
    print(f" LS Best Max Load:   {best_max_load}")
    print(f" Cải thiện:          {improvement} ({improvement/greedy_max*100:.1f}%)" if greedy_max > 0 else "")
    print(f" Min Load: {stats.get('min_load', 'N/A')}")
    print(f" Avg Load: {stats.get('avg_load', 'N/A')}")
    print(f" Std Dev:  {stats.get('std_dev', 'N/A')}")
    print(f" Thời gian: {elapsed:.6f} giây")
    print(f" Bộ nhớ peak: {peak / 1024:.2f} KB")
    
    # Thống kê toán tử
    op_stats = history["operator_stats"]
    print(f"\n Thống kê toán tử:")
    for op_name, op_data in op_stats.items():
        tried = op_data["tried"]
        success = op_data["success"]
        rate = (success / tried * 100) if tried > 0 else 0
        print(f"   {op_name.upper():>6}: thử {tried:>6}, thành công {success:>6} ({rate:.1f}%)")
    
    print(f" Chấp nhận: {history['accepted']}, Từ chối: {history['rejected']}, Cải thiện: {history['improved']}")

    # Kiểm tra ràng buộc
    for i in range(N):
        assert len(best_assignment[i]) == b, \
            f"Bài {i} có {len(best_assignment[i])} reviewer (cần {b})"
        for r in best_assignment[i]:
            assert r in L[i], f"Reviewer {r} không trong L({i})"

    if N <= 10:
        print("\n Phân công chi tiết:")
        for i in range(N):
            print(f"   Bài {i}: reviewers {best_assignment[i]}")
        print(f"\n Tải từng reviewer:")
        for j in range(M):
            bar = '█' * best_loads[j]
            print(f"   Reviewer {j}: {best_loads[j]:3d} | {bar}")

    return {
        "test_name": test_name,
        "N": N, "M": M, "b": b,
        "greedy_max_load": greedy_max,
        "ls_max_load": best_max_load,
        "improvement": improvement,
        "time_seconds": round(elapsed, 6),
        "peak_memory_kb": round(peak / 1024, 2),
        "accepted": history["accepted"],
        "rejected": history["rejected"],
        "improved": history["improved"],
        "operator_stats": op_stats,
        **stats,
    }


def main():
    print("╔" + "═"*58 + "╗")
    print("║   LOCAL SEARCH: SA + Tabu Search + LNS                  ║")
    print("║   Balanced Paper Assignment                             ║")
    print("╚" + "═"*58 + "╝")

    test_cases = [
        # (tên, N, M, b, density, seed, max_iterations)
        ("Nhỏ - Cơ bản",         5,   3, 2, 0.6,  42, 2000),
        ("Nhỏ - Thưa",           5,   3, 2, 0.3,  42, 2000),
        ("Trung bình",           20,  10, 3, 0.4,  42, 5000),
        ("Trung bình - Dày đặc", 20,  10, 3, 0.7,  42, 5000),
        ("Lớn",                 100,  30, 3, 0.3,  42, 10000),
        ("Lớn - Dày đặc",      100,  30, 3, 0.6,  42, 10000),
        ("Rất lớn",             500, 100, 3, 0.2,  42, 15000),
        ("Stress test",        1000, 200, 4, 0.15, 42, 20000),
        ("Cực lớn",            2000, 300, 3, 0.1,  42, 20000),
    ]

    results = []
    for test_name, N, M, b, density, seed, max_iter in test_cases:
        result = run_single_test(test_name, N, M, b, density, seed, max_iter)
        results.append(result)

    # Bảng tổng hợp
    print("\n\n" + "="*100)
    print(" BẢNG TỔNG HỢP KẾT QUẢ LOCAL SEARCH (SA + Tabu + LNS)")
    print("="*100)
    header = (f"{'Test':<25} {'N':>5} {'M':>5} {'b':>2} "
              f"{'Greedy':>7} {'LS':>5} {'Δ':>3} {'Time(s)':>10} {'Mem(KB)':>10}")
    print(header)
    print("-" * len(header))
    for r in results:
        print(f"{r['test_name']:<25} {r['N']:>5} {r['M']:>5} {r['b']:>2} "
              f"{r['greedy_max_load']:>7} {r['ls_max_load']:>5} "
              f"{r['improvement']:>+3} "
              f"{r['time_seconds']:>10.6f} {r['peak_memory_kb']:>10.2f}")

    with open("localsearch_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n Kết quả đã lưu vào localsearch_results.json")


if __name__ == "__main__":
    main()
