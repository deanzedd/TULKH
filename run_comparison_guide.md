# Huong dan chay `run_comparison.py`

File `run_comparison.py` dung de so sanh cac thuat toan:

- `HUSTack` neu co file output tham chieu
- `Greedy`
- `HillClimb`
- `LNS`
- `CP-SAT`

## Lenh co ban

Chay tu thu muc `TULKH`:

```powershell
cd "D:\Toi uu lap ke hoach\TULKH"
```

Neu lenh `python` khong nhan dung interpreter, dung Python day du duong dan:

```powershell
& "C:\Users\mailo\AppData\Local\Programs\Python\Python311\python.exe" run_comparison.py testcase.txt
```

## Chay file `testcase.txt`

`testcase.txt` co nhieu testcase trong cung mot file, nen chuong trinh se tu tach va chay lan luot.

```powershell
& "C:\Users\mailo\AppData\Local\Programs\Python\Python311\python.exe" run_comparison.py testcase.txt --hc-time-limit 1 --lns-time-limit 1 --cpsat-time-limit 2
```

## Chay input/output HUSTack

Dung khi co ca file input va output tham chieu:

```powershell
& "C:\Users\mailo\AppData\Local\Programs\Python\Python311\python.exe" run_comparison.py Input_hustack.txt --reference-output Output_hustack.txt --hc-time-limit 1 --lns-time-limit 1 --cpsat-time-limit 2
```

Ket qua se co them dong `HUSTack` de validate output tham chieu va so sanh `MaxLoad`.

## Luu ket qua ra Excel

```powershell
& "C:\Users\mailo\AppData\Local\Programs\Python\Python311\python.exe" run_comparison.py Input_hustack.txt --reference-output Output_hustack.txt --hc-time-limit 1 --lns-time-limit 1 --cpsat-time-limit 2 --output-excel hustack_comparison.xlsx
```

File sinh ra:

```text
TULKH/hustack_comparison.xlsx
```

## Luu ket qua ra JSON

```powershell
& "C:\Users\mailo\AppData\Local\Programs\Python\Python311\python.exe" run_comparison.py Input_hustack.txt --reference-output Output_hustack.txt --hc-time-limit 1 --lns-time-limit 1 --cpsat-time-limit 2 --output-json hustack_comparison.json
```

## Y nghia cac time limit

`--hc-time-limit`

Gioi han thoi gian cho Hill Climbing. HC thuong rat nhanh, co the de `1`.

`--lns-time-limit`

Gioi han thoi gian cho LNS. LNS la heuristic nen thuong chay gan het time limit da dat.

`--cpsat-time-limit`

Gioi han thoi gian cho CP-SAT. CP-SAT co the dung som neu chung minh duoc `OPTIMAL`; neu het gio ma chi co nghiem hop le thi trang thai co the la `FEASIBLE`.

## Goi y cau hinh

Test nho:

```powershell
--hc-time-limit 1 --lns-time-limit 1 --cpsat-time-limit 2
```

Test trung binh:

```powershell
--hc-time-limit 2 --lns-time-limit 3 --cpsat-time-limit 10
```

Test lon:

```powershell
--hc-time-limit 3 --lns-time-limit 5 --cpsat-time-limit 30
```

Test rat lon, uu tien thoi gian:

```powershell
--hc-time-limit 1 --lns-time-limit 2 --cpsat-time-limit 5
```

Test rat lon, uu tien CP-SAT chung minh toi uu:

```powershell
--hc-time-limit 3 --lns-time-limit 5 --cpsat-time-limit 60
```

## Doc ket qua

Cot quan trong nhat la `MaxLoad`. Bai toan can minimize `MaxLoad`.

Trang thai CP-SAT:

- `OPTIMAL`: da chung minh toi uu.
- `FEASIBLE`: co nghiem hop le nhung chua chung minh toi uu trong time limit.
- `UNKNOWN`: chua tim/chung minh duoc nghiem trong time limit.

Luu y: `LNS` co the vuot time limit mot chut vi phai hoan tat iteration dang chay.
