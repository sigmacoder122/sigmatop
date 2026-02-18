n, m = map(int, input().split())
a = []
for i in range(n):
    r = list(map(int, input().split()))
    a +=[r]
k = int(input())

ans = 0
for i in range(n):
    count = 0
    for j in range(m):
        if a[i][j] == 0:
            count += 1
        else:
            count = 0
        if count >= k:
            ans = i + 1
    if ans > 0:
        print(ans)
        ans = -1

if ans == 0:
    print(0)