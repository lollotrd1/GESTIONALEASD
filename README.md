# Gestionale Associazione Sportiva

Sistema di gestione completo per associazioni sportive, progettato per semplificare la gestione dei soci, eventi e attività amministrative.

## Funzionalità Principali

- 👥 **Gestione Soci**
  - Registrazione e gestione anagrafica
  - Gestione quote associative
  - Monitoraggio attività

- 🎫 **Gestione Quote**
  - Definizione tipologie quote
  - Tracciamento pagamenti
  - Gestione rinnovi

- 📅 **Gestione Eventi**
  - Creazione e gestione eventi
  - Registrazione partecipanti
  - Gestione quote evento

- 🏪 **Gestione Bar**
  - Catalogo prodotti
  - Gestione ordini
  - Tracciamento consumi

- 📊 **Report e Statistiche**
  - Report giornalieri
  - Statistiche mensili
  - Analisi dati

## Tecnologie Utilizzate

- Backend: Python Flask
- Database: PostgreSQL
- Frontend: Bootstrap, JavaScript
- Deployment: Replit

## Requisiti di Sistema

- Python 3.11+
- PostgreSQL 16+
- Browser web moderno

## Installazione

1. Clona il repository:
```bash
git clone https://github.com/lollotrd1/GESTIONALEASD.git
cd GESTIONALEASD
```

2. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

3. Configura le variabili d'ambiente:
Crea un file `.env` con:
```
DATABASE_URL=postgresql://...
```

4. Inizializza il database:
```bash
flask db upgrade
```

5. Avvia l'applicazione:
```bash
python main.py
```

## Struttura del Progetto

```
GESTIONALEASD/
├── templates/          # Template HTML
├── static/            # File statici (CSS, JS)
├── migrations/        # Migrazioni database
├── main.py           # App principale
└── data_manager.py   # Gestione dati
```

## Contribuire

1. Fai un fork del repository
2. Crea un branch per la tua feature (`git checkout -b feature/AmazingFeature`)
3. Commita i tuoi cambiamenti (`git commit -m 'Add some AmazingFeature'`)
4. Pusha al branch (`git push origin feature/AmazingFeature`)
5. Apri una Pull Request

## Licenza

Distribuito sotto licenza MIT. Vedi `LICENSE` per maggiori informazioni.

## Contatti

Lorenzo - [@lollotrd1](https://github.com/lollotrd1)

Link Progetto: [https://github.com/lollotrd1/GESTIONALEASD](https://github.com/lollotrd1/GESTIONALEASD)
