# Phan tich ket qua so sanh thuat toan

File nay tom tat ket qua doc tu:

- `result_comparison.xlsx`
- `hustack_comparison.xlsx`

Cot quan trong nhat la `MaxLoad`, vi muc tieu bai toan la minimize tai lon nhat cua reviewer.

## 1. Ket qua tren `result_comparison.xlsx`

File nay co 15 testcase tu `testcase.txt`.

Nhan xet tong quan:

- `Greedy` luon nhanh nhat, thoi gian gan nhu bang 0, nhung co the cho `MaxLoad` cao hon.
- `HillClimb` nhanh hon LNS rat nhieu va trong file nay cho ket qua bang LNS o tat ca 15 testcase.
- `LNS` thuong chay quanh 1 giay do cau hinh time limit, nen tren case nho no cham hon CP-SAT.
- `CP-SAT` deu dat `OPTIMAL` trong file nay, nhung thoi gian tang manh khi testcase lon.

Bang tom tat:

| Nhom case | Hien tuong chinh |
|---|---|
| Test 01-04, 10-11 | Ca 4 thuat toan cho cung `MaxLoad`; CP-SAT nhanh hon LNS vi case nho. |
| Test 05-08, 12-14 | `HillClimb` va `LNS` cai thien Greedy 1 don vi `MaxLoad`; CP-SAT xac nhan day la toi uu. |
| Test 09 | CP-SAT tim duoc `MaxLoad = 20`, con Greedy/HillClimb/LNS la 21. Day la case LNS chua bat kip toi uu voi time limit hien tai. |
| Test 15 | Tat ca bang nhau voi `MaxLoad = 34`, nhung CP-SAT mat hon 24 giay de chung minh `OPTIMAL`. |

So sanh thoi gian:

- Voi case nho va trung binh, CP-SAT co the nhanh hon LNS vi no giai va chung minh toi uu rat nhanh.
- Voi case lon, CP-SAT cham hon LNS ro ret. Vi du:
  - Test 08: LNS khoang 1.03s, CP-SAT khoang 6.69s.
  - Test 09: LNS khoang 1.06s, CP-SAT khoang 31.61s.
  - Test 15: LNS khoang 1.18s, CP-SAT khoang 24.37s.

Giai thich:

- `LNS` la heuristic, chi can tim nghiem tot trong time limit.
- `CP-SAT` la exact solver, muon co `OPTIMAL` thi phai chung minh khong co nghiem nao tot hon.
- Tren case lon, viec chung minh toi uu ton thoi gian hon viec tim mot nghiem tot.

## 2. Ket qua tren `hustack_comparison.xlsx`

File nay doc tu `Input_hustack.txt` va `Output_hustack.txt`.

Luu y: input/output HUSTack co 11 block testcase, nhung nhan `Test-case 9` bi lap, nen khi nhin theo ten case trong Excel co the thay nhu chi co 10 ten rieng biet.

Nhan xet tong quan:

- Dong `HUSTack` la output tham chieu, duoc validate hop le (`OK`).
- `LNS` dat cung `MaxLoad` voi CP-SAT tren tat ca block trong file nay.
- `HillClimb` thuong dat bang LNS, nhung co case LNS tot hon HillClimb.
- `HUSTack` va `Greedy` nhieu luc bang nhau, nhung o mot so case thua HillClimb/LNS/CP-SAT 1-2 don vi `MaxLoad`.

Mot so diem dang chu y:

| Case | HUSTack | Greedy | HillClimb | LNS | CP-SAT | Nhan xet |
|---|---:|---:|---:|---:|---:|---|
| Test-case 1 | 4 | 4 | 4 | 4 | 4 | Tat ca bang nhau. |
| Test-case 2 | 21 | 21 | 20 | 20 | 20 | HC/LNS/CP-SAT tot hon HUSTack va Greedy 1 don vi. |
| Test-case 3 | 31 | 31 | 30 | 30 | 30 | LNS dat toi uu, CP-SAT xac nhan. |
| Test-case 5 | 31 | 31 | 31 | 30 | 30 | LNS vuot HillClimb va Greedy. |
| Test-case 6 | 6 | 4 | 4 | 4 | 4 | HUSTack kem hon cac thuat toan trong repo 2 don vi. |
| Test-case 8 | 38 | 38 | 38 | 38 | 38 | Tat ca bang nhau. |
| Test-case 10 | 16 | 16 | 15 | 15 | 15 | HC/LNS/CP-SAT tot hon 1 don vi. |

Ve thoi gian:

- `Greedy` va `HillClimb` rat nhanh.
- `LNS` gan 1 giay do time limit dat cho LNS.
- `CP-SAT` nhanh tren case nho, nhung co case mat hon 2-3 giay.

## 3. Khac biet giua cac thuat toan khi dat time limit

### Greedy

Greedy gan reviewer co load thap nhat tai thoi diem xu ly tung paper.

Uu diem:

- Rat nhanh.
- Lam baseline tot.

Nhuoc diem:

- Quyet dinh tham lam ban dau co the lam mot so reviewer bi qua tai.
- Khong sua lai loi giai sau khi da gan.

### Hill Climbing

Hill Climbing bat dau tu Greedy, sau do thu swap cuc bo de giam `MaxLoad`.

Uu diem:

- Van rat nhanh.
- Thuong cai thien Greedy 1 don vi tren cac case co local move tot.

Nhuoc diem:

- Chi chap nhan move cai thien truc tiep.
- De ket o local optimum.

### LNS

LNS pha mot phan loi giai roi repair lai.

Uu diem:

- Co the thoat local optimum tot hon Hill Climbing.
- Trong `hustack_comparison.xlsx`, LNS dat bang CP-SAT tren tat ca block.
- Tren case lon, LNS cho nghiem tot trong thoi gian ngan hon CP-SAT.

Nhuoc diem:

- Neu time limit dat 1 giay, LNS thuong chay gan 1 giay.
- Khong chung minh toi uu.
- Neu destroy chua du lon hoac time limit qua ngan, co the chua bat kip CP-SAT, nhu Test 09 trong `result_comparison.xlsx`.

### CP-SAT

CP-SAT la exact solver.

Uu diem:

- Neu status la `OPTIMAL`, ket qua duoc chung minh toi uu.
- Tren case nho, CP-SAT co the nhanh hon LNS.

Nhuoc diem:

- Tren case lon, thoi gian tang nhanh.
- Neu time limit thap, CP-SAT co the chi tra `FEASIBLE` hoac `UNKNOWN`.

## 4. Ket luan cho bao cao

Co the viet:

> Greedy va Hill Climbing co thoi gian rat nho, phu hop lam baseline. Hill Climbing cai thien Greedy trong nhieu testcase nhung van co nguy co ket o local optimum. LNS ton thoi gian hon do chay theo time limit va thuc hien destroy-repair, nhung cho chat luong nghiem gan voi CP-SAT hon tren nhieu testcase. CP-SAT co kha nang chung minh toi uu, nhung thoi gian tang manh khi kich thuoc testcase lon. Vi vay, CP-SAT phu hop lam moc doi chieu cho case nho/trung binh, con LNS phu hop hon khi can nghiem tot nhanh tren case lon.

