# Lộ trình phát triển Local Search cho Balanced Paper Assignment

> **Baseline**: Greedy (sort papers by |L[i]|, pick b min-load reviewers)  
> **Mục tiêu**: Cải thiện `max_load` với thời gian hợp lý

---

## 1. Thứ tự thử các thuật toán

Nguyên tắc: **tăng dần độ phức tạp**, mỗi bước phải chứng minh cải thiện rõ ràng so với bước trước trước khi tiếp tục.

```
Greedy (baseline)
    │
    ▼
[Bước 1] Hill Climbing (HC)           ← đơn giản nhất, hiểu rõ landscape
    │
    ▼
[Bước 2] Iterated Local Search (ILS)  ← restart thông minh, thoát local optima
    │
    ▼
[Bước 3] Simulated Annealing (SA)     ← chấp nhận xấu hơn có kiểm soát
    │
    ▼
[Bước 4] Tabu Search (TS)             ← tránh cycling, khám phá rộng hơn
    │
    ▼
[Bước 5] Large Neighborhood Search (LNS)  ← phá hủy-sửa chữa, nhảy xa
    │
    ▼
[Bước 6] Hybrid: SA + Tabu + LNS      ← kết hợp ưu điểm từng phương pháp
```

---

## 2. Chi tiết từng bước

### Bước 1 — Hill Climbing (HC)

**Ý tưởng**: Từ lời giải greedy, liên tục thực hiện move cải thiện `max_load`.

```python
# Operator cơ bản: SWAP
# Tìm reviewer j* có load = max_load
# Tìm paper i có j* trong assignment[i]
# Thử thay j* bằng reviewer j' ∈ L[i] có loads[j'] < loads[j*] - 1
# → Nếu tìm được: thực hiện và lặp lại
```

**Ưu điểm**: Dễ implement, chạy nhanh, dễ debug  
**Nhược điểm**: Mắc kẹt tại **local optima** (rất phổ biến với bài toán này)  
**Khi dừng**: Khi không còn move nào cải thiện được `max_load`

---

### Bước 2 — Iterated Local Search (ILS)

**Ý tưởng**: Sau khi HC mắc kẹt, **perturbation** (khuấy động) ngẫu nhiên rồi chạy HC lại.

```
repeat R lần:
    s = HC(current_solution)
    if f(s) < f(best): best = s
    current = perturbate(s)   # swap ngẫu nhiên k cặp (paper, reviewer)
```

**Tại sao trước SA?**  
ILS đơn giản hơn SA (không cần nhiệt độ), dễ tune `k` (số perturbations), cho thấy liệu "restart" có ích không.

---

### Bước 3 — Simulated Annealing (SA)

**Thêm gì so với HC**: Chấp nhận move *xấu hơn* với xác suất `exp(-Δ/T)`.

| Parameter | Gợi ý khởi đầu | Ý nghĩa |
|-----------|---------------|---------|
| `T_init` | `max(5, N*0.05)` | Tỷ lệ với kích thước |
| `cooling` | `0.995` | Giảm chậm |
| `T_min` | `0.01` | Ngưỡng dừng |
| `iter/T` | `N` moves/nhiệt độ | Đủ khám phá |

**Điểm quan trọng**: Tracking `best_solution` riêng (SA có thể rời xa best).

---

### Bước 4 — Tabu Search (TS)

**Thêm gì so với HC**: Danh sách **tabu** lưu các move gần đây, không được phép quay lại.

```
tabu_list = deque(maxlen=tenure)  # tenure ≈ N/10 đến N/5

Mỗi bước: chọn move tốt nhất KHÔNG có trong tabu_list
           (trừ khi đạt aspiration: tốt hơn best_known)
```

**Khi nào TS > SA?**  
Khi bài toán có nhiều local optima gần nhau — TS thoát bằng cách "nhớ lối cũ" thay vì random walk.

---

### Bước 5 — LNS (Large Neighborhood Search)

**Ý tưởng**: Phá hủy một phần lớn lời giải, repair bằng greedy/exact.

```
destroy:  chọn ngẫu nhiên k paper, xóa assignment của chúng
repair:   re-assign k paper đó bằng greedy min-load
          (hoặc exact solver cho phần nhỏ nếu k ≤ 20)
```

**Tỷ lệ destroy hợp lý**: `destroy_ratio = min(0.3, 10/N)`  
- Nhỏ quá → không thoát được local optima  
- Lớn quá → gần như restart, lãng phí

---

### Bước 6 — Hybrid

Kết hợp theo logic:
```
SA điều phối acceptance (exploration vs exploitation)
  → trong mỗi iteration, chọn operator:
      60% SWAP (fine-grained)
      30% MOVE (medium)
      10% LNS  (coarse, nhảy xa)
  → Tabu ngăn cycling khi SA nguội dần
```

---

## 3. Thước đo đánh giá (Metrics)

### 3.1 Chất lượng lời giải

| Metric | Công thức | Ghi chú |
|--------|-----------|---------|
| **Optimality Gap** | `(LS_max_load - OPT) / OPT × 100%` | Cần exact solver để biết OPT |
| **Greedy Gap** | `(LS_max_load - Greedy_max_load) / Greedy_max_load × 100%` | Dùng khi không có OPT |
| **Lower Bound Gap** | `(LS_max_load - LB) / LB × 100%` | `LB = ⌈N×b/M⌉` |

> Với test nhỏ (test 01–06): **dùng Optimality Gap** (có exact solver).  
> Với test lớn (test 07–15): **dùng Greedy Gap + LB Gap**.

---

### 3.2 Thời gian

| Metric | Ý nghĩa |
|--------|---------|
| **Wall-clock time** | Thời gian thực chạy (giây) |
| **Time to best** | Thời điểm tìm được `best_solution` lần cuối |
| **Convergence iteration** | Iteration mà `best_solution` không còn cải thiện |
| **Iterations/second** | Throughput của thuật toán |

> `Time to best` quan trọng hơn `total time` — LS nên hội tụ sớm rồi "xác nhận".

---

### 3.3 Độ ổn định (Robustness)

Chạy mỗi thuật toán **10 lần** với seed khác nhau, đo:

| Metric | Công thức |
|--------|-----------|
| **Mean** | Trung bình `max_load` |
| **Std Dev** | Độ lệch chuẩn → thuật toán stochastic ổn định? |
| **Best of 10** | Kết quả tốt nhất → tiềm năng lý thuyết |
| **Worst of 10** | Kết quả xấu nhất → độ tin cậy |

---

### 3.4 Đường cong hội tụ (Convergence Curve)

Ghi lại `best_max_load` tại mỗi 100 iteration → vẽ đồ thị:

```
max_load
  │
7 │─────────────┐
  │             │
6 │             └──────┐
  │                    └─────────────
5 │                                  (plateau)
  └────────────────────────────────── iteration
     0        1000      5000    10000
```

Đường cong lý tưởng: **giảm nhanh ban đầu, hội tụ sớm**.  
Nếu đường cong vẫn giảm ở cuối → tăng `max_iterations`.

---

## 4. Bảng test case đề xuất để benchmark

| Test | N | M | Dùng để đánh giá |
|------|---|---|-----------------|
| 01, 02 | 5 | 3 | Verify correctness (so với enumerate) |
| 03, 04 | 20 | 10 | **So với OPT** — thấy rõ gap |
| 10, 11 | 10–50 | 5–20 | Edge case, b cao |
| 05, 06 | 100 | 30 | **Scalability trung bình** |
| 12 | 200 | 50 | Breakpoint HC vs SA |
| 07, 13 | 500 | 100 | **LNS cần thiết** hay không? |
| 08, 14 | 1000 | 200 | Chỉ LS + Greedy cạnh tranh được |
| 09, 15 | 2000 | 300 | Stress — đo Time to best |

---

## 5. Quy trình so sánh chuẩn

```python
# Cho mỗi thuật toán A trên mỗi test case:
for seed in [42, 123, 456, 789, 1000,
             2024, 314, 271, 999, 100]:
    result = run_algorithm_A(testcase, seed=seed)
    record(result.max_load, result.time, result.time_to_best)

# Tổng hợp:
print(f"Mean={mean}, Std={std}, Best={best}, Worst={worst}")
print(f"Greedy Gap={greedy_gap:.1%}, LB Gap={lb_gap:.1%}")
print(f"Mean Time to Best={mean_ttb:.2f}s")
```

---

## 6. Quyết định "thuật toán nào đủ tốt"

```
Optimality Gap < 5%  AND  Time ≤ 2× Greedy time  →  ✅ Chấp nhận
Optimality Gap < 2%  AND  Time ≤ 5× Greedy time  →  ✅ Tốt
Optimality Gap ≈ 0%  AND  đủ nhanh               →  ✅ Xuất sắc
```

> Với bài toán NP-hard: Gap < 5% trong thời gian hợp lý thường là **thực tế tốt nhất** mà không cần exact solver.
