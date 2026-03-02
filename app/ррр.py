n, m = map(int, input().split())
ma = [list(map(int, input().split())) for i in range(n)]

count = 0

for i in range(n):
    mini = min(ma[i])
    for j in range(m):
        if ma[i][j] == mini:
            maxi = ma[0][j]
            for k in range(1, n):
                if ma[k][j] > maxi:
                    maxi = ma[k][j]

            if ma[i][j] == maxi:
                print(i + 1, j + 1)
                count += 1

if count == 0:
    print(0)