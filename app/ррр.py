n, m = map(int, input().split())
ma = [[0] * m for i in range(n)]
num = 1
for i in range(n):
    for j in range(m):
        if (i + j) % 2 == 0:
            ma[i][j] = num
            num += 1

for r in ma:
    for i in r:
        print(f"{i:4d}", end="")
    print()