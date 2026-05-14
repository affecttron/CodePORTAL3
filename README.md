<div align="center">

<img src="assets/CODE3.png" alt="CODE Portal 3" width="500"/>

# CODE Portal³

### Kiberpunka 2D platformer ar programmēšanas uzdevumiem

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Pygame](https://img.shields.io/badge/Pygame--CE-2.5+-00B4D8?style=flat)](https://pyga.me/)
[![OOP](https://img.shields.io/badge/OOP-Inheritance%20%7C%20Polymorphism-0077B6?style=flat)]()
[![License](https://img.shields.io/badge/License-MIT-success?style=flat)]()

[Apraksts](#apraksts) • [Funkcijas](#funkcijas) • [Instalācija](#instalācija) • [Spēles vadība](#spēles-vadība) • [Arhitektūra](#arhitektūra)

</div>

<br>

## Apraksts

CODE Portal³ ir kiberpunka tematikas 2D platformer spēle, kurā spēlētājs uzņemas hakera lomu un cenšas izlauzties cauri trim drošības portāliem. Katrs portāls ir programmēšanas mīkla par Python valodas pamatkonceptiem - nosacījumiem, cikliem un funkcijām.

Spēle savieno klasisko platformer žanru ar interaktīvu mācīšanos. Spēlētājs staigā, lec un izvairās no šķēršļiem kiberpunka pasaulē, pa ceļam risinot uzdevumus, kas palīdz apgūt programmēšanu.

<br>

## Funkcijas

### Spēles mehānika
Pilnībā funkcionāls 2D platformer ar gravitāciju, lēkšanas fiziku un sadursmju sistēmu. Spēlētājs pārvietojas pa pasauli, kurā ir platformas, sienas, bīstami šķēršļi un trīs interaktīvi portāli, kas atver programmēšanas uzdevumus.

### Trīs portāli, trīs tēmas
| Portāls | Tēma | Apraksts |
|---------|------|----------|
| Sarkanais | Nosacījumi | `if`, `elif`, `else` konstrukciju izsekošana |
| Dzeltenais | Cikli | `for` un `while` ciklu rezultātu noteikšana |
| Zaļais | Funkcijas | Funkciju izsaukumu atgriežamo vērtību analīze |

### Punktu sistēma
- Pareiza atbilde no pirmā mēģinājuma 100 punkti
- Pareiza atbilde no otrā mēģinājuma 50 punkti
- Pareiza atbilde no trešā mēģinājuma 20 punkti
- Ātruma bonuss zem 15 sekundēm +25 punkti
- Trīs nepareizas atbildes nozīmē uzdevuma zaudējumu

### Vizuālais Level Editor
Iebūvēts redaktors, kurš ļauj vizuāli veidot pielāgotas pasaules. Lietotājs var izvēlēties starp 24 dažādiem tile veidiem, kas sadalīti sešās kategorijās. Visi līmeņi tiek saglabāti JSON formātā un automātiski ielādēti spēlē.

### Parallax fons
Daudzslāņu kiberpunka pilsētas fons ar dažādiem ritināšanas ātrumiem, kas rada dziļuma sajūtu. Atbalsta gan reālus attēlus, gan procedurāli ģenerētus placeholder slāņus.

### Datu noturība
Spēlētāju rezultāti tiek saglabāti CSV failā. Sistēma nodrošina top 5 rezultātu apkopošanu, atsevišķu spēlētāju statistikas izsekošanu un sesijas žurnālēšanu.

<br>

## Instalācija

### Priekšnosacījumi
Python 3.10 vai jaunāka versija un pip pakotņu pārvaldnieks.

### Soļi

Pirmkārt, lejupielādē projekta failus.

Otrkārt, instalē nepieciešamās bibliotēkas ar komandu:

```bash
pip install pygame-ce
```

Treškārt, palaiž spēli ar komandu:

```bash
python main.py
```

### Atkarības
| Bibliotēka | Versija | Mērķis |
|------------|---------|--------|
| Python | 3.10+ | Programmēšanas valoda |
| pygame-ce | 2.5+ | Grafiskā saskarne un fizika |

<br>

## Spēles vadība

### Pārvietošanās pasaulē
| Taustiņš | Darbība |
|----------|---------|
| `A` vai `←` | Staigāt pa kreisi |
| `D` vai `→` | Staigāt pa labi |
| `SPACE` vai `W` | Lekt |
| `R` | Atjaunot pozīciju |
| `ESC` | Iziet no spēles |

### Uzdevumu logā
| Taustiņš | Darbība |
|----------|---------|
| `Burti un cipari` | Rakstīt atbildi |
| `BACKSPACE` | Dzēst rakstzīmi |
| `ENTER` | Iesniegt atbildi |
| `ESC` | Atcelt uzdevumu |

### Level Editor
| Taustiņš | Darbība |
|----------|---------|
| Kreisais peles taustiņš | Likt tile |
| Labais peles taustiņš | Dzēst tile |
| `WASD` vai bultiņas | Kustināt kameru |
| `TAB` | Pārslēgt kategoriju |
| `G` | Ieslēgt režģi |
| `Ctrl+S` | Saglabāt līmeni |
| `Ctrl+N` | Jauns tukšs līmenis |
| `Ctrl+1/2/3` | Pārslēgt starp līmeņiem |

<br>

## Arhitektūra

Projekts izstrādāts pēc objektorientētās programmēšanas principiem ar skaidru atbildību sadalījumu starp klasēm.

### OOP principu izmantošana

| Princips | Pielietojums |
|----------|--------------|
| **Iekapsulēšana** | Visi klases atribūti deklarēti kā privāti, piekļuve nodrošināta caur getter un setter metodēm |
| **Mantošana** | Vairāku līmeņu klašu hierarhijas tile sistēmā un uzdevumu sistēmā |
| **Polimorfisms** | Virtuālās metodes, kas pārdefinētas apakšklasēs ar atšķirīgu uzvedību |
| **Kompozīcija** | Komplekso klasēs (Game, World) tiek izmantoti vienkāršāku klasu objekti |
| **Factory šablons** | Centralizētas funkcijas objektu izveidošanai |

### Klašu hierarhija

```
Tile (bāzes klase)
├── SolidTile          Cietie tile, kas darbojas kā sadursmes objekti
├── PortalTile         Portāli, kas atver programmēšanas uzdevumus
└── HazardTile         Bīstami objekti, kas nogalina spēlētāju

Level (bāzes klase)
├── ConditionLevel     if/else nosacījumu līmenis
├── LoopLevel          for/while ciklu līmenis
└── FunctionLevel      Funkciju līmenis
```

### Tehnoloģijas

**Python 3** kā galvenā programmēšanas valoda nodrošina objektorientētas programmēšanas iespējas un plašu standarta biblioteku.

**pygame-ce** ir modernā pygame versija, kas tiek aktīvi uzturēta. Tā nodrošina grafisko renderēšanu, lietotāja ievades apstrādi un audio atbalstu.

**JSON** formāts tiek izmantots gan uzdevumu datu glabāšanai, gan līmeņu saglabāšanai, gan tile sistēmas konfigurācijai. Šī formāta priekšrocība ir cilvēkam saprotama struktūra un viegla manipulācija.

**CSV** formāts izvēlēts spēlētāju rezultātu glabāšanai tā vienkāršības un saderības ar tabulu programmām dēļ.

<br>

## Spēles darbības princips

Spēlētājs sāk pasaules sākumā un caur platformer mehānikām pārvietojas līdz pirmajam portālam. Pieskaroties portālam, atveras uzdevumu logs ar Python koda fragmentu un jautājumu. Spēlētājam jāanalizē kods un jāievada pareizais rezultāts.

Pēc pareizas atbildes portāls deaktivējas un spēlētājs var doties tālāk uz nākamo. Pēc visu trīs portālu pabeigšanas tiek parādīts uzvaras ekrāns ar kopējo punktu skaitu. Visi rezultāti automātiski saglabājas CSV failā turpmākai analīzei.

<br>

## Izstrādes komanda

| Loma | Dalībnieks |
|------|------------|
| Projekta izstrāde, dizains, UML | Artūrs Skorikovs |

Komandas nosaukums **PORTAL 3** atsaucas uz to, ka Portal 2 jau bija paņemts.

<br>

## Licence

Šis projekts ir licencēts saskaņā ar MIT licenci.

<br>

<div align="center">

**Izstrādāts kā kursa darbs programmēšanas kursā**

</div>
