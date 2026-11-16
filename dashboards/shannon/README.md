# Shannon — stringhe di tessere, entropia e informazione

Nuova pagina del framework physchem-dashboards, route `/shannon`, ordine 5.5: dopo Ehrenfest e prima di Carnot.
Riutilizza `utilities.common_setup`, gli ID con prefisso, Bootstrap e le schede
aggiungibili/eliminabili delle altre dashboard. Non modifica i file esistenti
e non richiede nuove dipendenze.

## Modello concordato

Le singole occorrenze di ogni carattere sono tessere distinguibili, ad esempio
`o₁`, `o₂`, `t₁`, `t₂`. Il macrostato è la stringa visibile **ordinata**.
Per N caratteri con occorrenze nᵢ:

- `W = ∏ nᵢ!`: microstati compatibili con la stringa esatta.
- `S_B = k_B ln W`, con `k_B = 1.380649e-23 J/K`.
- `M = N! / W`: numero di sequenze visibili estraibili dal sacchetto.
- `P = 1/M = W/N!`: probabilità di ottenere la stringa specificata,
  se tutti gli ordini delle tessere etichettate sono equiprobabili.
- `I = log₂ M`: contenuto di informazione in bit della stringa, detto anche sorpresa.

Le barre impilate rappresentano `log₂ W` e `I`; la loro somma è `log₂(N!)`.
Il colore identifica la stringa, il tratteggio distingue il contributo nascosto.
La vista per carattere divide i contributi per N; non elimina tutta la dipendenza
dalla lunghezza nel modello senza reinserimento. La tabella riporta sempre i totali.

Ogni stringa definisce il proprio sacchetto. Le sequenze con le stesse occorrenze
hanno gli stessi risultati anche se l'ordine cambia. Queste quantità non misurano
significato linguistico, funzione biologica, energia metabolica o entropia fisica
completa di una molecola. L'entropia di Shannon della distribuzione delle sequenze
visibili coincide con I nel modello uniforme, ma non va confusa con l'entropia
per singola lettera `-∑pᵢ log₂pᵢ`.

## Interfaccia

- Due schede iniziali: `otto` e `atto`. Aggiunta e rimozione di ulteriori schede.
- Esempi: `AAAAA`, `AMORE`, `TTAGGG`, `TTAGGGTTAGGG`, ecc.
- Limite di 50 punti di codice Unicode nel testo inserito, prima dei filtri;
  validazione anche sul server e controllo del risultato normalizzato.
  Il browser può contare un simbolo fuori dal piano Unicode di base come due
  unità ai fini di `maxLength`, quindi applicare un limite più conservativo.
- Normalizzazione NFC degli accenti; maiuscole, spazi e punteggiatura sono
  distinti per default. Le opzioni comuni possono ignorarli per tutte le schede.
- Simboli definiti come punti di codice, non come grafemi complessi.
- S_B visualizzata sia in unità di k_B sia in J/K; I in bit; W intero esatto.
- Solo microstati compatibili: massimo 24 per scheda, in un pannello espandibile.
  Nessun riordinamento cambia la stringa visibile. Pedici distinguono le tessere.
- Spazi e caratteri di controllo resi visibili nelle tessere.
- Un input vuoto o privo di caratteri dopo i filtri non produce una barra.
  Le altre schede restano utilizzabili.

`model.py` usa soltanto la libreria standard. I fattoriali fino a 50 sono interi
esatti; i logaritmi sono calcolati sui conteggi interi, evitando cancellazioni.
La generazione dei microstati è lazy e si arresta a 24, senza enumerare W o N!
e senza costruire in memoria tutte le permutazioni dei gruppi.

## Installazione nel framework

Copiare l'intera directory `shannon`, compresi i cataloghi `.mo`, in
`Repo/dashboards/shannon`. Avviare normalmente `main.py` e aprire `/shannon`.
Dash Pages scopre automaticamente la pagina: non occorrono modifiche a `main.py`.
Il nome del tab è **Shannon**.

Per l'avvio autonomo, dalla radice Repo:

```bash
python dashboards/shannon/shannon.py
```

Il server standalone ascolta su `127.0.0.1:5000`, usa Bootstrap e riutilizza
la utility della radice tramite un percorso relativo al file, senza symlink.

## Traduzioni

Stringhe inglesi sorgente; cataloghi italiani `.po` e `.mo` inclusi.
La lingua segue il browser tramite il Flask-Babel del framework.
Per aggiornare le traduzioni, dalla directory `shannon`:

```bash
pybabel extract -F babel.cfg -o messages.pot .
pybabel update -i messages.pot -d translations
# Aggiornare il catalogo italiano
pybabel compile -d translations
```

## Verifica del 16 novembre 2026

Sei test numerici e combinatori: riferimenti analitici, confronto indipendente
con enumerazione esaustiva per stringhe corte, invarianza per riordinamento,
Unicode e filtri, input invalidi, 50 caratteri e arresto a 24 microstati.

Sei test di integrazione con l'app multipagina reale: caricamento pagina e CSS,
traduzioni italiane, richieste HTTP alle callback di calcolo, filtri e scala,
aggiunta/eliminazione/nuova aggiunta senza riuso degli ID, scelta degli esempi,
input vuoti e troppo lunghi e confronto senza schede.

Ambiente disponibile verificato: Python 3.12.1, Dash 2.14.2,
dash-bootstrap-components 1.5.0 e Plotly 5.18.0 (`dash_apps`).
Le versioni Dash e Bootstrap sono leggermente diverse da quelle in requirements.txt.
Nessun pacchetto è stato installato o aggiornato.
La verifica visuale nel browser non è stata completata: la sessione browser
ha restituito un errore e il sandbox non permette di aprire socket per un server
locale. Le richieste HTTP sono state simulate dal test client Flask, che esegue
realmente il routing e le callback senza aprire porte di rete. Anche l’avvio
standalone è stato controllato, sostituendo soltanto la chiamata di ascolto del server.

Il percorso originale del repository era montato in sola lettura: l'implementazione
è stata sviluppata e provata su una copia di lavoro. Nessun sorgente originale
è stato modificato.

Per eseguire i test dalla radice Repo nell’ambiente Dash:

```bash
python -m unittest discover -s tests -p "test_shannon*.py" -v
```
