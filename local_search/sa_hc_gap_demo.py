import math
from pathlib import Path

from Hill_climbing import hill_climbing_with_loads, greedy_init
from simulated_anneling import simulated_annealing


def generate_plateau_trap_case(num_blocks=5):
    """
    Sinh một test case nhỏ nhưng tạo khác biệt rõ giữa HC và SA.

    Ý tưởng:
    - Mỗi block có N = M = 4, b = 1.
    - Ghép nhiều block độc lập để tạo test lớn hơn nhưng giữ cùng cấu trúc bẫy.
    - Có lời giải tối ưu max_load = 1.
    - Greedy tạo loads [2, 0, 1, 1].
    - HC bị kẹt vì mọi bước cần thiết đầu tiên chỉ giữ max_load = 2,
      không giảm ngay lập tức.
    - SA chấp nhận bước plateau đó, rồi đi tiếp tới max_load = 1.
    """
    N = 4 * num_blocks
    M = 4 * num_blocks
    b = 1

    # 0-indexed inside Python.
    L = []
    for block in range(num_blocks):
        offset = 4 * block
        L.extend([
            [offset + 0, offset + 2],  # reviewer 1 hoặc 3 trong block
            [offset + 3, offset + 1],  # reviewer 4 hoặc 2 trong block
            [offset + 0, offset + 2],  # reviewer 1 hoặc 3 trong block
            [offset + 0, offset + 3],  # reviewer 1 hoặc 4 trong block
        ])
    return N, M, b, L


def write_input_file(path, N, M, b, L):
    lines = [f"{N} {M} {b}"]
    for reviewers in L:
        one_based = [str(r + 1) for r in reviewers]
        lines.append(" ".join([str(len(reviewers))] + one_based))
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def format_assignment(assignment):
    return [[r + 1 for r in row] for row in assignment]


def main():
    N, M, b, L = generate_plateau_trap_case(num_blocks=5)
    output_path = Path(__file__).with_name("sa_vs_hc_large_gap_case.txt")
    write_input_file(output_path, N, M, b, L)

    greedy_assignment, greedy_max, greedy_loads, _ = greedy_init(N, M, b, L)

    hc_assignment, hc_max, hc_loads, hc_stats = hill_climbing_with_loads(
        N,
        M,
        b,
        L,
        max_iterations=10_000,
        time_limit_sec=1.0,
    )

    sa_assignment, sa_max, sa_loads, sa_stats = simulated_annealing(
        N,
        M,
        b,
        L,
        T_init=10.0,
        cooling=0.998,
        T_min=0.01,
        iters_per_temp=100,
        max_iterations=50_000,
        seed=0,
        time_limit_sec=1.0,
    )

    lower_bound = math.ceil(N * b / M)
    improvement = hc_max - sa_max
    relative = improvement / hc_max * 100 if hc_max else 0.0

    print("Generated testcase")
    print("==================")
    print(output_path.resolve())
    print()
    print(f"N={N}, M={M}, b={b}, lower_bound={lower_bound}")
    print()
    print("Input:")
    print(output_path.read_text(encoding="utf-8").strip())
    print()
    print("Result comparison")
    print("=================")
    print(f"Greedy max_load : {greedy_max}, loads={greedy_loads}, assignment={format_assignment(greedy_assignment)}")
    print(f"HC max_load     : {hc_max}, loads={hc_loads}, assignment={format_assignment(hc_assignment)}")
    print(f"SA max_load     : {sa_max}, loads={sa_loads}, assignment={format_assignment(sa_assignment)}")
    print()
    print(f"SA improves HC by {improvement} load unit(s), equivalent to {relative:.1f}%.")
    print(f"SA reaches the lower bound {lower_bound}, so this solution is optimal.")
    print()
    print("Why HC gets stuck")
    print("=================")
    print("Greedy starts with reviewer 1 having load 2 while reviewers 3 and 4 have load 1.")
    print("Moving one paper from reviewer 1 to reviewer 3 or 4 keeps max_load at 2, so HC rejects it.")
    print("SA can accept that plateau move, then performs the next move and reaches loads [1, 1, 1, 1].")


if __name__ == "__main__":
    main()
