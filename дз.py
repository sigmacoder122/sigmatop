n = int(input())
c = list(map(int, input().split()))
k = int(input())
p = list(map(int, input().split()))

counts = [0] * n

for key in p:
    counts[key - 1] += 1
for i in range(n):
    if counts[i] > c[i]:
        print("YES")
    else:
        print("NO")