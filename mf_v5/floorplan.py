"""Corridor-aware deterministic BSP floorplan generation."""

from __future__ import annotations

import random
from typing import List, Sequence, Tuple

from .config import CORRIDOR_WIDTH, EPSILON, MIN_ROOM_SIZE, snap
from .datamodel import Corridor, Rect, Room


def split_rect(rect: Rect, vertical: bool, split_pos: float) -> Tuple[Rect, Rect]:
    if vertical:
        return (
            Rect(rect.min_x, rect.min_y, split_pos, rect.max_y),
            Rect(split_pos, rect.min_y, rect.max_x, rect.max_y),
        )
    return (
        Rect(rect.min_x, rect.min_y, rect.max_x, split_pos),
        Rect(rect.min_x, split_pos, rect.max_x, rect.max_y),
    )


def intersects(a: Rect, b: Rect) -> bool:
    return not (
        a.max_x <= b.min_x + EPSILON
        or a.min_x >= b.max_x - EPSILON
        or a.max_y <= b.min_y + EPSILON
        or a.min_y >= b.max_y - EPSILON
    )


def _room_large_enough(rect: Rect) -> bool:
    return rect.width() >= MIN_ROOM_SIZE - EPSILON and rect.height() >= MIN_ROOM_SIZE - EPSILON


def generate_floorplan(width: float, depth: float, seed: int, floor_index: int) -> Tuple[List[Room], Corridor]:
    rng = random.Random(seed + floor_index)
    width = snap(width)
    depth = snap(depth)

    main_rect = Rect(0.0, 0.0, width, depth)

    cx = snap(width / 2 - CORRIDOR_WIDTH / 2)
    corridor = Corridor(Rect(cx, 0.0, cx + CORRIDOR_WIDTH, depth), floor_index)

    rooms: List[Room] = []
    queue = [main_rect]
    room_id = 0

    while queue:
        rect = queue.pop()

        # If rect is already the corridor or inside it, skip
        if intersects(rect, corridor.rect) and (rect.min_x >= corridor.rect.min_x - EPSILON and rect.max_x <= corridor.rect.max_x + EPSILON):
            continue

        # Try to split to isolate corridor
        # If corridor is inside rect X-range, split at corridor boundaries
        if corridor.rect.min_x > rect.min_x + EPSILON and corridor.rect.min_x < rect.max_x - EPSILON:
            r1, r2 = split_rect(rect, True, corridor.rect.min_x)
            queue.append(r1)
            queue.append(r2)
            continue
        if corridor.rect.max_x > rect.min_x + EPSILON and corridor.rect.max_x < rect.max_x - EPSILON:
            r1, r2 = split_rect(rect, True, corridor.rect.max_x)
            queue.append(r1)
            queue.append(r2)
            continue

        # Normal BSP split
        if rect.width() < 2 * MIN_ROOM_SIZE and rect.height() < 2 * MIN_ROOM_SIZE:
            if not intersects(rect, corridor.rect) and _room_large_enough(rect):
                rooms.append(Room(rect, floor_index, room_id))
                room_id += 1
            continue

        # Choose split axis
        vertical = rect.width() > rect.height()
        split = snap(rect.min_x + rect.width() / 2) if vertical else snap(rect.min_y + rect.height() / 2)
        
        r1, r2 = split_rect(rect, vertical, split)
        
        if not _room_large_enough(r1) or not _room_large_enough(r2):
            if not intersects(rect, corridor.rect) and _room_large_enough(rect):
                rooms.append(Room(rect, floor_index, room_id))
                room_id += 1
            continue

        queue.append(r1)
        queue.append(r2)

    return sorted(rooms, key=lambda r: r.id), corridor
