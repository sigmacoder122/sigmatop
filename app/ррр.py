def ok(d):
    cnt = 0
    i = 0
    while i + C - 1 < N:
        if h[i + C - 1] - h[i] <= d:
            cnt += 1
            i += C
        else:
            i += 1
        if cnt >= R:
            return True
    return False


N, R, C = map(int
              , input().split())
h = [int(input()) for i in range(N)]
h.sort()
l, r = 0, h[-1] - h[0]
ans = r
while l <= r:
    m = (l + r) // 2
    if ok(m):
        ans = m
        r = m - 1
    else:
        l = m + 1

print(ans)