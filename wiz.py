#!/usr/bin/env python3
"""
Wizardry-style 3D Dungeon Crawler
First-person perspective grid-based dungeon exploration.
"""

import curses
import random
import json
import os
import math

# ── Direction constants ────────────────────────────────────────────────────
NORTH, EAST, SOUTH, WEST = 0, 1, 2, 3
DIR_NAMES = ['North', 'East', 'South', 'West']
DX = [0, 1, 0, -1]
DY = [-1, 0, 1, 0]

# ── 3D View settings ──────────────────────────────────────────────────────
VIEW_W = 60
VIEW_H = 20
FOV_DEG = 90.0
FOV_RAD = math.radians(FOV_DEG)
MAX_RENDER_DIST = 15.0
WALL_CHARS = '█▓▒░·'

# ── Emoji (HUD & sprites in inventory) ────────────────────────────────────
PLAYER_EMOJI = '🧙'
GOLD_EMOJI = '🪙'
FOOD_EMOJI = '🍗'
POTION_EMOJI = '🧪'
SWORD_EMOJI = '⚔️'
SPEAR_EMOJI = '🔱'
ARMOR_EMOJI = '🛡️'
MAGIC_EMOJI = '✨'
T_STAIRS_EMOJI = '🔽'

# ── Monster emoji (used in HUD/inventory, 3D view uses letters) ──────────
MONSTER_EMOJI = {
    'Ant': '🐜', 'Bat': '🦇', 'Centipede': '🦂', 'Dog': '🐕',
    'Eye': '🟡', 'Frog': '🐸', 'Goblin': '👾', 'Harpy': '🦅',
    'Imp': '🎃', 'Jackal': '🐺', 'Kobold': '🦎', 'Lich': '☠️',
    'Mummy': '🧛', 'Ogre': '🗿', 'Troll': '🦖', 'Wyrm': '🐉',
}

# ── Difficulty presets ─────────────────────────────────────────────────────
DIFFICULTIES = {
    1: {'name': 'Easy',   'mw': 20, 'mh': 14, 'dmg_scale': 0.5, 'spawn_scale': 0.6,
        'item_scale': 1.5, 'fov_r': 8, 'min_room': 3, 'max_room': 6, 'max_rooms': 6},
    2: {'name': 'Middle', 'mw': 28, 'mh': 20, 'dmg_scale': 1.0, 'spawn_scale': 1.0,
        'item_scale': 1.0, 'fov_r': 6, 'min_room': 4, 'max_room': 7, 'max_rooms': 8},
    3: {'name': 'Hard',   'mw': 28, 'mh': 20, 'dmg_scale': 1.5, 'spawn_scale': 1.4,
        'item_scale': 0.6, 'fov_r': 5, 'min_room': 4, 'max_room': 7, 'max_rooms': 11},
}

# ── Monster templates ──────────────────────────────────────────────────────
MONSTER_TEMPLATES = [
    ('Ant', 5, 2, 1), ('Bat', 8, 3, 2), ('Centipede', 10, 4, 3),
    ('Dog', 15, 5, 5), ('Eye', 20, 6, 8), ('Frog', 25, 7, 10),
    ('Goblin', 30, 8, 12), ('Harpy', 35, 9, 15), ('Imp', 40, 10, 18),
    ('Jackal', 45, 11, 20), ('Kobold', 50, 12, 22), ('Lich', 60, 15, 30),
    ('Mummy', 70, 16, 35), ('Ogre', 80, 18, 40), ('Troll', 90, 20, 45),
    ('Wyrm', 120, 25, 60),
]

# ── Equipment types ────────────────────────────────────────────────────────
EQ_FIST, EQ_SWORD, EQ_SPEAR, EQ_MAGIC, EQ_ARMOR = range(5)
EQUIP_NAMES = {EQ_FIST: 'Fist', EQ_SWORD: 'Sword', EQ_SPEAR: 'Spear',
               EQ_MAGIC: 'Magic', EQ_ARMOR: 'Armor'}
EQUIP_EMOJI = {EQ_FIST: '🤜', EQ_SWORD: SWORD_EMOJI, EQ_SPEAR: SPEAR_EMOJI,
               EQ_MAGIC: MAGIC_EMOJI, EQ_ARMOR: ARMOR_EMOJI}

# ── Colors ─────────────────────────────────────────────────────────────────
CP = {'player': 1, 'monster': 2, 'gold': 3, 'item': 4, 'wall': 5,
      'floor': 6, 'stairs': 7, 'msg': 8, 'hp': 9, 'hp_low': 10, 'title': 11,
      'inventory': 12, 'hud': 13}

# ── Types ──────────────────────────────────────────────────────────────────

class Rect:
    __slots__ = ('x', 'y', 'w', 'h')
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h
    @property
    def cx(self): return self.x + self.w // 2
    @property
    def cy(self): return self.y + self.h // 2
    def intersect(self, o):
        return (self.x <= o.x + o.w and self.x + self.w >= o.x and
                self.y <= o.y + o.h and self.y + self.h >= o.y)

class Entity:
    __slots__ = ('x', 'y', 'ch', 'color', 'blocks', 'name',
                 'hp', 'max_hp', 'damage', 'xp', 'gold',
                 'weapon_type', 'armor_bonus', 'inventory',
                 'weapon_item', 'armor_item', 'attack_range', 'facing')
    def __init__(self, x, y, ch, color, blocks=False,
                 name='', hp=0, max_hp=0, damage=0, xp=0):
        self.x, self.y = x, y
        self.ch, self.color = ch, color
        self.blocks = blocks
        self.name = name
        self.hp, self.max_hp, self.damage, self.xp = hp, max_hp, damage, xp
        self.gold = 0
        self.weapon_type = EQ_FIST
        self.armor_bonus = 0
        self.inventory = []
        self.weapon_item = None
        self.armor_item = None
        self.attack_range = 1
        self.facing = SOUTH

class Item:
    __slots__ = ('x', 'y', 'emoji', 'name', 'type', 'value',
                 'equip_type', 'range_val')
    def __init__(self, x, y, emoji, name, itype, value=0,
                 equip_type=None, range_val=0):
        self.x, self.y = x, y
        self.emoji = emoji
        self.name = name
        self.type = itype
        self.value = value
        self.equip_type = equip_type
        self.range_val = range_val

class Game:
    def __init__(self, diff=2):
        d = DIFFICULTIES[diff]
        self.diff = diff
        self.name = d['name']
        self.MAP_W = d['mw']
        self.MAP_H = d['mh']
        self.dmg_scale = d['dmg_scale']
        self.spawn_scale = d['spawn_scale']
        self.item_scale = d['item_scale']
        self.FOV_R = d['fov_r']
        self.min_room = d['min_room']
        self.max_room = d['max_room']
        self.max_rooms = d['max_rooms']
        self.map = None
        self.explored = None
        self.visible = None
        self.rooms = []
        self.entities = []
        self.items = []
        self.messages = []
        self.player = None
        self.game_over = False
        self.dlvl = 1
        self.current_slot = 0
    def add_msg(self, msg):
        self.messages.append(msg)
        if len(self.messages) > 100:
            self.messages = self.messages[-50:]

# ── Map Generation ─────────────────────────────────────────────────────────

def gen_level(g):
    W, H = g.MAP_W, g.MAP_H
    g.map = [[ord('#')] * W for _ in range(H)]
    g.explored = [[False] * W for _ in range(H)]
    g.visible = [[False] * W for _ in range(H)]
    g.rooms = []
    g.entities = [e for e in g.entities if e == g.player]
    g.items = []
    g.player.x, g.player.y = 1, 1
    g.player.facing = SOUTH

    rcount = random.randint(g.max_rooms - 2, g.max_rooms)
    for _ in range(rcount * 3):
        if len(g.rooms) >= rcount:
            break
        w = random.randint(g.min_room, g.max_room)
        h = random.randint(g.min_room, g.max_room)
        x = random.randint(1, W - w - 2)
        y = random.randint(1, H - h - 2)
        r = Rect(x, y, w, h)
        if not any(r.intersect(or_) for or_ in g.rooms):
            g.rooms.append(r)
            for ry in range(r.y, r.y + r.h):
                for rx in range(r.x, r.x + r.w):
                    if 0 <= ry < H and 0 <= rx < W:
                        g.map[ry][rx] = ord('.')

    if not g.rooms:
        r = Rect(1, 1, 5, 4)
        g.rooms.append(r)
        for ry in range(r.y, r.y + r.h):
            for rx in range(r.x, r.x + r.w):
                g.map[ry][rx] = ord('.')

    for i in range(1, len(g.rooms)):
        a, b = g.rooms[i - 1], g.rooms[i]
        if random.random() < 0.5:
            for x in range(min(a.cx, b.cx), max(a.cx, b.cx) + 1):
                if 0 < a.cy < H - 1 and 0 < x < W - 1:
                    g.map[a.cy][x] = ord('.')
            for y in range(min(a.cy, b.cy), max(a.cy, b.cy) + 1):
                if 0 < y < H - 1 and 0 < b.cx < W - 1:
                    g.map[y][b.cx] = ord('.')
        else:
            for y in range(min(a.cy, b.cy), max(a.cy, b.cy) + 1):
                if 0 < y < H - 1 and 0 < a.cx < W - 1:
                    g.map[y][a.cx] = ord('.')
            for x in range(min(a.cx, b.cx), max(a.cx, b.cx) + 1):
                if 0 < b.cy < H - 1 and 0 < x < W - 1:
                    g.map[b.cy][x] = ord('.')

    r0 = g.rooms[0]
    g.player.x, g.player.y = r0.cx, r0.cy

    rl = g.rooms[-1]
    if len(g.rooms) > 1:
        g.items.append(Item(rl.cx, rl.cy, T_STAIRS_EMOJI, 'Stairs Down', 'stairs'))

    spawn_count = max(1, int(3 * g.spawn_scale))
    for r in g.rooms[1:]:
        for _ in range(random.randint(0, spawn_count)):
            x = random.randint(r.x + 1, r.x + r.w - 2)
            y = random.randint(r.y + 1, r.y + r.h - 2)
            if any(e.x == x and e.y == y for e in g.entities):
                continue
            mname, hp, dmg, xp = random.choice(MONSTER_TEMPLATES)
            s = 1.0 + (g.dlvl - 1) * 0.3
            m = Entity(x, y, MONSTER_EMOJI.get(mname, '👾'), CP['monster'],
                       blocks=True, name=mname,
                       hp=max(1, int(hp * s * g.dmg_scale)),
                       max_hp=max(1, int(hp * s * g.dmg_scale)),
                       damage=max(1, int(dmg * s * g.dmg_scale)),
                       xp=max(1, int(xp * s)))
            g.entities.append(m)

    for r in g.rooms[1:]:
        for _ in range(random.randint(0, max(1, int(2 * g.item_scale)))):
            x = random.randint(r.x + 1, r.x + r.w - 2)
            y = random.randint(r.y + 1, r.y + r.h - 2)
            if any(e.x == x and e.y == y for e in g.entities):
                continue
            if any(it.x == x and it.y == y for it in g.items):
                continue
            roll = random.random()
            if roll < 0.2:
                g.items.append(Item(x, y, GOLD_EMOJI,
                    f'{random.randint(1, 10 * g.dlvl)} gold', 'gold',
                    random.randint(1, 10 * g.dlvl)))
            elif roll < 0.30:
                g.items.append(Item(x, y, FOOD_EMOJI, 'food ration', 'food'))
            elif roll < 0.45:
                g.items.append(Item(x, y, POTION_EMOJI,
                    'healing potion' if random.random() < 0.4 else 'strength potion',
                    'potion_heal' if random.random() < 0.4 else 'potion_str'))
            elif roll < 0.65:
                b = random.randint(1, max(1, g.dlvl))
                t = random.choice([EQ_SWORD, EQ_SPEAR])
                g.items.append(Item(x, y, SWORD_EMOJI if t == EQ_SWORD else SPEAR_EMOJI,
                    f"{EQUIP_NAMES[t]} +{b}", 'weapon', b, t, b))
            elif roll < 0.80:
                if random.random() < 0.3:
                    g.items.append(Item(x, y, MAGIC_EMOJI,
                        'Magic Staff', 'weapon', 2, EQ_MAGIC, 2))
                else:
                    b = random.randint(1, max(1, g.dlvl))
                    g.items.append(Item(x, y, ARMOR_EMOJI,
                        f'Armor +{b}', 'armor', b, EQ_ARMOR, b))
            else:
                b = random.randint(1, max(1, g.dlvl))
                g.items.append(Item(x, y, ARMOR_EMOJI,
                    f'Armor +{b}', 'armor', b, EQ_ARMOR, b))

# ── Raycasting ─────────────────────────────────────────────────────────────

def cast_ray(g, px, py, angle_deg):
    """Cast a ray from integer position px,py at angle_deg (0=East, 90=South).
    Returns (distance, side) where side=0 for vertical hit, 1 for horizontal."""
    rad = math.radians(angle_deg)
    rx, ry = px + 0.5, py + 0.5
    dx, dy = math.cos(rad), math.sin(rad)
    map_x, map_y = int(rx), int(ry)
    delta_x = abs(1 / dx) if dx != 0 else 1e30
    delta_y = abs(1 / dy) if dy != 0 else 1e30
    if dx < 0:
        step_x, side_x = -1, (rx - map_x) * delta_x
    else:
        step_x, side_x = 1, (map_x + 1.0 - rx) * delta_x
    if dy < 0:
        step_y, side_y = -1, (ry - map_y) * delta_y
    else:
        step_y, side_y = 1, (map_y + 1.0 - ry) * delta_y
    for _ in range(int(MAX_RENDER_DIST * 3)):
        if side_x < side_y:
            side_x += delta_x
            map_x += step_x
            side = 0
        else:
            side_y += delta_y
            map_y += step_y
            side = 1
        if not (0 <= map_x < g.MAP_W and 0 <= map_y < g.MAP_H):
            return (MAX_RENDER_DIST * 2, side)
        if g.map[map_y][map_x] == ord('#'):
            dist = (side_x - delta_x) if side == 0 else (side_y - delta_y)
            return (dist, side)
    return (MAX_RENDER_DIST * 2, 0)


def render_3d_view(g):
    """Wireframe 3D view — continuous polyline only."""
    buf = [[' ' for _ in range(VIEW_W)] for _ in range(VIEW_H)]
    p_deg = g.player.facing * 90 - 90
    p_rad = math.radians(p_deg)
    px, py = g.player.x, g.player.y

    strips = []
    for sx in range(VIEW_W):
        cam_x = 2.0 * sx / VIEW_W - 1.0
        a = p_deg + math.degrees(math.atan(cam_x * math.tan(FOV_RAD / 2)))
        dist, side = cast_ray(g, px, py, a)
        corr = dist * math.cos(math.radians(a - p_deg))
        if corr < 0.01:
            corr = 0.01
        wh = int(VIEW_H / corr)
        if wh > VIEW_H:
            wh = VIEW_H
        top = (VIEW_H - wh) // 2
        bot = top + wh
        strips.append((top, bot))

    def draw_line(y1, y2, x1, x2):
        if y1 == y2:
            for x in range(min(x1, x2), max(x1, x2) + 1):
                if 0 <= y1 < VIEW_H and 0 <= x < VIEW_W and buf[y1][x] == ' ':
                    buf[y1][x] = '─'
        elif x1 == x2:
            for y in range(min(y1, y2), max(y1, y2) + 1):
                if 0 <= y < VIEW_H and 0 <= x1 < VIEW_W and buf[y][x1] == ' ':
                    buf[y][x1] = '│'

    prev_x = None
    prev_top = None
    prev_bot = None
    for sx, (top, bot) in enumerate(strips):
        if prev_top is not None:
            draw_line(prev_top, top, prev_x, sx)
            draw_line(prev_bot, bot, prev_x, sx)
        prev_x, prev_top, prev_bot = sx, top, bot

    # ── Sprites (monsters: letter, items: symbol) ──────────────────────
    sprites = []
    for e in g.entities:
        if e is g.player or not g.visible[e.y][e.x]:
            continue
        rdx, rdy = e.x - px, e.y - py
        dist = math.sqrt(rdx * rdx + rdy * rdy)
        if dist > MAX_RENDER_DIST:
            continue
        a_to = math.atan2(rdy, rdx)
        a_diff = a_to - p_rad
        while a_diff < -math.pi: a_diff += 2 * math.pi
        while a_diff > math.pi: a_diff -= 2 * math.pi
        if abs(a_diff) > FOV_RAD / 2:
            continue
        sprites.append((dist, a_diff, e.name[0].upper()))

    for it in g.items:
        if it.type == 'stairs' or not g.visible[it.y][it.x]:
            continue
        rdx, rdy = it.x - px, it.y - py
        dist = math.sqrt(rdx * rdx + rdy * rdy)
        if dist > MAX_RENDER_DIST:
            continue
        a_to = math.atan2(rdy, rdx)
        a_diff = a_to - p_rad
        while a_diff < -math.pi: a_diff += 2 * math.pi
        while a_diff > math.pi: a_diff -= 2 * math.pi
        if abs(a_diff) > FOV_RAD / 2:
            continue
        sym = {'gold': '$', 'food': '%', 'potion_heal': '!', 'potion_str': '!',
               'weapon': ')', 'armor': '['}.get(it.type, '?')
        sprites.append((dist, a_diff, sym))

    sprites.sort(key=lambda s: -s[0])
    for dist, a_diff, ch in sprites:
        sx = int(((a_diff / FOV_RAD) + 0.5) * VIEW_W)
        if not (0 <= sx < VIEW_W):
            continue
        sh = max(1, int(VIEW_H / (dist * 1.5)))
        sy = (VIEW_H - sh) // 2
        if 0 <= sy < VIEW_H and buf[sy][sx] == ' ':
            buf[sy][sx] = ch

    return [''.join(row) for row in buf]


# ── FOV (for monster AI and sprite visibility) ─────────────────────────────

def has_los(g, x0, y0, x1, y1):
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    x, y = x0, y0
    while True:
        if x == x1 and y == y1:
            return True
        if (x != x0 or y != y0) and g.map[y][x] == ord('#'):
            return False
        e2 = 2 * err
        if e2 > -dy:
            err -= dy; x += sx
        if e2 < dx:
            err += dx; y += sy


def compute_fov(g):
    W, H = g.MAP_W, g.MAP_H
    for y in range(H):
        for x in range(W):
            g.visible[y][x] = False
    px, py = g.player.x, g.player.y
    g.visible[py][px] = True
    g.explored[py][px] = True
    r = g.FOV_R
    for y in range(max(0, py - r), min(H, py + r + 1)):
        for x in range(max(0, px - r), min(W, px + r + 1)):
            if (x - px) ** 2 + (y - py) ** 2 <= r * r:
                if has_los(g, px, py, x, y):
                    g.visible[y][x] = True
                    g.explored[y][x] = True


# ── Combat ─────────────────────────────────────────────────────────────────

def player_attack_at(g, tx, ty):
    for e in list(g.entities):
        if e is g.player or e.hp <= 0:
            continue
        if e.x == tx and e.y == ty:
            dmg = max(1, g.player.damage + random.randint(-2, 2))
            e.hp -= dmg
            g.add_msg(f"hit {e.name} for {dmg}")
            if e.hp <= 0:
                g.add_msg(f"{e.name} is slain!")
                g.entities.remove(e)
                g.player.xp += e.xp
                if g.player.xp >= g.player.max_hp * 2:
                    g.player.max_hp += 5
                    g.player.hp = min(g.player.hp + 5, g.player.max_hp)
                    g.add_msg("level up! HP +5")
            return True
    return False


def find_monster_ahead(g):
    d = DX[g.player.facing]
    dy = DY[g.player.facing]
    r = g.player.attack_range
    x, y = g.player.x, g.player.y
    for _ in range(r):
        x += d
        y += dy
        if not (0 < x < g.MAP_W - 1 and 0 < y < g.MAP_H - 1):
            return None
        if g.map[y][x] == ord('#'):
            return None
        for e in g.entities:
            if e is not g.player and e.x == x and e.y == y and e.hp > 0:
                return e
    return None


def magic_aoe(g):
    hit = False
    for e in list(g.entities):
        if e is g.player or e.hp <= 0:
            continue
        if abs(e.x - g.player.x) <= 2 and abs(e.y - g.player.y) <= 2:
            dmg = max(1, g.player.damage + random.randint(0, 4))
            e.hp -= dmg
            hit = True
            g.add_msg(f"magic hits {e.name} for {dmg}")
            if e.hp <= 0:
                g.add_msg(f"{e.name} is slain!")
                g.entities.remove(e)
                g.player.xp += e.xp
                if g.player.xp >= g.player.max_hp * 2:
                    g.player.max_hp += 5
                    g.player.hp = min(g.player.hp + 5, g.player.max_hp)
                    g.add_msg("level up! HP +5")
    if not hit:
        g.add_msg("magic fizzles...")
    return hit


def monster_tick(g):
    for e in list(g.entities):
        if e is g.player or e.hp <= 0:
            continue
        dx = g.player.x - e.x
        dy = g.player.y - e.y
        dist = abs(dx) + abs(dy)
        if dist == 0:
            continue
        if dist <= 15 and g.visible[e.y][e.x]:
            nx, ny = e.x, e.y
            if abs(dx) > abs(dy):
                nx += 1 if dx > 0 else -1
            else:
                ny += 1 if dy > 0 else -1
            if can_move(g, nx, ny):
                e.x, e.y = nx, ny
            elif nx != e.x and can_move(g, nx, e.y):
                e.x = nx
            elif ny != e.y and can_move(g, e.x, ny):
                e.y = ny
            if abs(g.player.x - e.x) + abs(g.player.y - e.y) == 1:
                dmg = max(1, int(e.damage + random.randint(-2, 2)))
                g.player.hp -= dmg
                g.add_msg(f"{e.name} hits you for {dmg}")
                if g.player.hp <= 0:
                    g.game_over = True
                    g.add_msg("You have died...")


def can_move(g, x, y):
    if not (0 < x < g.MAP_W - 1 and 0 < y < g.MAP_H - 1):
        return False
    if g.map[y][x] == ord('#'):
        return False
    for e in g.entities:
        if e.blocks and e.x == x and e.y == y:
            return False
    return True


# ── Player Actions ─────────────────────────────────────────────────────────

def move_forward(g):
    d = DX[g.player.facing]
    dy = DY[g.player.facing]
    nx, ny = g.player.x + d, g.player.y + dy
    if not (0 < nx < g.MAP_W - 1 and 0 < ny < g.MAP_H - 1):
        return False
    for e in g.entities:
        if e is not g.player and e.x == nx and e.y == ny:
            if e.hp > 0:
                player_attack_at(g, nx, ny)
                return True
    if g.player.weapon_type in (EQ_SWORD, EQ_SPEAR):
        t = find_monster_ahead(g)
        if t:
            player_attack_at(g, t.x, t.y)
            return True
    if g.map[ny][nx] != ord('#'):
        g.player.x, g.player.y = nx, ny
        pickup_at(g, nx, ny)
        return True
    return False


def move_backward(g):
    f = (g.player.facing + 2) % 4
    nx = g.player.x + DX[f]
    ny = g.player.y + DY[f]
    if can_move(g, nx, ny):
        g.player.x, g.player.y = nx, ny
        pickup_at(g, nx, ny)
        return True
    return False


def strafe_left(g):
    f = (g.player.facing - 1) % 4
    nx = g.player.x + DX[f]
    ny = g.player.y + DY[f]
    if can_move(g, nx, ny):
        g.player.x, g.player.y = nx, ny
        pickup_at(g, nx, ny)
        return True
    return False


def strafe_right(g):
    f = (g.player.facing + 1) % 4
    nx = g.player.x + DX[f]
    ny = g.player.y + DY[f]
    if can_move(g, nx, ny):
        g.player.x, g.player.y = nx, ny
        pickup_at(g, nx, ny)
        return True
    return False


def pickup_at(g, x, y):
    for it in list(g.items):
        if it.x == x and it.y == y:
            if it.type == 'stairs':
                g.dlvl += 1
                g.add_msg(f"Descend to level {g.dlvl}")
                gen_level(g)
                compute_fov(g)
                g.messages = g.messages[-10:]
                return True
            elif it.type == 'gold':
                g.player.gold += it.value
                g.add_msg(f"picked up {it.value} gold")
                g.items.remove(it)
                return True
            elif it.type == 'food':
                g.player.hp = min(g.player.hp + 10, g.player.max_hp)
                g.add_msg("yum! +10 HP")
                g.items.remove(it)
                return True
            elif it.type == 'potion_heal':
                g.player.hp = min(g.player.hp + 15, g.player.max_hp)
                g.add_msg("healing! +15 HP")
                g.items.remove(it)
                return True
            elif it.type == 'potion_str':
                g.player.damage += 2
                g.add_msg("strength +2!")
                g.items.remove(it)
                return True
            elif it.type in ('weapon', 'armor'):
                if len(g.player.inventory) >= 10:
                    g.add_msg("Inventory full!")
                    return False
                g.player.inventory.append(it)
                g.items.remove(it)
                g.add_msg(f"picked up {it.name}")
                return True
    return False


def rest(g):
    g.player.hp = min(g.player.hp + 1, g.player.max_hp)


def equip_item(g, idx):
    if idx < 0 or idx >= len(g.player.inventory):
        return
    it = g.player.inventory[idx]
    if it.type == 'weapon':
        old = g.player.weapon_item
        g.player.weapon_item = it
        g.player.weapon_type = it.equip_type
        g.player.attack_range = it.range_val if it.equip_type in (EQ_SWORD, EQ_SPEAR) else 1
        g.player.damage = 5 + it.value
        if old:
            g.player.inventory.append(old)
        g.player.inventory.pop(idx)
        g.add_msg(f"equipped {it.name}")
    elif it.type == 'armor':
        old = g.player.armor_item
        g.player.armor_item = it
        g.player.armor_bonus = it.value
        g.player.max_hp = 20 + it.value * 5
        g.player.hp = min(g.player.hp + 5, g.player.max_hp)
        if old:
            g.player.inventory.append(old)
        g.player.inventory.pop(idx)
        g.add_msg(f"equipped {it.name}")


def drop_item(g, idx, ground=True):
    if idx < 0 or idx >= len(g.player.inventory):
        return
    it = g.player.inventory.pop(idx)
    if ground:
        it.x, it.y = g.player.x, g.player.y
        g.items.append(it)
        g.add_msg(f"dropped {it.name}")


# ── Save / Load ────────────────────────────────────────────────────────────

SAVE_DIR = os.path.dirname(os.path.abspath(__file__))

def save_path(slot):
    return os.path.join(SAVE_DIR, f'wiz_save_{slot}.json')

def item_to_dict(it):
    if it is None:
        return None
    return {'x': it.x, 'y': it.y, 'emoji': it.emoji, 'name': it.name,
            'type': it.type, 'value': it.value,
            'equip_type': it.equip_type, 'range_val': it.range_val}

def item_from_dict(d):
    if d is None:
        return None
    return Item(d['x'], d['y'], d['emoji'], d['name'],
                d['type'], d['value'], d['equip_type'], d['range_val'])

def save_game(g, slot):
    data = {
        'version': 3, 'diff': g.diff, 'dlvl': g.dlvl,
        'MAP_W': g.MAP_W, 'MAP_H': g.MAP_H,
        'player': {
            'x': g.player.x, 'y': g.player.y,
            'hp': g.player.hp, 'max_hp': g.player.max_hp,
            'damage': g.player.damage, 'xp': g.player.xp,
            'gold': g.player.gold, 'facing': g.player.facing,
            'weapon_type': g.player.weapon_type,
            'attack_range': g.player.attack_range,
            'armor_bonus': g.player.armor_bonus,
            'inventory': [item_to_dict(it) for it in g.player.inventory],
            'weapon_item': item_to_dict(g.player.weapon_item),
            'armor_item': item_to_dict(g.player.armor_item),
        },
        'map': [[int(c) for c in row] for row in g.map],
        'explored': [[bool(v) for v in row] for row in g.explored],
        'entities': [],
        'items': [item_to_dict(it) for it in g.items],
        'messages': list(g.messages),
    }
    for e in g.entities:
        if e is g.player:
            continue
        data['entities'].append({
            'name': e.name, 'x': e.x, 'y': e.y,
            'hp': e.hp, 'max_hp': e.max_hp,
            'damage': e.damage, 'xp': e.xp,
        })
    try:
        with open(save_path(slot), 'w') as f:
            json.dump(data, f, ensure_ascii=False)
        return True
    except Exception:
        return False

def load_game(g, slot):
    try:
        with open(save_path(slot)) as f:
            data = json.load(f)
    except Exception:
        return False
    if data.get('version', 1) < 2:
        return False
    g.diff = data['diff']; g.dlvl = data['dlvl']
    g.MAP_W = data['MAP_W']; g.MAP_H = data['MAP_H']
    g.current_slot = slot
    d = DIFFICULTIES.get(g.diff, DIFFICULTIES[2])
    g.name = d['name']; g.dmg_scale = d['dmg_scale']
    g.spawn_scale = d['spawn_scale']; g.item_scale = d['item_scale']
    g.FOV_R = d['fov_r']; g.min_room = d['min_room']
    g.max_room = d['max_room']; g.max_rooms = d['max_rooms']
    g.map = data['map']; g.explored = data['explored']
    g.messages = data['messages']; g.game_over = False; g.rooms = []
    pd = data['player']
    g.player = Entity(pd['x'], pd['y'], PLAYER_EMOJI, CP['player'],
                      blocks=True, name='Player',
                      hp=pd['hp'], max_hp=pd['max_hp'],
                      damage=pd['damage'], xp=pd['xp'])
    g.player.gold = pd['gold']; g.player.facing = pd.get('facing', SOUTH)
    g.player.weapon_type = pd['weapon_type']
    g.player.attack_range = pd['attack_range']
    g.player.armor_bonus = pd['armor_bonus']
    g.player.inventory = [item_from_dict(it) for it in pd['inventory']]
    g.player.weapon_item = item_from_dict(pd['weapon_item'])
    g.player.armor_item = item_from_dict(pd['armor_item'])
    g.entities = [g.player]
    for ed in data['entities']:
        m = Entity(ed['x'], ed['y'], MONSTER_EMOJI.get(ed['name'], '👾'), CP['monster'],
                   blocks=True, name=ed['name'],
                   hp=ed['hp'], max_hp=ed['max_hp'],
                   damage=ed['damage'], xp=ed['xp'])
        g.entities.append(m)
    g.items = [item_from_dict(it) for it in data['items']]
    g.visible = [[False] * g.MAP_W for _ in range(g.MAP_H)]
    compute_fov(g)
    return True

def get_save_info(slot):
    p = save_path(slot)
    if not os.path.exists(p):
        return None
    try:
        with open(p) as f:
            d = json.load(f)
        return {'dlvl': d['dlvl'], 'hp': d['player']['hp'],
                'max_hp': d['player']['max_hp'], 'diff': d.get('diff', 2)}
    except Exception:
        return {'corrupted': True}

def any_save_exists():
    return any(os.path.exists(save_path(s)) for s in range(1, 4))


# ── Rendering ──────────────────────────────────────────────────────────────

def render(stdscr, g):
    stdscr.erase()
    h, w = stdscr.getmaxyx()

    rows = render_3d_view(g)
    for i, row in enumerate(rows):
        if i < h:
            stdscr.addstr(i, 0, row[:w - 1])

    hud_y = VIEW_H
    hp_pct = g.player.hp / g.player.max_hp if g.player.max_hp > 0 else 0
    hp_c = CP['hp_low'] if hp_pct < 0.3 else CP['hp']
    wn = EQUIP_NAMES.get(g.player.weapon_type, 'Fist')
    dn = DIR_NAMES[g.player.facing]
    hud = (f"HP:{g.player.hp}/{g.player.max_hp}  Atk:{g.player.damage}  "
           f"Gold:{g.player.gold}  Lv:{g.dlvl}  [{dn}] {wn}")
    if hud_y < h:
        stdscr.attron(curses.color_pair(hp_c) | curses.A_BOLD)
        stdscr.addstr(hud_y, 0, hud[:w - 1])
        stdscr.attroff(curses.color_pair(hp_c) | curses.A_BOLD)

    msgs = g.messages[-2:] if g.messages else [""]
    for i, msg in enumerate(msgs):
        y = hud_y + 1 + i
        if y < h:
            stdscr.attron(curses.color_pair(CP['msg']))
            stdscr.addstr(y, 0, msg[:w - 1])
            stdscr.attroff(curses.color_pair(CP['msg']))
    stdscr.refresh()


def render_map_view(stdscr, g):
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    title = f"── Map (Level {g.dlvl}) ── Facing: {DIR_NAMES[g.player.facing]}"
    stdscr.addstr(0, max(0, (w - len(title)) // 2), title)
    leg = "@=You  #=Wall  .=Floor  >=Stairs  A-Z=Monsters"
    stdscr.addstr(1, max(0, (w - len(leg)) // 2), leg)
    for y in range(g.MAP_H):
        row = ''
        for x in range(g.MAP_W):
            if not g.explored[y][x]:
                row += ' '
            elif y == g.player.y and x == g.player.x:
                rdir = {'North': '^', 'South': 'v', 'East': '>', 'West': '<'}
                row += rdir.get(DIR_NAMES[g.player.facing], '@')
            else:
                is_m = False
                for e in g.entities:
                    if e is not g.player and e.x == x and e.y == y:
                        row += e.name[0].upper()
                        is_m = True; break
                if is_m: continue
                is_s = False
                for it in g.items:
                    if it.x == x and it.y == y and it.type == 'stairs':
                        row += '>'; is_s = True; break
                if is_s: continue
                row += '#' if g.map[y][x] == ord('#') else '.'
        dy = y + 3
        if dy < h and row:
            stdscr.addstr(dy, 0, row)
    p = "Press any key to close"
    if h > 0:
        stdscr.addstr(h - 1, max(0, (w - len(p)) // 2), p)
    stdscr.refresh()
    stdscr.getch()


# ── Inventory Screen ───────────────────────────────────────────────────────

def inventory_screen(stdscr, g):
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    lines = ["┌─ Inventory ─────────────────────────────┐"]
    wn = EQUIP_NAMES.get(g.player.weapon_type, '?')
    lines.append(f"│ Weapon: {wn:8s}  Armor: +{g.player.armor_bonus}            │")
    lines.append("├─────────────────────────────────────────┤")
    inv = g.player.inventory
    if not inv:
        lines.append("│  (empty)                              │")
    else:
        for i, it in enumerate(inv):
            name = f"{it.emoji} {it.name}"
            pad = 37 - len(name)
            lines.append(f"│ [{i + 1}] {name}{' ' * pad}│")
    lines.append("├─────────────────────────────────────────┤")
    lines.append("│ 1-9: use/equip  d: drop  q: exit        │")
    lines.append("└─────────────────────────────────────────┘")
    for i, line in enumerate(lines):
        y = (h - len(lines)) // 2 + i
        if 0 <= y < h:
            stdscr.attron(curses.color_pair(CP['inventory']))
            stdscr.addstr(y, max(0, (w - 42) // 2), line)
            stdscr.attroff(curses.color_pair(CP['inventory']))
    stdscr.refresh()

    while True:
        k = stdscr.getch()
        if k == ord('q') or k == 27:
            return None
        elif k == ord('d'):
            return 'drop'
        elif ord('1') <= k <= ord('9'):
            idx = k - ord('1')
            if idx < len(inv):
                return ('select', idx)
        elif k == ord('0') and len(inv) >= 10:
            return ('select', 9)

def inventory_flow(stdscr, g):
    if not g.player.inventory:
        g.add_msg("Nothing in inventory"); return False
    res = inventory_screen(stdscr, g)
    if res is None: return False
    if isinstance(res, tuple) and res[0] == 'select':
        idx = res[1]
        if idx < len(g.player.inventory):
            it = g.player.inventory[idx]
            if it.type in ('weapon', 'armor'):
                equip_item(g, idx); return True
            elif it.type == 'potion_heal':
                g.player.hp = min(g.player.hp + 15, g.player.max_hp)
                g.add_msg("quaffed healing potion")
                g.player.inventory.pop(idx); return True
            elif it.type == 'potion_str':
                g.player.damage += 2
                g.add_msg("quaffed strength potion")
                g.player.inventory.pop(idx); return True
            elif it.type == 'food':
                g.player.hp = min(g.player.hp + 10, g.player.max_hp)
                g.add_msg("ate food")
                g.player.inventory.pop(idx); return True
            else:
                g.add_msg("Cannot use that"); return False
    return False

def drop_flow(stdscr, g):
    if not g.player.inventory:
        g.add_msg("Nothing to drop"); return False
    res = inventory_screen(stdscr, g)
    if res is None: return False
    if isinstance(res, tuple) and res[0] == 'select':
        idx = res[1]
        it = g.player.inventory[idx]
        if it is g.player.weapon_item:
            g.player.weapon_item = None; g.player.weapon_type = EQ_FIST
            g.player.attack_range = 1; g.player.damage = 5
        elif it is g.player.armor_item:
            g.player.armor_item = None; g.player.armor_bonus = 0
            g.player.max_hp = 20
            g.player.hp = min(g.player.hp, g.player.max_hp)
        drop_item(g, idx); return True
    return False


# ── Save Slot Selector ─────────────────────────────────────────────────────

def save_slot_selector(stdscr, g):
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    lines = ["  ┌─ Save to which slot? ────────────┐"]
    for slot in range(1, 4):
        info = get_save_info(slot)
        if info is None:
            lines.append(f"  │ [{slot}] Slot {slot} — (empty)            │")
        elif info.get('corrupted'):
            lines.append(f"  │ [{slot}] Slot {slot} — (corrupted)       │")
        else:
            lines.append(f"  │ [{slot}] Slot {slot} — Lv.{info['dlvl']} "
                         f"HP:{info['hp']}/{info['max_hp']} │")
    lines += ["  │                                   │",
              "  │ (will overwrite existing save)    │",
              "  └───────────────────────────────────┘",
              "", "  Press 1/2/3 to save, ESC to cancel"]
    for i, line in enumerate(lines):
        y = (h - len(lines)) // 2 + i
        if 0 <= y < h:
            stdscr.attron(curses.color_pair(CP['title']))
            stdscr.addstr(y, max(0, (w - 40) // 2), line)
            stdscr.attroff(curses.color_pair(CP['title']))
    stdscr.refresh()
    while True:
        k = stdscr.getch()
        if k == ord('1'): return 1
        elif k == ord('2'): return 2
        elif k == ord('3'): return 3
        elif k == 27: return None


# ── Title Screen ───────────────────────────────────────────────────────────

def title_screen(stdscr):
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    has = any_save_exists()
    if has:
        lines = [
            "  __          __              _       ",
            "  \\ \\        / /_ _ _ __ _ _| |_ _  ",
            "   \\ \\  /\\  / / _` | '__| | | | '_| ",
            "    \\ \\/  \\/ / (_| | |  | |_| | |_ ",
            "     \\__/\\__/ \\__,_|_|   \\__,_|\\__|",
            "                                    ",
            "    3D First-Person Dungeon Crawl    ",
            "                                    ",
        ]
        for slot in range(1, 4):
            info = get_save_info(slot)
            if info is None:
                lines.append(f"  [{slot}] Slot {slot} — (empty)")
            elif info.get('corrupted'):
                lines.append(f"  [{slot}] Slot {slot} — (corrupted)")
            else:
                dn = DIFFICULTIES.get(info['diff'], {}).get('name', '?')
                lines.append(f"  [{slot}] Lv.{info['dlvl']}  HP:{info['hp']}/{info['max_hp']}  [{dn}]")
        lines += ["", "  [n] New Game", "  [q] Quit"]
        for i, line in enumerate(lines):
            y = h // 2 - 9 + i
            x = (w - 32) // 2
            if 0 <= y < h:
                stdscr.attron(curses.color_pair(CP['title']) | curses.A_BOLD)
                stdscr.addstr(y, max(0, x), line)
                stdscr.attroff(curses.color_pair(CP['title']) | curses.A_BOLD)
        stdscr.refresh()
        while True:
            k = stdscr.getch()
            if k == ord('1'): return ('load', 1)
            elif k == ord('2'): return ('load', 2)
            elif k == ord('3'): return ('load', 3)
            elif k in (ord('n'), ord('N')): return ('new', None)
            elif k in (ord('q'), ord('Q')): return ('quit', None)
    else:
        title = [
            "  __          __              _       ",
            "  \\ \\        / /_ _ _ __ _ _| |_ _  ",
            "   \\ \\  /\\  / / _` | '__| | | | '_| ",
            "    \\ \\/  \\/ / (_| | |  | |_| | |_ ",
            "     \\__/__\\/ \\__,_|_|   \\__,_|\\__|",
            "                                    ",
            "    3D First-Person Dungeon Crawl    ",
            "                                    ",
            "  Select difficulty:                ",
            "                                    ",
            "  [1] Easy                          ",
            "  [2] Middle (recommended)          ",
            "  [3] Hard                          ",
            "                                    ",
            "  Press 1/2/3 to begin              ",
        ]
        for i, line in enumerate(title):
            y = h // 2 - 9 + i
            x = (w - 33) // 2
            if 0 <= y < h:
                stdscr.attron(curses.color_pair(CP['title']) | curses.A_BOLD)
                stdscr.addstr(y, max(0, x), line)
                stdscr.attroff(curses.color_pair(CP['title']) | curses.A_BOLD)
        stdscr.refresh()
        while True:
            k = stdscr.getch()
            if k == ord('1'): return ('new', 1)
            elif k == ord('2'): return ('new', 2)
            elif k == ord('3'): return ('new', 3)


# ── Game Over Screen ───────────────────────────────────────────────────────

def game_over_screen(stdscr, g):
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    lines = [
        "  ⚰️  GAME OVER ⚰️",
        f"  Level: {g.dlvl}  Gold: {g.player.gold}",
        f"  XP: {g.player.xp}  HP: {g.player.max_hp}",
        "",
        "  [r] Restart from scratch",
        "  [s] Strong New Game",
        "  [q] Quit",
    ]
    for i, line in enumerate(lines):
        y = h // 2 - 3 + i
        x = (w - 30) // 2
        if 0 <= y < h:
            c = CP['hp_low'] if i == 0 else CP['msg']
            stdscr.attron(curses.color_pair(c) | curses.A_BOLD)
            stdscr.addstr(y, max(0, x), line)
            stdscr.attroff(curses.color_pair(c) | curses.A_BOLD)
    stdscr.refresh()
    while True:
        k = stdscr.getch()
        if k in (ord('r'), ord('R')): return 'restart'
        elif k in (ord('s'), ord('S')): return 'strong'
        elif k in (ord('q'), ord('Q')): return 'quit'


# ── Main Game Loop ─────────────────────────────────────────────────────────

def play_game(stdscr):
    curses.curs_set(0)
    curses.use_default_colors()
    for c in range(1, 14):
        curses.init_pair(c, curses.COLOR_WHITE, -1)
    curses.init_pair(CP['player'], curses.COLOR_CYAN, -1)
    curses.init_pair(CP['monster'], curses.COLOR_RED, -1)
    curses.init_pair(CP['gold'], curses.COLOR_YELLOW, -1)
    curses.init_pair(CP['item'], curses.COLOR_GREEN, -1)
    curses.init_pair(CP['wall'], curses.COLOR_WHITE, -1)
    curses.init_pair(CP['floor'], curses.COLOR_WHITE, -1)
    curses.init_pair(CP['stairs'], curses.COLOR_YELLOW, -1)
    curses.init_pair(CP['msg'], curses.COLOR_WHITE, -1)
    curses.init_pair(CP['hp'], curses.COLOR_GREEN, -1)
    curses.init_pair(CP['hp_low'], curses.COLOR_RED, -1)
    curses.init_pair(CP['title'], curses.COLOR_YELLOW, -1)
    curses.init_pair(CP['inventory'], curses.COLOR_CYAN, -1)
    curses.init_pair(CP['hud'], curses.COLOR_WHITE, -1)

    stdscr.nodelay(0)
    stdscr.keypad(True)
    saved = None

    while True:
        result = title_screen(stdscr)
        if result is None: return
        action, value = result
        if action == 'quit': return

        g = None

        if action == 'load':
            g = Game(2)
            if not load_game(g, value):
                continue
            g.game_over = False
            g.add_msg("Game loaded. Welcome back!")

        elif action == 'new':
            if value is None:
                r2 = title_screen(stdscr)
                if r2 is None or r2[0] == 'quit': return
                _, diff = r2
            else:
                diff = value
            g = Game(diff)
            g.player = Entity(0, 0, PLAYER_EMOJI, CP['player'],
                              blocks=True, name='Player',
                              hp=20, max_hp=20, damage=5, xp=0)
            g.entities.append(g.player)
            if saved is not None:
                g.player.max_hp = saved['max_hp']
                g.player.hp = saved['hp']
                g.player.damage = saved['damage']
                g.player.gold = saved['gold']
                g.player.xp = saved['xp']
                g.player.weapon_type = saved['weapon_type']
                g.player.attack_range = saved['attack_range']
                g.player.armor_bonus = saved['armor_bonus']
                g.player.inventory = saved['inventory']
                g.player.weapon_item = saved['weapon_item']
                g.player.armor_item = saved['armor_item']
                g.player.facing = SOUTH
                if g.player.weapon_item:
                    g.player.damage = 5 + g.player.weapon_item.value
                if g.player.armor_item:
                    g.player.max_hp = 20 + g.player.armor_item.value * 5
                g.add_msg("Strong New Game begins!")
                saved = None
            gen_level(g)
            compute_fov(g)
            g.game_over = False

        while g and not g.game_over:
            render(stdscr, g)
            key = stdscr.getch()
            acted = False

            if key == ord('q'):
                return
            elif key == ord('Q'):
                if g.current_slot:
                    ok = save_game(g, g.current_slot)
                    g.add_msg(f"Saved to slot {g.current_slot}" if ok else "Save failed!")
                else:
                    sl = save_slot_selector(stdscr, g)
                    if sl is not None:
                        if save_game(g, sl):
                            g.current_slot = sl
                            g.add_msg(f"Saved to slot {sl}")
                        else:
                            g.add_msg("Save failed!")
            elif key == ord('S'):
                if g.current_slot:
                    ok = save_game(g, g.current_slot)
                    g.add_msg(f"Saved to slot {g.current_slot}" if ok else "Save failed!")
                else:
                    sl = save_slot_selector(stdscr, g)
                    if sl is not None:
                        if save_game(g, sl):
                            g.current_slot = sl
                            g.add_msg(f"Saved to slot {sl}")
                        else:
                            g.add_msg("Save failed!")
            elif key in (ord('k'), curses.KEY_UP):
                acted = move_forward(g)
            elif key in (ord('j'), curses.KEY_DOWN):
                acted = move_backward(g)
            elif key in (ord('h'), curses.KEY_LEFT):
                g.player.facing = (g.player.facing - 1) % 4
                acted = True
            elif key in (ord('l'), curses.KEY_RIGHT):
                g.player.facing = (g.player.facing + 1) % 4
                acted = True
            elif key == ord('y'):
                acted = strafe_left(g)
            elif key == ord('n'):
                acted = strafe_right(g)
            elif key == ord('u'):
                g.player.facing = (g.player.facing - 1) % 4
                acted = move_forward(g)
            elif key == ord('b'):
                g.player.facing = (g.player.facing + 1) % 4
                acted = move_backward(g)
            elif key == ord(' '):
                pickup_at(g, g.player.x, g.player.y)
                acted = True
            elif key == ord('.'):
                rest(g); acted = True
            elif key == ord('>'):
                found = False
                for it in g.items:
                    if it.x == g.player.x and it.y == g.player.y and it.type == 'stairs':
                        g.dlvl += 1; g.add_msg(f"Descend to level {g.dlvl}")
                        gen_level(g); compute_fov(g)
                        g.messages = g.messages[-10:]
                        found = True; acted = True; break
                if not found:
                    g.add_msg("No stairs here")
            elif key == ord('m'):
                render_map_view(stdscr, g)
            elif key == ord('i'):
                inventory_flow(stdscr, g)
            elif key == ord('d'):
                drop_flow(stdscr, g)
            elif key == ord('f'):
                if g.player.weapon_type == EQ_MAGIC:
                    magic_aoe(g)
                    acted = True
                else:
                    g.add_msg("No magic staff equipped")

            compute_fov(g)

            if acted:
                monster_tick(g)

            if g.player.hp <= 0:
                g.game_over = True

        if g and g.game_over:
            result = game_over_screen(stdscr, g)
            if result == 'restart':
                continue
            elif result == 'strong':
                saved = {
                    'max_hp': g.player.max_hp,
                    'hp': g.player.max_hp,
                    'damage': g.player.damage,
                    'gold': g.player.gold,
                    'xp': g.player.xp,
                    'weapon_type': g.player.weapon_type,
                    'attack_range': g.player.attack_range,
                    'armor_bonus': g.player.armor_bonus,
                    'inventory': list(g.player.inventory),
                    'weapon_item': g.player.weapon_item,
                    'armor_item': g.player.armor_item,
                }
                continue
            else:
                return


def main():
    curses.wrapper(play_game)


if __name__ == '__main__':
    main()
