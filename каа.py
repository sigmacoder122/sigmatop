n, k = map(int, input().split())
a = list(map(int, input().split()))
q = list(map(int, input().split()))

def lefts(a, x):
    left = 0
    right = len(a) - 1
    while left <= right:
        mid = (left + right)//2

        if x < a[mid]:
            right = mid - 1
        else:
            left = mid + 1
    return left

for i in q:
    print(lefts(a, i))

