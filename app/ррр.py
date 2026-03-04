s = input()
letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
y = 0
for i in range(8):
    if s[0] == letters[i]:
        y = i + 2
x = 8 - int(s[1]) + 2
a = [['.'] * 12 for i in range(12)]
a[x][y] = 'K'
moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
         (1, -2), (1, 2), (2, -1), (2, 1)]
for dx, dy in moves:
    a[x + dx][y + dy] = '*'
for i in range(2, 10):
    print(*a[i][2:10])