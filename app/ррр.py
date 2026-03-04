n = int(input())
a = [list(map(int, input().split())) for i in range(n)]

b = [x for r in a for x in r]
if sorted(b) != list(range(1, n * n + 1)):
    print("NO")
else:
    s = sum(a[0])
    ok = True
    for r in a:
        if sum(r) != s:
            ok = False
    for j in range(n):
        if sum(a[i][j] for i in range(n)) != s:
            ok = False
    if sum(a[i][i] for i in range(n)) != s:
        ok = False
    if sum(a[i][n - 1 - i] for i in range(n)) != s:
        ok = False
    print("YES" if ok else "NO")