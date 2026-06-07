import time
import tracemalloc
import sys
from ortools.sat.python import cp_model


def input():
    """
    Doc du lieu tu stdin (terminal), tung dong mot.
    Doc dong 1 lay N, roi doc dung N dong tiep theo.
    Chuong trinh tu dong chay ngay sau dong cuoi cung - khong can Ctrl+Z.

    Format:
      Dong 1: N M b
      Dong i+1 (i=1..N): k r1 r2 ... rk  (reviewer 1-indexed)
    """
    # Dong 1: N M b
    first_line = sys.stdin.readline()
    N, M, b = map(int, first_line.strip().split())

    # Doc dung N dong, moi dong la mot paper
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
    print(N)
    for i in range(N):
        # do lúc xử lí mảng ta quy ước index từ 0
        # nhưng đầu ra đề bài yêu cầu index từ 1 
        reviewer_1idx = [r+1 for r in assignment[i]] 
        print(b, *reviewer_1idx)


def exact_GG_ORTOI(N, M, b, L, time_limit_sec=60):
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
    model = cp_model.CpModel()
    # tạo ma trận assign giữa paper i và reviewer j
    x = {}
    for i in range(N):
        for j in L[i]:
            x[i, j] = model.NewBoolVar(f"x_{i}_{j}")

    # thêm các ràng buộc
    for i in range(N):
        model.Add(sum(x[i, j] for j in L[i]) == b)

    # biến mục tiêu max_load
    max_load_var = model.NewIntVar(0, N*b, "max_load")

    # tải tối đa của mỗi reviewer
    for j in range(M):
        papers_for_j = [i for i in range(N) if j in L[i]]
        if papers_for_j:
            load_j = sum(x[i, j] for i in papers_for_j)
            model.Add(load_j <= max_load_var)

    # hàm mục tiêu 
    model.Minimize(max_load_var)

    solver = cp_model.CpSolver()
    #đặt time limit
    solver.parameters.max_time_in_seconds = time_limit_sec
    solver.parameters.num_search_workers = 4

    status = solver.Solve(model)
    status_str = solver.StatusName(status)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        assignment = [[] for _ in range(N)]
        load = [0] * M

        for i in range(N):
            for j in L[i]:
                if solver.Value(x[i,j]) == 1:
                    assignment[i].append(j)
                    load[j]+=1

        max_load = max(load) if load else 0
        return assignment, max_load, load, status_str
    else:
        return None, None, None, status_str
        
        

def main():
    N, M, b, L = input()

    tracemalloc.start()
    start_time = time.perf_counter()
    assignments, max_load, load, status_str = exact_GG_ORTOI(N, M, b, L, time_limit_sec=600)
    end_time = time.perf_counter()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"Status: {status_str} | Max Load: {max_load} | Time: {end_time - start_time:.3f}s", file=sys.stderr)
    if assignments is not None:
        print_output(N, b, assignments)
    else:
        print("INFEASIBLE", file=sys.stderr)


if __name__ == "__main__":
    main()