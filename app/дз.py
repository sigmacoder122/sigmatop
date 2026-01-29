def ff(a, x):
    l, r = 0, len(a) - 1
    ans = -1
    while l <= r:
        m = (l + r) // 2
        if a[m] < x:
            ans = m
            r = m - 1
        else:
            l = m + 1
    return ans + 1 if ans != -1 else 0

n, k = map(int, input().split())
a = list(map(int, input().split()))
mass = list(map(int, input().split()))

for x in mass:
    print(ff(a, x))