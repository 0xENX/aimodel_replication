# Occupazione per eta: fonti e metodo

Ricerca e download: 10 ottobre 2026. Il progetto distingue dati osservati,
calibrazione parziale e ipotesi di scenario; non stima ancora effetti causali AI.

## Fonti gia importate

### Eurostat, EU Labour Force Survey

- [Stock per eta, lfsa_pganws](https://ec.europa.eu/eurostat/databrowser/view/lfsa_pganws/default/table): Italia e UE-27, 2019-2025 archiviati, nei grafici solo 2024-2025, sesso totale, cittadinanza totale. Stock di popolazione, forza lavoro, occupati, disoccupati, inattivi in migliaia di persone.
- [Metodologia LFS](https://ec.europa.eu/eurostat/cache/metadata/en/employ_simslfs2_rs.htm): occupati e disoccupati costituiscono la forza lavoro; inattivi esclusi. Unemployment/population e unemployment/labour force sono indicatori differenti.
- [Transizioni lfsi_long_q](https://ec.europa.eu/eurostat/databrowser/view/lfsi_long_q/default/table): Italia/UE, trimestri 2024-2025, transizioni fra occupazione, disoccupazione, inattivita. I dati scaricati NON hanno una dimensione eta. Le tabelle sperimentali piu dettagliate e i microdati vanno esplorati separatamente.
- [Metodologia transizioni](https://ec.europa.eu/eurostat/cache/metadata/EN/lfsi_long_esms.htm): flussi fra stati non equivalgono alle assunzioni amministrative; un cambio datore di lavoro puo rimanere EMP_EMP. Non convertire un tasso trimestrale in annuale moltiplicandolo per quattro.

Le quattro fasce vengono costruite dai gruppi quinquennali: somma dei numeratori e
denominatori, poi rapporto. Celle mancanti causano un errore; non sono zeri.
I flag originali sono conservati; la revisione LFS nel 2021 richiede cautela nei confronti temporali.

Nel profilo opzionale `employment_eu_proxy.json`, solo la struttura iniziale ADV
e parzialmente ancorata all'UE-27 2025: quote di popolazione e partecipazione;
forma della disoccupazione per fascia, riscalata al 5% aggregato originale.
I singoli anni dentro ciascun gruppo di cinque anni sono inizialmente uniformi.
Questo e un PROXY, non una calibrazione completa delle economie avanzate o dell'Italia.
EME/LIC restano assunzioni, cosi come probabilita di assunzione, turnover, ricollocamento
e scoraggiamento. Nessun coefficiente causale AI e ricavato da Eurostat.

### Stanford Digital Economy Lab / ADP

[Canaries Dashboard](https://digitaleconomy.stanford.edu/project/indicators/canaries-dashboard/)
pubblica ZIP scaricabili con CSV e dizionari. Sono stati archiviati gli indici per
esposizione, eta x esposizione, eta aggregata, composizione del campione,
sviluppatori software e assistenza clienti. Vintage: 17 settembre 2026;
ultima osservazione degli indici: agosto 2026. Base della fonte: novembre 2022 = 100.

**Anni pesati.** Le serie complete restano nei grafici, nel report e nel libro. Per leggere
l'effetto dell'AI ogni variazione pesa secondo il suo anno: 2026 e 2025 100%, 2024 50%, 2023 5%,
2022 1% (mensile per Stanford/ADP, annuale per Eurostat; `observed_weights.py`). Il 2022 e il 2023
risentono delle assunzioni eccessive del dopo-Covid e del rialzo dei tassi. Con questi pesi i 22-25enni
nelle professioni piu esposte calano del 4,2% l'anno contro lo 0,3% dei meno esposti; in Italia
l'occupazione dei 15-24enni scende di 1,35 punti l'anno (UE 0,32). I file originali restano archiviati
senza modifiche. Le serie storiche lunghe usate per costruire il mondo senza AI (per esempio la quota
del lavoro ILO 2004-2024) restano: servono come termine di confronto, non misurano l'effetto dell'AI.

Gli indici per eta usano 22-25, 26-30, 31-34, 35-40, 41-49, 50+; questi gruppi
NON sono ricostruibili esattamente nelle quattro fasce del modello. I grafici
osservati conservano quindi la classificazione originale. I dati non consentono
da soli di identificare una probabilita causale di perdita del lavoro o un hazard
di assunzione. Campione bilanciato ADP: non rappresenta l'intero mercato USA e
non include tutte le entrate e uscite di imprese. Importante confronto empirico,
non parametro da estendere automaticamente a tutti i paesi.

## Fonti utili identificate, non ancora importate

| Fonte | Cosa puo aggiungere | Accesso / limiti |
| --- | --- | --- |
| [ILOSTAT](https://ilostat.ilo.org/data/) e [Global Employment Trends for Youth 2026](https://ilostat.ilo.org/dataviz/getyouth/) | Occupazione e partecipazione per eta; catalogo di occupazione per eta ed esposizione GenAI; aggregati per reddito | Dati pubblici e download. Giovani 15-24 negli aggregati, spesso 15-29 nei dettagli nazionali; stime ILO anche imputate, distinte da osservazioni |
| [ILO / NASK, indice GenAI 2025](https://www.ilo.org/publications/generative-ai-and-jobs-refined-global-index-occupational-exposure) | Esposizione per professione ISCO, da incrociare con eta | Esposizione tecnica non equivale a sostituzione effettiva; occorre ponte fra classificazioni |
| [INPS, Osservatorio mercato del lavoro](https://servizi2.inps.it/servizi/osservatoristatistici/14) e [report XLS/PDF](https://www.inps.it/it/it/dati-e-bilanci/osservatori-statistici-e-altre-statistiche/report-cartaceo.html) | Assunzioni, trasformazioni, cessazioni, apprendistato per approfondimento italiano | Rapporti di lavoro, possibili episodi multipli per persona; verificare classificazione eta e perimetro privato |
| [EU-LFS microdati](https://ec.europa.eu/eurostat/en/web/microdata/collections-research/european-union-labour-force-survey) | Eta x professione x istruzione, flussi e controlli | Accesso scientifico richiede ente/progetto approvato; non e stato richiesto |
| [Humlum / Vestergaard, NBER 33777](https://www.nber.org/papers/w33777) | Adozione AI collegata a registri amministrativi danesi; confronto europeo | Studio di breve periodo e contesto danese; non estrapolare automaticamente a 2046 |
| [OECD, AI e domanda di competenze](https://www.oecd.org/en/publications/artificial-intelligence-and-the-changing-demand-for-skills-in-the-labour-market_88684e36-en.html) | Cambiamento delle competenze negli annunci; vincoli alla riconversione | Annunci e occupati sono grandezze differenti; microdati possono essere proprietari |

## Architettura e assunzioni

Il modello macroeconomico v2 e preservato. Il nuovo modulo occupazionale e un
satellite collegato in UNA direzione: domanda macro -> flussi per eta. I risultati
di occupazione del satellite non alimentano ancora salari, redditi, PIL o finanza pubblica.
Non presentare dunque i vecchi dati fiscali come risultati della nuova occupazione.

Stati per singolo anno d'eta 15..64: occupati E, cercatori del primo lavoro F,
disoccupati gia occupati U, scoraggiati del primo lavoro DF e scoraggiati gia occupati DU.
Ogni anno le persone passano all'eta successiva; a 65 anni escono dal perimetro
(ipotesi di uscita, non pensionamenti osservati). Nuovi ingressi a 15 anni.
La popolazione e riscalata a ogni anno per mantenere l'offerta POTENZIALE regionale
coerente con la demografia v2: fattore residuo demografico, non previsione UN per singola eta.

Identita: offerta attiva L = E+F+U; offerta potenziale P* = L+DF+DU.
F e U si spostano nello scoraggiamento e possono tornare a cercare; istruzione,
NEET e disponibilita effettiva al lavoro non sono modellati separatamente.
Gli stati di ricerca sono quindi proxy di disoccupazione: nessuna equivalenza
perfetta con tutte le condizioni della definizione statistica ILO.

La domanda aggregata D arriva da `economy.py`; la sua distribuzione per eta
segue pesi di offerta potenziale e vulnerabilita, normalizzati in modo che
la somma per eta corrisponda alla domanda macro. La domanda per eta rappresenta
capacita di posti accessibili, NON preferenze discriminatorie dei datori di lavoro
misurate nei dati. Il matching avviene dentro la fascia; la mobilita tra fasce
e solo l'invecchiamento. Le difficolta di matching sono assunzioni e possono
sovrastimare le rigidita: servono dati su competenze/professioni per migliorarle.

Flussi: separazioni ordinarie, tagli quando i posti richiesti sono inferiori
agli occupati rimasti, assunzioni limitate da posti e probabilita di ingresso,
ricollocamento, scoraggiamento e ritorno alla ricerca. La contabilita dei flussi
e verificata a ogni anno. Un anno contiene al massimo un episodio di assunzione
modellato per persona: non confrontare direttamente con conteggi INPS di contratti.

Sono confrontati quattro scenari senza assegnare loro probabilita:
ipotesi originali, compensazione efficace, riconversione lenta, sostituzione persistente.
Cambiano intervalli di creazione nuovi task, ritardi, elasticita salariale,
automazione e matching. Sono scenari di stress espliciti, non risultati stimati
dagli studi scaricati. Le differenze sono calcolate tra coppie con stessa estrazione
e stesso matching di base; l'effetto del matching piu lento senza AI non e attribuito all'AI.

## Prossima calibrazione empirica

1. Definire regioni/country mapping coerente con IMF e ILO: non usare EU come ADV senza etichetta.
2. Importare ILOSTAT per eta e classe di reddito, separando fonti nazionali e stime imputate.
3. Collegare professioni ISCO/SOC all'esposizione ILO; non stimare esposizione dalla sola eta.
4. Stimare hazards di ingresso/uscita e ricollocamento da microdati o flussi con fasce disponibili.
5. Validare fuori campione e separare ciclo economico, demografia, tassi di interesse ed effetto AI.
6. Integrare il feedback dell'occupazione nel modello macro, con nuova verifica contabile e validazione.
   (Versione 3.1: realizzato come esperimento, vedi sotto. La validazione empirica resta da fare.)

## Versione 3.1: scelte di metodo

### Taratura di coerenza

Senza taratura il mondo senza AI del modulo per eta si allontanava dalla disoccupazione
strutturale del modello macro: nelle economie avanzate saliva a circa 7% nello scenario di
riferimento e 10% nella riconversione lenta, contro il 5% del modello macro. La causa sono le
probabilita di assunzione, ipotizzate e non tarate: posti vacanti e disoccupazione crescevano
insieme anche senza AI. `calibrate_consistency.py` sceglie per ogni regione un fattore unico sulle
due probabilita di assunzione (primo ingresso e rientro), cosi che nel mondo senza AI dello
scenario di riferimento, a parametri centrali, la disoccupazione attiva media 2027-2046 sia uguale
a u* (5%, 5,5%, 6%). Fattori ottenuti: 1,375 ADV, 1,295 EME, 1,295 LIC. E una condizione di
coerenza fra i due modelli, non una stima. Effetto: nello scenario di riferimento i risultati
cambiano poco; negli scenari di stress l'effetto dell'AI sull'ingresso dei giovani diventa piu
grande, perche il confronto non attribuisce piu a entrambi i mondi un mercato gia inceppato.

### Collegamento a due vie

`aimodel/core/coupled.py`. La disoccupazione entra nel modello macro in due punti: la curva dei
salari (termine di Phillips) e il costo dei sussidi. Il tasso passato al modello macro e
1 - occupati / offerta potenziale del modulo per eta, la stessa definizione del modello macro, che
non distingue gli scoraggiati: chi smette di cercare conta ancora come capacita inutilizzata per i
salari e per il costo dei sussidi. E un'ipotesi; contare solo i cercatori attivi ridurrebbe la
pressione sui salari e la spesa. I due mondi appaiati sono collegati allo stesso modo e risolti per
iterazione sull'intera traiettoria fino a una variazione massima inferiore a 1e-9. L'identita
contabile resta verificata alla precisione numerica. Il reddito da lavoro aggregato resta
determinato dal contenuto di lavoro dei compiti (quota del lavoro): il collegamento cambia salari,
domanda di lavoro e sussidi, non la ripartizione fra lavoro e capitale.

### Politiche d'ingresso a parita di costo

Tre politiche costano ogni anno, dal 2027 e in ogni regione, lo 0,7% del PIL: il costo del
sostegno al reddito nel report. Si applicano in entrambi i mondi appaiati; il loro costo NON
torna nel modello macro (collegamento a una via).

- Posti pubblici: posti aggiuntivi = costo / salario, distribuiti per eta come l'offerta potenziale.
- Incentivo all'occupazione giovanile: contributo pari al 50% del salario annuo (ipotesi) per
  lavoratori 15-34; i posti aggiuntivi sono quelli finanziati meno quelli che sarebbero esistiti
  comunque, quota estratta fra 40% e 80% (ipotesi; la letteratura sugli incentivi alle assunzioni
  trova effetti molto diversi secondo disegno e ciclo).
- Riduzione dell'orario con integrazione salariale: lo Stato sostituisce il 60% delle ore perse
  (aliquota base del Kurzarbeitergeld tedesco); il taglio d'orario che il bilancio permette e
  1 - h = costo / (0,6 x quota del lavoro); la domanda in persone cresce di 1/h. I lavoratori
  perdono il restante 40% delle ore tagliate.

### Sensibilita del modulo per eta

Disegno di Saltelli con N = 4.096, stimatori di Saltelli (primo ordine) e Jansen (totale), solo
NumPy. Percorso macro fisso ai parametri centrali, per isolare le ipotesi del modulo. Fattori:
efficienza dell'incontro 0,5-1,5 (assorbe anche l'estrazione per simulazione), barriera d'ingresso
0-0,9, disallineamento 0-0,8, scoraggiamento aggiuntivo 0-0,07. Gli intervalli coprono i quattro
scenari; non sono stimati.

Non e corretto trattare la forbice crescente negli scenari di stress come prova
che la previsione sia vera: dimostra quali ipotesi possono produrla.

## Previsione per mestiere (capitolo 36, Tabella 65; simulatore)

Un'unica fonte: `aimodel/analysis/occupations.py` scrive `outputs/occupations.json`; la tabella del
libro e il simulatore (`simulator/sync_occupations.py`) leggono quel file. Nessuno scenario alternativo:
un solo insieme di dati e regole, un solo risultato per mestiere. Il test `tests/test_occupations.py`
controlla che modulo, file e simulatore coincidano.

Dati: esposizione Eloundou et al. (Science 2024, misura gamma, valutazione degli esperti); per i lavori
d'ufficio di routine il valore piu alto fra Eloundou e Frey-Osborne (impiegati 0,96, contabili 0,94,
assistenza clienti 0,55); robot Frey-Osborne per i lavori manuali, cinque anni dopo l'AI; calo osservato
Stanford/ADP con anni pesati, come differenza con i coetanei nei lavori meno esposti (assistenza
clienti -1,9% l'anno; sviluppatori nessun calo complessivo, solo sotto i 30 anni). Regole: tipo di lavoro secondo la distinzione FMI fra esposizione e
complementarita (Pizzinelli et al., WP/23/216); curva di adozione del libro (appendice A1); 0,15 ruoli
nuovi dentro il mestiere per ogni compito perso, entro tre anni.

Domanda del mestiere: il lavoro preso dalle macchine non coincide con i posti persi quando la domanda
cresce (infermieri, cuochi, elettricisti). Ogni mestiere tiene il ritmo annuo delle BLS Employment
Projections 2025-35 (pubblicate il 21 settembre 2026, tabella "Occupational projections and
characteristics"), prolungato fino al 2046 e usato per tutte le regioni. Il BLS attribuisce all'AI solo il
calo dei lavori d'ufficio e amministrativi (SOC 43): per impiegati e addetti ai call center la domanda resta
ferma, per non contare due volte l'automazione. Posti = indice di domanda x (1 - lavoro preso da AI e robot
+ ruoli nuovi). La calibrazione sul calo osservato include la domanda. Nel file restano entrambe le misure:
`work` (lavoro preso dalle macchine) e `results` (posti).
