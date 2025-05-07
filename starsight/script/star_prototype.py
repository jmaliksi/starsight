from dataclasses import dataclass
from enum import Enum
from typing import Optional, List
import math
import pprint
import random
import requests
import uuid

import drawsvg

SOLAR_MASS = 2 * 10**30 # irl **30

ONOMANCER_NAMES = []


def populate_names():
    global ONOMANCER_NAMES
    res = requests.get('https://onomancer.wobscale.lol/api/getNames?threshold=2&limit=20&random=1')
    ONOMANCER_NAMES = res.json()


def get_onomancer_name() -> str:
    global ONOMANCER_NAMES
    if not ONOMANCER_NAMES:
        populate_names()
    return ONOMANCER_NAMES.pop()


@dataclass
class System:
    id: str
    seed: int
    name: str
    gravicenter: 'Spob'


class SpobType(Enum):
    BARYCENTER = 1
    STAR = 2
    PLANET = 3
    MOON = 4
    ASTEROID = 5
    STATION = 6


@dataclass
class Spob:
    id: str
    name: str
    type_: SpobType
    #system: System
    children: List['Spob']
    description: str = ''
    mass: float = 0


@dataclass
class Orbit:
    semi_major: float
    eccentricity: float
    anomaly: float
    theta: float = 0

    @property
    def semi_minor(self):
        return self.semi_major * ((1.0 - (self.eccentricity**2))**(1/2))

    @property
    def x(self):
        return self.semi_major * math.cos(self.theta)

    @property
    def y(self):
        return self.semi_minor * math.sin(self.theta)


@dataclass
class Point:
    x: float
    y: float

    def __str__(self):
        return f'{self.x},{self.y}'


def generate_system(seed: Optional[int] = None) -> System:
    id = uuid.uuid4()
    if seed is None:
        seed = id.int
    rng = random.Random(seed)
    star_system = System(id=str(id), seed=seed, name=get_onomancer_name(), gravicenter=None)
    if rng.random() <= 0.5:
        # binary stars
        barycenter = Spob(
            id=str(uuid.uuid4()),
            name='',
            type_=SpobType.BARYCENTER,
            description='',
            children=[
                generate_star(rng),
                generate_star(rng),
            ] + [
                generate_planet(rng) for _ in range(rng.randint(0, 10))
            ],
        )
        star_system.gravicenter = barycenter
    else:
        star = generate_star(rng)
        star_system.gravicenter = star

    return star_system


def generate_star(rng: random.Random) -> Spob:
    id = uuid.uuid4()
    star = Spob(
        id=str(id),
        name=get_onomancer_name(),
        type_=SpobType.STAR,
        description='',
        children=[
            generate_planet(rng) for _ in range(rng.randint(0, 10))
        ],
    )
    return star


def generate_planet(rng: random.Random) -> Spob:
    planet = Spob(
        id=str(uuid.uuid4()),
        name=get_onomancer_name(),
        type_=SpobType.PLANET,
        description='',
        children=[
            generate_moon(rng) for _ in range(rng.randint(0, 5))
        ],
    )
    return planet


def generate_moon(rng: random.Random) -> Spob:
    moon = Spob(
        id=str(uuid.uuid4()),
        name=get_onomancer_name(),
        type_=SpobType.MOON,
        description='',
        children=[],
    )
    return moon


def draw_star():
    width = 2000
    d = drawsvg.Drawing(
        width,
        width,
        origin='center',
        animation_config=drawsvg.types.SyncedAnimationConfig(
            duration=10,
            #show_playback_progress=True,
            #show_playback_controls=True,
        ),
    )

    def mass_to_radius(m):
        #return ((width / 8) * m) / (150 * SOLAR_MASS)
        FACTOR = 3
        return ((width / 8) * m) / (150 * SOLAR_MASS) / FACTOR

    star1 = Spob(
        id=str(uuid.uuid4()),
        name='',#get_onomancer_name(),
        type_=SpobType.STAR,
        children=[],
        mass=random.uniform(0.09 * SOLAR_MASS, 150 * SOLAR_MASS),
    )
    star2 = Spob(
        id=str(uuid.uuid4()),
        name=get_onomancer_name(),
        type_=SpobType.STAR,
        children=[],
        mass=random.uniform(0.09 * SOLAR_MASS, 150 * SOLAR_MASS),
    )
    barycenter = Spob(
        id=str(uuid.uuid4()),
        name='', #get_onomancer_name(),
        type_=SpobType.BARYCENTER,
        children=[star1, star2],
        mass=star1.mass + star2.mass,
    )
    radius1 = mass_to_radius(star1.mass)
    radius2 = mass_to_radius(star2.mass)
    roche1 = radius1 * 1.26
    roche2 = radius2 * 1.26
    min_distance = roche1 + roche2
    #min_distance = radius2 * ((2*(star1.mass / star2.mass)) ** (1/3)) + (radius1 + radius2)
    max_distance = width / 2
    distance = random.uniform(min_distance, max_distance)

    eccentricity = random.random() * 0.5
    semi_major1 = distance / (1 + star1.mass / star2.mass)
    semi_major2 = distance - semi_major1

    orbit1 = Orbit(
        semi_major=semi_major1,
        eccentricity=eccentricity,
        anomaly=random.random() * math.pi * 2,
        theta=0,
    )
    orbit2 = Orbit(
        semi_major=semi_major2,
        eccentricity=eccentricity,
        anomaly=orbit1.anomaly + math.pi,
        theta=math.pi,
    )
    hill1 = orbit2.semi_major * math.pow(star2.mass / (3 *star2.mass + barycenter.mass), 1/3)
    hill2 = orbit1.semi_major * math.pow(star1.mass / (3 * star1.mass + barycenter.mass), 1/3)

    rocheb = max(orbit1.semi_major + hill1, orbit2.semi_major + hill2) * 1.26
    wiggle = lambda x: x / 100
    coords1 = [
        Point(
            x=orbit1.semi_major * math.cos(wiggle(t) * math.pi * 2),
            y=orbit1.semi_minor * math.sin(wiggle(t) * math.pi * 2),
        ) for t in range(0, 101)
    ]
    coords2 = [
        Point(
            x=orbit2.semi_major * math.cos(math.atan2(c.y, c.x) + math.pi),
            y=orbit2.semi_minor * math.sin(math.atan2(c.y, c.x) + math.pi),
        ) for c in coords1
    ]

    starsystem = drawsvg.Group(id='starsystem', transform=f'rotate({random.random() * 360})')

    group1 = drawsvg.Group(
        id='group1',
        fill_opacity='0',
        origin='center',
        transform=f'translate({orbit1.x - (orbit1.semi_major * eccentricity)}, {orbit1.y})',
    )
    group1.append_anim(drawsvg.AnimateTransform(
        'translate',
        '10s',
        ';'.join(map(str, [Point(x=p.x - (orbit1.semi_major * eccentricity), y=p.y) for p in coords1])),
        repeatCount='indefinite',
    ))
    starsystem.append(group1)
    group2 = drawsvg.Group(
        id='group2',
        fill_opacity='0',
        origin='center',
        transform=f'translate({orbit2.x + (orbit2.semi_major * eccentricity)}, {orbit2.y})',
    )
    group2.append_anim(drawsvg.AnimateTransform(
        'translate',
        '10s',
        ';'.join(map(str, [Point(x=p.x + (orbit2.semi_major * eccentricity), y=p.y) for p in coords2])),
        repeatCount='indefinite',
    ))
    starsystem.append(group2)

    # hill spheres
    group1.append(drawsvg.Circle(
        0, 0,
        hill1,
        stroke='blue',
        fill_opacity='0',
    ))
    group2.append(drawsvg.Circle(
        0, 0,
        hill2,
        stroke='blue',
        fill_opacity='0',
    ))

    # orbits
    starsystem.append(drawsvg.Ellipse(
        -(orbit1.semi_major * eccentricity),
        0,
        orbit1.semi_major,
        orbit1.semi_minor,
        fill_opacity='0',
        stroke='grey',
    ))
    starsystem.append(drawsvg.Ellipse(
        orbit2.semi_major * eccentricity,
        0,
        orbit2.semi_major,
        orbit2.semi_minor,
        fill_opacity='0',
        stroke='grey',
    ))

    # roche
    group1.append(drawsvg.Circle(
        0, 0,
        roche1,
        fill='white',
        stroke='red',
        fill_opacity='0',
    ))
    group2.append(drawsvg.Circle(
        0, 0,
        roche2,
        fill='white',
        stroke='red',
        fill_opacity='0',
    ))
    d.append(drawsvg.Circle(
        0, 0, rocheb, fill_opacity='0', stroke='red', stroke_dasharray='5,5'
    ))

    # star
    starsvg = drawsvg.Circle(
        0, 0,
        radius1,
        fill_opacity='0.5',
        stroke='black',
        fill='white',
    )
    group1.append(starsvg)
    group2.append(drawsvg.Circle(
        0, 0,
        radius2,
        fill_opacity='0.5',
        stroke='black',
        fill='white',
    ))

    # barycenter
    d.append(drawsvg.Line(-5, 0, 5, 0, stroke='black', fill_opacity='0'))
    d.append(drawsvg.Line(0, -5, 0, 5, stroke='black', fill_opacity='0'))
    d.append(starsystem)

    d.save_html('stars.html')


def main():
    # pprint.pprint(generate_system())
    draw_star()

    '''
    d = drawsvg.Drawing(500, 500, origin='center')
    d.append(drawsvg.Ellipse(0, 200, 20, 80, stroke='green', fill='yellow'))
    d.append(drawsvg.Ellipse(0, 0, 10, 10, stroke='blue'))
    d.save_html('output.html')
    '''


if __name__ == '__main__':
    main()
