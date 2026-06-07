# Giai thich thuat toan LNS va cach chon tham so destroy

File nay giai thich thuat toan `LNS` trong `lns/lns_solver.py`.

## 1. Muc tieu bai toan

Bai toan Balanced Paper Assignment:

- Co `N` bai bao.
- Co `M` reviewer.
- Moi bai `i` chi duoc gan reviewer trong danh sach `L[i]`.
- Moi bai can dung `b` reviewer.
- Muc tieu la minimize:

```text
MaxLoad = tai lon nhat cua mot reviewer
```

## 2. Y tuong cua LNS

`LNS` la viet tat cua `Large Neighborhood Search`.

Thay vi chi swap mot cap nho nhu Hill Climbing, LNS lam viec tren mot vung lon hon cua loi giai:

1. Tao loi giai ban dau bang Greedy.
2. Chon mot nhom paper de pha, goi la `destroy`.
3. Xoa assignment cua nhom paper do.
4. Gan lai cac paper vua xoa bang greedy repair.
5. Polish cuc bo de giam reviewer dang tai cao.
6. Quyet dinh chap nhan hoac rollback loi giai moi.
7. Lap lai toi khi het `time_limit` hoac `max_iterations`.

Truc giac:

- Hill Climbing di tung buoc nho.
- LNS cho phep nhay xa hon bang cach pha nhieu paper cung luc.

## 3. Cac buoc trong code

### 3.1. Khoi tao

Trong `lns_solve`, loi giai ban dau duoc tao bang:

```python
assignment, _, loads, feasible = greedy_assign(N, M, b, L)
```

Sau do objective la:

```python
objective(loads) = max(loads)
```

### 3.2. Chon kich thuoc destroy

Ham:

```python
choose_destroy_size(rng, destroy_min, destroy_max, stale, restart_after)
```

Neu lau khong cai thien (`stale` lon), ham se chon destroy size lon hon de nhay xa hon.

Neu chua bi stale, destroy size duoc random trong khoang:

```text
[destroy_min, destroy_max]
```

### 3.3. Chon paper de destroy

Ham:

```python
select_destroy_papers(assignment, loads, L, k, rng, heavy_bias)
```

Code uu tien cac paper dang gan reviewer co tai cao.

Cu the:

- Tinh `max_load`.
- Reviewer nong la reviewer co load gan max:

```text
load >= max_load - 1
```

- Paper nao chua reviewer nong se duoc uu tien destroy.
- Mot phan paper con lai duoc chon random de giu da dang.

Tham so `heavy_bias` dieu khien ty le uu tien reviewer tai cao.

Vi du:

```text
heavy_bias = 0.70
```

nghia la khoang 70% paper bi destroy se den tu vung co reviewer tai cao, 30% con lai random.

### 3.4. Destroy

Ham:

```python
destroy_assignment(assignment, loads, papers)
```

Voi moi paper duoc chon:

- Tru load cua cac reviewer dang gan.
- Xoa assignment cua paper.

### 3.5. Repair

Ham:

```python
repair_assignment(assignment, loads, b, L, papers, rng, repair_noise)
```

Cach repair:

- Paper co it candidate hon duoc gan truoc.
- Moi paper chon `b` reviewer co load thap nhat.
- Them `repair_noise` nho de pha tie va tao da dang.

Neu `repair_noise = 0`, repair gan nhu deterministic.

Neu `repair_noise` qua lon, repair co the mat tinh min-load.

### 3.6. Polish

Ham:

```python
polish_hot_reviewers(assignment, loads, L, polish_steps)
```

Buoc nay thu chuyen paper khoi reviewer dang max-load sang reviewer nhe hon neu move do khong lam tang max-load.

Day la buoc local improvement nho sau repair.

### 3.7. Accept hoac rollback

Neu loi giai moi tot hon hoac bang:

```text
new_obj <= old_obj
```

thi chap nhan.

Neu xau hon, co the van chap nhan voi xac suat giam dan theo temperature:

```python
exp(-delta / temperature)
```

Co che nay giup LNS tranh ket cuc bo.

## 4. Cach chon tham so destroy trong code hien tai

Ham:

```python
choose_lns_parameters(N)
```

Dang chon:

```python
sqrt_n = int(sqrt(N))
destroy_min = max(1, min(N, sqrt_n // 2))
destroy_max = max(destroy_min, min(N, max(8, 2 * sqrt_n, int(0.04 * N))))
```

Truc giac:

- `destroy_min` khoang `sqrt(N) / 2`.
- `destroy_max` la max cua:
  - 8
  - `2 * sqrt(N)`
  - `4% * N`

nhung khong vuot qua `N`.

## 5. Vi du destroy theo kich thuoc N

| N | sqrt(N) | destroy_min | destroy_max gan dung |
|---:|---:|---:|---:|
| 30 | 5 | 2 | 10 |
| 100 | 10 | 5 | 20 |
| 200 | 14 | 7 | 28 |
| 500 | 22 | 11 | 44 |
| 1000 | 31 | 15 | 62 |
| 2000 | 44 | 22 | 88 |

Voi `N = 1000`, moi iteration LNS se pha khoang 15 den 62 paper.

## 6. Khi nao destroy qua nho?

Destroy qua nho neu:

- LNS cho ket qua giong Greedy/HillClimb.
- Rat it `best_updates`.
- MaxLoad khong giam sau nhieu iteration.

Hau qua:

- LNS chi sua cuc bo.
- De ket o local optimum.

Cach xu ly:

```text
tang destroy_min va destroy_max
```

Vi du:

```powershell
--lns-time-limit 3
```

hoac neu expose tham so trong CLI:

```text
destroy_min = 0.02 * N
destroy_max = 0.08 * N
```

## 7. Khi nao destroy qua lon?

Destroy qua lon neu:

- LNS chay cham hon nhieu.
- Nghiem dao dong manh.
- Repair gan nhu tao lai loi giai moi moi vong.
- Ket qua khong on dinh theo seed.

Hau qua:

- Mat cau truc tot cua loi giai hien tai.
- Gan giong random restart.

Cach xu ly:

```text
giam destroy_max
```

## 8. Goi y chon destroy

### Case nho

```text
N <= 50
destroy_min: 1-3
destroy_max: 8-12
```

### Case trung binh

```text
50 < N <= 300
destroy_min: sqrt(N)/2
destroy_max: 2*sqrt(N) den 4%*N
```

### Case lon

```text
N > 300
destroy_min: 1%*N den 2%*N
destroy_max: 4%*N den 8%*N
```

Neu LNS khong cai thien Greedy, tang destroy.

Neu LNS cham va ket qua dao dong, giam destroy.

## 9. Cach chon heavy_bias

`heavy_bias` la ty le paper destroy duoc chon quanh reviewer tai cao.

Mac dinh:

```text
heavy_bias = 0.70
```

Goi y:

| Tinh huong | heavy_bias |
|---|---:|
| Muon tap trung giam max-load | 0.70 - 0.90 |
| Muon da dang hon | 0.40 - 0.60 |
| Loi giai ket lau, it cai thien | giam heavy_bias hoac tang destroy_max |

## 10. Cach chon repair_noise

`repair_noise` them nhieu nho vao load khi sap xep candidate.

Mac dinh:

```text
repair_noise = 0.10
```

Goi y:

- `0.00`: repair deterministic, on dinh nhung de lap lai loi giai cu.
- `0.05 - 0.15`: can bang tot.
- `> 0.30`: da dang hon nhung co the lam repair kem min-load.

## 11. Cach chon time limit

LNS thuong chay gan het `--lns-time-limit`.

Goi y:

| Muc tieu | lns_time_limit |
|---|---:|
| Test nhanh | 1s |
| Bao cao chat luong tot hon | 3-5s |
| Case rat lon | 5-10s |

Luu y: thoi gian thuc te co the vuot time limit mot chut vi LNS can hoan tat iteration dang chay.

## 12. Ket luan

LNS phu hop khi:

- Case lon lam CP-SAT cham.
- Can nghiem tot nhanh.
- Khong bat buoc phai co chung nhan toi uu.

Destroy parameter la diem quan trong nhat:

- Qua nho: ket local optimum.
- Qua lon: gan nhu restart, cham.
- Tot nhat: pha vua du lon de sua vung reviewer tai cao, nhung van giu cau truc tot cua loi giai hien tai.

