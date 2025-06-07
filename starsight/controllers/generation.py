import random
from collections import namedtuple
import functools
from typing import Optional
from starsight.models import Spob, SpobType, System, Galaxy
import uuid
import noise

SOLAR_MASS = 2 * 10**30
SOLAR_RAD = 696340

_OCTAVES = 4


Range = namedtuple('Range', ['min', 'max'])


GENERATION_PARAMS = {
    "galaxy_seed": uuid.UUID("fc35429a-dd41-42d7-8559-20b0e6cb6500"),
    "galaxy_cell_size": 20,
    "star_threshold": 0.7,
    "max_jump_dist": 100,
    "jump_threshold": 0.5,

    "binary_chance": 0.333,
    "system_size_max_km": 150000000 * 75,
    "eccentricity_max": 0.5,
    "solar_mass_max": 150 * SOLAR_MASS,
    "solar_mass_min": 0.09 * SOLAR_MASS,
    "solar_rad_max": 40 * SOLAR_RAD,
    "solar_rad_min": 0.12 * SOLAR_RAD,
}

GREEK_ALPHA = ['alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta', 'theta', 'iota', 'kappa', 'lambda', 'mu', 'nu', 'xi', 'omicron', 'pi', 'rho', 'sigma', 'tau', 'upsiolon', 'phi', 'chi', 'psi', 'omega']


def system_designation(guid: str) -> str:
    letters = ''.join({l:'' for l in guid if l in 'abcdef'}.keys()).upper()
    numbers = ''.join({n:'' for n in guid if n in '1234567890'}.keys())
    return f'{letters}-{numbers}'


class Starfield:

    def __init__(self, galaxy: Galaxy):
        self._galaxy: Galaxy = galaxy
        self._cell_size = 20
        self._star_threshold = 0.7
        self._max_jump_dist = 100
        self._jump_threshold = 0.5

        self._snoise_base = self._galaxy.seed.int & 0xFFFFF

        self._systems: dict[System] = {}

    def generate_star_field(self) -> set[System]:
        ...


def generate_star_field(galaxy: Galaxy, window_x: int, window_y: int, width: int, height: int) -> list[System]:
    """
    window_x: x coord in cartesian plane
    window_y: y coord in cartesian plane
    """
    # TODO check for existing guys in the DB
    systems = []
    hyperlinks = []
    seed = galaxy.seed
    base = galaxy.snoise_base
    buckets = {}

    step = GENERATION_PARAMS['galaxy_cell_size']
    for x in range(window_x, window_x + width, step):
        for y in range(window_y, window_y + height, step):
            print(x, y)
            value = (noise.snoise3(x, y, base, octaves=_OCTAVES) + 1.0) / 2.0

            if value < GENERATION_PARAMS['star_threshold']:
                continue
            guid = uuid.uuid5(seed, f'{x},{y}')
            # TODO bake in some semblance of what the stars will be like so it can be used for radius and color
            system = System(
                id=guid,
                galaxy_id=galaxy.id,
                name=system_designation(str(guid)),
                x=x,
                y=y,
            )
            systems.append(system)
            buckets.setdefault(system.bucket(GENERATION_PARAMS['max_jump_dist']), []).append(system)
    print(len(systems))
    print(len(buckets))

    for coords, bucket in buckets.items():
        brothers = bucket[:]
        brothers.extend(buckets.get((coords[0]-1, coords[1]), []))
        brothers.extend(buckets.get((coords[0]+1, coords[1]), []))
        brothers.extend(buckets.get((coords[0]-1, coords[1]+1), []))
        brothers.extend(buckets.get((coords[0], coords[1]+1), []))
        brothers.extend(buckets.get((coords[0]+1, coords[1]+1), []))
        brothers.extend(buckets.get((coords[0]-1, coords[1]-1), []))
        brothers.extend(buckets.get((coords[0], coords[1]-1), []))
        brothers.extend(buckets.get((coords[0]+1, coords[1]-1), []))
        for i, s1 in enumerate(brothers):
            for s2 in brothers[i:]:
                if not s1.are_neighbors(s2, GENERATION_PARAMS['max_jump_dist']):
                    continue
                nx = (s1.x + s2.x) / 2
                ny = (s1.y + s2.y) / 2
                value = (noise.snoise3(nx, ny, base, octaves=_OCTAVES) + 1.0) / 2.0
                if value < GENERATION_PARAMS['jump_threshold']:
                    continue
                s1.hyperlinks.append(s2)


    return systems
