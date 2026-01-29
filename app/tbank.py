n = int(input())
for _ in range(n):
    p1 = input()
    p2 = input()
    c1, r1 = p1[0], int(p1[1])
    c2, r2 = p2[0], int(p2[1])

    def move_piece(a, b, x, y, piece):
        dc = abs(ord(x) - ord(a))
        dr = abs(y - b)
        if piece == 'q':
            return dc == dr or dc == 0 or dr == 0
        if piece == 'r':
            return dc == 0 or dr == 0
        if piece == 'b':
            return dc == dr
        if piece == 'k':
            return (dc == 1 and dr == 2) or (dc == 2 and dr == 1)
        return False

    res = "NO"
    moves = []
    if r1 == 2:
        moves.append((c1, r1 + 1))
        moves.append((c1, r1 + 2))
    else:
        moves.append((c1, r1 + 1))

    for mc, mr in moves:
        if mr == 8:
            for pc in ['q', 'r', 'b', 'k']:
                if move_piece(mc, mr, c2, r2, pc):
                    res = "YES"
                    break
            if res == "YES":
                break
        else:
            if c2 == mc and r2 == mr + 1:
                res = "YES"
                break

    print(res)