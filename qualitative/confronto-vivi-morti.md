# Confronto — Progetti DH attivi vs discontinuati

_Sintesi comparativa basata su `report-progetti-vivi.md` (n=14) e `report-progetti-morti.md` (n=12), generati da `analyze_surveys.py`. Campioni piccoli: le percentuali vanno lette come indicative, non inferenziali._

## 1. Profilo dei due gruppi

| Dimensione | Morti (n=12) | Vivi (n=14) |
|---|---|---|
| Rispondente prevalente (A1) | PI / Coordinatore (67%) | PI / Coordinatore (43%), più ruoli tecnici e junior |
| Istituzione (A2) | Università (75%) | Università (57%), maggiore varietà (biblioteche, enti locali, GitHub) |
| Avvio (A3) | 67% tra 2011 e 2020, solo 1 dopo il 2020 | 71% dal 2016 in poi |
| Output (B1) | Database (58%), archivi (50%), edizioni (42%) | Database (57%), archivi (43%), edizioni (29%) |
| Team (B3) | 2–5 persone (58%) | 2–5 persone (71%) |
| Figura tecnica (B4) | presente nel 92% (58% part-time) | presente nel 79% (57% part-time) |

I due gruppi sono strutturalmente simili (stessi output, stessi team piccoli, stessa prevalenza universitaria): le differenze rilevanti non stanno nel *cosa* viene prodotto ma nel *come* viene sostenuto.

## 2. Differenze principali

### 2.1 Documentazione tecnica — il divario più ampio (C3)

| Item Likert (1–5) | Morti | Vivi | Δ |
|---|---|---|---|
| C1 — piano di sostenibilità iniziale | 2.67 | 3.14 | +0.47 |
| C2 — discussione fine finanziamento | 3.08 | 3.50 | +0.42 |
| **C3 — documentazione tecnica** | **2.58** | **4.07** | **+1.49** |
| C4 — accessibilità a lungo termine (FAIR) | 2.75 | 3.29 | +0.54 |

I progetti vivi superano i morti su tutti e quattro gli item di sostenibilità, ma il distacco sulla documentazione tecnica (C3) è di un'altra grandezza: mediana 4.5 contro 2.5, moda 5 contro 3.

### 2.2 Figura responsabile della manutenzione (C5)

- Morti: presente nel **33%** dei casi.
- Vivi: presente nel **57%** dei casi.

### 2.3 Infrastruttura di hosting (B5)

- Morti: **83% infrastruttura istituzionale**, 17% esterna.
- Vivi: 43% istituzionale, **43% hosting esterno**, 14% misto.

Dato controintuitivo: l'infrastruttura istituzionale, in teoria più stabile, è associata al gruppo dei progetti discontinuati — coerente con il fatto che la *mancanza di supporto istituzionale* è il primo fattore di rischio percepito dai progetti morti (D2, media 3.83).

### 2.4 Finanziamento (B2)

- Morti: più finanziamento europeo (25% vs 7%) e fonti estere/locali una tantum.
- Vivi: più finanziamento nazionale (36% vs 25%) e più fondi istituzionali ordinari (21% vs 8%); presente anche lavoro volontario.

I progetti vivi poggiano più spesso su fonti ricorrenti o interne; i morti su grant a termine.

## 3. Il divario tra cause attese e cause reali

Le cause di discontinuazione **attese** dai progetti vivi (D3) non coincidono con quelle **effettivamente riportate** dai progetti morti (D1):

| Causa | Attesa (vivi, D3) | Reale (morti, D1) |
|---|---|---|
| Obsolescenza tecnologica | **64%** (1ª) | 25% |
| Orphaning (abbandono del personale chiave) | 57% (2ª) | 25% |
| Fine del finanziamento senza piano | 43% (3ª) | **75%** (1ª) |
| Ristrutturazione / mancanza di supporto istituzionale | 36% | **50%** (2ª) |

I progetti attivi temono soprattutto la tecnologia; i progetti discontinuati sono morti soprattutto per ragioni economico-istituzionali. Il ranking dei fattori di rischio D2 dei morti lo conferma: in testa supporto istituzionale (3.83), finanziamento (3.75) e assenza di pianificazione (3.58), mentre i fattori tecnici stanno in fondo (bit rot 2.30, tecnologie deprecate 1.92, mancato rinnovo dominio/hosting 1.83).

## 4. Tratti comuni (problemi sistemici)

- **Il finanziatore non chiede sostenibilità**: nessun piano di sostenibilità/gestione dati richiesto nell'83% dei casi (morti) e nel 71% (vivi, con il restante 29% "non lo so" — nessun "sì").
- **Team piccoli e supporto tecnico part-time** in entrambi i gruppi: la manutenzione dipende da poche persone, raramente a tempo pieno.
- **Segnali premonitori poco riconosciuti**: l'83% dei progetti morti dichiara che non c'erano segnali (D4), ma quando indicati riguardano personale in uscita e fine del finanziamento — esattamente le cause reali di morte. Tra i vivi, il 29% riconosce già segnali analoghi (personale in uscita 29%, debito tecnico 14%).
- **Rischio percepito alto anche tra i vivi**: probabilità di future problematiche di mantenimento media 3.50/5, moda 5 (D2 vivi). Il 21% ha già subito episodi di inaccessibilità (attacchi informatici, limiti di spazio, server istituzionali indisponibili, personale precario).

## 5. Sintesi dei pattern

1. La sopravvivenza non dipende dal tipo di progetto ma dalle pratiche: documentazione tecnica (Δ +1.49), figura di manutenzione dedicata (+24 pp) e pianificazione iniziale distinguono i vivi dai morti.
2. I progetti muoiono per soldi e istituzioni, non per tecnologia — ma chi è vivo teme la tecnologia: c'è un disallineamento sistematico nella percezione del rischio.
3. L'hosting istituzionale non protegge: senza impegno formale dell'ente, l'infrastruttura "interna" è il contesto in cui la maggior parte dei progetti è morta.
4. L'assenza di requisiti di sostenibilità da parte dei finanziatori è trasversale ai due gruppi ed è il principale fattore sistemico su cui intervenire.
