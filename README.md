<div align="center">

<img src="assets/CODE3.png" alt="CODE Portal 3 Logo" width="600"/>

# CODE Portal³

### Programmēšanas loģikas mācību spēle kiberpunka stilā

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![tkinter](https://img.shields.io/badge/GUI-tkinter-00B4D8?style=for-the-badge)](https://docs.python.org/3/library/tkinter.html)
[![OOP](https://img.shields.io/badge/OOP-8%20klases-0077B6?style=for-the-badge)]()
[![License](https://img.shields.io/badge/Licence-MIT-success?style=for-the-badge)]()

</div>

---

## Par spēli

**CODE Portal³** ir kiberpunka tematikas mācību spēle, kurā spēlētājs piedalās misijā kā hakeris, kas iziet cauri trim drošības portāliem. Katrs portāls ir programmēšanas puzle - nosacījumi, cikli, funkcijas. Portāls atveras tikai tad, kad atbilde ir pareiza. Nepareiza atbilde? Signalizācija iedarbojas un zaudē laiku!

> Projekts izstrādāts kā kursa darbs programmēšanas kursā. Komanda: **PORTAL 3**.

---

## Spēles mehānika

| Līmenis | Temats | Uzdevumu tips |
|---------|--------|--------------|
| 🔴 **1. Drošības vārti** | `if / else` nosacījumi | Pseidokods → izvēlies pareizo zaru |
| 🟡 **2. Datu tunelis** | `for / while` cikli | Izseko ciklu → nosaki galīgo vērtību |
| 🟢 **3. Galvenā servera istaba** | Funkcijas | Funkcijas izsaukums → ko atgriež? |

### Punktu sistēma

| Rezultāts | Punkti |
|-----------|--------|
| Pareiza atbilde no 1. mēģinājuma | **100 pts** |
| Pareiza atbilde no 2. mēģinājuma | **50 pts** |
| Pareiza atbilde no 3. mēģinājuma | **20 pts** |
| Ātruma bonuss (< 15 sek) | **+25 pts** |
| 3 nepareizas atbildes | Līmenis zaudēts |

---

## Projekta struktūra

```
code-portal3/
│
├── main.py               # Galvenais ieejas punkts
├── game.py               # Game klase — spēles vadība
├── player.py             # Player klase — spēlētāja dati
├── level.py              # Level bāzes klase + apakšklases
├── task.py               # Task klase — uzdevumu modelis
├── score_log.py          # ScoreLog klase — rezultātu saglabāšana
│
├── data/
│   ├── tasks.json        # Visi uzdevumi un pareizās atbildes
│   └── scores.csv        # Spēlētāju rezultātu statistika
│
├── assets/
│   └── CODE3.png         # Spēles logo
│
└── README.md
```

---

## OOP arhitektūra

```
Game
 ├── Player          (asociācija — izmanto)
 ├── ScoreLog        (asociācija — saglabā rezultātus)
 └── Level           (asociācija — menedžē)
      ├── Task            (kompozīcija — satur)
      ├── ConditionLevel  (mantošana ↳ pārdefinē display_task())
      ├── LoopLevel       (mantošana ↳ pārdefinē display_task())
      └── FunctionLevel   (mantošana ↳ pārdefinē display_task())
```

| OOP princips | Kur izmantots |
|---|---|
| **Iekapsulēšana** | Visi atribūti `private` vai `protected`, piekļuve ar getter/setter |
| **Mantošana** | `Level` → `ConditionLevel`, `LoopLevel`, `FunctionLevel` |
| **Polimorfisms** | `display_task()` darbojas atšķirīgi katrā apakšklasē |
| **Virtuālās funkcijas** | `display_task()` bāzes klasē `Level` |
| **Dinamiskie objekti** | `Task` objekti dinamiski alocēti `_tasks` sarakstā |
| **Failu apstrāde** | `tasks.json` uzdevumiem, `scores.csv` statistikai |

---

## Kā palaist

**Prasības:** Python 3.10+

```bash
# Klonē repozitoriju
git clone https://github.com/AffectTron/CodePORTAL3.git
cd CodePORTAL3

# Palaid spēli (tkinter ir iekļauts Python standarta bibliotēkā)
python main.py
```

> Nav nepieciešama papildu bibliotēku instalēšana - viss izmanto Python standarta bibliotēku.

---

## Tehnoloģijas

| Tehnoloģija | Izmantojums |
|---|---|
| **Python 3.10+** | Galvenā programmēšanas valoda |
| **tkinter** | Grafiskā lietotāja saskarne |
| **JSON** | Uzdevumu datu glabāšana |
| **CSV** | Spēlētāju statistikas glabāšana |

---

## Komanda

| Dalībnieks | Loma |
|---|---|
| Artūrs Skorikovs | Projekta izstrāde, UML diagramma, grafiskais dizains |


---

<div align="center">


**PORTAL 3** · Programmēšanas kursa projekts

</div>
