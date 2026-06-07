# Greedy vs LNS vs Local Search vs CP-SAT Test Suite

Bo test nay duoc chon de so sanh ca 3 cach giai tren bai toan
Balanced Paper Assignment:

- `Greedy`: baseline tham lam goi tu `greedy_solver.greedy_assign`.
- `LNS`: Large Neighborhood Search.
- `LocalSearch`: goi truc tiep `local_search_solver.local_search_solve`.
- `CP-SAT`: exact solver goi truc tiep `exact_ORTOOLS.exact_GG_ORTOI`.

Chay lai toan bo:

```powershell
python .\TULKH\greedy_lns_cpsat\run_comparison_suite.py
```

Chay toan bo va luu Excel:

```powershell
python .\TULKH\greedy_lns_cpsat\run_comparison_suite.py --output-excel .\TULKH\greedy_lns_cpsat\comparison_results.xlsx
```

Chay so sanh tren mot case:

```powershell
python .\TULKH\greedy_lns_cpsat\run_comparison.py .\TULKH\greedy_lns_cpsat\cases\case_01_small.txt
```

Chay mot case va luu Excel:

```powershell
python .\TULKH\greedy_lns_cpsat\run_comparison.py .\TULKH\greedy_lns_cpsat\cases\case_01_small.txt --output-excel .\TULKH\greedy_lns_cpsat\case_01_result.xlsx
```

Bang so sanh gom ca 4 thuat toan:
- `Greedy`: baseline tham lam goi tu `greedy_solver.greedy_assign`.
- `LNS`: Large Neighborhood Search trong folder nay.
- `LocalSearch`: SA + Tabu + LNS trong `local_search_solver.py`.
- `CP-SAT`: goi truc tiep `exact_ORTOOLS.exact_GG_ORTOI`.

Y nghia cot:
- `MaxLoad`: tai lon nhat cua mot reviewer.
- `ΔCP = MaxLoad - MaxLoad(CP-SAT)`, so duong nghia la kem CP-SAT.
- `GainGreedy = MaxLoad(Greedy) - MaxLoad`, so duong nghia la tot hon Greedy.
- `Time(s)`: thoi gian chay tung thuat toan.

Sinh lai cac file case neu can:

```powershell
python .\TULKH\greedy_lns_cpsat\generate_comparison_cases.py
```

Ket qua ky vong tren may hien tai:

| Case | N | M | b | LB | Greedy | LNS | CP-SAT | Diem nhan |
|------|---:|---:|---:|---:|---:|---:|---:|-------------|
| case_01_small.txt | 30 | 10 | 2 | 6 | 8 | 6 | 6 | LNS dat OPT, giam 2 max_load |
| case_02_medium.txt | 50 | 15 | 2 | 7 | 9 | 7 | 7 | LNS dat OPT, giam 2 max_load |
| case_03_medium_b3.txt | 60 | 15 | 3 | 12 | 14 | 12 | 12 | LNS dat OPT, giam 2 max_load |
| case_04_harder.txt | 60 | 15 | 3 | 12 | 15 | 13 | 13 | OPT lon hon LB, LNS van dat OPT |
| case_05_large.txt | 100 | 25 | 3 | 12 | 14 | 13 | 13 | Case lon hon, LNS dat OPT va tot hon Greedy |

Ghi chu:
- `LB = ceil(N*b/M)` la lower bound ly thuyet.
- `CP-SAT = OPTIMAL` xac nhan gia tri toi uu neu OR-Tools chay duoc trong time limit.
- Greedy nhanh hon, nhung co the ket o phan cong lam mot so reviewer qua tai.
- LNS ton them thoi gian de destroy-repair cac vung quanh reviewer tai cao, doi lai max_load tot hon.
