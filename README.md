<div align="center">

<img src="CODE3.png" alt="CODE Portal 3 Logo" width="600"/>

# CODE Portal³
### 🎮 Programmēšanas loģikas mācību spēle

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![tkinter](https://img.shields.io/badge/GUI-tkinter-00B4D8?style=for-the-badge)](https://docs.python.org/3/library/tkinter.html)
[![OOP](https://img.shields.io/badge/OOP-8%20klases-0077B6?style=for-the-badge)]()
[![License](https://img.shields.io/badge/Licence-MIT-success?style=for-the-badge)]()


</div>

---

## 📖 Par spēli

**CODE Portal³** ir kiberpunka tematikas mācību spēle, kurā spēlētājs piedalās misijā kā hakeris, kas iziet cauri trim drošības portāliem. Katrs portāls ir programmēšanas puzle - nosacījumi, cikli, funkcijas. Portāls atveras tikai tad, kad atbilde ir pareiza. Nepareiza atbilde? Signalizācija iedarbojas un zaudē laiku! ⚡

> Projekts izstrādāts kā kursa darbs programmēšanas kursā. Komanda: **PORTAL 3**.

---

## 🕹️ Spēles mehānika

| Līmenis | Temats | Uzdevumi |
|---------|--------|----------|
| 🔴 **1. Drošības vārti** | `if / else` nosacījumi | Pseidokods → izvēlies pareizo zaru |
| 🟡 **2. Datu tunelis** | `for / while` cikli | Izseko ciklu → nosaki galīgo vērtību |
| 🟢 **3. Galvenā servera istaba** | Funkcijas | Funkcijas izsaukums → ko atgriež? |

**Punktu sistēma:**
- ✅ Pareiza atbilde no 1. mēģinājuma → **100 pts**
- ✅ Pareiza atbilde no 2. mēģinājuma → **50 pts**
- ✅ Pareiza atbilde no 3. mēģinājuma → **20 pts**
- ⚡ Ātruma bonuss (< 15 sek) → **+25 pts**
- 💀 3 nepareizas atbildes → līmenis zaudēts

## 📁 Projekta struktūra

```
code-portal3/
│
├── main.py               # Galvenais ieejas punkts
├── game.py               # Game klase - spēles vadība
├── player.py             # Player klase - spēlētāja dati
├── level.py              # Level bāzes klase + apakšklases
├── task.py               # Task klase - uzdevumu modelis
├── score_log.py          # ScoreLog klase - rezultātu saglabāšana
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

## 🏗️ OOP arhitektūra

```
Game
 ├── Player          (asociācija - izmanto)
 ├── ScoreLog        (asociācija - saglabā rezultātus)
 └── Level           (asociācija - menedžē)
      ├── Task            (kompozīcija - satur)
      ├── ConditionLevel  (mantošana ↳ pārdefinē display_task())
      ├── LoopLevel       (mantošana ↳ pārdefinē display_task())
      └── FunctionLevel   (mantošana ↳ pārdefinē display_task())
```

| OOP princips | Kur izmantots |
|---|---|
| **Iekapsulēšana** | Visi atribūti `private` vai `protected`, piekļuve ar getter/setter |
| **Mantošana** | `Level` → `ConditionLevel`, `LoopLevel`, `FunctionLevel` |
| **Polimorfisms** | `display_task()` darbojas atšķirīgi katrā apakšklasē |
| **Virtuālās funkcijas** | `display_task()` bāzes klasē Level |
| **Dinamiskie objekti** | Task objekti dinamiski alocēti `_tasks` sarakstā |
| **Failu apstrāde** | `tasks.json` uzdevumiem, `scores.csv` statistikai |

---

## 👾 Komanda

| Dalībnieks | Loma |
|---|---|
| Artūrs Skorikovs | UML diagramma, dizains |


> Komandas nosaukums: **PORTAL 3** — jo Portal 2 jau bija paņemts 🌀

---

## 📚 Tehnoloģijas

- **Python 3** — programmēšanas valoda
- **tkinter** — grafiskā lietotāja saskarne
- **JSON** — uzdevumu datu glabāšana
- **CSV** — spēlētāju statistikas glabāšana

---

<div align="center">

*Izstrādāts ar ☕ un pārāk daudziem if/else zariem*

**PORTAL 3 komanda** · Programmēšanas kursa projekts

</div>
