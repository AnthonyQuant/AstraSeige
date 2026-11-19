"""src/ui/effects.py

Visual effects engine providing a smooth 3-layer parallax scrolling starfield,
fiery pixel explosion bursts, Mothership plasma beam rendering, shockwave rings,
and floating score/power-up callouts for AstraSeige with delta-time support.
"""

from dataclasses import dataclass
import math
import random
import turtle
from typing import List, Tuple

from config import SCREEN_HEIGHT, SCREEN_WIDTH


@dataclass
class _Star:
    """Represents a persistent star Turtle in one of three parallax depth layers."""

    sprite: turtle.Turtle
    x: float
    y: float
    speed: float


@dataclass
class _Particle:
    """Represents a short-lived pixel explosion spark rendered via pen dots."""

    x: float
    y: float
    vx: float
    vy: float
    life: float
    color: str
    size: int


@dataclass
class _PulseRing:
    """Represents an expanding circular shockwave for shield impacts and pickups."""

    x: float
    y: float
    radius: float
    growth: float
    life: float
    color: str


@dataclass
class _FloatingLabel:
    """Represents a brief upward-drifting text callout (e.g., +10Pt, SHIELD BLOCK!)."""

    x: float
    y: float
    vy: float
    life: float
    text: str
    color: str


class Effects:
    """Manages ambient starfield motion, plasma beams, and transient combat effects."""

    MAX_PARTICLES: int = 120
    MAX_RINGS: int = 10
    MAX_LABELS: int = 10

    def __init__(self, star_count: int = 34) -> None:
        self._half_w: float = SCREEN_WIDTH / 2.0
        self._half_h: float = SCREEN_HEIGHT / 2.0

        self._fx_pen = turtle.Turtle(visible=False)
        self._fx_pen.penup()
        self._fx_pen.speed(0)

        self._stars: List[_Star] = []
        self._particles: List[_Particle] = []
        self._rings: List[_PulseRing] = []
        self._labels: List[_FloatingLabel] = []
        self._fx_dirty: bool = False

        self._init_starfield(max(12, int(star_count)))

    def _init_starfield(self, count: int) -> None:
        for star in self._stars:
            try:
                star.sprite.hideturtle()
            except Exception:
                pass
        self._stars.clear()

        layers: Tuple[Tuple[float, float, str, float], ...] = (
            (0.35, 0.10, "#334155", 0.50),
            (0.85, 0.13, "#64748B", 0.32),
            (1.55, 0.17, "#94A3B8", 0.18),
        )

        for _ in range(count):
            roll = random.random()
            if roll < layers[0][3]:
                speed, scale, color, _ = layers[0]
            elif roll < layers[0][3] + layers[1][3]:
                speed, scale, color, _ = layers[1]
            else:
                speed, scale, color, _ = layers[2]

            x = random.uniform(-self._half_w + 10, self._half_w - 10)
            y = random.uniform(-self._half_h + 10, self._half_h - 10)

            star_turtle = turtle.Turtle(visible=False)
            star_turtle.penup()
            star_turtle.speed(0)
            star_turtle.shape("square")
            star_turtle.shapesize(stretch_wid=scale, stretch_len=scale)
            star_turtle.color(color)
            star_turtle.goto(x, y)
            star_turtle.showturtle()

            self._stars.append(_Star(sprite=star_turtle, x=x, y=y, speed=speed))

    def _update_stars(self, speed_scale: float = 1.0, dt: float = 1.0) -> None:
        top_edge = self._half_h - 6.0
        bottom_edge = -self._half_h + 6.0
        step = speed_scale * dt

        for star in self._stars:
            star.y -= star.speed * step
            if star.y < bottom_edge:
                star.y = top_edge
                star.x = random.uniform(-self._half_w + 10, self._half_w - 10)
                star.sprite.goto(star.x, star.y)
            else:
                star.sprite.sety(star.y)

    def spawn_explosion(
        self,
        x: float,
        y: float,
        color: str = "#FACC15",
        count: int = 12,
    ) -> None:
        palette = ("#EF4444", "#F97316", "#FACC15", color, "#FEF9C3")

        for _ in range(3):
            if len(self._particles) >= self.MAX_PARTICLES:
                self._particles.pop(0)
            self._particles.append(
                _Particle(
                    x=x + random.uniform(-4.0, 4.0),
                    y=y + random.uniform(-4.0, 4.0),
                    vx=random.uniform(-0.8, 0.8),
                    vy=random.uniform(-0.8, 0.8),
                    life=float(random.randint(8, 12)),
                    color=random.choice(("#FACC15", "#FEF9C3", "#F97316")),
                    size=random.choice((6, 8)),
                )
            )

        for idx in range(max(4, int(count))):
            if len(self._particles) >= self.MAX_PARTICLES:
                self._particles.pop(0)

            angle = (2.0 * math.pi * idx / count) + random.uniform(-0.28, 0.28)
            speed = random.uniform(1.8, 5.4)
            self._particles.append(
                _Particle(
                    x=x,
                    y=y,
                    vx=math.cos(angle) * speed,
                    vy=math.sin(angle) * speed,
                    life=float(random.randint(10, 18)),
                    color=random.choice(palette),
                    size=random.choice((4, 5, 6)),
                )
            )

    def spawn_ring_flash(
        self,
        x: float,
        y: float,
        color: str = "#38BDF8",
        start_radius: float = 14.0,
        growth: float = 3.2,
        life: int = 10,
    ) -> None:
        if len(self._rings) >= self.MAX_RINGS:
            self._rings.pop(0)

        self._rings.append(
            _PulseRing(
                x=x,
                y=y,
                radius=start_radius,
                growth=growth,
                life=float(max(3, int(life))),
                color=color,
            )
        )

    def spawn_floating_label(
        self,
        x: float,
        y: float,
        text: str,
        color: str = "#FACC15",
    ) -> None:
        if not text:
            return
        if len(self._labels) >= self.MAX_LABELS:
            self._labels.pop(0)

        self._labels.append(
            _FloatingLabel(
                x=x,
                y=y,
                vy=1.35,
                life=24.0,
                text=text,
                color=color,
            )
        )

    def draw_plasma_beam(
        self,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
    ) -> None:
        self._fx_dirty = True

        self._fx_pen.pensize(14)
        self._fx_pen.color("#EA580C")
        self._fx_pen.goto(start_x, start_y)
        self._fx_pen.pendown()
        self._fx_pen.goto(end_x, end_y)
        self._fx_pen.penup()

        self._fx_pen.pensize(8)
        self._fx_pen.color("#FACC15")
        self._fx_pen.goto(start_x, start_y)
        self._fx_pen.pendown()
        self._fx_pen.goto(end_x, end_y)
        self._fx_pen.penup()

        self._fx_pen.pensize(3)
        self._fx_pen.color("#FEF9C3")
        self._fx_pen.goto(start_x, start_y)
        self._fx_pen.pendown()
        self._fx_pen.goto(end_x, end_y)
        self._fx_pen.penup()

        flare_palette = ("#DC2626", "#F97316", "#FACC15", "#FEF08A")
        for _ in range(8):
            jitter_x = end_x + random.uniform(-18.0, 18.0)
            jitter_y = end_y + random.uniform(-16.0, 16.0)
            self._fx_pen.goto(jitter_x, jitter_y)
            self._fx_pen.dot(random.choice((6, 8, 10)), random.choice(flare_palette))

    def clear_transient(self) -> None:
        self._particles.clear()
        self._rings.clear()
        self._labels.clear()
        self._fx_pen.clear()
        self._fx_dirty = False

    def update(
        self,
        scroll_stars: bool = True,
        star_speed_scale: float = 1.0,
        dt: float = 1.0,
    ) -> None:
        """Advances ambient stars and renders active combat effects scaled by `dt`."""
        if scroll_stars:
            self._update_stars(speed_scale=star_speed_scale, dt=dt)

        if self._fx_dirty:
            self._fx_pen.clear()
            self._fx_dirty = False

        if not self._particles and not self._rings and not self._labels:
            return

        self._fx_dirty = True
        drag = 0.93 ** dt

        if self._particles:
            surviving_particles: List[_Particle] = []
            for p in self._particles:
                p.x += p.vx * dt
                p.y += p.vy * dt
                p.vx *= drag
                p.vy *= drag
                p.life -= dt
                if p.life > 0:
                    dot_size = max(2, int(p.size * (p.life / 14.0)))
                    self._fx_pen.goto(p.x, p.y)
                    self._fx_pen.dot(dot_size, p.color)
                    surviving_particles.append(p)
            self._particles = surviving_particles

        if self._rings:
            surviving_rings: List[_PulseRing] = []
            self._fx_pen.pensize(2)
            for ring in self._rings:
                ring.radius += ring.growth * dt
                ring.life -= dt
                if ring.life > 0:
                    self._fx_pen.color(ring.color)
                    self._fx_pen.goto(ring.x, ring.y - ring.radius)
                    self._fx_pen.pendown()
                    self._fx_pen.circle(ring.radius)
                    self._fx_pen.penup()
                    surviving_rings.append(ring)
            self._rings = surviving_rings

        if self._labels:
            surviving_labels: List[_FloatingLabel] = []
            for label in self._labels:
                label.y += label.vy * dt
                label.life -= dt
                if label.life > 0:
                    self._fx_pen.color(label.color)
                    self._fx_pen.goto(label.x, label.y)
                    self._fx_pen.write(
                        label.text,
                        align="center",
                        font=("Courier", 10, "bold"),
                    )
                    surviving_labels.append(label)
            self._labels = surviving_labels