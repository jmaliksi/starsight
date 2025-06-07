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
BUFFER = CELL_SIZE * 2

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


from starsight.models import Galaxy
import uuid
galaxy = Galaxy(
    id=uuid.UUID("fc35429a-dd41-42d7-8559-20b0e6cb6500"),
    seed=uuid.UUID("fc35429a-dd41-42d7-8559-20b0e6cb6500"),
    name='wat',
)

def generate_starfield():
    from starsight.controllers.generation import generate_star_field
    #systems = generate_star_field(galaxy, round(OFFSET_X - WIDTH/2), round(OFFSET_Y - HEIGHT/2), WIDTH, HEIGHT)
    systems = generate_star_field(galaxy, -10000, -10000, 10000, 10000)
    print(len(systems))
    return systems


def draw_starfield(canvas, systems):
    canvas.delete('all')
    for system in systems:
        if system.x > OFFSET_X + BUFFER + WIDTH/2:
            continue
        if system.y > OFFSET_Y + BUFFER + HEIGHT/2:
            continue
        if system.x < OFFSET_X - BUFFER - WIDTH/2:
            continue
        if system.y < OFFSET_Y - BUFFER - HEIGHT/2:
            continue

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
        canvas.create_text(
            dx,
            dy,
            text=f"{system.name}",
            font=("Arial", 8),
            fill="white",
        )


def move(canvas, systems, dx, dy):
    global OFFSET_X
    global OFFSET_Y
    OFFSET_X += dx
    OFFSET_Y += dy
    draw_starfield(canvas, systems)


def new_base(_):
    global BASE
    BASE +=1

def zoom(canvas, systems, f):
    global SCALE
    SCALE *= f
    draw_starfield(canvas, systems)


def main():
    root = tkinter.Tk()
    canvas = tkinter.Canvas(root, width=WIDTH, height=HEIGHT, bg='black')
    canvas.pack()
    s = generate_starfield()
    draw_starfield(canvas, s)
    STEP = 20
    root.bind('w', lambda _: move(canvas, s, 0, STEP))
    root.bind('s', lambda _: move(canvas, s, 0, -STEP))
    root.bind('a', lambda _: move(canvas, s, -STEP, 0))
    root.bind('d', lambda _: move(canvas, s, STEP, 0))
    root.bind('q', new_base)
    root.bind('[', lambda _: zoom(canvas, s, 0.8))
    root.bind(']', lambda _: zoom(canvas, s, 1.1))
    root.mainloop()


if __name__ == '__main__':
    main()
