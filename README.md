<div align="center">

<img src="assets/CODE3.png" alt="CODE Portal 3" width="720"/>

# CODE Portal³

**Kiberpunka 2D platformer ar Python programmēšanas uzdevumiem**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Pygame](https://img.shields.io/badge/Pygame--CE-2.5+-00B4D8?style=flat)](https://pyga.me/)
[![OOP](https://img.shields.io/badge/OOP-4_Principi-0077B6?style=flat)]()
[![License](https://img.shields.io/badge/License-MIT-success?style=flat)]()

</div>

---

## Par spēli

Uzņemies hakera lomu un izlauzies cauri trim drošības portāliem kiberpunka pasaulē. Katrs portāls ir Python mīkla — risinot uzdevumus, apgūsti programmēšanas pamatkonceptus klasiskā platformer žanrā.

## Portāli

| Portāls | Tēma | Konteksts |
|:-:|:-:|:--|
| 🔴 **Sarkanais** | Nosacījumi | `if`, `elif`, `else` izsekošana |
| 🟡 **Dzeltenais** | Cikli | `for` un `while` rezultātu noteikšana |
| 🟢 **Zaļais** | Funkcijas | Funkciju atgriežamo vērtību analīze |

## Galvenās iespējas

- **Platformer fizika** — gravitācija, lēkšana, sadursmes, šķēršļi
- **Vizuāls Level Editor** — 24 tile veidi, 6 kategorijas, JSON saglabāšana
- **Parallax fons** — daudzslāņu kiberpunka pilsēta
- **Punktu sistēma** — 100/50/20 pēc mēģinājuma + ātruma bonuss (−15s = +25)
- **CSV statistika** — top 5 rezultāti un sesijas žurnāls

## Instalācija

```bash
pip install pygame-ce
python main.py
```

> Nepieciešams Python 3.10+

## Vadība

<table>
<tr><td valign="top">

**Pasaulē**
| Taustiņš | Darbība |
|:-:|:--|
| `A` `D` / `←` `→` | Kustība |
| `SPACE` / `W` | Lēkt |
| `R` | Atjaunot pozīciju |
| `ESC` | Iziet |

</td><td valign="top">

**Uzdevumā**
| Taustiņš | Darbība |
|:-:|:--|
| `0-9` `A-Z` | Atbilde |
| `ENTER` | Iesniegt |
| `BACKSPACE` | Dzēst |
| `ESC` | Atcelt |

</td><td valign="top">

**Editorā**
| Taustiņš | Darbība |
|:-:|:--|
| `LMB` / `RMB` | Likt / dzēst |
| `TAB` | Kategorija |
| `G` | Režģis |
| `Ctrl+S` / `N` | Saglabāt / jauns |

</td></tr>
</table>

## Arhitektūra

Projekts balstīts uz **objektorientētās programmēšanas** principiem ar skaidru klašu atbildību sadali.

| Princips | Pielietojums |
|:--|:--|
| **Iekapsulēšana** | Privāti atribūti, piekļuve caur getter/setter |
| **Mantošana** | Tile un Level klašu hierarhijas |
| **Polimorfisms** | Virtuālās metodes pārdefinētas apakšklasēs |
| **Kompozīcija** | Game/World izmanto vienkāršāku klašu objektus |

```
Tile                              Level
├── SolidTile                     ├── ConditionLevel
├── PortalTile                    ├── LoopLevel
└── HazardTile                    └── FunctionLevel
```

**Tehnoloģijas:** Python 3 · pygame-ce · JSON (līmeņi, uzdevumi) · CSV (rezultāti)

## Spēles plūsma

Spēlētājs pārvietojas pa pasauli līdz portālam → atveras uzdevumu logs ar Python koda fragmentu → analizē kodu un ievada rezultātu → pareiza atbilde deaktivē portālu → pēc visu trīs portālu pabeigšanas tiek parādīts uzvaras ekrāns ar punktu skaitu.

---

<div align="center">

**Artūrs Skorikovs** · Komanda **PORTAL 3** *(jo Portal 2 jau bija paņemts)*

Kursa darbs programmēšanas kursā · MIT License

</div>
