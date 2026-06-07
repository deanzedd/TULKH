import argparse
import random
from pathlib import Path

from Hill_climbing import hill_climbing_with_loads
from simulated_anneling import simulated_annealing


def generate_random_case(N, M, b, density, seed):
    rng = random.Random(seed)
    L = []

    for _ in range(N):
        reviewers = [j for j in range(M) if rng.random() < density]

        # Giữ ít nhất b+1 lựa chọn nếu có thể, để SA có không gian swap.
        while len(reviewers) < min(M, b + 1):
            r = rng.randrange(M)
            if r not in reviewers:
                reviewers.append(r)

        rng.shuffle(reviewers)
        L.append(reviewers)

    return L


def write_case(path, N, M, b, L):
    lines = [f"{N} {M} {b}"]
    for reviewers in L:
        one_based = [str(r + 1) for r in reviewers]
        lines.append(" ".join([str(len(reviewers))] + one_based))
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def evaluate_case(N, M, b, L, sa_runs, time_limit):
    _, hc_max, _, hc_stats = hill_climbing_with_loads(
        N, M, b, L,
        max_iterations=50_000,
        time_limit_sec=time_limit,
    )

    best_sa = 10**9
    best_seed = None
    for run in range(sa_runs):
        seed = 1000 + run
        _, sa_max, _, _ = simulated_annealing(
            N, M, b, L,
            T_init=max(5.0, N * 0.1),
            cooling=0.995,
            T_min=0.01,
            iters_per_temp=max(50, N),
            max_iterations=30_000,
            seed=seed,
            time_limit_sec=time_limit,
        )
        if sa_max < best_sa:
            best_sa = sa_max
            best_seed = seed

    return hc_max, best_sa, best_seed, hc_stats


def main():
    parser = argparse.ArgumentParser(
        description="Generate a Balanced Paper Assignment testcase where SA beats HC."
    )
    parser.add_argument("--N", type=int, default=12)
    parser.add_argument("--M", type=int, default=5)
    parser.add_argument("--b", type=int, default=2)
    parser.add_argument("--density", type=float, default=0.25)
    parser.add_argument("--max-seed", type=int, default=1000)
    parser.add_argument("--target-gap", type=int, default=1)
    parser.add_argument("--sa-runs", type=int, default=5)
    parser.add_argument("--time-limit", type=float, default=0.25)
    parser.add_argument("--output", default="sa_vs_hc_case.txt")
    args = parser.parse_args()

    best = None
    for seed in range(args.max_seed):
        L = generate_random_case(args.N, args.M, args.b, args.density, seed)
        hc_max, sa_max, sa_seed, hc_stats = evaluate_case(
            args.N, args.M, args.b, L, args.sa_runs, args.time_limit
        )
        gap = hc_max - sa_max

        if best is None or gap > best[0]:
            best = (gap, seed, hc_max, sa_max, sa_seed, L)
            print(
                f"best so far: gap={gap}, gen_seed={seed}, "
                f"HC={hc_max}, SA={sa_max}, SA_seed={sa_seed}"
            )

        if gap >= args.target_gap:
            write_case(args.output, args.N, args.M, args.b, L)
            print("\nFOUND")
            print(f"generator seed : {seed}")
            print(f"HC max_load    : {hc_max}")
            print(f"SA max_load    : {sa_max}")
            print(f"gap            : {gap}")
            print(f"saved to       : {Path(args.output).resolve()}")
            return

    gap, seed, hc_max, sa_max, sa_seed, L = best
    write_case(args.output, args.N, args.M, args.b, L)
    print("\nNo case reached target gap, saved best case instead.")
    print(f"generator seed : {seed}")
    print(f"HC max_load    : {hc_max}")
    print(f"SA max_load    : {sa_max}")
    print(f"gap            : {gap}")
    print(f"saved to       : {Path(args.output).resolve()}")


if __name__ == "__main__":
    main()
