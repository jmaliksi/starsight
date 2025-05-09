import noise
import tkinter
import collections

WIDTH = 1000
HEIGHT = 1000

SCALE = 1
OCTAVES = 4
THRESHOLD = 0.7
CELL_SIZE = 20
BASE = 32
OFFSET_X = 0
OFFSET_Y = 0

MAX_JUMP = 100
LINK_THRESHOLD = 0.5

Star = collections.namedtuple('Star', ['x', 'y', 'r'])


def c2s(x, y):
    return WIDTH / 2 + x, HEIGHT / 2 - y

def s2c(x, y):
    return x - WIDTH / 2, HEIGHT / 2 - y

def jitter(x):
    return 0

def jitter_(x, a=-CELL_SIZE//2, b=CELL_SIZE//2):
    n = int(x * 49033) & 0xFFFFFFFF
    n = int((n ^ (n >> 13)) * 94543) & 0xFFFFFFFF
    n = (n ^ (n >> 16)) & 0xFFFFFFFF
    d = b - a
    r = a + (abs(n) % d)
    return r


def dist(s1, s2, m):
    return (m * m) > (((s1.x - s2.x) ** 2) + ((s1.y - s2.y) ** 2))


def generate_starfield2(canvas, root=None):
    canvas.delete('all')

    stars = []

    step = round(CELL_SIZE * SCALE)

    for y in range(0, int(HEIGHT/SCALE), step):
        for x in range(0, int(WIDTH/SCALE), step):
            nx, ny = s2c(x, y)
            nx = (nx + OFFSET_X - (OFFSET_X % step))
            ny = (ny + OFFSET_Y - (OFFSET_Y % step))
            jx, jy = jitter(nx), jitter(ny)
            nx += jx
            ny += jy
            value = (noise.snoise2(nx * SCALE, ny * SCALE, octaves=OCTAVES, base=BASE) + 1.0) / 2.0

            if value < THRESHOLD:
                continue
            brightness = (value - THRESHOLD) / (1 - THRESHOLD)
            r = max(2.0, brightness * 7)

            stars.append(Star(nx, ny, r))

    for i, star in enumerate(stars):
        for s2 in stars[i:]:
            if not dist(star, s2, MAX_JUMP*SCALE):
                continue
            nx = (star.x + s2.x) / 2
            ny = (star.y + s2.y) / 2
            value = (noise.snoise2(nx*SCALE, ny*SCALE, octaves=OCTAVES, base=BASE) + 1.0) / 2.0
            if value < LINK_THRESHOLD:
                continue
            x1, y1 = c2s(star.x - OFFSET_X, star.y - OFFSET_Y)
            x2, y2 = c2s(s2.x - OFFSET_X, s2.y - OFFSET_Y)

            canvas.create_line(x1, y1, x2, y2, fill='grey', width='1')

    for star in stars:
        dx, dy = c2s(star.x - OFFSET_X, star.y - OFFSET_Y)
        canvas.create_oval(
            dx - star.r, dy - star.r,
            dx + star.r, dy + star.r,
            fill='white', outline='',
        )

from starsight.models import Galaxy
import uuid
galaxy = Galaxy(
    id=uuid.UUID("fc35429a-dd41-42d7-8559-20b0e6cb6500"),
    seed=uuid.UUID("fc35429a-dd41-42d7-8559-20b0e6cb6500"),
    name='wat',
)

def generate_starfield(canvas):
    canvas.delete('all')
    from starsight.controllers.generation import generate_star_field
    systems = generate_star_field(galaxy, round(OFFSET_X - WIDTH/2), round(OFFSET_Y - HEIGHT/2), WIDTH, HEIGHT)

    for system in systems:
        for link in system.hyperlinks:
            x1, y1 = c2s(system.x - OFFSET_X, system.y - OFFSET_Y)
            x2, y2 = c2s(link.x - OFFSET_X, link.y - OFFSET_Y)
            canvas.create_line(x1, y1, x2, y2, fill='grey', width='1')
        dx, dy = c2s(system.x - OFFSET_X, system.y - OFFSET_Y)
        canvas.create_oval(
            dx - 2, dy - 2,
            dx + 2, dy + 2,
            fill='white', outline='',
        )


def move(canvas, dx, dy):
    global OFFSET_X
    global OFFSET_Y
    OFFSET_X += dx
    OFFSET_Y += dy
    generate_starfield(canvas)


def new_base(_):
    global BASE
    BASE +=1

def zoom(canvas, f):
    global SCALE
    SCALE *= f
    generate_starfield(canvas)


def main():
    root = tkinter.Tk()
    canvas = tkinter.Canvas(root, width=WIDTH, height=HEIGHT, bg='black')
    canvas.pack()
    generate_starfield(canvas)
    STEP = 20
    root.bind('w', lambda _: move(canvas, 0, STEP))
    root.bind('s', lambda _: move(canvas, 0, -STEP))
    root.bind('a', lambda _: move(canvas, -STEP, 0))
    root.bind('d', lambda _: move(canvas, STEP, 0))
    root.bind('q', new_base)
    root.bind('[', lambda _: zoom(canvas, 0.8))
    root.bind(']', lambda _: zoom(canvas, 1.1))
    root.mainloop()


if __name__ == '__main__':
    main()
