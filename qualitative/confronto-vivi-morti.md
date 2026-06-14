# Confronto — Progetti DH attivi vs discontinuati

_Sintesi comparativa basata su `report-progetti-vivi.md` (n=14) e `report-progetti-morti.md` (n=12), generati da `analyze_surveys.py`. Campioni piccoli: le percentuali vanno lette come indicative, non inferenziali._

_Le citazioni provengono da **risposte via email** dei responsabili dei progetti (follow-up del questionario), qui **anonimizzate**: rimossi nomi, URL e riferimenti identificativi univoci, conservati concetti e categorie generali. Cfr. anche `patterns-vivi-morti.md`._

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

Una testimonianza (progetto vivo) segnala però un limite di misura: _«i progetti vanno avanti con più tipi di finanziamento nel tempo — prima un finanziamento regionale, poi i contributi di una fondazione, poi fondi personali di ricerca»_ _(anonimizzata)_. La domanda B2 a scelta singola **sottostima la natura sequenziale e "a mosaico"** del finanziamento reale: il dato va letto con questa cautela.

## 3. Il divario tra cause attese e cause reali

Le cause di discontinuazione **attese** dai progetti vivi (D3) non coincidono con quelle **effettivamente riportate** dai progetti morti (D1):

| Causa | Attesa (vivi, D3) | Reale (morti, D1) |
|---|---|---|
| Obsolescenza tecnologica | **64%** (1ª) | 25% |
| Orphaning (abbandono del personale chiave) | 57% (2ª) | 25% |
| Fine del finanziamento senza piano | 43% (3ª) | **75%** (1ª) |
| Ristrutturazione / mancanza di supporto istituzionale | 36% | **50%** (2ª) |

I progetti attivi temono soprattutto la tecnologia; i progetti discontinuati sono morti soprattutto per ragioni economico-istituzionali. Il ranking dei fattori di rischio D2 dei morti lo conferma: in testa supporto istituzionale (3.83), finanziamento (3.75) e assenza di pianificazione (3.58), mentre i fattori tecnici stanno in fondo (bit rot 2.30, tecnologie deprecate 1.92, mancato rinnovo dominio/hosting 1.83).

Due risposte via email illustrano il meccanismo. In un caso, **il pensionamento dei referenti strutturati** (un ordinario e un associato di informatica, un ricercatore senior) nei cinque anni dopo la pubblicazione ha tolto al progetto un referente interno capace di sostenere la richiesta di fondi per l'aggiornamento: _«la macchina è stata spenta; non essendo io in quell'ateneo non sono stato nemmeno informato in anticipo, e la mia richiesta formale al rettorato non ha mai ricevuto risposta»_ _(anonimizzata)_ — pur trattandosi di una piattaforma finanziata da fondi di ateneo, da un fondo nazionale estero e da finanziamenti internazionali, e legata a materiali di rilevante valore patrimoniale. In un altro, la causa è un **passaggio di proprietà societario**: _«dopo l'ultimo passaggio di proprietà dell'azienda e di questo asset il sito è stato chiuso; non me la sono sentita di prenderlo in carico a titolo gratuito»_ _(anonimizzata)_. In entrambi i casi l'innesco è organizzativo, non tecnico.

## 4. Tratti comuni (problemi sistemici)

- **Il finanziatore non chiede sostenibilità**: nessun piano di sostenibilità/gestione dati richiesto nell'83% dei casi (morti) e nel 71% (vivi, con il restante 29% "non lo so" — nessun "sì").
- **Team piccoli e supporto tecnico part-time** in entrambi i gruppi: la manutenzione dipende da poche persone, raramente a tempo pieno.
- **Segnali premonitori poco riconosciuti**: l'83% dei progetti morti dichiara che non c'erano segnali (D4), ma quando indicati riguardano personale in uscita e fine del finanziamento — esattamente le cause reali di morte. Tra i vivi, il 29% riconosce già segnali analoghi (personale in uscita 29%, debito tecnico 14%).
- **Rischio percepito alto anche tra i vivi**: probabilità di future problematiche di mantenimento media 3.50/5, moda 5 (D2 vivi). Il 21% ha già subito episodi di inaccessibilità (attacchi informatici, limiti di spazio, server istituzionali indisponibili, personale precario).

## 5. La morte apparente: muore l'URL, non sempre il progetto

Le risposte via email rivelano un fatto che i dati quantitativi non colgono: **diversi progetti classificati come discontinuati sono, in qualche forma, ancora vivi.** La «morte» rilevata dal controllo di liveness sull'URL (cfr. `archivechecker3.py`) misura la disponibilità del *servizio pubblico*, non la sopravvivenza del *progetto* o dei suoi dati.

| Stato reale (dei 12 progetti "morti" che hanno risposto) | n | Esempi (anonimizzati) |
|---|---|---|
| Confluito in un nuovo progetto finanziato | 2 | prosegue in un nuovo PRIN + infrastruttura CNR; ampliato dopo il grant europeo |
| Ancora online a un altro indirizzo | 1 | sito spostato, nessun reindirizzamento |
| Servizio spento ma codice/dati conservati | 2 | codice su repository pubblico; dati ancora in possesso del responsabile |
| Spento, esito dei dati non noto | 2 | reindirizzamento decaduto; macchina spenta dall'ente |
| Nessun dettaglio sullo stato / NDA | 5 | — |

Almeno **5 dei 12** progetti per cui è arrivata una risposta mostrano sopravvivenza di servizio, dati o codice, o migrazione in nuove iniziative; solo 2 risultano spenti con esito dei dati incerto.

> _«Il progetto non ha mai smesso di essere implementato; senza i fondi europei è stato un lavoro un po' "sotterraneo", e a breve confluirà in un nuovo progetto ampliato. […] è la non-sostenibilità di un sistema basato su progetti a termine.»_ _(anonimizzata)_

**Implicazione per il dataset:** una quota dei «morti» è in realtà migrata, rinominata o ridotta a dati/codice conservati — uno stato intermedio che il binario vivo/morto non rappresenta e che meriterebbe una codifica a sé.

## 6. Sintesi dei pattern

1. La sopravvivenza non dipende dal tipo di progetto ma dalle pratiche: documentazione tecnica (Δ +1.49), figura di manutenzione dedicata (+24 pp) e pianificazione iniziale distinguono i vivi dai morti.
2. I progetti muoiono per soldi e istituzioni, non per tecnologia — ma chi è vivo teme la tecnologia: c'è un disallineamento sistematico nella percezione del rischio.
3. L'hosting istituzionale non protegge: senza impegno formale dell'ente, l'infrastruttura "interna" è il contesto in cui la maggior parte dei progetti è morta.
4. L'assenza di requisiti di sostenibilità da parte dei finanziatori è trasversale ai due gruppi ed è il principale fattore sistemico su cui intervenire.
5. La morte è spesso **apparente**: a livello di URL il servizio è giù, ma dati, codice o l'intero progetto sopravvivono, spesso migrando in nuovi finanziamenti — misurare la discontinuazione sul solo URL la sovrastima.
