// ── Mystic Dungeon — Browser Edition ────────────────────────────────────
const CELL = 20, UI_H = 60;
let canvas, ctx, MAP_W = 40, MAP_H = 24, canvasW, canvasH;

function resize() {
    const w = window.innerWidth - 10, h = window.innerHeight - 10;
    const cols = Math.floor(w / CELL), rows = Math.floor((h - UI_H) / CELL);
    canvasW = cols * CELL;
    canvasH = rows * CELL + UI_H;
    canvas.width = canvasW;
    canvas.height = canvasH;
    canvas.style.width = canvasW + 'px';
    canvas.style.height = canvasH + 'px';
}

// ── Helpers ──────────────────────────────────────────────────────────────
const rnd = (a, b) => Math.floor(Math.random() * (b - a + 1)) + a;
const choice = (arr) => arr[Math.floor(Math.random() * arr.length)];
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

// ── Colors ───────────────────────────────────────────────────────────────
const C = {
    bg: '#1a1a2e', panel: '#16213e', border: '#0f3460',
    text: '#e0e0e0', dim: '#888', hp: '#4ecca3', hpLow: '#e23e57',
    gold: '#ffd700', title: '#ffd700', prompt: '#a8d8ea',
    player: '#00d4ff', monster: '#ff6b6b', item: '#7bed9f',
    wall: '#57606f', floor: '#2f3542', stairs: '#ffd700',
    hpBar: '#2ed573', hpBg: '#444',
    rare: '#ffd700', uncommon: '#7bed9f',
    battleBg: '#0f0f23',
    rarity: ['#e0e0e0', '#7bed9f', '#4fc3f7', '#ffd700'],
};

const ATK_PHYS = 'physical', ATK_MAGIC = 'magic';

// ── Data ─────────────────────────────────────────────────────────────────
const MONSTER_EMOJI = {
    Ant:'🐜', Bat:'🦇', Centipede:'🦂', Dog:'🐕', Eye:'🟡', Frog:'🐸',
    Goblin:'👾', Harpy:'🦅', Imp:'🎃', Jackal:'🐺', Kobold:'🦎',
    Lich:'☠️', Mummy:'🧛', Ogre:'🗿', Troll:'🦖', Wyrm:'🐉',
};

const MONSTERS = [
    ['Ant',5,1,2,0,0,0,0.02,1.5,null],
    ['Bat',8,2,3,0,0,0,0.05,1.5,null],
    ['Centipede',10,3,4,0,1,0,0.02,1.5,'physical'],
    ['Dog',15,5,4,1,1,1,0.05,1.5,null],
    ['Eye',20,8,1,4,0,2,0.08,2.0,'magic'],
    ['Frog',25,10,2,5,1,2,0.05,1.5,'magic'],
    ['Goblin',30,12,5,2,2,1,0.05,1.5,'physical'],
    ['Harpy',35,15,3,6,2,3,0.08,1.5,'magic'],
    ['Imp',40,18,6,2,3,2,0.05,1.5,'physical'],
    ['Jackal',45,20,7,2,3,2,0.08,1.5,'physical'],
    ['Kobold',50,22,7,3,4,3,0.05,1.5,null],
    ['Lich',60,30,3,9,3,5,0.10,2.0,'magic'],
    ['Mummy',70,35,8,4,5,4,0.05,1.5,'physical'],
    ['Ogre',80,40,9,3,6,3,0.08,2.0,'physical'],
    ['Troll',90,45,8,5,6,5,0.05,1.5,null],
    ['Wyrm',120,60,10,10,8,8,0.10,2.0,null],
];

const WEAPON_DB = [
    ['Dagger','🗡️','physical',1,0,0.05,1.5,0],
    ['Short Sword','⚔️','physical',2,0,0.05,1.5,0],
    ['Club','🏏','physical',1,0,0.08,2.0,0],
    ['Wand','🪄','magic',0,2,0.05,1.5,0],
    ['Bone Rod','🦴','magic',0,1,0.05,1.5,0],
    ['Long Sword','⚔️','physical',3,0,0.05,1.5,1],
    ['War Hammer','🔨','physical',3,0,0.08,2.0,1],
    ['Spear','🔱','physical',2,1,0.08,1.5,1],
    ['Magic Staff','🪄','magic',0,4,0.08,2.0,1],
    ['Flail','⛓️','physical',4,0,0.05,1.5,1],
    ['Great Sword','⚔️','physical',5,0,0.10,2.5,2],
    ['Battle Axe','🪓','physical',5,0,0.12,2.0,2],
    ['Arcane Rod','✨','magic',0,6,0.10,2.5,2],
    ['Crystal Staff','💎','magic',1,5,0.08,2.0,2],
    ['Muramasa','🗡️','physical',7,0,0.15,3.0,3],
    ['Excalibur','⚔️','physical',8,2,0.10,2.5,3],
    ['Zantetsuken','⚔️','physical',6,0,0.20,3.5,3],
    ['Shuriken','⭐','physical',4,0,0.25,2.0,3],
    ['Gungnir','🔱','physical',9,0,0.08,2.5,3],
    ['Mjolnir','🔨','physical',7,3,0.12,3.0,3],
];

const ARMOR_DB = [
    ['Leather Armor','🛡️',2,0,0],
    ['Mage Robe','👘',0,3,0],
    ['Wooden Shield','🛡️',1,1,0],
    ['Chain Mail','🛡️',3,1,1],
    ['Arcane Cloak','🔮',1,4,1],
    ['Iron Shield','🛡️',3,0,1],
    ['Plate Armor','🛡️',5,2,2],
    ['Mithril Mail','✨',4,4,2],
    ['Dragon Mail','🐉',6,5,3],
    ['Aegis','🛡️',8,8,3],
];

const POTIONS = [
    ['Healing Potion','potion_heal',30],
    ['Strength Potion','potion_str',50],
    ['Mana Bread','food',20],
];

const RARITY_NAME = ['','+','★','✦'];
const RARITY_BONUS_MIN = [0,0,1,2];
const RARITY_BONUS_MAX = [0,1,3,5];
const RARITY_WEIGHT = [40,30,20,10];

// ── Classes ──────────────────────────────────────────────────────────────
class Rect {
    constructor(x,y,w,h) { this.x=x; this.y=y; this.w=w; this.h=h; }
    get cx() { return this.x + Math.floor(this.w/2); }
    get cy() { return this.y + Math.floor(this.h/2); }
    intersect(o) {
        return this.x <= o.x+o.w && this.x+this.w >= o.x &&
               this.y <= o.y+o.h && this.y+this.h >= o.y;
    }
    inside(x,y) { return x>=this.x && x<this.x+this.w && y>=this.y && y<this.y+this.h; }
}

class Entity {
    constructor(x,y,ch,color,blocks=false,name='',hp=0,max_hp=0,xp=0,
                patk=0,matk=0,pdef=0,mdef=0,crit_rate=0,crit_dmg=1,weakness=null) {
        this.x=x; this.y=y; this.ch=ch; this.color=color; this.blocks=blocks;
        this.name=name; this.hp=hp; this.max_hp=max_hp; this.xp=xp;
        this.gold=0; this.patk=patk; this.matk=matk; this.pdef=pdef; this.mdef=mdef;
        this.crit_rate=crit_rate; this.crit_dmg=crit_dmg; this.weakness=weakness;
        this.inventory=[]; this.weapon_item=null; this.armor_item=null;
        this.rare_bearer=false;
    }
}

class Item {
    constructor(x,y,emoji,name,type,value=0,patk=0,matk=0,pdef=0,mdef=0,
                crit_rate=0,crit_dmg=1,attack_type=null,rarity=0) {
        this.x=x; this.y=y; this.emoji=emoji; this.name=name; this.type=type;
        this.value=value; this.patk=patk; this.matk=matk; this.pdef=pdef; this.mdef=mdef;
        this.crit_rate=crit_rate; this.crit_dmg=crit_dmg; this.attack_type=attack_type;
        this.rarity=rarity;
    }
}

class Game {
    constructor(diff=2) {
        const d = DIFF[diff];
        this.diff=diff; this.MAP_W=d.mw; this.MAP_H=d.mh;
        this.dmg_scale=d.dmg; this.spawn_scale=d.spawn; this.item_scale=d.item;
        this.FOV_RADIUS=d.fov; this.min_room=d.minR; this.max_room=d.maxR;
        this.max_rooms=d.maxRooms;
        this.goldMul=d.goldMul; this.shopPriceMul=d.shopPriceMul;
        this.maxFloor=d.maxFloor;
        this.map=null; this.explored=null; this.visible=null;
        this.rooms=[]; this.entities=[]; this.items=[]; this.messages=[];
        this.player=null; this.game_over=false; this.dlvl=1;
        this.current_slot=0; this.rare_dropped_this_floor=false;
        this.victory=false;
    }
    add_msg(m) {
        this.messages.push(m);
        if (this.messages.length>100) this.messages=this.messages.slice(-50);
    }
}

const DIFF = {
    1: {mw:30,mh:18,dmg:0.5,spawn:0.6,item:1.5,fov:8,minR:3,maxR:7,maxRooms:7,goldMul:3,shopPriceMul:0.5,maxFloor:10},
    2: {mw:40,mh:24,dmg:1,spawn:1,item:1,fov:6,minR:4,maxR:8,maxRooms:9,goldMul:1,shopPriceMul:1,maxFloor:100},
    3: {mw:40,mh:24,dmg:1.5,spawn:1.4,item:0.6,fov:5,minR:4,maxR:8,maxRooms:12,goldMul:0.6,shopPriceMul:1.5,maxFloor:Infinity},
};

// ── Map Gen ──────────────────────────────────────────────────────────────
function genLevel(g) {
    const W=g.MAP_W, H=g.MAP_H;
    g.map=Array.from({length:H},()=>Array(W).fill(35));
    g.explored=Array.from({length:H},()=>Array(W).fill(false));
    g.visible=Array.from({length:H},()=>Array(W).fill(false));
    g.rooms=[];
    g.entities=g.entities.filter(e=>e===g.player);
    g.items=[];
    g.player.x=g.player.y=1;
    g.rare_dropped_this_floor=false;

    const rcount=rnd(g.max_rooms-2,g.max_rooms);
    for (let t=0;t<rcount*3;t++) {
        if (g.rooms.length>=rcount) break;
        const w=rnd(g.min_room,g.max_room), h=rnd(g.min_room,g.max_room);
        const x=rnd(1,W-w-2), y=rnd(1,H-h-2);
        const r=new Rect(x,y,w,h);
        if (!g.rooms.some(o=>r.intersect(o))) {
            g.rooms.push(r);
            carveRoom(g,r);
        }
    }
    if (!g.rooms.length) {
        const r=new Rect(1,1,6,5);
        g.rooms.push(r);
        carveRoom(g,r);
    }
    for (let i=1;i<g.rooms.length;i++) {
        const a=g.rooms[i-1], b=g.rooms[i];
        if (Math.random()<0.5) {
            carveHTunnel(g,a.cx,b.cx,a.cy);
            carveVTunnel(g,a.cy,b.cy,b.cx);
        } else {
            carveVTunnel(g,a.cy,b.cy,a.cx);
            carveHTunnel(g,a.cx,b.cx,b.cy);
        }
    }
    const r0=g.rooms[0];
    g.player.x=r0.cx; g.player.y=r0.cy;

    const rl=g.rooms[g.rooms.length-1];
    const bossFloor = g.maxFloor!==Infinity && g.dlvl >= g.maxFloor;
    if (g.rooms.length>1 && !bossFloor)
        g.items.push(new Item(rl.cx,rl.cy,'🔽','Stairs Down','stairs'));
    if (bossFloor) {
        const sc=1+(g.dlvl-1)*0.3;
        const hp=Math.max(1,Math.floor(300*sc*g.dmg_scale));
        const xp=Math.max(1,Math.floor(200*sc));
        const atk=Math.max(0,Math.floor(12*sc*g.dmg_scale));
        const pdf=Math.max(0,Math.floor(10*sc*g.dmg_scale));
        const boss=new Entity(rl.cx,rl.cy,'🐉','Boss Wyrm','monster',true,'Boss Wyrm',
            hp,hp,xp,atk,atk,pdf,pdf,0.1,2.0,null);
        boss.rare_bearer=true;
        g.entities.push(boss);
        g.add_msg('A mighty dragon blocks your path!');
    }

    const spawnCount=Math.max(1,Math.floor(3*g.spawn_scale));
    for (let ri=1;ri<g.rooms.length;ri++) {
        const r=g.rooms[ri];
        const n=rnd(0,spawnCount);
        for (let i=0;i<n;i++) {
            const x=rnd(r.x+1,r.x+r.w-2), y=rnd(r.y+1,r.y+r.h-2);
            if (g.entities.some(e=>e.x===x&&e.y===y)) continue;
            const mt=choice(MONSTERS);
            let [name,hp,xp,patk,matk,pdef,mdef,cr,cd,weak]=mt;
            const sc=1+(g.dlvl-1)*0.3;
            hp=Math.max(1,Math.floor(hp*sc*g.dmg_scale));
            xp=Math.max(1,Math.floor(xp*sc));
            patk=Math.max(0,Math.floor(patk*sc*g.dmg_scale));
            matk=Math.max(0,Math.floor(matk*sc*g.dmg_scale));
            pdef=Math.max(0,Math.floor(pdef*sc*g.dmg_scale));
            mdef=Math.max(0,Math.floor(mdef*sc*g.dmg_scale));
            const e=new Entity(x,y,MONSTER_EMOJI[name]||'👾','monster',true,name,
                hp,hp,xp,patk,matk,pdef,mdef,cr,cd,weak);
            g.entities.push(e);
        }
    }

    for (let ri=1;ri<g.rooms.length;ri++) {
        const r=g.rooms[ri];
        const n=rnd(0,Math.max(1,Math.floor(2*g.item_scale)));
        for (let i=0;i<n;i++) {
            const x=rnd(r.x+1,r.x+r.w-2), y=rnd(r.y+1,r.y+r.h-2);
            if (g.entities.some(e=>e.x===x&&e.y===y)) continue;
            if (g.items.some(it=>it.x===x&&it.y===y)) continue;
            const v=Math.max(1,Math.floor(rnd(1,10*g.dlvl)*g.goldMul));
            g.items.push(new Item(x,y,'🪙',v+' gold','gold',v));
        }
    }

    const shopRooms=g.rooms.slice(1,-1);
    if (shopRooms.length&&Math.random()<0.35) {
        const r=choice(shopRooms);
        const sx=rnd(r.x+1,r.x+r.w-2), sy=rnd(r.y+1,r.y+r.h-2);
        if (!g.entities.some(e=>e.x===sx&&e.y===sy)&&
            !g.items.some(it=>it.x===sx&&it.y===sy))
            g.items.push(new Item(sx,sy,'🏪','Item Shop','shop'));
    }

    const bearers=g.entities.filter(e=>e!==g.player);
    if (bearers.length) choice(bearers).rare_bearer=true;
}

function carveRoom(g,r) {
    for (let y=r.y;y<r.y+r.h;y++)
        for (let x=r.x;x<r.x+r.w;x++)
            if (y>=0&&y<g.MAP_H&&x>=0&&x<g.MAP_W) g.map[y][x]=46;
}
function carveHTunnel(g,x1,x2,y) {
    for (let x=Math.min(x1,x2);x<=Math.max(x1,x2);x++)
        if (y>0&&y<g.MAP_H-1&&x>0&&x<g.MAP_W-1) g.map[y][x]=46;
}
function carveVTunnel(g,y1,y2,x) {
    for (let y=Math.min(y1,y2);y<=Math.max(y1,y2);y++)
        if (y>0&&y<g.MAP_H-1&&x>0&&x<g.MAP_W-1) g.map[y][x]=46;
}

// ── FOV ──────────────────────────────────────────────────────────────────
function hasLos(g,x0,y0,x1,y1) {
    let dx=Math.abs(x1-x0),dy=Math.abs(y1-y0);
    const sx=x0<x1?1:-1, sy=y0<y1?1:-1;
    let err=dx-dy, x=x0, y=y0;
    while (true) {
        if (x===x1&&y===y1) return true;
        if ((x!==x0||y!==y0)&&g.map[y][x]===35) return false;
        const e2=2*err;
        if (e2>-dy) { err-=dy; x+=sx; }
        if (e2<dx) { err+=dx; y+=sy; }
    }
}
function computeFov(g) {
    const W=g.MAP_W, H=g.MAP_H;
    for (let y=0;y<H;y++) for (let x=0;x<W;x++) g.visible[y][x]=false;
    const px=g.player.x, py=g.player.y, r=g.FOV_RADIUS;
    g.visible[py][px]=true;
    g.explored[py][px]=true;
    for (let y=Math.max(0,py-r);y<Math.min(H,py+r+1);y++)
        for (let x=Math.max(0,px-r);x<Math.min(W,px+r+1);x++)
            if ((x-px)*(x-px)+(y-py)*(y-py)<=r*r)
                if (hasLos(g,px,py,x,y)) { g.visible[y][x]=true; g.explored[y][x]=true; }
}

// ── Combat ───────────────────────────────────────────────────────────────
function calcAttack(entity,weapon) {
    if (weapon&&weapon.attack_type===ATK_MAGIC)
        return [entity.matk+weapon.matk, ATK_MAGIC];
    else if (weapon)
        return [entity.patk+weapon.patk, ATK_PHYS];
    return [entity.patk, ATK_PHYS];
}
function calcDefense(entity,type) {
    return type===ATK_MAGIC?entity.mdef:entity.pdef;
}
function calcDamage(attacker,weapon,defender) {
    let [atk,type]=calcAttack(attacker,weapon);
    let cr=attacker.crit_rate, cd=attacker.crit_dmg;
    if (weapon) { cr+=weapon.crit_rate; cd+=weapon.crit_dmg-1; }
    const isCrit=Math.random()<cr;
    if (defender.weakness===type) atk=Math.floor(atk*1.5);
    let dmg;
    if (isCrit) dmg=Math.floor(atk*cd);
    else {
        const def=calcDefense(defender,type);
        dmg=Math.max(3,atk-def);
    }
    return [Math.max(1,dmg),isCrit,type];
}
function levelUp(g) {
    if (g.player.xp>=g.player.max_hp*2) {
        g.player.max_hp+=5;
        g.player.hp=Math.min(g.player.hp+5,g.player.max_hp);
        g.player.patk++; g.player.pdef++; g.player.mdef++;
        g.add_msg('Level up! HP+5 ATK+1 DEF+1');
    }
}
function pickRarity(g,isBearer) {
    if (isBearer&&!g.rare_dropped_this_floor) {
        g.rare_dropped_this_floor=true;
        return Math.random()<0.6?2:3;
    }
    const w=[...RARITY_WEIGHT];
    if (!g.rare_dropped_this_floor) { w[2]*=3; w[3]*=3; }
    const total=w.reduce((a,b)=>a+b,0);
    let r=Math.random()*total;
    for (let i=0;i<w.length;i++) { r-=w[i]; if (r<=0) { if (i>=2) g.rare_dropped_this_floor=true; return i; } }
    return 0;
}
function makeWeapon(g,rarity) {
    const cand=WEAPON_DB.filter(w=>w[7]===rarity);
    const wt=cand.length?choice(cand):choice(WEAPON_DB);
    const [name,emoji,at,bp,bm,bcr,bcd]=wt;
    const bonus=Math.max(0,rnd(RARITY_BONUS_MIN[rarity],RARITY_BONUS_MAX[rarity]+Math.floor(g.dlvl/2)));
    const patk=Math.max(0,bp+bonus);
    const matk=Math.max(0,bm+bonus);
    const cr=Math.min(0.5,bcr+bonus*0.01);
    const wname=bonus>0?name+'+'+bonus:name;
    return new Item(0,0,emoji,wname,'weapon',50+bonus*30,patk,matk,0,0,cr,bcd,at,rarity);
}
function makeArmor(g,rarity) {
    const cand=ARMOR_DB.filter(a=>a[4]===rarity);
    const at=cand.length?choice(cand):choice(ARMOR_DB);
    const [name,emoji,bp,bm]=at;
    const bonus=Math.max(0,rnd(RARITY_BONUS_MIN[rarity],RARITY_BONUS_MAX[rarity]+Math.floor(g.dlvl/2)));
    const pdef=Math.max(0,bp+bonus*2);
    const mdef=Math.max(0,bm+bonus*2);
    const aname=bonus>0?name+'+'+bonus:name;
    return new Item(0,0,emoji,aname,'armor',40+bonus*40,0,0,pdef,mdef,0,1,null,rarity);
}
function makeConsumable() {
    const pt=choice(POTIONS);
    return new Item(0,0,pt[1]==='food'?'🍗':'🧪',pt[0],pt[1],pt[2]);
}
function enemyDrop(g,enemy) {
    g.player.xp+=enemy.xp;
    const gold=Math.max(1,Math.floor(rnd(1,5)*(1+g.dlvl)*g.goldMul));
    g.player.gold+=gold;
    g.add_msg('Dropped '+gold+' gold');
    if (enemy.rare_bearer) g.add_msg('A rare aura emanates from the corpse!');
    const dropRoll=0.4+(enemy.rare_bearer?0.2:0);
    if (Math.random()>=dropRoll||g.player.inventory.length>=10) return;
    const rarity=pickRarity(g,enemy.rare_bearer);
    let item;
    const roll=Math.random();
    if (roll<0.35) item=makeWeapon(g,rarity);
    else if (roll<0.65) item=makeArmor(g,rarity);
    else item=makeConsumable();
    g.player.inventory.push(item);
    g.add_msg('Found: '+item.name+RARITY_NAME[rarity]);
}

function monsterTick(g) {
    for (const e of [...g.entities]) {
        if (e===g.player||e.hp<=0) continue;
        const dx=g.player.x-e.x, dy=g.player.y-e.y;
        const dist=Math.abs(dx)+Math.abs(dy);
        if (dist===0||dist>15||!g.visible[e.y][e.x]) continue;
        let nx=e.x, ny=e.y;
        if (Math.abs(dx)>Math.abs(dy)) nx+=dx>0?1:-1;
        else ny+=dy>0?1:-1;
        if (canMove(g,nx,ny)) { e.x=nx; e.y=ny; }
        else if (nx!==e.x&&canMove(g,nx,e.y)) e.x=nx;
        else if (ny!==e.y&&canMove(g,e.x,ny)) e.y=ny;
        if (Math.abs(g.player.x-e.x)+Math.abs(g.player.y-e.y)===1)
            return e; // return monster that triggered combat
    }
    return null;
}
function canMove(g,x,y) {
    return x>0&&x<g.MAP_W-1&&y>0&&y<g.MAP_H-1&&
           g.map[y][x]!==35&&!g.entities.some(e=>e.blocks&&e.x===x&&e.y===y);
}

// ── Save / Load ──────────────────────────────────────────────────────────
function toDict(it) {
    if (!it) return null;
    return {x:it.x,y:it.y,emoji:it.emoji,name:it.name,type:it.type,value:it.value,
        patk:it.patk,matk:it.matk,pdef:it.pdef,mdef:it.mdef,
        crit_rate:it.crit_rate,crit_dmg:it.crit_dmg,attack_type:it.attack_type,rarity:it.rarity};
}
function fromDict(d) {
    if (!d) return null;
    return new Item(d.x,d.y,d.emoji,d.name,d.type,d.value||0,
        d.patk||0,d.matk||0,d.pdef||0,d.mdef||0,
        d.crit_rate||0,d.crit_dmg||1,d.attack_type||null,d.rarity||0);
}
function saveGame(g,slot) {
    try {
        const data={
            version:4,diff:g.diff,dlvl:g.dlvl,MAP_W:g.MAP_W,MAP_H:g.MAP_H,
            rare_dropped_this_floor:g.rare_dropped_this_floor,
            player:{
                x:g.player.x,y:g.player.y,hp:g.player.hp,max_hp:g.player.max_hp,
                xp:g.player.xp,gold:g.player.gold,
                patk:g.player.patk,matk:g.player.matk,
                pdef:g.player.pdef,mdef:g.player.mdef,
                crit_rate:g.player.crit_rate,crit_dmg:g.player.crit_dmg,
                inventory:g.player.inventory.map(toDict),
                weapon_item:toDict(g.player.weapon_item),
                armor_item:toDict(g.player.armor_item),
            },
            map:g.map.map(r=>[...r]),
            explored:g.explored.map(r=>[...r]),
            visible:g.visible.map(r=>[...r]),
            entities:g.entities.filter(e=>e!==g.player).map(e=>({
                name:e.name,x:e.x,y:e.y,hp:e.hp,max_hp:e.max_hp,
                patk:e.patk,matk:e.matk,pdef:e.pdef,mdef:e.mdef,
                crit_rate:e.crit_rate,crit_dmg:e.crit_dmg,
                weakness:e.weakness,xp:e.xp,rare_bearer:e.rare_bearer,
            })),
            items:g.items.map(toDict),
            messages:g.messages,
        };
        localStorage.setItem('md_save_'+slot,JSON.stringify(data));
        return true;
    } catch(e) { return false; }
}
function loadGame(g,slot) {
    try {
        const data=JSON.parse(localStorage.getItem('md_save_'+slot));
        if (!data||(data.version||1)<2) return false;
        g.diff=data.diff; g.dlvl=data.dlvl; g.MAP_W=data.MAP_W; g.MAP_H=data.MAP_H;
        g.current_slot=slot;
        const d=DIFF[g.diff]||DIFF[2];
        g.dmg_scale=d.dmg; g.spawn_scale=d.spawn; g.item_scale=d.item;
        g.FOV_RADIUS=d.fov; g.min_room=d.minR; g.max_room=d.maxR; g.max_rooms=d.maxRooms;
        g.map=data.map; g.explored=data.explored; g.visible=data.visible;
        g.messages=data.messages||[]; g.game_over=false; g.rooms=[];
        g.rare_dropped_this_floor=data.rare_dropped_this_floor||false;
        const pd=data.player;
        g.player=new Entity(pd.x,pd.y,'🧙','player',true,'Player',
            pd.hp||20,pd.max_hp||20,pd.xp||0,
            pd.patk||3,pd.matk||2,pd.pdef||1,pd.mdef||1,
            pd.crit_rate||0.05,pd.crit_dmg||1.5);
        g.player.gold=pd.gold||0;
        g.player.inventory=(pd.inventory||[]).map(fromDict);
        g.player.weapon_item=fromDict(pd.weapon_item);
        g.player.armor_item=fromDict(pd.armor_item);
        g.entities=[g.player];
        for (const ed of data.entities||[]) {
            const e=new Entity(ed.x,ed.y,MONSTER_EMOJI[ed.name]||'👾','monster',true,
                ed.name,ed.hp||5,ed.max_hp||5,ed.xp||0,
                ed.patk||2,ed.matk||0,ed.pdef||0,ed.mdef||0,
                ed.crit_rate||0.05,ed.crit_dmg||1.5,ed.weakness||null);
            e.rare_bearer=ed.rare_bearer||false;
            g.entities.push(e);
        }
        g.items=(data.items||[]).map(fromDict);
        computeFov(g);
        return true;
    } catch(e) { return false; }
}
function getSaveInfo(slot) {
    try {
        const data=JSON.parse(localStorage.getItem('md_save_'+slot));
        if (!data) return null;
        return {dlvl:data.dlvl,hp:data.player.hp,max_hp:data.player.max_hp,diff:data.diff};
    } catch(e) { return {corrupted:true}; }
}
function anySaveExists() {
    for (let s=1;s<=3;s++)
        if (localStorage.getItem('md_save_'+s)) return true;
    return false;
}
const AS_KEY = 'md_autosave';
function saveAutosave(g) {
    try {
        const data={
            version:4,diff:g.diff,dlvl:g.dlvl,MAP_W:g.MAP_W,MAP_H:g.MAP_H,
            rare_dropped_this_floor:g.rare_dropped_this_floor,
            player:{
                x:g.player.x,y:g.player.y,hp:g.player.hp,max_hp:g.player.max_hp,
                xp:g.player.xp,gold:g.player.gold,
                patk:g.player.patk,matk:g.player.matk,
                pdef:g.player.pdef,mdef:g.player.mdef,
                crit_rate:g.player.crit_rate,crit_dmg:g.player.crit_dmg,
                inventory:g.player.inventory.map(toDict),
                weapon_item:toDict(g.player.weapon_item),
                armor_item:toDict(g.player.armor_item),
            },
            map:g.map.map(r=>[...r]),
            explored:g.explored.map(r=>[...r]),
            visible:g.visible.map(r=>[...r]),
            entities:g.entities.filter(e=>e!==g.player).map(e=>({
                name:e.name,x:e.x,y:e.y,hp:e.hp,max_hp:e.max_hp,
                patk:e.patk,matk:e.matk,pdef:e.pdef,mdef:e.mdef,
                crit_rate:e.crit_rate,crit_dmg:e.crit_dmg,
                weakness:e.weakness,xp:e.xp,rare_bearer:e.rare_bearer,
            })),
            items:g.items.map(toDict),
            messages:g.messages,
        };
        localStorage.setItem(AS_KEY,JSON.stringify(data));
        return true;
    } catch(e) { return false; }
}
function autosaveExists() {
    return !!localStorage.getItem(AS_KEY);
}
function clearAutosave() {
    localStorage.removeItem(AS_KEY);
}
const SCORE_KEY = 'md_score';
function getScore() {
    try { return JSON.parse(localStorage.getItem(SCORE_KEY))||{best:0,attempts:0}; }
    catch(e) { return {best:0,attempts:0}; }
}
function saveScore(s) {
    localStorage.setItem(SCORE_KEY,JSON.stringify(s));
}
function loadAutosave(g) {
    try {
        const data=JSON.parse(localStorage.getItem(AS_KEY));
        if (!data||(data.version||1)<2) return false;
        g.diff=data.diff; g.dlvl=data.dlvl; g.MAP_W=data.MAP_W; g.MAP_H=data.MAP_H;
        const d=DIFF[g.diff]||DIFF[2];
        g.dmg_scale=d.dmg; g.spawn_scale=d.spawn; g.item_scale=d.item;
        g.FOV_RADIUS=d.fov; g.min_room=d.minR; g.max_room=d.maxR; g.max_rooms=d.maxRooms;
        g.goldMul=d.goldMul; g.shopPriceMul=d.shopPriceMul;
        g.map=data.map; g.explored=data.explored; g.visible=data.visible;
        g.messages=data.messages||[]; g.game_over=false; g.rooms=[];
        g.rare_dropped_this_floor=data.rare_dropped_this_floor||false;
        const pd=data.player;
        g.player=new Entity(pd.x,pd.y,'🧙','player',true,'Player',
            pd.hp||20,pd.max_hp||20,pd.xp||0,
            pd.patk||3,pd.matk||2,pd.pdef||1,pd.mdef||1,
            pd.crit_rate||0.05,pd.crit_dmg||1.5);
        g.player.gold=pd.gold||0;
        g.player.inventory=(pd.inventory||[]).map(fromDict).filter(Boolean);
        g.player.weapon_item=fromDict(pd.weapon_item);
        g.player.armor_item=fromDict(pd.armor_item);
        if (g.player.hp<=0) g.player.hp=1;
        g.entities=[g.player];
        for (const ed of data.entities||[]) {
            const e=new Entity(ed.x,ed.y,'?','monster',true,ed.name,
                ed.hp||1,ed.max_hp||1,ed.xp||0,
                ed.patk||1,ed.matk||1,ed.pdef||0,ed.mdef||0,
                ed.crit_rate||0,ed.crit_dmg||1,
                ed.weakness||null,1,false);
            e.rare_bearer=!!ed.rare_bearer;
            g.entities.push(e);
        }
        g.items=(data.items||[]).map(fromDict).filter(Boolean);
        return true;
    } catch(e) { return false; }
}

// ── Canvas Renderer ──────────────────────────────────────────────────────
function draw(ctx, g, state, extra) {
    ctx.fillStyle=C.bg; ctx.fillRect(0,0,canvasW,canvasH);
    if (state==='playing') drawMap(ctx,g);
    else if (state==='title') drawTitle(ctx,g,extra);
    else if (state==='gameover') drawGameOver(ctx,g);
    else if (state==='victory') drawVictory(ctx,g);
    else if (state==='battle') drawBattle(ctx,g,extra);
    else if (state==='inventory') drawInventory(ctx,g,extra);
    else if (state==='shop') drawShop(ctx,g,extra);
    else if (state==='mapview') drawMapView(ctx,g);
    else if (state==='saveslot') drawSaveSlot(ctx,g,extra);
}
function drawMap(ctx,g) {
    const W=g.MAP_W, H=g.MAP_H;
    for (let y=0;y<H;y++) for (let x=0;x<W;x++) {
        const px=x*CELL, py=y*CELL;
        if (y===g.player.y&&x===g.player.x) {
            ctx.fillStyle=C.player; ctx.font='bold '+CELL+'px monospace';
            ctx.fillText('🧙',px+2,py+CELL-2);
        } else if (g.visible[y][x]) {
            ctx.fillStyle=g.map[y][x]===35?C.wall:C.floor;
            ctx.fillRect(px+1,py+1,CELL-2,CELL-2);
            let ch=null;
            for (const it of g.items)
                if (it.x===x&&it.y===y) { ch=it.emoji; break; }
            if (!ch) for (const e of g.entities)
                if (e!==g.player&&e.x===x&&e.y===y) { ch=e.ch; break; }
            if (ch) { ctx.font=CELL+'px monospace'; ctx.fillText(ch,px+2,py+CELL-2); }
        } else if (g.explored[y][x]) {
            ctx.fillStyle=g.map[y][x]===35?C.wall:C.floor;
            ctx.fillRect(px+1,py+1,CELL-2,CELL-2);
            ctx.fillStyle=C.dim; ctx.font=CELL+'px serif';
            ctx.fillText('·',px+4,py+CELL-4);
        }
    }
    // Status bar
    const sy=H*CELL;
    ctx.fillStyle=C.panel; ctx.fillRect(0,sy,canvasW,UI_H);
    const p=g.player;
    const wpn=p.weapon_item?p.weapon_item.name:'Fist';
    const arm=p.armor_item?p.armor_item.name:'None';
    const hpPct=p.hp/p.max_hp;
    const hpC=hpPct<0.3?C.hpLow:C.hp;
    ctx.fillStyle=C.text; ctx.font='14px monospace';
    let s='HP:'; drawText(ctx,s,0,sy+18,hpC,true);
    const hpW=120;
    ctx.fillStyle=C.hpBg; ctx.fillRect(30,sy+4,hpW,14);
    ctx.fillStyle=C.hpBar; ctx.fillRect(30,sy+4,Math.max(0,hpPct*hpW),14);
    ctx.fillStyle=C.text; ctx.font='bold 11px monospace';
    ctx.fillText(p.hp+'/'+p.max_hp,36,sy+15);
    ctx.font='13px monospace';
    const wpnExtra=p.weapon_item?'+'+p.weapon_item.patk:'';
    ctx.fillStyle=C.text;
    ctx.fillText('P:'+p.patk+wpnExtra+' ',170,sy+18);
    ctx.fillText('G:'+p.gold+' Lv:'+g.dlvl+' ['+wpn+'] ['+arm+']',280,sy+18);
    const msgs=g.messages.slice(-2);
    for (let i=0;i<msgs.length;i++) {
        ctx.fillStyle=C.dim; ctx.font='12px monospace';
        ctx.fillText(msgs[i],10,sy+40+i*16);
    }
}
function drawText(ctx,t,x,y,color,bold) {
    ctx.fillStyle=color||C.text;
    ctx.font=(bold?'bold ':'')+'14px monospace';
    ctx.fillText(t,x,y);
}
function drawTitle(ctx,g,extra) {
    const cx=canvasW/2, cy=canvasH/2-60;
    ctx.fillStyle=C.title; ctx.font='bold 36px monospace';
    ctx.textAlign='center';
    ctx.fillText('Mystic Dungeon',cx,cy);
    ctx.font='20px monospace'; ctx.fillStyle=C.text;
    ctx.fillText('⚔️ A turn-based dungeon crawler 🛡️',cx,cy+40);
    let y=cy+90;
    if (extra&&extra.hasAutosave) {
        ctx.fillStyle=C.hp; ctx.font='bold 16px monospace';
        ctx.fillText('▶ Continue [c]',cx,y);
        y+=30;
    }
    if (extra&&extra.hasSaves) {
        ctx.fillStyle=C.prompt; ctx.font='16px monospace';
        ctx.fillText('Load Game:',cx,y);
        y+=24;
        for (let s=1;s<=3;s++) {
            const info=getSaveInfo(s);
            let line='';
            if (!info) line='  ['+s+'] Slot '+s+' — (empty)';
            else if (info.corrupted) line='  ['+s+'] Slot '+s+' — (corrupted)';
            else line='  ['+s+'] Lv.'+info.dlvl+' HP:'+info.hp+'/'+info.max_hp;
            ctx.fillStyle=C.text; ctx.fillText(line,cx,y);
            y+=24;
        }
        ctx.fillStyle=C.prompt; ctx.font='14px monospace';
        ctx.fillText('[n] New Game    [q] Quit',cx,y+10);
    } else if (!extra||!extra.hasAutosave) {
        ctx.font='16px monospace'; ctx.fillStyle=C.prompt;
        ctx.fillText('Select Difficulty:',cx,y);
        ctx.fillStyle=C.text; ctx.font='14px monospace';
        ctx.fillText('[1] Easy — 10F boss, gold 3x, shop half price',cx,y+30);
        ctx.fillText('[2] Middle — 100F boss (Recommended)',cx,y+55);
        ctx.fillText('[3] Hard — Endless, record best floor',cx,y+80);
        const sc=getScore();
        if (sc.best>0||sc.attempts>0) {
            ctx.fillStyle=C.dim; ctx.font='12px monospace';
            ctx.fillText('Hard record: Floor '+sc.best+' / Attempts: '+sc.attempts,cx,y+110);
        }
        ctx.fillStyle=C.dim; ctx.fillText('Press 1/2/3',cx,y+120);
    }
    ctx.fillStyle=C.dim; ctx.font='12px monospace';
    ctx.fillText('[x] Clear All Save Data',cx,canvasH-20);
    ctx.textAlign='left';
}
function drawGameOver(ctx,g) {
    const cx=canvasW/2, cy=canvasH/2-50;
    ctx.textAlign='center';
    ctx.fillStyle=C.hpLow; ctx.font='bold 28px monospace';
    ctx.fillText('GAME OVER',cx,cy);
    ctx.fillStyle=C.text; ctx.font='16px monospace';
    ctx.fillText('Level: '+g.dlvl+'  Gold: '+g.player.gold, cx, cy+40);
    ctx.fillText('XP: '+g.player.xp+'  HP: '+g.player.max_hp, cx, cy+65);
    const sc=getScore();
    if (g.diff===3) {
        ctx.fillStyle=C.dim; ctx.font='13px monospace';
        ctx.fillText('Best: Floor '+sc.best+' / Attempts: '+sc.attempts, cx, cy+90);
    }
    ctx.font='14px monospace';
    ctx.fillStyle=C.prompt;
    ctx.fillText('[r] Restart    [s] Strong New Game    [q] Quit', cx, cy+115);
    ctx.textAlign='left';
}
function drawVictory(ctx,g) {
    const cx=canvasW/2, cy=canvasH/2-60;
    ctx.textAlign='center';
    ctx.fillStyle=C.gold; ctx.font='bold 28px monospace';
    ctx.fillText('🎉 VICTORY! 🎉',cx,cy);
    ctx.fillStyle=C.title; ctx.font='bold 20px monospace';
    ctx.fillText('The dragon has been defeated!',cx,cy+40);
    ctx.fillStyle=C.text; ctx.font='16px monospace';
    ctx.fillText('Floor: '+g.dlvl+'  Gold: '+g.player.gold, cx, cy+80);
    ctx.fillText('XP: '+g.player.xp+'  HP: '+g.player.max_hp, cx, cy+105);
    ctx.font='14px monospace';
    ctx.fillStyle=C.prompt;
    ctx.fillText('[s] Strong New Game    [n] New Game    [q] Quit', cx, cy+145);
    ctx.textAlign='left';
}
function drawBattle(ctx,g,extra) {
    const ox=60, oy=30, bw=canvasW-120, bh=canvasH-60;
    ctx.fillStyle=C.battleBg;
    ctx.strokeStyle=C.border; ctx.lineWidth=2;
    ctx.fillRect(ox,oy,bw,bh); ctx.strokeRect(ox,oy,bw,bh);
    ctx.textAlign='left';
    ctx.font='bold 14px monospace';
    ctx.fillStyle=C.title; ctx.fillText('⚔ BATTLE ⚔',ox+20,oy+25);
    const enemy=extra.enemy;
    ctx.fillStyle=C.monster; ctx.font='16px monospace';
    ctx.fillText(enemy.ch+' '+enemy.name, ox+20, oy+55);
    ctx.fillStyle=C.text; ctx.font='13px monospace';
    ctx.fillText('HP: '+Math.max(0,enemy.hp)+'/'+enemy.max_hp, ox+20, oy+78);
    // Player info
    const p=g.player;
    ctx.fillStyle=C.player; ctx.font='16px monospace';
    ctx.fillText('🧙 '+p.name, ox+20, oy+110);
    ctx.fillStyle=C.text; ctx.font='13px monospace';
    ctx.fillText('HP: '+Math.max(0,p.hp)+'/'+p.max_hp, ox+20, oy+133);

    if (extra.playerTurn) {
        ctx.fillStyle=C.prompt; ctx.font='bold 13px monospace';
        ctx.fillText('Your turn — choose weapon:', ox+20, oy+165);
        let ly=oy+190;
        if (p.weapon_item) {
            const rtag=RARITY_NAME[p.weapon_item.rarity];
            ctx.fillStyle=C.rarity[p.weapon_item.rarity]||C.text; ctx.font='13px monospace';
            ctx.fillText('[e] '+p.weapon_item.name+rtag+' P+'+p.weapon_item.patk, ox+25, ly);
            ly+=20;
        }
        for (let i=0;i<p.inventory.length;i++) {
            const it=p.inventory[i];
            if (it.type!=='weapon'||it===p.weapon_item) continue;
            const rtag=RARITY_NAME[it.rarity];
            ctx.fillStyle=C.rarity[it.rarity]||C.text; ctx.font='13px monospace';
            const tag=(i+1)%10;
            const at=it.attack_type;
            const info=at===ATK_MAGIC?'M+'+it.matk+' CRIT'+Math.floor(it.crit_rate*100)+'%':
                       'P+'+it.patk+' CRIT'+Math.floor(it.crit_rate*100)+'%';
            ctx.fillText('['+tag+'] '+it.name+rtag+' '+info, ox+25, ly);
            ly+=20;
        }
        ctx.fillStyle=C.dim; ctx.font='12px monospace';
        ctx.fillText('[f] Fist', ox+25, ly);
    } else {
        ctx.fillStyle=C.dim; ctx.font='bold 14px monospace';
        ctx.fillText('Enemy turn...', ox+20, oy+165);
    }
}
function drawInventory(ctx,g,extra) {
    const ox=Math.max(0,(canvasW-420)/2), oy=Math.max(0,(canvasH-320)/2), bw=420, bh=320;
    ctx.fillStyle=C.panel; ctx.strokeStyle=C.border; ctx.lineWidth=2;
    ctx.fillRect(ox,oy,bw,bh); ctx.strokeRect(ox,oy,bw,bh);
    ctx.textAlign='left';
    const dropMode=extra&&extra.dropMode;
    ctx.fillStyle=C.title; ctx.font='bold 16px monospace';
    ctx.fillText(dropMode?'DROP ITEM':'Inventory',ox+15,oy+25);
    const p=g.player;
    ctx.fillStyle=C.text; ctx.font='13px monospace';
    ctx.fillText('Weapon: '+(p.weapon_item?p.weapon_item.name:'Fist'), ox+15, oy+50);
    ctx.fillText('Armor: '+(p.armor_item?p.armor_item.name:'None'), ox+250, oy+50);
    let ly=oy+75;
    if (!p.inventory.length) {
        ctx.fillStyle=C.dim; ctx.fillText('(empty)', ox+20, ly);
    } else {
        for (let i=0;i<p.inventory.length;i++) {
            const it=p.inventory[i];
            let itemInfo='';
            if (it.type==='weapon') {
                itemInfo=it.attack_type===ATK_MAGIC?' M+'+it.matk:' P+'+it.patk;
                itemInfo+=' C'+Math.floor(it.crit_rate*100)+'%';
            } else if (it.type==='armor') {
                itemInfo=' PD+'+it.pdef+' MD+'+it.mdef;
            }
            const rtag=RARITY_NAME[it.rarity];
            ctx.fillStyle=C.rarity[it.rarity]||C.text;
            ctx.font='12px monospace';
            ctx.fillText('['+(i+1)+'] '+it.emoji+' '+it.name+rtag+itemInfo, ox+20, ly);
            ly+=18;
        }
    }
    ctx.fillStyle=C.dim; ctx.font='12px monospace';
    ctx.fillText(dropMode?'Select number to drop, [q] cancel':'1-9: use/equip  d: drop  q: exit', ox+15, oy+bh-15);
}
function drawShop(ctx,g,extra) {
    const ox=Math.max(0,(canvasW-460)/2), oy=Math.max(0,(canvasH-380)/2), bw=460, bh=380;
    ctx.fillStyle=C.panel; ctx.strokeStyle=C.border; ctx.lineWidth=2;
    ctx.fillRect(ox,oy,bw,bh); ctx.strokeRect(ox,oy,bw,bh);
    ctx.textAlign='left';
    const sellMode=extra&&extra.sellMode;
    ctx.fillStyle=C.title; ctx.font='bold 16px monospace';
    ctx.fillText(sellMode?'SHOP — SELL MODE':'SHOP',ox+15,oy+25);
    ctx.fillStyle=C.gold; ctx.font='13px monospace';
    ctx.fillText('Gold: '+g.player.gold, ox+350, oy+25);
    ctx.fillStyle=C.text; ctx.font='bold 13px monospace';
    ctx.fillText('Buy:',ox+15,oy+50);
    let ly=oy+72;
    for (let i=0;i<extra.shop.length;i++) {
        const it=extra.shop[i];
        const rtag=RARITY_NAME[it.rarity];
        ctx.fillStyle=sellMode?C.dim:(C.rarity[it.rarity]||C.text); ctx.font='12px monospace';
        const info=it.type==='weapon'?'P+'+it.patk+' M+'+it.matk:'PD+'+it.pdef+' MD+'+it.mdef;
        ctx.fillText('['+(i+1)+'] '+it.name+rtag+' '+info+' $'+it.value, ox+20, ly);
        ly+=18;
    }
    ly+=8;
    ctx.fillStyle=C.text; ctx.font='bold 13px monospace';
    ctx.fillText('Sell:',ox+15,ly); ly+=22;
    for (let i=0;i<Math.min(extra.sell.length,6);i++) {
        const it=extra.sell[i];
        const val=Math.max(1,Math.floor(it.value/2));
        ctx.fillStyle=sellMode?C.hp:C.text; ctx.font='12px monospace';
        ctx.fillText('['+(i+1)+'] '+it.name+' $'+val, ox+20, ly);
        ly+=18;
    }
    ctx.fillStyle=C.prompt; ctx.font='12px monospace';
    ctx.fillText(sellMode?'Select number to sell, [s] cancel, [q] exit':'1-9: buy  s: sell mode  q: exit', ox+15, oy+bh-15);
}
function drawMapView(ctx,g) {
    ctx.fillStyle=C.bg; ctx.fillRect(0,0,canvasW,canvasH);
    ctx.fillStyle=C.title; ctx.font='bold 16px monospace';
    ctx.textAlign='center';
    ctx.fillText('Explored Map (Level '+g.dlvl+')',canvasW/2,30);
    ctx.fillStyle=C.dim; ctx.font='12px monospace';
    ctx.fillText('@=You  #=Wall  .=Floor  >=Stairs  A-Z=Monsters',canvasW/2,50);
    ctx.textAlign='left';
    const s=12, ox=10, oy=65;
    for (let y=0;y<g.MAP_H;y++) {
        for (let x=0;x<g.MAP_W;x++) {
            const px=ox+x*s, py=oy+y*s;
            if (!g.explored[y][x]) continue;
            if (y===g.player.y&&x===g.player.x) {
                ctx.fillStyle=C.player; ctx.fillText('@',px,py+s);
            } else {
                let ch=null;
                for (const e of g.entities)
                    if (e!==g.player&&e.x===x&&e.y===y) { ch=e.name[0]; break; }
                if (!ch) for (const it of g.items)
                    if (it.x===x&&it.y===y&&it.type==='stairs') { ch='>'; break; }
                if (ch) { ctx.fillStyle=C.monster; ctx.fillText(ch,px,py+s); }
                else {
                    ctx.fillStyle=g.map[y][x]===35?C.wall:C.floor;
                    ctx.fillText(g.map[y][x]===35?'#':'.',px,py+s);
                }
            }
        }
    }
    ctx.textAlign='center';
    ctx.fillStyle=C.dim; ctx.font='12px monospace';
    ctx.fillText('Press any key to close',canvasW/2,canvasH-20);
    ctx.textAlign='left';
}
function drawSaveSlot(ctx,g,extra) {
    const ox=Math.max(0,(canvasW-380)/2), oy=Math.max(0,(canvasH-260)/2), bw=380, bh=260;
    ctx.fillStyle=C.panel; ctx.strokeStyle=C.border; ctx.lineWidth=2;
    ctx.fillRect(ox,oy,bw,bh); ctx.strokeRect(ox,oy,bw,bh);
    ctx.textAlign='left';
    ctx.fillStyle=C.title; ctx.font='bold 14px monospace';
    ctx.fillText('Save to which slot?',ox+20,oy+30);
    for (let s=1;s<=3;s++) {
        const info=getSaveInfo(s);
        let line;
        if (!info) line='['+s+'] Slot '+s+' — (empty)';
        else if (info.corrupted) line='['+s+'] Slot '+s+' — (corrupted)';
        else line='['+s+'] Slot '+s+' — Lv.'+info.dlvl+' HP:'+info.hp+'/'+info.max_hp;
        ctx.fillStyle=C.text; ctx.font='13px monospace';
        ctx.fillText(line,ox+30,oy+65+s*24);
    }
    ctx.fillStyle=C.dim; ctx.font='12px monospace';
    ctx.fillText('Press 1/2/3 to save, ESC to cancel',ox+20,oy+bh-20);
}

// ── Input / Game Loop ────────────────────────────────────────────────────
let g = null;
let state = 'title';
let stateData = {};
let actionResolve = null;
let saved = null;
let pendingMonster = null;

function waitKey() {
    return new Promise(resolve => { actionResolve = resolve; });
}

function handleKey(key) {
    if (actionResolve) {
        actionResolve(key);
        actionResolve = null;
    }
}

const KEY_MAP = {
    'ArrowLeft':'h','ArrowDown':'j','ArrowUp':'k','ArrowRight':'l',
    ' ':'space', '.':'period', '>':'>', 'i':'i', 'd':'d',
    'm':'m', 's':'s', 'S':'S', 'Q':'Q', 'q':'q',
    'y':'y','u':'u','b':'b','n':'n',
    'e':'e','f':'f',
};

document.addEventListener('keydown', (e) => {
    if (e.key === 'Shift' || e.key === 'Control' || e.key === 'Alt' || e.key === 'Meta' || e.key === 'CapsLock') return;
    const key = KEY_MAP[e.key] || e.key;
    if (key.length===1||key==='space'||key==='period'||key==='escape') { handleKey(key); e.preventDefault(); }
    if (e.key>='0'&&e.key<='9') { handleKey(e.key); e.preventDefault(); }
});

// ── Game Screens ─────────────────────────────────────────────────────────
async function titleScreen() {
    const hasSaves=anySaveExists();
    const hasAutosave=autosaveExists();
    draw(ctx,g,'title',{hasSaves,hasAutosave});
    while (true) {
        const k=await waitKey();
        if (k==='x'||k==='X') {
            for (let s=1;s<=3;s++) localStorage.removeItem('md_save_'+s);
            clearAutosave();
            return ['cleared'];
        }
        if (hasAutosave&&(k==='c'||k==='C')) return ['continue'];
        if (hasSaves) {
            if (k==='1'||k==='2'||k==='3') return ['load',parseInt(k)];
            if (k==='n'||k==='N') return ['new',null];
            if (k==='q'||k==='Q') return ['quit',null];
        } else {
            if (k==='1') return ['new',1];
            if (k==='2') return ['new',2];
            if (k==='3') return ['new',3];
        }
    }
}

async function saveSlotSelector(g) {
    draw(ctx,g,'saveslot');
    while (true) {
        const k=await waitKey();
        if (k==='1'||k==='2'||k==='3') return parseInt(k);
        if (k==='escape') return null;
    }
}

async function gameOverScreen(g) {
    draw(ctx,g,'gameover');
    while (true) {
        const k=await waitKey();
        if (k==='r'||k==='R') return 'restart';
        if (k==='s'||k==='S') return 'strong';
        if (k==='q'||k==='Q') return 'quit';
    }
}

async function victoryScreen(g) {
    draw(ctx,g,'victory');
    while (true) {
        const k=await waitKey();
        if (k==='s'||k==='S') return 'strong';
        if (k==='n'||k==='N') return 'new';
        if (k==='q'||k==='Q') return 'quit';
    }
}

async function battleScreen(g,enemy,playerFirst) {
    let playerTurn=playerFirst;
    while (enemy.hp>0&&g.player.hp>0) {
        draw(ctx,g,'battle',{enemy,playerTurn});
        if (playerTurn) {
            let chosen=null;
            while (true) {
                const k=await waitKey();
                if (k==='e'&&g.player.weapon_item) { chosen=g.player.weapon_item; break; }
                else if (k==='f') { chosen=null; break; }
                else if (k>='1'&&k<='9') {
                    const idx=parseInt(k)-1;
                    if (idx<g.player.inventory.length) {
                        const it=g.player.inventory[idx];
                        if (it.type==='weapon'&&it!==g.player.weapon_item) { chosen=it; break; }
                    }
                }
            }
            playerTurn=false;
            const [dmg,isCrit,type]=calcDamage(g.player,chosen,enemy);
            g.add_msg((isCrit?'CRIT! ':'')+g.player.name+' hits '+enemy.name+' for '+dmg+' ('+type+')');
            enemy.hp-=dmg;
            if (enemy.hp<=0) {
                g.add_msg(enemy.name+' is slain!');
                g.entities=g.entities.filter(e=>e!==enemy);
                levelUp(g);
                enemyDrop(g,enemy);
                if (g.dlvl>=g.maxFloor&&g.entities.filter(e=>e!==g.player).length===0)
                    return 'victory';
                return true;
            }
        } else {
            await waitKey();
            const chosen=enemy.weapon_item;
            const [dmg,isCrit,type]=calcDamage(enemy,chosen,g.player);
            g.add_msg((isCrit?'CRIT! ':'')+enemy.name+' hits '+g.player.name+' for '+dmg+' ('+type+')');
            g.player.hp-=dmg;
            playerTurn=true;
            if (g.player.hp<=0) {
                g.game_over=true;
                g.add_msg('You have died...');
                return false;
            }
        }
    }
    return g.player.hp>0;
}

async function inventoryFlow(g) {
    while (true) {
        draw(ctx,g,'inventory');
        const k=await waitKey();
        if (k==='q'||k==='escape') return;
        if (k==='d') { await dropFlow(g); return; }
        if (k>='1'&&k<='9') {
            const idx=parseInt(k)-1;
            if (idx<g.player.inventory.length) {
                const it=g.player.inventory[idx];
                if (it.type==='weapon'||it.type==='armor') {
                    const old=it.type==='weapon'?g.player.weapon_item:g.player.armor_item;
                    if (it.type==='weapon') g.player.weapon_item=it;
                    else g.player.armor_item=it;
                    if (old) g.player.inventory.push(old);
                    g.player.inventory.splice(idx,1);
                    g.add_msg('equipped '+it.name);
                    return;
                } else if (it.type==='potion_heal') {
                    g.player.hp=Math.min(g.player.hp+15,g.player.max_hp);
                    g.add_msg('quaffed healing potion');
                    g.player.inventory.splice(idx,1);
                    return;
                } else if (it.type==='potion_str') {
                    g.player.patk+=2; g.player.matk+=1;
                    g.add_msg('strength +2!');
                    g.player.inventory.splice(idx,1);
                    return;
                } else if (it.type==='food') {
                    g.player.hp=Math.min(g.player.hp+10,g.player.max_hp);
                    g.add_msg('ate food');
                    g.player.inventory.splice(idx,1);
                    return;
                }
            }
        }
    }
}

async function dropFlow(g) {
    while (true) {
        draw(ctx,g,'inventory',{dropMode:true});
        const k=await waitKey();
        if (k==='q'||k==='escape') return;
        if (k>='1'&&k<='9') {
            const idx=parseInt(k)-1;
            if (idx<g.player.inventory.length) {
                const it=g.player.inventory[idx];
                if (it===g.player.weapon_item) g.player.weapon_item=null;
                if (it===g.player.armor_item) g.player.armor_item=null;
                g.player.inventory.splice(idx,1);
                g.add_msg('dropped '+it.name);
                return;
            }
        }
    }
}

async function shopScreen(g) {
    const shop=[];
    for (let i=0;i<rnd(3,5);i++) {
        const r=Math.random()<0.5?makeWeapon(g,0):makeArmor(g,0);
        r.value=Math.max(10,Math.floor((r.value+r.patk*30+r.matk*30+r.pdef*25+r.mdef*25)*g.shopPriceMul));
        shop.push(r);
    }
    let sellMode=false;
    while (true) {
        const sellItems=g.player.inventory.filter(it=>['weapon','armor','potion_heal','food','potion_str'].includes(it.type));
        draw(ctx,g,'shop',{shop,sell:sellItems,sellMode});
        const k=await waitKey();
        if (k==='q'||k==='escape') { if (sellMode) sellMode=false; else return; }
        else if (k==='s') { sellMode=!sellMode; }
        else if (k>='1'&&k<='9') {
            const idx=parseInt(k)-1;
            if (sellMode) {
                if (idx<sellItems.length) {
                    const it=sellItems[idx];
                    const val=Math.max(1,Math.floor(it.value/2));
                    g.player.gold+=val;
                    const i=g.player.inventory.indexOf(it);
                    if (i>=0) {
                        if (it===g.player.weapon_item) g.player.weapon_item=null;
                        if (it===g.player.armor_item) g.player.armor_item=null;
                        g.player.inventory.splice(i,1);
                    }
                    g.add_msg('Sold '+it.name+' for $'+val);
                    sellMode=false;
                }
            } else {
                if (idx<shop.length&&g.player.gold>=shop[idx].value) {
                    g.player.gold-=shop[idx].value;
                    if (g.player.inventory.length<10) {
                        shop[idx].x=0; shop[idx].y=0;
                        g.player.inventory.push(shop[idx]);
                        g.add_msg('Bought '+shop[idx].name+' for $'+shop[idx].value);
                        shop.splice(idx,1);
                    } else g.add_msg('Inventory full!');
                }
            }
        }
    }
}

// ── Main Game Loop ───────────────────────────────────────────────────────
async function playGame() {
    while (true) {
        const result=await titleScreen();
        if (!result||result[0]==='quit') return;

        if (result[0]==='load') {
            g=new Game(2);
            if (!loadGame(g,result[1])) continue;
            g.add_msg('Game loaded. Welcome back!');
            g.game_over=false;
        } else if (result[0]==='continue') {
            g=new Game(2);
            if (!loadAutosave(g)) continue;
            g.add_msg('Continue from autosave...');
        } else if (result[0]==='new') {
            const diff=result[1]||(await (async()=>{
                const r=await titleScreen();
                if (!r||r[0]==='quit') return null;
                return r[1];
            })());
            if (!diff) return;

            clearAutosave();
            g=new Game(diff);
            g.player=new Entity(0,0,'🧙','player',true,'Player',20,20,0,3,2,1,1,0.05,1.5);
            g.entities.push(g.player);

            if (saved) {
                g.player.max_hp=saved.max_hp; g.player.hp=saved.hp;
                g.player.patk=saved.patk; g.player.matk=saved.matk;
                g.player.pdef=saved.pdef; g.player.mdef=saved.mdef;
                g.player.crit_rate=saved.crit_rate; g.player.crit_dmg=saved.crit_dmg;
                g.player.gold=saved.gold; g.player.xp=saved.xp;
                g.player.inventory=[...saved.inventory];
                g.player.weapon_item=saved.weapon_item;
                g.player.armor_item=saved.armor_item;
                g.add_msg('Strong New Game begins!');
                saved=null;
            }
            genLevel(g);
            computeFov(g);
            g.game_over=false;
        }

        while (g&&!g.game_over&&!g.victory) {
            computeFov(g);
            draw(ctx,g,'playing');
            const key=await waitKey();
            let dx=0, dy=0, acted=false;

            if (key==='q') return;
            else if (key==='Q') {
                if (g.current_slot) { saveGame(g,g.current_slot); g.add_msg('Saved!'); }
                else { const s=await saveSlotSelector(g); if (s) { saveGame(g,s); g.current_slot=s; g.add_msg('Saved!'); } }
            } else if (key==='S') {
                if (g.current_slot) { saveGame(g,g.current_slot); g.add_msg('Saved!'); }
                else { const s=await saveSlotSelector(g); if (s) { saveGame(g,s); g.current_slot=s; g.add_msg('Saved!'); } }
            } else if (key==='h') { dx=-1; }
            else if (key==='j') { dy=1; }
            else if (key==='k') { dy=-1; }
            else if (key==='l') { dx=1; }
            else if (key==='y') { dx=-1; dy=-1; }
            else if (key==='u') { dx=1; dy=-1; }
            else if (key==='b') { dx=-1; dy=1; }
            else if (key==='n') { dx=1; dy=1; }
            else if (key==='space') { acted=true; }
            else if (key==='period') { g.player.hp=Math.min(g.player.hp+1,g.player.max_hp); acted=true; }
            else if (key==='>') {
                let found=false;
                for (const it of g.items) {
                    if (it.x===g.player.x&&it.y===g.player.y&&it.type==='stairs') {
                        g.dlvl++; g.add_msg('Descend to level '+g.dlvl);
                        if (g.dlvl>(getScore().best)) { const s=getScore(); s.best=g.dlvl; saveScore(s); }
                        genLevel(g); computeFov(g);
                        g.messages=g.messages.slice(-10);
                        g.add_msg('You arrive on a new floor');
                        saveAutosave(g);
                        found=true; acted=true; break;
                    }
                }
                if (!found) g.add_msg('No stairs here');
            } else if (key==='i') { await inventoryFlow(g); }
            else if (key==='d') { await dropFlow(g); }
            else if (key==='m') { draw(ctx,g,'mapview'); await waitKey(); }
            else if (key==='s') {
                let found=false;
                for (const it of g.items) {
                    if (it.x===g.player.x&&it.y===g.player.y&&it.type==='shop') {
                        await shopScreen(g); found=true; break;
                    }
                }
                if (!found) g.add_msg('No shop here');
            }

            if (dx||dy) {
                const nx=g.player.x+dx, ny=g.player.y+dy;
                if (nx>0&&nx<g.MAP_W-1&&ny>0&&ny<g.MAP_H-1) {
                    const enemy=g.entities.find(e=>e!==g.player&&e.x===nx&&e.y===ny&&e.hp>0);
                    if (enemy) {
                        const r=await battleScreen(g,enemy,true);
                        if (r==='victory') { g.victory=true; break; }
                        acted=true;
                    } else if (g.map[ny][nx]!==35) {
                        g.player.x=nx; g.player.y=ny;
                        for (const it of [...g.items]) {
                            if (it.x===nx&&it.y===ny) {
                                if (it.type==='gold') { g.player.gold+=it.value; g.add_msg('picked up '+it.value+' gold'); g.items.splice(g.items.indexOf(it),1); }
                                else if (it.type==='shop') g.add_msg('Press [s] to enter the shop');
                                else if (it.type==='stairs') { /* handled above */ }
                            }
                        }
                        acted=true;
                    }
                }
            }

            if (acted) {
                const monster=monsterTick(g);
                if (monster) {
                    const r=await battleScreen(g,monster,false);
                    if (r==='victory') { g.victory=true; break; }
                }
            }
            if (g.player.hp<=0) { g.game_over=true; draw(ctx,g,'playing'); }
        }

        if (g&&g.victory) {
            saveAutosave(g);
            clearAutosave();
            const result=await victoryScreen(g);
            if (result==='strong') {
                saved={
                    max_hp:g.player.max_hp, hp:g.player.max_hp,
                    patk:g.player.patk, matk:g.player.matk,
                    pdef:g.player.pdef, mdef:g.player.mdef,
                    crit_rate:g.player.crit_rate, crit_dmg:g.player.crit_dmg,
                    gold:g.player.gold, xp:g.player.xp,
                    inventory:[...g.player.inventory],
                    weapon_item:g.player.weapon_item,
                    armor_item:g.player.armor_item,
                };
                continue;
            } else if (result==='new') continue;
            else return;
        }

        if (g&&g.game_over) {
            const s=getScore(); s.attempts++; saveScore(s);
            const result=await gameOverScreen(g);
            if (result==='restart') { clearAutosave(); continue; }
            else if (result==='strong') {
                clearAutosave();
                saved={
                    max_hp:g.player.max_hp, hp:g.player.max_hp,
                    patk:g.player.patk, matk:g.player.matk,
                    pdef:g.player.pdef, mdef:g.player.mdef,
                    crit_rate:g.player.crit_rate, crit_dmg:g.player.crit_dmg,
                    gold:g.player.gold, xp:g.player.xp,
                    inventory:[...g.player.inventory],
                    weapon_item:g.player.weapon_item,
                    armor_item:g.player.armor_item,
                };
                continue;
            } else return;
        }
    }
}

// ── Boot ─────────────────────────────────────────────────────────────────
window.addEventListener('load',()=>{
    canvas=document.getElementById('game');
    ctx=canvas.getContext('2d');
    resize();
    window.addEventListener('resize',resize);
    playGame();
});
