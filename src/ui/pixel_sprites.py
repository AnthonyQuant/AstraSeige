"""src/ui/pixel_sprites.py

Multi-color retro pixel-art sprite builder and Turtle compound-shape
registry for AstraSeige (with horizontal run-length polygon merging).
"""

import turtle
from typing import Dict, Optional, Sequence, Tuple

PIXEL_PALETTE: Dict[str, str] = {
    ".": "",          # Transparent
    "K": "#090D16",   # Deep outline / eye cutout
    "W": "#F8FAFC",   # Pure white highlight
    "S": "#CBD5E1",   # Silver hull
    "M": "#64748B",   # Mid slate metal
    "G": "#22C55E",   # Neon alien green
    "L": "#86EFAC",   # Light green highlight
    "P": "#9333EA",   # Deep purple invader / hull
    "V": "#C084FC",   # Violet armor highlight
    "I": "#6366F1",   # Indigo wing shading
    "R": "#F43F5E",   # Crimson red crab / dome
    "O": "#FB923C",   # Coral orange crab / flame
    "Y": "#FACC15",   # Golden yellow crab / coin
    "D": "#D97706",   # Amber coin shadow
    "C": "#38BDF8",   # Electric cyan invader / shield / canopy
    "B": "#0284C7",   # Deep royal blue shield / thruster
    "H": "#EC4899",   # Hot pink invader / heart
}

PURPLE_INVADER_GRID: Tuple[str, ...] = (
    "..P.......P..",
    "..PP.....PP..",
    ".PVPP...PPVP.",
    "PPVPPPPPPPVPP",
    "PPPPVPPPVPPPP",
    "PPP.VPPPV.PPP",
    "PPP.VPPPV.PPP",
    "PPPPPPPPPPPPP",
    ".PPPPPPPPPPP.",
    "..PPP...PPP..",
    ".PP.......PP.",
    "PP.........PP",
)

GREEN_INVADER_GRID: Tuple[str, ...] = (
    "..G.....G..",
    "...G...G...",
    "..GGGGGGG..",
    ".GGLGGGLGG.",
    "GGGGGGGGGGG",
    "GG.GGGGG.GG",
    "GGGGGGGGGGG",
    "G.GGGGGGG.G",
    "G.G.....G.G",
    "...GG.GG...",
)

CRAB_INVADER_TEMPLATE: Tuple[str, ...] = (
    "..X.....X..",
    "...X...X...",
    "..XXXXXXX..",
    ".XX.XXX.XX.",
    "XXXXXXXXXXX",
    "X.XXXXXXX.X",
    "X.X.....X.X",
    "...XX.XX...",
)

SAUCER_ENEMY_GRID: Tuple[str, ...] = (
    ".....RRR.....",
    "....RWWWR....",
    "...RRRRRRR...",
    "..SSSSSSSSS..",
    ".GGGGGGGGGGG.",
    "GGGGGGGGGGGGG",
    "..GG.....GG..",
)

MOTHERSHIP_BOSS_GRID: Tuple[str, ...] = (
    "........RRRRR........",
    "......RRWWWRRRR......",
    ".....RRRWWWRRRRR.....",
    "....RRRRRRRRRRRRR....",
    "..SSSSSSSSSSSSSSSSS..",
    "SSSSSSSSSSSSSSSSSSSSS",
    ".MMMMMMMMMMMMMMMMMMM.",
    "....MMMMMMMMMMMMM....",
    ".......SSSSSSS.......",
    "........MMMMM........",
)

PLAYER_VIPER_GRID: Tuple[str, ...] = (
    "......S......",
    ".....SSS.....",
    ".....SCS.....",
    "....SPCCS....",
    "....SPPPS....",
    "...ISPPPPI...",
    "..IISPPPSII..",
    ".PPISPPPSIPP.",
    "PPPPPPPPPPPPP",
    "PP..YYYYY..PP",
    "....OOOOO....",
    ".....RRR.....",
    "......H......",
)

SHIELD_POWERUP_GRID: Tuple[str, ...] = (
    "....KKKKK....",
    "..KKWWCBBKK..",
    ".KWWWWCBBBBK.",
    "KWWWWWCBBBBBK",
    "KWWWWWCBBBBBK",
    "KBBBBBCWWWWWK",
    "KBBBBBCWWWWWK",
    ".KBBBBCWWWWK.",
    "..KBBBCWWWK..",
    "...KBBCWWK...",
    "....KBCWK....",
    ".....KKK.....",
)

VULCAN_POWERUP_GRID: Tuple[str, ...] = (
    "....YYYY....",
    "..YYOOOOYY..",
    ".YOORRRROOY.",
    "YORRWWWWWRRY",
    "YORRWWWWWRRY",
    ".YOORRRROOY.",
    "..YYOOOOYY..",
    "....YYYY....",
)

CRYSTAL_POWERUP_GRID: Tuple[str, ...] = (
    ".....PP.....",
    "....PVVP....",
    "...PVWWVP...",
    "..PVWWWWVP..",
    ".PVWWCCWWVP.",
    "PVWWCCCCWWVP",
    ".PVWWCCWWVP.",
    "..PVWWWWVP..",
    "...PVWWVP...",
    "....PVVP....",
    ".....PP.....",
)

HEART_FULL_GRID: Tuple[str, ...] = (
    ".HH...HH.",
    "HRRH.HRRH",
    "HRRRRRRRH",
    "HRRRRRRRH",
    ".HRRRRRH.",
    "..HRRRH..",
    "...HRH...",
    "....H....",
)

HEART_EMPTY_GRID: Tuple[str, ...] = (
    ".HH...HH.",
    "H..H.H..H",
    "H...H...H",
    "H.......H",
    ".H.....H.",
    "..H...H..",
    "...H.H...",
    "....H....",
)

GOLD_COIN_GRID: Tuple[str, ...] = (
    "..YYYY..",
    ".YWWWWY.",
    "YWYYYYDY",
    "YWYDDYDY",
    "YWYDDYDY",
    "YWYYYYDY",
    ".YDDDDY.",
    "..DDDD..",
)

MINI_FIGHTER_GRID: Tuple[str, ...] = (
    "...G...",
    "...G...",
    "..GGG..",
    ".GGGGG.",
    "GG.G.GG",
    "G..G..G",
)


def _tint_grid(grid: Sequence[str], token: str) -> Tuple[str, ...]:
    """Replaces placeholder 'X' cells in a template grid with a palette code."""
    return tuple(row.replace("X", token) for row in grid)


def build_compound_shape(
    grid: Sequence[str],
    pixel_size: float = 2.6,
    rotate_for_north: bool = False,
) -> turtle.Shape:
    """Converts a 2D pixel grid into a merged-polygon Turtle compound shape."""
    compound = turtle.Shape("compound")
    rows = len(grid)
    cols = max((len(r) for r in grid), default=0)
    half_w = cols / 2.0
    half_h = rows / 2.0

    for r_idx, row in enumerate(grid):
        c_idx = 0
        row_len = len(row)
        while c_idx < row_len:
            cell = row[c_idx]
            color = PIXEL_PALETTE.get(cell, "")
            if not color:
                c_idx += 1
                continue

            # Merge horizontally contiguous pixels of the same color into 1 rectangle
            span = 1
            while (c_idx + span) < row_len and row[c_idx + span] == cell:
                span += 1

            x0 = (c_idx - half_w) * pixel_size
            x1 = (c_idx + span - half_w) * pixel_size
            y1 = (half_h - r_idx) * pixel_size
            y0 = y1 - pixel_size

            corners = ((x0, y0), (x1, y0), (x1, y1), (x0, y1))
            if rotate_for_north:
                poly = tuple((cy, -cx) for cx, cy in corners)
            else:
                poly = corners

            compound.addcomponent(poly, color, color)
            c_idx += span

    return compound


PIXEL_SPRITE_SPECS: Dict[str, Tuple[Tuple[str, ...], float, bool]] = {
    "purple_invader": (PURPLE_INVADER_GRID, 2.7, False),
    "green_invader": (GREEN_INVADER_GRID, 2.8, False),
    "crab_red": (_tint_grid(CRAB_INVADER_TEMPLATE, "R"), 2.7, False),
    "crab_orange": (_tint_grid(CRAB_INVADER_TEMPLATE, "O"), 2.7, False),
    "crab_cyan": (_tint_grid(CRAB_INVADER_TEMPLATE, "C"), 2.7, False),
    "crab_pink": (_tint_grid(CRAB_INVADER_TEMPLATE, "H"), 2.7, False),
    "crab_yellow": (_tint_grid(CRAB_INVADER_TEMPLATE, "Y"), 2.7, False),
    "saucer_enemy": (SAUCER_ENEMY_GRID, 2.8, False),
    "mothership_boss": (MOTHERSHIP_BOSS_GRID, 4.2, False),
    "player_viper": (PLAYER_VIPER_GRID, 2.9, False),
    "powerup_shield": (SHIELD_POWERUP_GRID, 2.2, False),
    "powerup_vulcan": (VULCAN_POWERUP_GRID, 2.5, False),
    "powerup_crystal": (CRYSTAL_POWERUP_GRID, 2.2, False),
    "hud_heart_full": (HEART_FULL_GRID, 2.3, False),
    "hud_heart_empty": (HEART_EMPTY_GRID, 2.3, False),
    "hud_coin": (GOLD_COIN_GRID, 2.2, False),
    "hud_mini_ship": (MINI_FIGHTER_GRID, 2.5, False),
}


def register_pixel_sprites(screen: Optional[turtle._Screen] = None) -> None:
    """Registers all multi-color pixel-art compound shapes onto the Turtle screen."""
    target_screen = screen if screen is not None else turtle.Screen()
    existing = set(target_screen.getshapes())

    for name, (grid, pixel_size, rotate_north) in PIXEL_SPRITE_SPECS.items():
        if name not in existing:
            shape = build_compound_shape(
                grid=grid,
                pixel_size=pixel_size,
                rotate_for_north=rotate_north,
            )
            target_screen.register_shape(name, shape)


def resolve_pixel_sprite(
    preferred_shape: str,
    fallback_shape: str,
    screen: Optional[turtle._Screen] = None,
) -> str:
    """Returns `preferred_shape` if registered on the Turtle screen, else `fallback_shape`."""
    try:
        target_screen = screen if screen is not None else turtle.Screen()
        if preferred_shape in target_screen.getshapes():
            return preferred_shape
    except Exception:
        pass
    return fallback_shape