#Embedded file name: eve/client/script/ui/shared/mapView/hexagonal\hexUtil.py
__author__ = 'fridrik'
import geo2
import math
HEX_NEIGHBORS_AXIAL = [[1, 0],
 [1, -1],
 [0, -1],
 [-1, 0],
 [0, 1],
 [1, 1]]
HEX_NEIGHBORS_AXIAL_FLATTOP = [[1, -1],
 [0, -1],
 [-1, -1],
 [-1, 0],
 [0, 1],
 [1, 0]]
neighbors = [[[+1, 0],
  [0, -1],
  [-1, -1],
  [-1, 0],
  [-1, +1],
  [0, +1]], [[+1, 0],
  [+1, -1],
  [0, -1],
  [-1, 0],
  [0, +1],
  [+1, +1]]]
HEX_NEIGHBORS_CUBE = [[+1, -1, 0],
 [+1, 0, -1],
 [0, +1, -1],
 [-1, +1, 0],
 [-1, 0, +1],
 [0, -1, +1]]

def neighbour_cube(xyz, i):
    x, y, z = xyz
    nx, ny, nz = HEX_NEIGHBORS_CUBE[i]
    return (x + nx, y + ny, z + nz)


def neighbours_from_pos(column_row, startRange, endRange, isFlatTop):
    startpos = column_row
    for i in xrange(startRange):
        startpos = neighbour_axial(startpos, 4, isFlatTop)

    ret = []
    for i in xrange(startRange, endRange):
        startpos = neighbour_axial(startpos, 4, isFlatTop)
        cr = startpos
        for direction in xrange(6):
            for length in xrange(i + 1):
                cr = neighbour_axial(cr, direction, isFlatTop)
                ret.append(cr)

    return ret


def neighbour_axial(cr, direction, isFlatTop):
    c, r = cr
    if isFlatTop:
        parity = c & 1
        neighbors = [[[1, -1],
          [0, -1],
          [-1, -1],
          [-1, 0],
          [0, 1],
          [1, 0]], [[1, 0],
          [0, -1],
          [-1, 0],
          [-1, 1],
          [0, 1],
          [1, 1]]]
        c1, r1 = neighbors[parity][direction]
    else:
        parity = r & 1
        neighbors = [[[1, 0],
          [0, -1],
          [-1, -1],
          [-1, 0],
          [-1, 1],
          [0, 1]], [[1, 0],
          [1, -1],
          [0, -1],
          [-1, 0],
          [0, 1],
          [1, 1]]]
        c1, r1 = neighbors[parity][direction]
    return (c + c1, r + r1)


def line_intersection(line1, line2):
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
        return None
    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return (x, y)


def line(p1, p2):
    A = p1[1] - p2[1]
    B = p2[0] - p1[0]
    C = p1[0] * p2[1] - p2[0] * p1[1]
    return (A, B, -C)


def perp(a):
    b = empty_like(a)
    b[0] = -a[1]
    b[1] = a[0]
    return b


def seg_intersect(line1, line2):
    a1, a2 = line1
    b1, b2 = line2
    da = geo2.Vec2Subtract(a2, a1)
    db = geo2.Vec2Subtract(b2, b1)
    dp = geo2.Vec2Subtract(a1, b1)
    dap = (-da[1], da[0])
    denom = geo2.Vec2Dot(dap, db)
    if not denom:
        return False
    num = geo2.Vec2Dot(dap, dp)
    return geo2.Vec2Scale(geo2.Vec2Add(db, b1), num / denom)


def intersection(L1, L2):
    L1 = line(*L1)
    L2 = line(*L2)
    D = L1[0] * L2[1] - L1[1] * L2[0]
    Dx = L1[2] * L2[1] - L1[1] * L2[2]
    Dy = L1[0] * L2[2] - L1[2] * L2[0]
    if D != 0:
        x = Dx / D
        y = Dy / D
        return (x, y)
    else:
        return False


def intersect_line_segments(seg1, seg2):
    A, B = seg1
    C, D = seg2
    if seg1 == seg2:
        return geo2.Vec2Lerp(A, B, 0.5)
    cV = segment_circle(A, B, C)
    cL = geo2.Vec2Length(cV)
    dV = segment_circle(A, B, D)
    dL = geo2.Vec2Length(dV)
    aV = segment_circle(C, D, A)
    aL = geo2.Vec2Length(aV)
    bV = segment_circle(C, D, B)
    bL = geo2.Vec2Length(bV)
    Ax, Ay = A
    Bx, By = B
    Cx, Cy = C
    Dx, Dy = D
    X = Y = 0.0
    if Ax == Bx and Ay == By or Cx == Dx and Cy == Dy:
        print 'False1'
        return False
    if Ax == Cx and Ay == Cy or Bx == Cx and By == Cy or Ax == Dx and Ay == Dy or Bx == Dx and By == Dy:
        return False
    Bx -= Ax
    By -= Ay
    Cx -= Ax
    Cy -= Ay
    Dx -= Ax
    Dy -= Ay
    distAB = math.sqrt(Bx * Bx + By * By)
    theCos = Bx / distAB
    theSin = By / distAB
    newX = Cx * theCos + Cy * theSin
    Cy = Cy * theCos - Cx * theSin
    Cx = newX
    newX = Dx * theCos + Dy * theSin
    Dy = Dy * theCos - Dx * theSin
    Dx = newX
    if Cy < 0 and Dy < 0 or Cy >= 0 and Dy >= 0:
        return False
    ABpos = Dx + (Cx - Dx) * Dy / (Dy - Cy)
    if ABpos < 0 or ABpos > distAB:
        return False
    X = Ax + ABpos * theCos
    Y = Ay + ABpos * theSin
    return (X, Y)


def closest_point_on_seg(seg_a, seg_b, circ_pos):
    seg_v = geo2.Vec2Subtract(seg_b, seg_a)
    pt_v = geo2.Vec2Subtract(circ_pos, seg_a)
    if geo2.Vec2Length(seg_v) <= 0:
        raise ValueError, 'Invalid segment length'
    seg_v_unit = geo2.Vec2Normalize(seg_v)
    proj = geo2.Vec2Dot(seg_v_unit, pt_v)
    if proj <= 0:
        return seg_a
    if proj >= geo2.Vec2Length(seg_v):
        return seg_b
    proj_v = geo2.Vec2Scale(seg_v_unit, proj)
    closest = geo2.Vec2Add(proj_v, seg_a)
    return closest


def segment_circle(seg_a, seg_b, circ_pos, circ_rad = 1):
    closest = closest_point_on_seg(seg_a, seg_b, circ_pos)
    dist_v = geo2.Vec2Subtract(circ_pos, closest)
    return dist_v


def hex_distance(cr1, cr2):
    r1, c1 = cr1
    r2, c2 = cr2
    return (abs(c1 - c2) + abs(r1 - r2) + abs(c1 + r1 - c2 - r2)) / 2


def hex_path_between(cr1, cr2):
    dist = hex_distance(cr1, cr2)
    c1, r1 = cr1
    c2, r2 = cr2
    ret = []
    for i in xrange(dist):
        ret.append((c1 * (1 - float(i) / dist) + c2 * float(i) / dist, r1 * (1 - float(i) / dist) + r2 * float(i) / dist))

    return ret


def hex_slot_size(isFlatTop, hexSize):
    if isFlatTop:
        width = hexSize * 2
        height = math.sqrt(3.0) / 2.0 * width
    else:
        height = hexSize * 2
        width = math.sqrt(3.0) / 2.0 * height
    return (width, height)


def ccw(A, B, C):
    return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])


def intersect(A, B, C, D):
    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)


def hex_slot_center_position(column, row, isFlatTop, hexSize):
    width, height = hex_slot_size(isFlatTop, hexSize)
    x, y = column, row
    if isFlatTop:
        cX = 0.75 * width * x
        cY = height * y + x % 2 * height * 0.5
    else:
        cX = width * x + y % 2 * width * 0.5
        cY = 0.75 * height * y
    return (cX, cY)


def hex_slot_position(column, row, isFlatTop, hexSize):
    width, height = hex_slot_size(isFlatTop, hexSize)
    x, y = column, row
    if isFlatTop:
        cX = 0.75 * width * x
        cY = height * y + x % 2 * height * 0.5
    else:
        cX = width * x + y % 2 * width * 0.5
        cY = 0.75 * height * y
    return (cX, cY)


def hex_round(x, y, z):
    rx = round(x)
    ry = round(y)
    rz = round(z)
    x_diff = abs(rx - x)
    y_diff = abs(ry - y)
    z_diff = abs(rz - z)
    if x_diff > y_diff and x_diff > z_diff:
        rx = -ry - rz
    elif y_diff > z_diff:
        ry = -rx - rz
    else:
        rz = -rx - ry
    return (int(rx), int(ry), int(rz))


def axial_neighbours(column_row, isFlatTop):
    ret = []
    for direction in xrange(6):
        cr = neighbour_axial(column_row, direction, isFlatTop)
        ret.append(cr)

    return ret


def neighbours_amount_step(column_row, amount, step, isFlatTop, exact = False):
    startpos = column_row
    ret = []
    i = 0
    while len(ret) < amount:
        for s in xrange(step):
            startpos = neighbour_axial(startpos, 4, isFlatTop)

        cr = startpos
        for direction in xrange(6):
            for length in xrange(i + 1):
                for s in xrange(step):
                    cr = neighbour_axial(cr, direction, isFlatTop)

                ret.append(cr)
                if exact and len(ret) == amount:
                    return ret

        if len(ret) >= amount:
            return ret
        i += 1

    return ret


def hex_round_float(x, y, z):
    rx = round(x)
    ry = round(y)
    rz = round(z)
    x_diff = abs(rx - x)
    y_diff = abs(ry - y)
    z_diff = abs(rz - z)
    if x_diff > y_diff and x_diff > z_diff:
        rx = -ry - rz
    elif y_diff > z_diff:
        ry = -rx - rz
    else:
        rz = -rx - ry
    return (rx, ry, rz)


def pixel_to_hex(x, y, hexSize, isFlatTop):
    if isFlatTop:
        column = 2.0 / 3.0 * x / hexSize
        row = (-1.0 / 3.0 * x + 1.0 / 3.0 * math.sqrt(3.0) * y) / hexSize
    else:
        column = (1.0 / 3.0 * math.sqrt(3.0) * x - 1.0 / 3.0 * y) / hexSize
        row = 2.0 / 3.0 * y / hexSize
    return (column, row)


def axial_to_cube_coordinate(column, row):
    x = column
    z = row
    y = -x - z
    return (x, y, z)


def cube_to_axial_coordinate(x, y, z):
    column = x
    row = z
    return (column, row)


def cube_to_odd_r_axial_coordinate(x, y, z):
    column = x + (z - (z & 1)) / 2
    row = z
    return (column, row)


def cube_to_odd_q_axial_coordinate(x, y, z):
    column = x
    row = z + (x - (x & 1)) / 2
    return (column, row)


def sphere_line_intersection(l1, l2, sp, r):
    x1, _, y1 = l1
    x2, _, y2 = l2
    x, _, y = sp
    A = x - x1
    B = y - y1
    C = x2 - x1
    D = y2 - y1
    dot = A * C + B * D
    len_sq = C * C + D * D
    param = dot / len_sq
    if param < 0:
        xx = x1
        yy = y1
    elif param > 1:
        xx = x2
        yy = y2
    else:
        xx = x1 + param * C
        yy = y1 + param * D
    diffVec = geo2.Vec2Subtract((x, y), (xx, yy))
    return diffVec

    def square(f):
        return f * f

    p1 = p2 = None
    a = square(l2[0] - l1[0]) + square(l2[1] - l1[1]) + square(l2[2] - l1[2])
    b = 2.0 * ((l2[0] - l1[0]) * (l1[0] - sp[0]) + (l2[1] - l1[1]) * (l1[1] - sp[1]) + (l2[2] - l1[2]) * (l1[2] - sp[2]))
    c = square(sp[0]) + square(sp[1]) + square(sp[2]) + square(l1[0]) + square(l1[1]) + square(l1[2]) - 2.0 * (sp[0] * l1[0] + sp[1] * l1[1] + sp[2] * l1[2]) - square(r)
    i = b * b - 4.0 * a * c
    from math import sqrt
    if i < 0.0:
        pass
    elif i == 0.0:
        p[0] = 1.0
        mu = -b / (2.0 * a)
        p1 = (l1[0] + mu * (l2[0] - l1[0]), l1[1] + mu * (l2[1] - l1[1]), l1[2] + mu * (l2[2] - l1[2]))
    elif i > 0.0:
        mu = (-b + sqrt(i)) / (2.0 * a)
        p1 = (l1[0] + mu * (l2[0] - l1[0]), l1[1] + mu * (l2[1] - l1[1]), l1[2] + mu * (l2[2] - l1[2]))
        mu = (-b - sqrt(i)) / (2.0 * a)
        p2 = (l1[0] + mu * (l2[0] - l1[0]), l1[1] + mu * (l2[1] - l1[1]), l1[2] + mu * (l2[2] - l1[2]))
    return (p1, p2)
