#!/usr/bin/env python3
"""
Mystic Dungeon - A dungeon-crawling game with turn-based combat and shops.
"""

import curses
import random
import json
import os
import math

# ── Emoji ──────────────────────────────────────────────────────────────────
T_WALL_EMOJI   = '🧱'
T_FLOOR_EMOJI  = '⬜'
T_STAIRS_EMOJI = '🔽'
T_SHOP_EMOJI   = '🏪'
PLAYER_EMOJI   = '🧙'
GOLD_EMOJI     = '🪙'
SWORD_EMOJI    = '⚔️'
ARMOR_EMOJI    = '🛡️'
POTION_EMOJI   = '🧪'
FOOD_EMOJI     = '🍗'

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

# ── Monster templates: (name, hp, xp, patk, matk, pdef, mdef, crit_rate, crit_dmg, weakness) ──
MONSTER_TEMPLATES = [
    ('Ant',        5,   1,  2, 0, 0, 0, 0.02, 1.5, None),
    ('Bat',        8,   2,  3, 0, 0, 0, 0.05, 1.5, None),
    ('Centipede', 10,   3,  4, 0, 1, 0, 0.02, 1.5, 'physical'),
    ('Dog',       15,   5,  4, 1, 1, 1, 0.05, 1.5, None),
    ('Eye',       20,   8,  1, 4, 0, 2, 0.08, 2.0, 'magic'),
    ('Frog',      25,  10,  2, 5, 1, 2, 0.05, 1.5, 'magic'),
    ('Goblin',    30,  12,  5, 2, 2, 1, 0.05, 1.5, 'physical'),
    ('Harpy',     35,  15,  3, 6, 2, 3, 0.08, 1.5, 'magic'),
    ('Imp',       40,  18,  6, 2, 3, 2, 0.05, 1.5, 'physical'),
    ('Jackal',    45,  20,  7, 2, 3, 2, 0.08, 1.5, 'physical'),
    ('Kobold',    50,  22,  7, 3, 4, 3, 0.05, 1.5, None),
    ('Lich',      60,  30,  3, 9, 3, 5, 0.10, 2.0, 'magic'),
    ('Mummy',     70,  35,  8, 4, 5, 4, 0.05, 1.5, 'physical'),
    ('Ogre',      80,  40,  9, 3, 6, 3, 0.08, 2.0, 'physical'),
    ('Troll',     90,  45,  8, 5, 6, 5, 0.05, 1.5, None),
    ('Wyrm',     120,  60, 10, 10, 8, 8, 0.10, 2.0, None),
]

# ── Weapon DB: (name, emoji, attack_type, base_patk, base_matk, crit_rate, crit_dmg, rarity) ──
# rarity: 0=Common, 1=Uncommon, 2=Rare, 3=Legendary
WEAPON_DB = [
    # Common
    ('Dagger',       '🗡️', 'physical', 1, 0, 0.05, 1.5, 0),
    ('Short Sword',  '⚔️', 'physical', 2, 0, 0.05, 1.5, 0),
    ('Club',         '🏏', 'physical', 1, 0, 0.08, 2.0, 0),
    ('Wand',         '🪄', 'magic',    0, 2, 0.05, 1.5, 0),
    ('Bone Rod',     '🦴', 'magic',    0, 1, 0.05, 1.5, 0),
    # Uncommon
    ('Long Sword',   '⚔️', 'physical', 3, 0, 0.05, 1.5, 1),
    ('War Hammer',   '🔨', 'physical', 3, 0, 0.08, 2.0, 1),
    ('Spear',        '🔱', 'physical', 2, 1, 0.08, 1.5, 1),
    ('Magic Staff',  '🪄', 'magic',    0, 4, 0.08, 2.0, 1),
    ('Flail',        '⛓️', 'physical', 4, 0, 0.05, 1.5, 1),
    # Rare
    ('Great Sword',  '⚔️', 'physical', 5, 0, 0.10, 2.5, 2),
    ('Battle Axe',   '🪓', 'physical', 5, 0, 0.12, 2.0, 2),
    ('Arcane Rod',   '✨', 'magic',    0, 6, 0.10, 2.5, 2),
    ('Crystal Staff','💎', 'magic',    1, 5, 0.08, 2.0, 2),
    # Legendary
    ('Muramasa',     '🗡️', 'physical', 7, 0, 0.15, 3.0, 3),
    ('Excalibur',    '⚔️', 'physical', 8, 2, 0.10, 2.5, 3),
    ('Zantetsuken',  '⚔️', 'physical', 6, 0, 0.20, 3.5, 3),
    ('Shuriken',     '⭐', 'physical', 4, 0, 0.25, 2.0, 3),
    ('Gungnir',      '🔱', 'physical', 9, 0, 0.08, 2.5, 3),
    ('Mjolnir',      '🔨', 'physical', 7, 3, 0.12, 3.0, 3),
]

# ── Armor DB: (name, emoji, base_pdef, base_mdef, rarity) ──────────────────
ARMOR_DB = [
    # Common
    ('Leather Armor', '🛡️', 2, 0, 0),
    ('Mage Robe',     '👘', 0, 3, 0),
    ('Wooden Shield', '🛡️', 1, 1, 0),
    # Uncommon
    ('Chain Mail',    '🛡️', 3, 1, 1),
    ('Arcane Cloak',  '🔮', 1, 4, 1),
    ('Iron Shield',   '🛡️', 3, 0, 1),
    # Rare
    ('Plate Armor',   '🛡️', 5, 2, 2),
    ('Mithril Mail',  '✨',  4, 4, 2),
    # Legendary
    ('Dragon Mail',   '🐉', 6, 5, 3),
    ('Aegis',         '🛡️', 8, 8, 3),
]

# ── Potion templates ───────────────────────────────────────────────────────
POTION_TEMPLATES = [
    ('Healing Potion', 'potion_heal', 30),
    ('Strength Potion', 'potion_str', 50),
    ('Mana Bread', 'food', 20),
]

# ── Rarity bonus range per level ───────────────────────────────────────────
RARITY_BONUS_MIN = {0: 0, 1: 0, 2: 1, 3: 2}
RARITY_BONUS_MAX = {0: 0, 1: 1, 2: 3, 3: 5}
RARITY_DROP_WEIGHT = {0: 40, 1: 30, 2: 20, 3: 10}

# ── Colors ─────────────────────────────────────────────────────────────────
CP = {'player': 1, 'monster': 2, 'gold': 3, 'item': 4, 'wall': 5,
      'floor': 6, 'stairs': 7, 'msg': 8, 'hp': 9, 'hp_low': 10, 'title': 11,
      'inventory': 12, 'equipped': 13, 'battle_hp': 14, 'battle_text': 15}

# ── Attack type helpers ────────────────────────────────────────────────────
ATK_PHYSICAL = 'physical'
ATK_MAGIC = 'magic'

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


RARITY_NAMES = {0: 'Common', 1: 'Uncommon', 2: 'Rare', 3: 'Legendary'}
RARITY_COLORS = {0: 0, 1: 2, 2: 4, 3: 3}


class Entity:
    __slots__ = ('x', 'y', 'ch', 'color', 'blocks', 'name',
                 'hp', 'max_hp', 'xp', 'gold',
                 'patk', 'matk', 'pdef', 'mdef', 'crit_rate', 'crit_dmg',
                 'weakness', 'inventory', 'weapon_item', 'armor_item',
                 'rare_bearer')
    def __init__(self, x, y, ch, color, blocks=False,
                 name='', hp=0, max_hp=0, xp=0,
                 patk=0, matk=0, pdef=0, mdef=0,
                 crit_rate=0.0, crit_dmg=1.0, weakness=None):
        self.x, self.y = x, y
        self.ch, self.color = ch, color
        self.blocks = blocks
        self.name = name
        self.hp, self.max_hp, self.xp = hp, max_hp, xp
        self.gold = 0
        self.patk = patk
        self.matk = matk
        self.pdef = pdef
        self.mdef = mdef
        self.crit_rate = crit_rate
        self.crit_dmg = crit_dmg
        self.weakness = weakness
        self.inventory = []
        self.weapon_item = None
        self.armor_item = None
        self.rare_bearer = False


class Item:
    __slots__ = ('x', 'y', 'emoji', 'name', 'type', 'value',
                 'patk', 'matk', 'pdef', 'mdef',
                 'crit_rate', 'crit_dmg', 'attack_type', 'rarity')
    def __init__(self, x, y, emoji, name, itype, value=0,
                 patk=0, matk=0, pdef=0, mdef=0,
                 crit_rate=0.0, crit_dmg=1.0, attack_type=None,
                 rarity=0):
        self.x, self.y = x, y
        self.emoji = emoji
        self.name = name
        self.type = itype
        self.value = value
        self.patk = patk
        self.matk = matk
        self.pdef = pdef
        self.mdef = mdef
        self.crit_rate = crit_rate
        self.crit_dmg = crit_dmg
        self.attack_type = attack_type
        self.rarity = rarity


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
        self.rare_dropped_this_floor = False

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
            mt = random.choice(MONSTER_TEMPLATES)
            mname, hp, xp, patk, matk, pdef, mdef, crit_rate, crit_dmg, weakness = mt
            dlvl_scale = 1.0 + (g.dlvl - 1) * 0.3
            hp = max(1, int(hp * dlvl_scale * g.dmg_scale))
            xp = max(1, int(xp * dlvl_scale))
            patk = max(0, int(patk * dlvl_scale * g.dmg_scale))
            matk = max(0, int(matk * dlvl_scale * g.dmg_scale))
            pdef = max(0, int(pdef * dlvl_scale * g.dmg_scale))
            mdef = max(0, int(mdef * dlvl_scale * g.dmg_scale))
            sym = MONSTER_EMOJI.get(mname, '👾')
            m = Entity(x, y, sym, CP['monster'],
                       blocks=True, name=mname,
                       hp=hp, max_hp=hp, xp=xp,
                       patk=patk, matk=matk, pdef=pdef, mdef=mdef,
                       crit_rate=crit_rate, crit_dmg=crit_dmg, weakness=weakness)
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
            v = random.randint(1, 10 * g.dlvl)
            g.items.append(Item(x, y, GOLD_EMOJI,
                                f'{v} gold', 'gold', v))

    shop_rooms = [r for r in g.rooms[1:-1] if len(g.rooms) > 2]
    if shop_rooms and random.random() < 0.35:
        r = random.choice(shop_rooms)
        sx = random.randint(r.x + 1, r.x + r.w - 2)
        sy = random.randint(r.y + 1, r.y + r.h - 2)
        if not any(e.x == sx and e.y == sy for e in g.entities):
            if not any(it.x == sx and it.y == sy for it in g.items):
                g.items.append(Item(sx, sy, T_SHOP_EMOJI, 'Item Shop', 'shop'))

    g.rare_dropped_this_floor = False
    rare_candidates = [e for e in g.entities if e is not g.player]
    if rare_candidates:
        random.choice(rare_candidates).rare_bearer = True


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


# ── Damage Calculation ────────────────────────────────────────────────────

def calc_attack_power(entity, weapon_item):
    if weapon_item and weapon_item.attack_type == ATK_MAGIC:
        return entity.matk + weapon_item.matk, ATK_MAGIC
    elif weapon_item:
        return entity.patk + weapon_item.patk, ATK_PHYSICAL
    return entity.patk, ATK_PHYSICAL


def calc_defense(entity, attack_type):
    if attack_type == ATK_MAGIC:
        return entity.mdef
    return entity.pdef


def calc_damage(attacker, weapon_item, defender):
    atk_power, atk_type = calc_attack_power(attacker, weapon_item)
    c_rate = attacker.crit_rate
    c_dmg = attacker.crit_dmg
    if weapon_item:
        c_rate += weapon_item.crit_rate
        c_dmg += weapon_item.crit_dmg - 1.0

    is_crit = random.random() < c_rate

    if defender.weakness == atk_type:
        atk_power = int(atk_power * 1.5)

    if is_crit:
        dmg = int(atk_power * c_dmg)
    else:
        defense = calc_defense(defender, atk_type)
        dmg = max(3, atk_power - defense)

    return max(1, dmg), is_crit, atk_type


def level_up_check(g):
    if g.player.xp >= g.player.max_hp * 2:
        g.player.max_hp += 5
        g.player.hp = min(g.player.hp + 5, g.player.max_hp)
        g.player.patk += 1
        g.player.pdef += 1
        g.player.mdef += 1
        g.add_msg("Level up! HP+5 ATK+1 DEF+1")


def pick_rarity(g, is_rare_bearer):
    if is_rare_bearer and not g.rare_dropped_this_floor:
        g.rare_dropped_this_floor = True
        return random.choices([2, 3], weights=[60, 40])[0]
    weights = list(RARITY_DROP_WEIGHT.values())
    if g.rare_dropped_this_floor:
        return random.choices([0, 1, 2, 3], weights=weights)[0]
    else:
        w2 = weights[:]
        w2[2] *= 3
        w2[3] *= 3
        r = random.choices([0, 1, 2, 3], weights=w2)[0]
        if r >= 2:
            g.rare_dropped_this_floor = True
        return r


def make_weapon(g, rarity):
    candidates = [w for w in WEAPON_DB if w[7] == rarity]
    if not candidates:
        candidates = [w for w in WEAPON_DB]
    name, emoji, at, bpatk, bmatk, bcr, bcd, _ = random.choice(candidates)
    bonus = random.randint(RARITY_BONUS_MIN[rarity], RARITY_BONUS_MAX[rarity] + g.dlvl // 2)
    bonus = max(0, bonus)
    patk = max(0, bpatk + bonus)
    matk = max(0, bmatk + bonus)
    cr = min(0.5, bcr + bonus * 0.01)
    cd = bcd
    wname = f"{name}+{bonus}" if bonus > 0 else name
    w = Item(0, 0, emoji, wname, 'weapon',
             patk=patk, matk=matk, crit_rate=cr, crit_dmg=cd,
             attack_type=at, value=50 + bonus * 30, rarity=rarity)
    return w


def make_armor(g, rarity):
    candidates = [a for a in ARMOR_DB if a[4] == rarity]
    if not candidates:
        candidates = [a for a in ARMOR_DB]
    name, emoji, bpdef, bmdef, _ = random.choice(candidates)
    bonus = random.randint(RARITY_BONUS_MIN[rarity], RARITY_BONUS_MAX[rarity] + g.dlvl // 2)
    bonus = max(0, bonus)
    pdef = max(0, bpdef + bonus * 2)
    mdef = max(0, bmdef + bonus * 2)
    aname = f"{name}+{bonus}" if bonus > 0 else name
    a = Item(0, 0, emoji, aname, 'armor',
             pdef=pdef, mdef=mdef, value=40 + bonus * 40, rarity=rarity)
    return a


def make_consumable(g):
    pt = random.choice(POTION_TEMPLATES)
    pname, ptype, pval = pt
    emoji = FOOD_EMOJI if ptype == 'food' else POTION_EMOJI
    return Item(0, 0, emoji, pname, ptype, value=pval)


def enemy_drop(g, enemy):
    g.player.xp += enemy.xp
    gold_drop = random.randint(1, 5) * (1 + g.dlvl)
    g.player.gold += gold_drop
    g.add_msg(f"Dropped {gold_drop} gold")

    if enemy.rare_bearer:
        g.add_msg("A rare aura emanates from the corpse!")

    drop_roll = 0.4 + (0.2 if enemy.rare_bearer else 0.0)
    if random.random() >= drop_roll:
        return
    if len(g.player.inventory) >= 10:
        return

    rarity = pick_rarity(g, enemy.rare_bearer)

    roll = random.random()
    if roll < 0.35:
        item = make_weapon(g, rarity)
    elif roll < 0.65:
        item = make_armor(g, rarity)
    else:
        item = make_consumable(g)

    g.player.inventory.append(item)
    rarity_tag = ['', ' +', ' ★', ' ✦'][rarity]
    g.add_msg(f"Found: {item.name}{rarity_tag}")


# ── Battle Screen ─────────────────────────────────────────────────────────

def battle_screen(stdscr, g, enemy, player_first):
    curses.curs_set(0)
    BOX_W = 50
    BOX_H = 16
    player_turn = player_first

    while enemy.hp > 0 and g.player.hp > 0:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        ox = max(0, (w - BOX_W) // 2)
        oy = max(0, (h - BOX_H) // 2)

        lines = [
            "╔══════════════════════ BATTLE ══════════════════════╗",
            f"║  {enemy.ch} {enemy.name:<20s}                           ║",
            f"║  HP: {max(0,enemy.hp):>3d}/{enemy.max_hp:<3d}                                 ║",
            "╠══════════════════════════════════════════════════╣",
            f"║  {PLAYER_EMOJI} {g.player.name:<20s}                           ║",
            f"║  HP: {max(0,g.player.hp):>3d}/{g.player.max_hp:<3d}                                 ║",
            "╠══════════════════════════════════════════════════╣",
        ]

        if player_turn:
            lines.append("║  Your turn — choose weapon:                    ║")
            lines.append("║                                                  ║")

            wpn_choices = []
            if g.player.weapon_item:
                wpn_choices.append(('e', g.player.weapon_item))
            for idx, it in enumerate(g.player.inventory):
                if it.type == 'weapon' and it is not g.player.weapon_item:
                    tag = str((idx + 1) % 10)
                    wpn_choices.append((tag, it, idx))

            if not wpn_choices:
                lines.append("║  No weapons available! (fist)                  ║")
                wpn_choices.append(('f', None, -1))

            for tag, it, _ in wpn_choices:
                if it is None:
                    info = "Fist (PATK:0)"
                else:
                    rarity_tag = ['', ' +', ' ★', ' ✦'][it.rarity]
                    at = it.attack_type or ATK_PHYSICAL
                    if at == ATK_PHYSICAL:
                        info = f"{it.name}{rarity_tag} P+{it.patk} CRIT{int(it.crit_rate*100)}%"
                    else:
                        info = f"{it.name}{rarity_tag} M+{it.matk} CRIT{int(it.crit_rate*100)}%"
                lines.append(f"║  [{tag}] {info:<44s}║")
        else:
            lines.append(f"║  Enemy turn...                                  ║")
            lines.append("║                                                  ║")
            lines.append("║                                                  ║")
            lines.append("║                                                  ║")

        lines.append("╚══════════════════════════════════════════════════╝")
        for i, line in enumerate(lines):
            ly = oy + i
            if 0 <= ly < h:
                stdscr.attron(curses.color_pair(CP['battle_text']))
                stdscr.addstr(ly, ox, line[:BOX_W])
                stdscr.attroff(curses.color_pair(CP['battle_text']))

        stdscr.refresh()

        if player_turn:
            while True:
                k = stdscr.getch()
                if k == ord('f'):
                    chosen_wpn = None
                    break
                elif k == ord('e') and g.player.weapon_item:
                    chosen_wpn = g.player.weapon_item
                    break
                elif k == ord('0'):
                    chosen_wpn = None
                    g.add_msg("Invalid choice")
                    continue
                elif ord('1') <= k <= ord('9'):
                    idx = k - ord('1')
                    if 0 <= idx < len(g.player.inventory):
                        it = g.player.inventory[idx]
                        if it.type == 'weapon' and it is not g.player.weapon_item:
                            chosen_wpn = it
                            break
        else:
            stdscr.nodelay(1)
            stdscr.getch()
            stdscr.nodelay(0)
            chosen_wpn = enemy.weapon_item if enemy.weapon_item else None

        dmg, is_crit, at_type = calc_damage(g.player if player_turn else enemy,
                                            chosen_wpn,
                                            enemy if player_turn else g.player)
        attacker_name = g.player.name if player_turn else enemy.name
        g.add_msg(f"{'CRIT! ' if is_crit else ''}{attacker_name} hits {enemy.name if player_turn else g.player.name} for {dmg} ({at_type})")

        if player_turn:
            enemy.hp -= dmg
            player_turn = False
            if enemy.hp <= 0:
                g.add_msg(f"{enemy.name} is slain!")
                g.entities.remove(enemy)
                level_up_check(g)
                enemy_drop(g, enemy)
                return True
        else:
            g.player.hp -= dmg
            player_turn = True
            if g.player.hp <= 0:
                g.game_over = True
                g.add_msg("You have died...")
                return False

    return g.player.hp > 0


# ── Monster AI ────────────────────────────────────────────────────────────

def monster_tick(stdscr, g):
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
                battle_screen(stdscr, g, e, player_first=False)
                return


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

def move_or_attack(stdscr, g, dx, dy):
    nx, ny = g.player.x + dx, g.player.y + dy
    if not (0 < nx < g.MAP_W - 1 and 0 < ny < g.MAP_H - 1):
        return False

    for e in g.entities:
        if e is not g.player and e.x == nx and e.y == ny and e.hp > 0:
            battle_screen(stdscr, g, e, player_first=True)
            return True

    if g.map[ny][nx] != ord('#'):
        g.player.x, g.player.y = nx, ny
        pickup_at(stdscr, g, nx, ny)
        return True
    return False


def pickup_at(stdscr, g, x, y):
    for it in list(g.items):
        if it.x == x and it.y == y:
            if it.type == 'stairs':
                g.dlvl += 1
                g.add_msg(f"Descend to level {g.dlvl}")
                gen_level(g)
                compute_fov(g)
                g.messages = g.messages[-10:]
                g.add_msg("You arrive on a new floor")
                return True
            elif it.type == 'gold':
                g.player.gold += it.value
                g.add_msg(f"picked up {it.value} gold")
                g.items.remove(it)
                return True
            elif it.type == 'shop':
                g.add_msg("Press [s] to enter the shop")
                return True


def equip_item(g, idx):
    if idx < 0 or idx >= len(g.player.inventory):
        return
    it = g.player.inventory[idx]
    if it.type == 'weapon':
        old = g.player.weapon_item
        g.player.weapon_item = it
        if old:
            g.player.inventory.append(old)
        g.player.inventory.pop(idx)
        g.add_msg(f"equipped {it.name}")
    elif it.type == 'armor':
        old = g.player.armor_item
        g.player.armor_item = it
        if old:
            g.player.inventory.append(old)
        g.player.inventory.pop(idx)
        g.add_msg(f"equipped {it.name}")


# ── Shop Screen ───────────────────────────────────────────────────────────

def shop_screen(stdscr, g):
    inv = [it for it in g.player.inventory if it.type in ('weapon', 'armor', 'potion_heal', 'food', 'potion_str')]
    shop_inv = []
    for _ in range(random.randint(3, 5)):
        r = random.choices([0, 1, 2, 3], weights=[30, 30, 25, 15])[0]
        if random.random() < 0.5:
            item = make_weapon(g, r)
        else:
            item = make_armor(g, r)
        item.value = max(20, item.value + item.patk * 30 + item.matk * 30 + item.pdef * 25 + item.mdef * 25)
        shop_inv.append(item)

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        lines = [
            "╔═══════════════ SHOP ═══════════════════╗",
            f"║  Gold: {g.player.gold:<5d}                              ║",
            "╠═══════════ Buy ───────────────────────╣",
        ]
        for i, it in enumerate(shop_inv):
            rarity_tag = ['', ' +', ' ★', ' ✦'][it.rarity]
            if it.type == 'weapon':
                info = f"{it.name}{rarity_tag} P+{it.patk} M+{it.matk}"
            else:
                info = f"{it.name}{rarity_tag} PD+{it.pdef} MD+{it.mdef}"
            lines.append(f"║  [{i+1}] {info:<25s} ${it.value:>4d}  ║")
        lines.append("╠═══════════ Sell ──────────────────────╣")
        if not inv:
            lines.append("║  (no items to sell)                     ║")
        else:
            for i, it in enumerate(inv[:6]):
                val = max(1, it.value // 2)
                lines.append(f"║  [s{i+1}] {it.name:<25s} ${val:>4d}  ║")
        lines.append("╠══════════════════════════════════════╣")
        lines.append("║  q: exit    b1-9: buy   s1-9: sell  ║")
        lines.append("╚══════════════════════════════════════╝")

        for i, line in enumerate(lines):
            if i < h:
                stdscr.attron(curses.color_pair(CP['title']))
                stdscr.addstr(i, max(0, (w - 42) // 2), line[:w-1])
                stdscr.attroff(curses.color_pair(CP['title']))
        stdscr.refresh()

        k = stdscr.getch()
        if k == ord('q') or k == 27:
            return
        elif ord('1') <= k <= ord('9'):
            idx = k - ord('1')
            if idx < len(shop_inv):
                it = shop_inv[idx]
                if g.player.gold >= it.value:
                    g.player.gold -= it.value
                    if len(g.player.inventory) < 10:
                        it.x, it.y = 0, 0
                        g.player.inventory.append(it)
                        g.add_msg(f"Bought {it.name} for ${it.value}")
                        shop_inv.pop(idx)
                    else:
                        g.add_msg("Inventory full!")
                else:
                    g.add_msg("Not enough gold!")
        elif k == ord('s') or k == ord('S'):
            stdscr.nodelay(1)
            stdscr.getch()
            stdscr.nodelay(0)
            continue
        elif k >= ord('s') and k <= ord('s') + 9:
            idx = k - ord('s') - 1
            if idx < len(inv):
                it = inv[idx]
                val = max(1, it.value // 2)
                g.player.gold += val
                g.player.inventory.remove(it)
                if it is g.player.weapon_item:
                    g.player.weapon_item = None
                if it is g.player.armor_item:
                    g.player.armor_item = None
                g.add_msg(f"Sold {it.name} for ${val}")
                inv = [i for i in g.player.inventory if i.type in ('weapon', 'armor', 'potion_heal', 'food', 'potion_str')]


def drop_item(g, idx, ground=True):
    if idx < 0 or idx >= len(g.player.inventory):
        return
    it = g.player.inventory.pop(idx)
    if it is g.player.weapon_item:
        g.player.weapon_item = None
    if it is g.player.armor_item:
        g.player.armor_item = None
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
        'patk': it.patk, 'matk': it.matk,
        'pdef': it.pdef, 'mdef': it.mdef,
        'crit_rate': it.crit_rate, 'crit_dmg': it.crit_dmg,
        'attack_type': it.attack_type,
        'rarity': it.rarity,
    }


def item_from_dict(d):
    if d is None:
        return None
    return Item(d['x'], d['y'], d['emoji'], d['name'],
                d['type'], d.get('value', 0),
                d.get('patk', 0), d.get('matk', 0),
                d.get('pdef', 0), d.get('mdef', 0),
                d.get('crit_rate', 0.0), d.get('crit_dmg', 1.0),
                d.get('attack_type'),
                d.get('rarity', 0))


def save_game(g, slot):
    data = {
        'version': 4,
        'diff': g.diff,
        'dlvl': g.dlvl,
        'MAP_W': g.MAP_W,
        'MAP_H': g.MAP_H,
        'player': {
            'x': g.player.x, 'y': g.player.y,
            'hp': g.player.hp, 'max_hp': g.player.max_hp,
            'xp': g.player.xp,
            'gold': g.player.gold,
            'patk': g.player.patk, 'matk': g.player.matk,
            'pdef': g.player.pdef, 'mdef': g.player.mdef,
            'crit_rate': g.player.crit_rate, 'crit_dmg': g.player.crit_dmg,
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
        'rare_dropped_this_floor': g.rare_dropped_this_floor,
    }
    for e in g.entities:
        if e is g.player:
            continue
        data['entities'].append({
            'name': e.name, 'x': e.x, 'y': e.y,
            'hp': e.hp, 'max_hp': e.max_hp,
            'patk': e.patk, 'matk': e.matk,
            'pdef': e.pdef, 'mdef': e.mdef,
            'crit_rate': e.crit_rate, 'crit_dmg': e.crit_dmg,
            'weakness': e.weakness, 'xp': e.xp,
            'rare_bearer': e.rare_bearer,
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

    ver = data.get('version', 1)
    if ver < 2:
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
                      hp=pd.get('hp', 20), max_hp=pd.get('max_hp', 20),
                      xp=pd.get('xp', 0),
                      patk=pd.get('patk', 3), matk=pd.get('matk', 2),
                      pdef=pd.get('pdef', 1), mdef=pd.get('mdef', 1),
                      crit_rate=pd.get('crit_rate', 0.05),
                      crit_dmg=pd.get('crit_dmg', 1.5))
    g.player.gold = pd.get('gold', 0)
    g.player.inventory = [item_from_dict(it) for it in pd.get('inventory', [])]
    g.player.weapon_item = item_from_dict(pd.get('weapon_item'))
    g.player.armor_item = item_from_dict(pd.get('armor_item'))

    g.entities = [g.player]
    for ed in data.get('entities', []):
        mname = ed['name']
        sym = MONSTER_EMOJI.get(mname, '👾')
        m = Entity(ed['x'], ed['y'], sym, CP['monster'],
                   blocks=True, name=mname,
                   hp=ed.get('hp', 5), max_hp=ed.get('max_hp', 5),
                   xp=ed.get('xp', 0),
                   patk=ed.get('patk', 2), matk=ed.get('matk', 0),
                   pdef=ed.get('pdef', 0), mdef=ed.get('mdef', 0),
                   crit_rate=ed.get('crit_rate', 0.05),
                   crit_dmg=ed.get('crit_dmg', 1.5),
                   weakness=ed.get('weakness'))
        m.rare_bearer = ed.get('rare_bearer', False)
        g.entities.append(m)

    g.items = [item_from_dict(it) for it in data.get('items', [])]
    g.rare_dropped_this_floor = data.get('rare_dropped_this_floor', False)
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

    wpn_name = g.player.weapon_item.name if g.player.weapon_item else 'Fist'
    arm_name = g.player.armor_item.name[:8] if g.player.armor_item else 'None'
    hp_pct = g.player.hp / g.player.max_hp if g.player.max_hp > 0 else 0
    hp_color = CP['hp_low'] if hp_pct < 0.3 else CP['hp']
    status = (f"HP:{g.player.hp}/{g.player.max_hp}  "
              f"P:{g.player.patk}+{g.player.weapon_item.patk if g.player.weapon_item else 0} "
              f"M:{g.player.matk}+{g.player.armor_item.matk if g.player.armor_item else 0}  "
              f"Gold:{g.player.gold}  "
              f"Lv:{g.dlvl}  [{wpn_name}] [{arm_name}]  "
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
    wpn = g.player.weapon_item.name if g.player.weapon_item else 'Fist'
    arm = g.player.armor_item.name if g.player.armor_item else 'None'
    lines.append(f"│ Weapon: {wpn:>12s}  Armor: {arm:>12s}  │")
    lines.append("├─────────────────────────────────────────┤")
    inv = g.player.inventory
    if not inv:
        lines.append("│  (empty)                              │")
    else:
        for i, it in enumerate(inv):
            extra = ''
            if it.type == 'weapon':
                at = it.attack_type or ATK_PHYSICAL
                if at == ATK_PHYSICAL:
                    extra = f" P+{it.patk} C{int(it.crit_rate*100)}%"
                else:
                    extra = f" M+{it.matk} C{int(it.crit_rate*100)}%"
            elif it.type == 'armor':
                extra = f" PD+{it.pdef} MD+{it.mdef}"
            rarity_tag = ['', ' +', ' ★', ' ✦'][it.rarity]
            name = f"{it.emoji} {it.name}{rarity_tag}{extra}"
            pad = 37 - min(len(name), 37)
            lines.append(f"│ [{i + 1}] {name[:37]}{' ' * pad}│")
    lines.append("├─────────────────────────────────────────┤")
    lines.append("│ 1-9: use/equip  d: drop  q: exit        │")
    lines.append("└─────────────────────────────────────────┘")

    for i, line in enumerate(lines):
        y = (h - len(lines)) // 2 + i
        if 0 <= y < h:
            stdscr.attron(curses.color_pair(CP['inventory']))
            stdscr.addstr(y, max(0, (w - 42) // 2), line[:w - 1])
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
                g.player.patk += 2
                g.player.matk += 1
                g.add_msg("strength +2!")
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
            "  __  __         _   _              ",
            " |  \/  |_  _ __| |_(_)_ _  __ _    ",
            " | |\/| | || / _|  _| | ' \/ _\` |  ",
            " |_|  |_|\_,_\__|\__|_|_||_\__, |   ",
            "                          |___/    ",
            "  ⚔️  Mystic Dungeon  🛡️            ",
            "                                  ",
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
            "  __  __         _   _              ",
            " |  \/  |_  _ __| |_(_)_ _  __ _    ",
            " | |\/| | || / _|  _| | ' \/ _\` |  ",
            " |_|  |_|\_,_\__|\__|_|_||_\__, |   ",
            "                          |___/    ",
            "  ⚔️  Mystic Dungeon  🛡️            ",
            "                                  ",
            "  Select difficulty:              ",
            "                                  ",
            "  [1] Easy                        ",
            "      Small map, weak foes        ",
            "                                  ",
            "  [2] Middle (recommended)        ",
            "      Standard adventure          ",
            "                                  ",
            "  [3] Hard                        ",
            "      Many tough monsters         ",
            "                                  ",
            "  Press 1/2/3 to begin            ",
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
        "  ⚰️  GAME OVER ⚰️     ",
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
    curses.init_pair(CP['battle_hp'], curses.COLOR_RED, -1)
    curses.init_pair(CP['battle_text'], curses.COLOR_WHITE, -1)

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
                               hp=20, max_hp=20, xp=0,
                               patk=3, matk=2, pdef=1, mdef=1,
                               crit_rate=0.05, crit_dmg=1.5)
            g.entities.append(g.player)

            if saved is not None:
                g.player.max_hp = saved['max_hp']
                g.player.hp = saved['hp']
                g.player.patk = saved['patk']
                g.player.matk = saved['matk']
                g.player.pdef = saved['pdef']
                g.player.mdef = saved['mdef']
                g.player.crit_rate = saved['crit_rate']
                g.player.crit_dmg = saved['crit_dmg']
                g.player.gold = saved['gold']
                g.player.xp = saved['xp']
                g.player.inventory = list(saved['inventory'])
                g.player.weapon_item = saved['weapon_item']
                g.player.armor_item = saved['armor_item']
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
                pickup_at(stdscr, g, g.player.x, g.player.y)
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
                        g.add_msg("You arrive on a new floor")
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
            elif key == ord('s'):
                for it in g.items:
                    if (it.x == g.player.x and it.y == g.player.y
                            and it.type == 'shop'):
                        shop_screen(stdscr, g)
                        break
                else:
                    g.add_msg("No shop here")
                render(stdscr, g)

            if dx != 0 or dy != 0:
                acted = move_or_attack(stdscr, g, dx, dy)

            compute_fov(g)

            if acted:
                monster_tick(stdscr, g)

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
                    'patk': g.player.patk,
                    'matk': g.player.matk,
                    'pdef': g.player.pdef,
                    'mdef': g.player.mdef,
                    'crit_rate': g.player.crit_rate,
                    'crit_dmg': g.player.crit_dmg,
                    'gold': g.player.gold,
                    'xp': g.player.xp,
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
