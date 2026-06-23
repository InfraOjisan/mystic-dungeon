#!/usr/bin/env python3
"""
Rogue - A classic dungeon-crawling game with emoji graphics.
"""

import curses
import random
import json
import os

# ── Emoji ──────────────────────────────────────────────────────────────────
T_WALL_EMOJI   = '🧱'
T_FLOOR_EMOJI  = '⬜'
T_STAIRS_EMOJI = '🔽'
PLAYER_EMOJI   = '🧙'
GOLD_EMOJI     = '🪙'
FOOD_EMOJI     = '🍗'
POTION_EMOJI   = '🧪'
SWORD_EMOJI    = '⚔️'
SPEAR_EMOJI    = '🔱'
ARMOR_EMOJI    = '🛡️'
MAGIC_EMOJI    = '✨'

MONSTER_EMOJI = {
    'Ant': '🐜', 'Bat': '🦇', 'Centipede': '🦂', 'Dog': '🐕',
    'Eye': '🟡', 'Frog': '🐸', 'Goblin': '👾', 'Harpy': '🦅',
    'Imp': '🎃', 'Jackal': '🐺', 'Kobold': '🦎', 'Lich': '☠️',
    'Mummy': '🧛', 'Ogre': '🗿', 'Troll': '🦖', 'Wyrm': '🐉',
}

# ── Difficulty presets ─────────────────────────────────────────────────────
DIFFICULTIES = {
    1: {'name': 'Easy',   'mw': 30, 'mh': 18, 'dmg_scale': 0.5, 'spawn_scale': 0.6,
        'item_scale': 1.5, 'fov': 8, 'min_room': 3, 'max_room': 7, 'max_rooms': 7},
    2: {'name': 'Middle', 'mw': 40, 'mh': 24, 'dmg_scale': 1.0, 'spawn_scale': 1.0,
        'item_scale': 1.0, 'fov': 6, 'min_room': 4, 'max_room': 8, 'max_rooms': 9},
    3: {'name': 'Hard',   'mw': 40, 'mh': 24, 'dmg_scale': 1.5, 'spawn_scale': 1.4,
        'item_scale': 0.6, 'fov': 5, 'min_room': 4, 'max_room': 8, 'max_rooms': 12},
}

# ── Monster templates: (name, hp, damage, xp) ──────────────────────────────
MONSTER_TEMPLATES = [
    ('Ant', 5, 2, 1), ('Bat', 8, 3, 2), ('Centipede', 10, 4, 3),
    ('Dog', 15, 5, 5), ('Eye', 20, 6, 8), ('Frog', 25, 7, 10),
    ('Goblin', 30, 8, 12), ('Harpy', 35, 9, 15), ('Imp', 40, 10, 18),
    ('Jackal', 45, 11, 20), ('Kobold', 50, 12, 22), ('Lich', 60, 15, 30),
    ('Mummy', 70, 16, 35), ('Ogre', 80, 18, 40), ('Troll', 90, 20, 45),
    ('Wyrm', 120, 25, 60),
]

# ── Colors ─────────────────────────────────────────────────────────────────
CP = {'player': 1, 'monster': 2, 'gold': 3, 'item': 4, 'wall': 5,
      'floor': 6, 'stairs': 7, 'msg': 8, 'hp': 9, 'hp_low': 10, 'title': 11,
      'inventory': 12, 'equipped': 13}

# ── Equipment types ────────────────────────────────────────────────────────
EQ_FIST  = 0
EQ_SWORD = 1
EQ_SPEAR = 2
EQ_MAGIC = 3
EQ_ARMOR = 4

EQUIP_NAMES = {EQ_FIST: 'Fist', EQ_SWORD: 'Sword', EQ_SPEAR: 'Spear',
               EQ_MAGIC: 'Magic Staff', EQ_ARMOR: 'Armor'}
EQUIP_EMOJI = {EQ_FIST: '🤜', EQ_SWORD: SWORD_EMOJI, EQ_SPEAR: SPEAR_EMOJI,
               EQ_MAGIC: MAGIC_EMOJI, EQ_ARMOR: ARMOR_EMOJI}

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
    def inside(self, x, y):
        return self.x <= x < self.x + self.w and self.y <= y < self.y + self.h


class Entity:
    __slots__ = ('x', 'y', 'ch', 'color', 'blocks', 'name',
                 'hp', 'max_hp', 'damage', 'xp', 'gold',
                 'weapon_type', 'armor_bonus', 'inventory',
                 'weapon_item', 'armor_item', 'attack_range', 'aoe')
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
        self.aoe = 0


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
        self.FOV_RADIUS = d['fov']
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
    T_WALL, T_FLOOR = ord('#'), ord('.')
    g.map = [[T_WALL] * W for _ in range(H)]
    g.explored = [[False] * W for _ in range(H)]
    g.visible = [[False] * W for _ in range(H)]
    g.rooms = []
    g.entities = [e for e in g.entities if e == g.player]
    g.items = []
    g.player.x, g.player.y = 1, 1

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
            carve_room(g, r, T_FLOOR)

    if not g.rooms:
        r = Rect(1, 1, 6, 5)
        g.rooms.append(r)
        carve_room(g, r, T_FLOOR)

    for i in range(1, len(g.rooms)):
        a, b = g.rooms[i - 1], g.rooms[i]
        if random.random() < 0.5:
            carve_h_tunnel(g, a.cx, b.cx, a.cy, T_FLOOR)
            carve_v_tunnel(g, a.cy, b.cy, b.cx, T_FLOOR)
        else:
            carve_v_tunnel(g, a.cy, b.cy, a.cx, T_FLOOR)
            carve_h_tunnel(g, a.cx, b.cx, b.cy, T_FLOOR)

    r0 = g.rooms[0]
    g.player.x, g.player.y = r0.cx, r0.cy

    rl = g.rooms[-1]
    if len(g.rooms) > 1:
        g.items.append(Item(rl.cx, rl.cy, T_STAIRS_EMOJI,
                            'Stairs Down', 'stairs'))

    spawn_count = max(1, int(3 * g.spawn_scale))
    for r in g.rooms[1:]:
        n = random.randint(0, spawn_count)
        for _ in range(n):
            x = random.randint(r.x + 1, r.x + r.w - 2)
            y = random.randint(r.y + 1, r.y + r.h - 2)
            if any(e.x == x and e.y == y for e in g.entities):
                continue
            mname, hp, dmg, xp = random.choice(MONSTER_TEMPLATES)
            dlvl_scale = 1.0 + (g.dlvl - 1) * 0.3
            hp = max(1, int(hp * dlvl_scale * g.dmg_scale))
            dmg = max(1, int(dmg * dlvl_scale * g.dmg_scale))
            xp = max(1, int(xp * dlvl_scale))
            sym = MONSTER_EMOJI.get(mname, '👾')
            m = Entity(x, y, sym, CP['monster'],
                       blocks=True, name=mname,
                       hp=hp, max_hp=hp, damage=dmg, xp=xp)
            g.entities.append(m)

    for r in g.rooms[1:]:
        n = random.randint(0, max(1, int(2 * g.item_scale)))
        for _ in range(n):
            x = random.randint(r.x + 1, r.x + r.w - 2)
            y = random.randint(r.y + 1, r.y + r.h - 2)
            if any(e.x == x and e.y == y for e in g.entities):
                continue
            if any(it.x == x and it.y == y for it in g.items):
                continue
            roll = random.random()
            if roll < 0.2:
                v = random.randint(1, 10 * g.dlvl)
                g.items.append(Item(x, y, GOLD_EMOJI,
                                    f'{v} gold', 'gold', v))
            elif roll < 0.30:
                g.items.append(Item(x, y, FOOD_EMOJI,
                                    'food ration', 'food'))
            elif roll < 0.45:
                if random.random() < 0.4:
                    g.items.append(Item(x, y, POTION_EMOJI,
                                        'healing potion', 'potion_heal'))
                else:
                    g.items.append(Item(x, y, POTION_EMOJI,
                                        'strength potion', 'potion_str'))
            elif roll < 0.65:
                bonus = random.randint(1, max(1, g.dlvl))
                eq_type = random.choice([EQ_SWORD, EQ_SPEAR])
                emoji = SWORD_EMOJI if eq_type == EQ_SWORD else SPEAR_EMOJI
                ename = EQUIP_NAMES[eq_type]
                g.items.append(Item(x, y, emoji,
                                    f'{ename} +{bonus}', 'weapon',
                                    bonus, eq_type, bonus))
            elif roll < 0.80:
                pet = random.random()
                if pet < 0.3:
                    eq_type = EQ_MAGIC
                    emoji = MAGIC_EMOJI
                    ename = EQUIP_NAMES[eq_type]
                    g.items.append(Item(x, y, emoji,
                                        f'{ename}', 'weapon',
                                        2, eq_type, 2))
                else:
                    eq_type = EQ_ARMOR
                    emoji = ARMOR_EMOJI
                    ename = EQUIP_NAMES[eq_type]
                    bonus = random.randint(1, max(1, g.dlvl))
                    g.items.append(Item(x, y, emoji,
                                        f'{ename} +{bonus}', 'armor',
                                        bonus, eq_type, bonus))
            else:
                bonus = random.randint(1, max(1, g.dlvl))
                g.items.append(Item(x, y, ARMOR_EMOJI,
                                    f'Armor +{bonus}', 'armor',
                                    bonus, EQ_ARMOR, bonus))


def carve_room(g, r, floor_ch):
    for y in range(r.y, r.y + r.h):
        for x in range(r.x, r.x + r.w):
            if 0 <= y < g.MAP_H and 0 <= x < g.MAP_W:
                g.map[y][x] = floor_ch


def carve_h_tunnel(g, x1, x2, y, floor_ch):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        if 0 < y < g.MAP_H - 1 and 0 < x < g.MAP_W - 1:
            g.map[y][x] = floor_ch


def carve_v_tunnel(g, y1, y2, x, floor_ch):
    for y in range(min(y1, y2), max(y1, y2) + 1):
        if 0 < y < g.MAP_H - 1 and 0 < x < g.MAP_W - 1:
            g.map[y][x] = floor_ch


# ── FOV ────────────────────────────────────────────────────────────────────

def has_los(g, x0, y0, x1, y1):
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
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
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy


def compute_fov(g):
    W, H = g.MAP_W, g.MAP_H
    for y in range(H):
        for x in range(W):
            g.visible[y][x] = False
    px, py = g.player.x, g.player.y
    g.visible[py][px] = True
    g.explored[py][px] = True
    r = g.FOV_RADIUS
    for y in range(max(0, py - r), min(H, py + r + 1)):
        for x in range(max(0, px - r), min(W, px + r + 1)):
            if (x - px) ** 2 + (y - py) ** 2 <= r * r:
                if has_los(g, px, py, x, y):
                    g.visible[y][x] = True
                    g.explored[y][x] = True


# ── Combat ─────────────────────────────────────────────────────────────────

def get_weapon_range(g):
    return g.player.attack_range


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


def find_monster_in_dir(g, dx, dy):
    r = get_weapon_range(g)
    x, y = g.player.x, g.player.y
    for _ in range(r):
        x += dx
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
    r = 2
    hit_any = False
    for e in list(g.entities):
        if e is g.player or e.hp <= 0:
            continue
        if abs(e.x - g.player.x) <= r and abs(e.y - g.player.y) <= r:
            dmg = max(1, g.player.damage + random.randint(0, 4))
            e.hp -= dmg
            hit_any = True
            g.add_msg(f"magic hits {e.name} for {dmg}")
            if e.hp <= 0:
                g.add_msg(f"{e.name} is slain!")
                g.entities.remove(e)
                g.player.xp += e.xp
                if g.player.xp >= g.player.max_hp * 2:
                    g.player.max_hp += 5
                    g.player.hp = min(g.player.hp + 5, g.player.max_hp)
                    g.add_msg("level up! HP +5")
    if hit_any:
        return True
    g.add_msg("magic fizzles...")
    return False


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

def move_or_attack(g, dx, dy):
    nx, ny = g.player.x + dx, g.player.y + dy
    if not (0 < nx < g.MAP_W - 1 and 0 < ny < g.MAP_H - 1):
        return False

    for e in g.entities:
        if e is not g.player and e.x == nx and e.y == ny and e.hp > 0:
            player_attack_at(g, nx, ny)
            return True

    if g.player.weapon_type in (EQ_SWORD, EQ_SPEAR):
        target = find_monster_in_dir(g, dx, dy)
        if target:
            player_attack_at(g, target.x, target.y)
            return True

    if g.map[ny][nx] != ord('#'):
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
                    g.add_msg("Inventory full! Drop something first.")
                    return False
                g.player.inventory.append(it)
                g.items.remove(it)
                g.add_msg(f"picked up {it.name}")
                return True


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
    return os.path.join(SAVE_DIR, f'rogue_save_{slot}.json')


def item_to_dict(it):
    if it is None:
        return None
    return {
        'x': it.x, 'y': it.y, 'emoji': it.emoji, 'name': it.name,
        'type': it.type, 'value': it.value,
        'equip_type': it.equip_type, 'range_val': it.range_val,
    }


def item_from_dict(d):
    if d is None:
        return None
    return Item(d['x'], d['y'], d['emoji'], d['name'],
                d['type'], d['value'], d['equip_type'], d['range_val'])


def save_game(g, slot):
    data = {
        'version': 2,
        'diff': g.diff,
        'dlvl': g.dlvl,
        'MAP_W': g.MAP_W,
        'MAP_H': g.MAP_H,
        'player': {
            'x': g.player.x, 'y': g.player.y,
            'hp': g.player.hp, 'max_hp': g.player.max_hp,
            'damage': g.player.damage, 'xp': g.player.xp,
            'gold': g.player.gold,
            'weapon_type': g.player.weapon_type,
            'attack_range': g.player.attack_range,
            'armor_bonus': g.player.armor_bonus,
            'inventory': [item_to_dict(it) for it in g.player.inventory],
            'weapon_item': item_to_dict(g.player.weapon_item),
            'armor_item': item_to_dict(g.player.armor_item),
        },
        'map': [[int(c) for c in row] for row in g.map],
        'explored': [[bool(v) for v in row] for row in g.explored],
        'visible': [[bool(v) for v in row] for row in g.visible],
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

    g.diff = data['diff']
    g.dlvl = data['dlvl']
    g.MAP_W = data['MAP_W']
    g.MAP_H = data['MAP_H']
    g.current_slot = slot
    d = DIFFICULTIES.get(g.diff, DIFFICULTIES[2])
    g.name = d['name']
    g.dmg_scale = d['dmg_scale']
    g.spawn_scale = d['spawn_scale']
    g.item_scale = d['item_scale']
    g.FOV_RADIUS = d['fov']
    g.min_room = d['min_room']
    g.max_room = d['max_room']
    g.max_rooms = d['max_rooms']

    g.map = data['map']
    g.explored = data['explored']
    g.visible = data['visible']
    g.messages = data['messages']
    g.game_over = False
    g.rooms = []

    pd = data['player']
    g.player = Entity(pd['x'], pd['y'], PLAYER_EMOJI, CP['player'],
                      blocks=True, name='Player',
                      hp=pd['hp'], max_hp=pd['max_hp'],
                      damage=pd['damage'], xp=pd['xp'])
    g.player.gold = pd['gold']
    g.player.weapon_type = pd['weapon_type']
    g.player.attack_range = pd['attack_range']
    g.player.armor_bonus = pd['armor_bonus']
    g.player.inventory = [item_from_dict(it) for it in pd['inventory']]
    g.player.weapon_item = item_from_dict(pd['weapon_item'])
    g.player.armor_item = item_from_dict(pd['armor_item'])

    g.entities = [g.player]
    for ed in data['entities']:
        mname = ed['name']
        sym = MONSTER_EMOJI.get(mname, '👾')
        m = Entity(ed['x'], ed['y'], sym, CP['monster'],
                   blocks=True, name=mname,
                   hp=ed['hp'], max_hp=ed['max_hp'],
                   damage=ed['damage'], xp=ed['xp'])
        g.entities.append(m)

    g.items = [item_from_dict(it) for it in data['items']]
    compute_fov(g)
    return True


def get_save_info(slot):
    path = save_path(slot)
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        return {
            'dlvl': data['dlvl'],
            'hp': data['player']['hp'],
            'max_hp': data['player']['max_hp'],
            'diff': data.get('diff', 2),
        }
    except Exception:
        return {'corrupted': True}


def any_save_exists():
    for slot in range(1, 4):
        if os.path.exists(save_path(slot)):
            return True
    return False


# ── Rendering ──────────────────────────────────────────────────────────────

def cell_char(g, x, y):
    if g.map[y][x] == ord('#'):
        return T_WALL_EMOJI
    else:
        return T_FLOOR_EMOJI


def render(stdscr, g):
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    if h < g.MAP_H + 3 or w < g.MAP_W:
        return

    for y in range(g.MAP_H):
        row = ''
        for x in range(g.MAP_W):
            if y == g.player.y and x == g.player.x:
                row += PLAYER_EMOJI
            elif g.visible[y][x]:
                ch = cell_char(g, x, y)
                for it in g.items:
                    if it.x == x and it.y == y:
                        ch = it.emoji
                        break
                for e in g.entities:
                    if e is not g.player and e.x == x and e.y == y:
                        ch = e.ch if isinstance(e.ch, str) else chr(e.ch)
                        break
                row += ch
            elif g.explored[y][x]:
                row += '·'
            else:
                row += ' '
        stdscr.addstr(y, 0, row)

    hp_pct = g.player.hp / g.player.max_hp if g.player.max_hp > 0 else 0
    hp_color = CP['hp_low'] if hp_pct < 0.3 else CP['hp']
    wpn_name = EQUIP_NAMES.get(g.player.weapon_type, 'Fist')
    status = (f"HP:{g.player.hp}/{g.player.max_hp}  "
              f"Atk:{g.player.damage}  Gold:{g.player.gold}  "
              f"Lv:{g.dlvl}  [{wpn_name}]  "
              f"Slot:{g.current_slot or '-'}")
    stdscr.attron(curses.color_pair(hp_color) | curses.A_BOLD)
    stdscr.addstr(g.MAP_H, 0, status[:w - 1])
    stdscr.attroff(curses.color_pair(hp_color) | curses.A_BOLD)

    msgs = g.messages[-2:] if g.messages else [""]
    for i, msg in enumerate(msgs):
        y = g.MAP_H + 1 + i
        if y < h:
            stdscr.attron(curses.color_pair(CP['msg']))
            stdscr.addstr(y, 0, msg[:w - 1])
            stdscr.attroff(curses.color_pair(CP['msg']))

    stdscr.refresh()


# ── Map View ───────────────────────────────────────────────────────────────

def render_map_view(stdscr, g):
    stdscr.erase()
    h, w = stdscr.getmaxyx()

    title = f"── Explored Map (Level {g.dlvl}) ──"
    stdscr.addstr(0, max(0, (w - len(title)) // 2), title)

    legend = "@=You  #=Wall  .=Floor  >=Stairs  A-Z=Monsters"
    stdscr.addstr(1, max(0, (w - len(legend)) // 2), legend)

    for y in range(g.MAP_H):
        row = ''
        for x in range(g.MAP_W):
            if not g.explored[y][x]:
                row += ' '
            elif y == g.player.y and x == g.player.x:
                row += '@'
            else:
                is_monster = False
                for e in g.entities:
                    if e is not g.player and e.x == x and e.y == y:
                        row += e.name[0].upper()
                        is_monster = True
                        break
                if is_monster:
                    continue
                is_stairs = False
                for it in g.items:
                    if it.x == x and it.y == y and it.type == 'stairs':
                        row += '>'
                        is_stairs = True
                        break
                if is_stairs:
                    continue
                if g.map[y][x] == ord('#'):
                    row += '#'
                else:
                    row += '.'

        dy = y + 3
        if dy < h and row:
            stdscr.addstr(dy, 0, row)

    prompt = "Press any key to close"
    if h > 0:
        stdscr.addstr(h - 1, max(0, (w - len(prompt)) // 2), prompt)
    stdscr.refresh()
    stdscr.getch()


# ── Inventory Screen ───────────────────────────────────────────────────────

def inventory_screen(stdscr, g):
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    lines = []
    lines.append("┌─ Inventory ─────────────────────────────┐")
    lines.append(f"│ Weapon: {EQUIP_NAMES.get(g.player.weapon_type, '?'):8s}  "
                 f"Armor: +{g.player.armor_bonus}{'':10s}│")
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
        elif k == ord('0'):
            if len(inv) >= 10:
                return ('select', 9)
            if 0 < len(inv):
                return ('select', len(inv) - 1)


def inventory_flow(stdscr, g):
    if not g.player.inventory:
        g.add_msg("Nothing in inventory")
        return False
    res = inventory_screen(stdscr, g)
    if res is None:
        return False
    if isinstance(res, tuple) and res[0] == 'select':
        idx = res[1]
        if idx < len(g.player.inventory):
            it = g.player.inventory[idx]
            if it.type in ('weapon', 'armor'):
                equip_item(g, idx)
                return True
            elif it.type == 'potion_heal':
                g.player.hp = min(g.player.hp + 15, g.player.max_hp)
                g.add_msg("quaffed healing potion")
                g.player.inventory.pop(idx)
                return True
            elif it.type == 'potion_str':
                g.player.damage += 2
                g.add_msg("quaffed strength potion")
                g.player.inventory.pop(idx)
                return True
            elif it.type == 'food':
                g.player.hp = min(g.player.hp + 10, g.player.max_hp)
                g.add_msg("ate food")
                g.player.inventory.pop(idx)
                return True
            else:
                g.add_msg("Cannot use that")
                return False
    return False


def drop_flow(stdscr, g):
    if not g.player.inventory:
        g.add_msg("Nothing to drop")
        return False
    res = inventory_screen(stdscr, g)
    if res is None:
        return False
    if isinstance(res, tuple) and res[0] == 'select':
        idx = res[1]
        it = g.player.inventory[idx]
        if it is g.player.weapon_item:
            g.player.weapon_item = None
            g.player.weapon_type = EQ_FIST
            g.player.attack_range = 1
            g.player.damage = 5
        elif it is g.player.armor_item:
            g.player.armor_item = None
            g.player.armor_bonus = 0
            g.player.max_hp = 20
            g.player.hp = min(g.player.hp, g.player.max_hp)
        drop_item(g, idx)
        return True
    return False


# ── Save Slot Selection ────────────────────────────────────────────────────

def save_slot_selector(stdscr, g):
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    lines = [
        "  ┌─ Save to which slot? ────────────┐",
    ]
    for slot in range(1, 4):
        info = get_save_info(slot)
        if info is None:
            lines.append(f"  │ [{slot}] Slot {slot} — (empty)            │")
        elif info.get('corrupted'):
            lines.append(f"  │ [{slot}] Slot {slot} — (corrupted)       │")
        else:
            lines.append(f"  │ [{slot}] Slot {slot} — Lv.{info['dlvl']} "
                         f"HP:{info['hp']}/{info['max_hp']} │")
    lines.append("  │                                   │")
    lines.append("  │ (will overwrite existing save)    │")
    lines.append("  └───────────────────────────────────┘")
    lines.append("")
    lines.append("  Press 1/2/3 to save, ESC to cancel")

    for i, line in enumerate(lines):
        y = (h - len(lines)) // 2 + i
        if 0 <= y < h:
            stdscr.attron(curses.color_pair(CP['title']))
            stdscr.addstr(y, max(0, (w - 40) // 2), line)
            stdscr.attroff(curses.color_pair(CP['title']))

    stdscr.refresh()

    while True:
        k = stdscr.getch()
        if k == ord('1'):
            return 1
        elif k == ord('2'):
            return 2
        elif k == ord('3'):
            return 3
        elif k == 27:
            return None


# ── Title Screen ───────────────────────────────────────────────────────────

def title_screen(stdscr):
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    has_saves = any_save_exists()

    if has_saves:
        lines = [
            "  _____                    ",
            " |  _  |___ ___ ___ ___   ",
            " |     |  _| . |   |_ -|  ",
            " |__|__|_| |___|_|_|___|  ",
            "                          ",
            "  ⚔️  A classic dungeon-crawl  🛡️",
            "                          ",
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
        lines += [
            "                          ",
            "  [n] New Game            ",
            "  [q] Quit                ",
        ]
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
            if k == ord('1'):
                return ('load', 1)
            elif k == ord('2'):
                return ('load', 2)
            elif k == ord('3'):
                return ('load', 3)
            elif k in (ord('n'), ord('N')):
                return ('new', None)
            elif k in (ord('q'), ord('Q')):
                return ('quit', None)
    else:
        title = [
            "  _____                    ",
            " |  _  |___ ___ ___ ___   ",
            " |     |  _| . |   |_ -|  ",
            " |__|__|_| |___|_|_|___|  ",
            "                          ",
            "  ⚔️  A classic dungeon-crawl  🛡️",
            "                          ",
            "  Select difficulty:      ",
            "                          ",
            "  [1] Easy                ",
            "      Small map, weak foes",
            "                          ",
            "  [2] Middle (recommended)",
            "      Standard adventure  ",
            "                          ",
            "  [3] Hard                ",
            "      Many tough monsters ",
            "                          ",
            "  Press 1/2/3 to begin    ",
        ]
        for i, line in enumerate(title):
            y = h // 2 - 9 + i
            x = (w - 30) // 2
            if 0 <= y < h:
                stdscr.attron(curses.color_pair(CP['title']) | curses.A_BOLD)
                stdscr.addstr(y, max(0, x), line)
                stdscr.attroff(curses.color_pair(CP['title']) | curses.A_BOLD)
        stdscr.refresh()

        while True:
            k = stdscr.getch()
            if k == ord('1'):
                return ('new', 1)
            elif k == ord('2'):
                return ('new', 2)
            elif k == ord('3'):
                return ('new', 3)


# ── Game Over Screen ───────────────────────────────────────────────────────

def game_over_screen(stdscr, g):
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    lines = [
        "  ⚰️  GAME OVER ⚰️  ",
        f"  Level: {g.dlvl}  Gold: {g.player.gold}",
        f"  XP: {g.player.xp}  HP: {g.player.max_hp}",
        "",
        "  [r] Restart from scratch",
        "  [s] Strong New Game (keep stats & items)",
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
        if k in (ord('r'), ord('R')):
            return 'restart'
        elif k in (ord('s'), ord('S')):
            return 'strong'
        elif k in (ord('q'), ord('Q')):
            return 'quit'


# ── Main Game Loop ─────────────────────────────────────────────────────────

def play_game(stdscr):
    curses.curs_set(0)
    curses.use_default_colors()
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
    curses.init_pair(CP['equipped'], curses.COLOR_GREEN, -1)

    stdscr.nodelay(0)
    stdscr.keypad(True)

    saved = None

    while True:
        result = title_screen(stdscr)
        if result is None:
            return
        action, value = result

        if action == 'quit':
            return

        g = None

        if action == 'load':
            g = Game(2)
            ok = load_game(g, value)
            if not ok:
                continue
            g.add_msg("Game loaded. Welcome back!")
            g.game_over = False

        elif action == 'new':
            if value is None:
                diff_res = title_screen(stdscr)
                if diff_res is None or diff_res[0] == 'quit':
                    return
                _, diff = diff_res
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

            dx, dy = 0, 0
            acted = False

            if key == ord('q'):
                return
            elif key == ord('Q'):
                if g.current_slot:
                    ok = save_game(g, g.current_slot)
                    if ok:
                        g.add_msg(f"Saved to slot {g.current_slot}")
                    else:
                        g.add_msg("Save failed!")
                else:
                    slot = save_slot_selector(stdscr, g)
                    if slot is not None:
                        ok = save_game(g, slot)
                        if ok:
                            g.current_slot = slot
                            g.add_msg(f"Saved to slot {slot}")
                        else:
                            g.add_msg("Save failed!")
                render(stdscr, g)
            elif key == ord('S'):
                if g.current_slot:
                    ok = save_game(g, g.current_slot)
                    if ok:
                        g.add_msg(f"Saved to slot {g.current_slot}")
                    else:
                        g.add_msg("Save failed!")
                else:
                    slot = save_slot_selector(stdscr, g)
                    if slot is not None:
                        ok = save_game(g, slot)
                        if ok:
                            g.current_slot = slot
                            g.add_msg(f"Saved to slot {slot}")
                        else:
                            g.add_msg("Save failed!")
                render(stdscr, g)
            elif key in (ord('h'), curses.KEY_LEFT):
                dx, dy = -1, 0
            elif key in (ord('j'), curses.KEY_DOWN):
                dx, dy = 0, 1
            elif key in (ord('k'), curses.KEY_UP):
                dx, dy = 0, -1
            elif key in (ord('l'), curses.KEY_RIGHT):
                dx, dy = 1, 0
            elif key == ord('y'):
                dx, dy = -1, -1
            elif key == ord('u'):
                dx, dy = 1, -1
            elif key == ord('b'):
                dx, dy = -1, 1
            elif key == ord('n'):
                dx, dy = 1, 1
            elif key == ord(' '):
                pickup_at(g, g.player.x, g.player.y)
                acted = True
            elif key == ord('.'):
                g.player.hp = min(g.player.hp + 1, g.player.max_hp)
                acted = True
            elif key == ord('>'):
                found = False
                for it in g.items:
                    if (it.x == g.player.x and it.y == g.player.y
                            and it.type == 'stairs'):
                        g.dlvl += 1
                        g.add_msg(f"You descend to level {g.dlvl}")
                        gen_level(g)
                        compute_fov(g)
                        g.messages = g.messages[-10:]
                        found = True
                        acted = True
                        break
                if not found:
                    g.add_msg("No stairs here")
            elif key == ord('i'):
                inventory_flow(stdscr, g)
                render(stdscr, g)
            elif key == ord('d'):
                drop_flow(stdscr, g)
                render(stdscr, g)
            elif key == ord('m'):
                render_map_view(stdscr, g)
                render(stdscr, g)
            elif key == ord('f'):
                if g.player.weapon_type == EQ_MAGIC:
                    magic_aoe(g)
                    acted = True
                else:
                    g.add_msg("No magic staff equipped")

            if dx != 0 or dy != 0:
                acted = move_or_attack(g, dx, dy)

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
