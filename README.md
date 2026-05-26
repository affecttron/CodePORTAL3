<div align="center">

<img src="assets/CODE3.png" alt="CODE Portal 3" width="720"/>

# CODE Portal³

**Kiberpunka 2D platformer, kur programmēšana ir vienīgais ierocis**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Pygame CE](https://img.shields.io/badge/Pygame--CE-2.5+-00B4D8?style=flat)](https://pyga.me/)
[![OOP](https://img.shields.io/badge/OOP-4_Principi-0077B6?style=flat)]()

</div>

---

Tu esi hakeris. Sistēma ir bruņota ar trīs drošības portāliem. Vienīgais veids, kā tos apiet, ir zināt Python. Atrisini uzdevumu, portāls deaktivizējas. Atrodi izeju. Tiec tālāk.

Tas ir kursa darbs, kas izskatās pēc spēles, bet faktiski māca programmēšanu.

---

## Pasaules

Spēle satur trīs pasaules ar pieaugošu grūtību. Katrā pasaulē ir trīs portāli, katrs ar savu tēmu.

| Pasaule | Nosaukums | Portāli | Mēģinājumi | Overclock |
|:-:|:--|:--|:-:|:-:|
| 1 | INITIATION | if/else, for/while, funkcijas | 3 | 15 sek |
| 2 | INFILTRATION | Sarežģīti nosacījumi, ciklu kombinācijas, funkciju loģika | 3 | 12 sek |
| 3 | CORE BREACH | Algoritmi, datu manipulācija, elite tests | 2 | 9 sek |

Pēc trešās pasaules var turpināt Endless režīmā bez limita.

---

## Kā tas strādā

Staigā pa platformer līmeni. Uzskriej portālam. Atveras terminālis ar Python koda fragmentu un jautājumu. Tu analizē kodu ar galvu un ievadi atbildi. Nav interneta, nav hints sākumā, nav laika tēriņiem. Pēc kļūdas hints parādās.

Pareizi: portāls izslēdzas, saņem punktus un laika bonusu ja biji ātrs.  
Nepareizi: zaudē 5 punktus, redzat padomu.  
Kritieni hazardā: zaudē 10 punktus, nomirst dramatiskā raudzenē.  
Visi trīs portāli pabeigti: durvis uz nākamo pasauli atveras.

---

## Punkti

Katram uzdevumam ir trīs mēģinājumi. Punktus skaita šādi:

- 1. mēģinājums: 100 pts
- 2. mēģinājums: 50 pts
- 3. mēģinājums: 20 pts

Ja atbildi pirms Overclock taimera beigām, saņem papildu 10 punktus. Overclock logs ir 15/12/9 sekundes atkarībā no pasaules. Pēc kļūdas Overclock bonuss pazūd uz šo uzdevumu.

---

## Uzdevumi

Katrā portālā ir 15 unikāli uzdevumi par dažādiem tematiem. Katrs uzdevums dod koda fragmentu un prasa precīzu atbildi ko Python izpildītu.

```
Pasaule 1:  if/else nosacījumi  |  for/while cikli  |  funkcijas
Pasaule 2:  sarežģīti nosacījumi  |  ciklu kombinācijas  |  funkciju loģika
Pasaule 3:  algoritmi  |  datu manipulācija  |  elite tests
```

Kopā 9 līmeņi, katrā 15 uzdevumi. Tas ir 135 jautājumi.

---

## Instalācija

```bash
pip install pygame-ce
python main.py
```

Nepieciešams Python 3.10 vai jaunāks.

---

## Vadība

**Pasaulē**

| Taustiņš | Darbība |
|:-:|:--|
| `A` `D` vai bultiņas | Kustība |
| `SPACE` vai `W` | Lēkt |
| `W` `S` | Rāpties pa kāpnēm |
| `R` | Respawn |
| `F1` | Ieslēgt/izslēgt vizuālos efektus |
| `F9` | Izlaist pasauli (testēšanai) |
| `ESC` | Iziet |

**Uzdevumā**

| Taustiņš | Darbība |
|:-:|:--|
| Tastatūra | Ievadīt atbildi |
| `ENTER` | Iesniegt |
| `TAB` | Izlaist typewriter animāciju |
| `BACKSPACE` | Dzēst (tur nospiestu: ātri dzēš) |
| `ESC` | Atcelt un atgriezties pasaulē |

**Līmeņu redaktorā**

| Taustiņš | Darbība |
|:-:|:--|
| `LMB` | Likt tile |
| `RMB` | Dzēst tile |
| `TAB` | Pārslēgt kategoriju |
| `G` | Rādīt/slēpt režģi |
| `Ctrl+S` | Saglabāt |
| `N` | Jauns līmenis |

---

## Arhitektūra

Projekts izmanto četrus OOP principus.

| Princips | Kur |
|:--|:--|
| Iekapsulēšana | Privāti atribūti ar `_`, piekļuve caur metodēm |
| Mantošana | `Tile` un `Level` klašu hierarhijas |
| Polimorfisms | `draw()`, `verify()`, `to_dict()` pārdefinētas apakšklasēs |
| Kompozīcija | `Game` satur `World`, `Player`, `Camera`, `Level` u.c. |

```
Tile                    Level
├── SolidTile           ├── ConditionLevel   (pasaules 1, 2)
├── PortalTile          ├── LoopLevel        (pasaules 1, 2)
├── HazardTile          ├── FunctionLevel    (pasaules 1, 2)
├── ClimbableTile       ├── AdvancedLevel    (pasaule 3)
└── DoorExitTile        └── ExpertLevel      (pasaule 3)
```

Tehnoloģijas: Python 3, pygame-ce, JSON (līmeņi un uzdevumi), CSV (rezultāti), moderngl (shaderi).

---

## Failu struktūra

```
main.py              Galvenā izvēlne
game.py              Spēles stāvokļu mašīna
level.py             Uzdevumu panelis un tipu hierarhija
world.py             Tile pārvaldība un sadursmes
player.py            Spēlētāja dati un punkti
player_sprite.py     Kustība un fizika
camera.py            Kamera ar smooth follow
tile.py              Tile klases
tile_registry.py     Tile attēlu kešs
parallax_background  Fona slāņi
shader_pipeline.py   Cyberpunk vizuālie efekti
sound_manager.py     Skaņa un mūzika
level_editor.py      Grafiskais līmeņu redaktors
score_log.py         CSV rezultātu saglabāšana
data/tasks.json      Visi 135 uzdevumi
data/levels/         Līmeņu JSON faili
```

---

<div align="center">

Veidoja **Artūrs Skorikovs** · Komanda **PORTAL 3**

*(jo Portal 2 jau bija paņemts)*

Kursa darbs programmēšanas kursā

</div>
