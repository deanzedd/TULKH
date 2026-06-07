from pathlib import Path

from Hill_climbing import hill_climbing_with_loads, greedy_init
from simulated_anneling import simulated_annealing

import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
from local_search_solver import local_search_solve  # noqa: E402


def generate_chain_plateau_case(G=50):
    """
    Sinh test "chain plateau" để tạo khoảng cách lớn giữa HC và SA-based LS.

    Với b = 1, mỗi paper có đúng 2 reviewer liên tiếp trên một chuỗi:
        [i, i+1]

    Các nhóm paper được sắp theo thứ tự từ cuối chuỗi về đầu chuỗi để Greedy tạo
    phân bố tải:
        [G, G-1, G-2, ..., 2, 1, 0]

    Hill Climbing bị kẹt tại reviewer đầu tiên có tải G, vì chuyển một bài từ
    reviewer 0 sang reviewer 1 sẽ làm reviewer 1 tăng từ G-1 lên G, tức max_load
    không giảm ngay. SA-based local search có thể đi qua plateau này.
    """
    N = G * (G + 1) // 2
    M = G + 1
    b = 1
    L = []

    for i in range(G - 1, -1, -1):
        for _ in range(G - i):
            L.append([i, i + 1])

    return N, M, b, L


def write_input_file(path, N, M, b, L):
    lines = [f"{N} {M} {b}"]
    for reviewers in L:
        one_based = [str(r + 1) for r in reviewers]
        lines.append(" ".join([str(len(reviewers))] + one_based))
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    N, M, b, L = generate_chain_plateau_case(G=50)
    output_path = Path(__file__).with_name("sa_vs_hc_gap_6_case.txt")
    write_input_file(output_path, N, M, b, L)

    _, greedy_max, greedy_loads, _ = greedy_init(N, M, b, L)

    _, hc_max, hc_loads, _ = hill_climbing_with_loads(
        N,
        M,
        b,
        L,
        max_iterations=100_000,
        time_limit_sec=2.0,
    )

    # SA thuần thường cũng cải thiện HC, nhưng gap lớn hơn và ổn định hơn
    # khi dùng đúng solver hybrid của local_search_solver.py.
    _, pure_sa_max, _, _ = simulated_annealing(
        N,
        M,
        b,
        L,
        T_init=150.0,
        cooling=0.9995,
        T_min=0.01,
        iters_per_temp=max(800, N * 2),
        max_iterations=1_500_000,
        seed=7,
        time_limit_sec=5.0,
    )

    _, hybrid_sa_max, hybrid_loads, _ = local_search_solve(
        N,
        M,
        b,
        L,
        max_iterations=12_000,
        initial_temp=100.0,
        cooling_rate=0.999,
        tabu_tenure=100,
        lns_frequency=50,
        destroy_ratio=min(0.3, 30 / N),
        seed=0,
    )

    print("Generated testcase")
    print("==================")
    print(output_path.resolve())
    print()
    print(f"N={N}, M={M}, b={b}")
    print()
    print("Result comparison")
    print("=================")
    print(f"Greedy max_load        : {greedy_max}")
    print(f"HC max_load            : {hc_max}")
    print(f"Pure SA max_load       : {pure_sa_max}")
    print(f"SA+Tabu+LNS max_load   : {hybrid_sa_max}")
    print()
    print(f"Pure SA gap vs HC      : {hc_max - pure_sa_max}")
    print(f"Hybrid SA gap vs HC    : {hc_max - hybrid_sa_max}")
    print()
    print("First 12 greedy loads:")
    print(greedy_loads[:12])
    print("First 12 hybrid loads:")
    print(hybrid_loads[:12])


if __name__ == "__main__":
    main()
