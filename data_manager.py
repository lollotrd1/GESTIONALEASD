import os
import psycopg2
from datetime import datetime
from psycopg2.extras import DictCursor

class DataManager:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        self.init_db()

    def get_connection(self):
        return psycopg2.connect(self.db_url)

    def init_db(self):
        """Inizializza il database con le tabelle necessarie"""
        conn = self.get_connection()
        c = conn.cursor()

        # Tabella soci con nuovi campi
        c.execute('''
        CREATE TABLE IF NOT EXISTS soci (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            cognome VARCHAR(255) NOT NULL,
            tipo_pesca VARCHAR(255) NOT NULL,
            stato VARCHAR(50) NOT NULL,
            inizio_attivita TIMESTAMP,
            costo_quota DECIMAL(10,2) DEFAULT 0,
            costo_bar DECIMAL(10,2) DEFAULT 0,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Aggiunta colonne se non esistono
        try:
            c.execute('''
            ALTER TABLE soci 
            ADD COLUMN IF NOT EXISTS costo_quota DECIMAL(10,2) DEFAULT 0,
            ADD COLUMN IF NOT EXISTS costo_bar DECIMAL(10,2) DEFAULT 0
            ''')
        except psycopg2.Error:
            pass

        # Tabella tariffe (unica tabella per le tariffe)
        c.execute('''
        CREATE TABLE IF NOT EXISTS tariffe (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            prezzo DECIMAL(10,2) NOT NULL,
            tipo VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Tabella prodotti_bar
        c.execute('''
        CREATE TABLE IF NOT EXISTS prodotti_bar (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            prezzo DECIMAL(10,2) NOT NULL,
            categoria VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Tabella eventi
        c.execute('''
        CREATE TABLE IF NOT EXISTS eventi (
            id SERIAL PRIMARY KEY,
            titolo VARCHAR(255) NOT NULL,
            data DATE NOT NULL,
            ora TIME NOT NULL,
            descrizione TEXT,
            data_fine DATE,
            ora_fine TIME,
            max_partecipanti INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Tabella eventi_partecipanti con i nuovi campi
        c.execute('''
        CREATE TABLE IF NOT EXISTS eventi_partecipanti (
            id SERIAL PRIMARY KEY,
            evento_id INTEGER REFERENCES eventi(id) ON DELETE CASCADE,
            nome VARCHAR(255) NOT NULL,
            cognome VARCHAR(255) NOT NULL,
            quota_versata BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        conn.commit()
        conn.close()

    def get_all_quote(self):
        """Recupera tutte le tariffe"""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM tariffe ORDER BY tipo, nome')
        tariffe = c.fetchall()
        conn.close()
        return tariffe

    def add_quota(self, nome, prezzo, tipo):
        """Aggiunge una nuova tariffa"""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            c.execute('''
            INSERT INTO tariffe (nome, prezzo, tipo)
            VALUES (%s, %s, %s)
            ''', (nome, prezzo, tipo))
            conn.commit()
            return True
        except psycopg2.Error:
            return False
        finally:
            conn.close()

    def update_quota(self, quota_id, nome, prezzo, tipo):
        """Aggiorna una tariffa esistente"""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            c.execute('''
            UPDATE tariffe 
            SET nome = %s, prezzo = %s, tipo = %s
            WHERE id = %s
            ''', (nome, prezzo, tipo, quota_id))
            conn.commit()
            return True
        except psycopg2.Error:
            return False
        finally:
            conn.close()

    def delete_quota(self, quota_id):
        """Elimina una tariffa"""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            c.execute('DELETE FROM tariffe WHERE id = %s', (quota_id,))
            conn.commit()
            return True
        except psycopg2.Error:
            return False
        finally:
            conn.close()

    def get_soci_by_stato(self, stato=None):
        """Recupera i soci filtrati per stato"""
        conn = self.get_connection()
        c = conn.cursor(cursor_factory=DictCursor)
        try:
            if stato:
                c.execute('''
                SELECT * FROM soci
                WHERE stato = %s
                ORDER BY nome, cognome
                ''', (stato,))
            else:
                c.execute('''
                SELECT * FROM soci
                ORDER BY nome, cognome
                ''')

            soci = []
            for row in c.fetchall():
                socio = dict(row)
                soci.append(socio)
            return soci
        except psycopg2.Error as e:
            print(f"Errore nel recupero dei soci: {e}")
            return []
        finally:
            conn.close()

    def get_stats_soci(self):
        """Recupera le statistiche dei soci"""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            stats = {
                'attivi': 0,
                'in_pausa': 0,
                'terminati': 0,
                'totale': 0
            }

            c.execute('''
            SELECT stato, COUNT(*) as count
            FROM soci
            GROUP BY stato
            ''')

            for stato, count in c.fetchall():
                if stato == 'Attivo':
                    stats['attivi'] = count
                elif stato == 'In Pausa':
                    stats['in_pausa'] = count
                elif stato == 'Terminato':
                    stats['terminati'] = count
                stats['totale'] += count

            return stats
        except psycopg2.Error as e:
            print(f"Errore nel recupero delle statistiche: {e}")
            return {'attivi': 0, 'in_pausa': 0, 'terminati': 0, 'totale': 0}
        finally:
            conn.close()

    def add_socio(self, nome_cognome, quota, note='', stato='Attivo'):
        """Aggiunge un nuovo socio e ritorna il suo ID"""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            nome, cognome = nome_cognome.split(' ', 1) if ' ' in nome_cognome else (nome_cognome, '')

            # Recupera il prezzo della quota selezionata solo se è stata selezionata una quota
            costo_quota = 0
            if quota:
                c.execute('SELECT prezzo FROM tariffe WHERE nome = %s', (quota,))
                result = c.fetchone()
                if result:
                    costo_quota = result[0]

            c.execute('''
            INSERT INTO soci (nome, cognome, tipo_pesca, stato, note, inizio_attivita, costo_quota, costo_bar)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s)
            RETURNING id
            ''', (nome, cognome, quota or 'Nessuna', stato, note, costo_quota, 0))

            socio_id = c.fetchone()[0]
            conn.commit()
            return socio_id
        except psycopg2.Error as e:
            print(f"Errore nell'aggiunta del socio: {e}")
            return None
        finally:
            conn.close()

    def get_all_prodotti_bar(self):
        """Recupera tutti i prodotti del bar"""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM prodotti_bar ORDER BY categoria, nome')
        prodotti = c.fetchall()
        conn.close()
        return prodotti

    def add_prodotto_bar(self, nome, prezzo, categoria):
        """Aggiunge un nuovo prodotto al bar"""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            c.execute('''
            INSERT INTO prodotti_bar (nome, prezzo, categoria)
            VALUES (%s, %s, %s)
            ''', (nome, prezzo, categoria))
            conn.commit()
            return True
        except psycopg2.Error:
            return False
        finally:
            conn.close()

    def update_prodotto_bar(self, prodotto_id, nome, prezzo, categoria):
        """Aggiorna un prodotto del bar esistente"""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            c.execute('''
            UPDATE prodotti_bar 
            SET nome = %s, prezzo = %s, categoria = %s
            WHERE id = %s
            ''', (nome, prezzo, categoria, prodotto_id))
            conn.commit()
            return True
        except psycopg2.Error:
            return False
        finally:
            conn.close()

    def delete_prodotto_bar(self, prodotto_id):
        """Elimina un prodotto del bar"""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            c.execute('DELETE FROM prodotti_bar WHERE id = %s', (prodotto_id,))
            conn.commit()
            return True
        except psycopg2.Error:
            return False
        finally:
            conn.close()

    def update_quota_socio(self, socio_id, quota):
        """Aggiorna la quota di un socio"""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            # Recupera il prezzo della quota
            c.execute('SELECT prezzo FROM tariffe WHERE nome = %s', (quota,))
            result = c.fetchone()
            costo_quota = result[0] if result else 0

            c.execute('''
            UPDATE soci 
            SET tipo_pesca = %s, costo_quota = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            ''', (quota, costo_quota, socio_id))
            conn.commit()
            return True
        except psycopg2.Error as e:
            print(f"Errore nell'aggiornamento della quota: {e}")
            return False
        finally:
            conn.close()

    def update_note_socio(self, socio_id, note):
        """Aggiorna le note di un socio"""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            c.execute('''
            UPDATE soci 
            SET note = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            ''', (note, socio_id))
            conn.commit()
            return True
        except psycopg2.Error as e:
            print(f"Errore nell'aggiornamento delle note: {e}")
            return False
        finally:
            conn.close()

    def add_prodotto_to_socio(self, socio_id, prodotto_id, quantita=1):
        """Aggiunge un prodotto al conto bar di un socio"""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            # Recupera il prezzo del prodotto
            c.execute('SELECT prezzo FROM prodotti_bar WHERE id = %s', (prodotto_id,))
            result = c.fetchone()
            if not result:
                return False

            prezzo_totale = result[0] * quantita

            # Aggiorna il costo bar del socio
            c.execute('''
            UPDATE soci 
            SET costo_bar = costo_bar + %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            ''', (prezzo_totale, socio_id))

            conn.commit()
            return True
        except psycopg2.Error as e:
            print(f"Errore nell'aggiunta del prodotto: {e}")
            return False
        finally:
            conn.close()

    def update_stato_socio(self, socio_id, stato):
        """Aggiorna lo stato di un socio"""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            c.execute('''
            UPDATE soci 
            SET stato = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            ''', (stato, socio_id))
            conn.commit()
            return True
        except psycopg2.Error as e:
            print(f"Errore nell'aggiornamento dello stato: {e}")
            return False
        finally:
            conn.close()

    def get_incassi_giornalieri(self):
        """Recupera gli incassi totali dei soci terminati"""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            c.execute('''
            SELECT 
                COALESCE(SUM(costo_quota + costo_bar), 0) as totale_incassi
            FROM soci 
            WHERE stato = 'Terminato'
            ''')
            result = c.fetchone()
            return {
                'Totale': float(result[0]) if result[0] is not None else 0.0
            }
        except psycopg2.Error as e:
            print(f"Errore nel recupero degli incassi giornalieri: {e}")
            return {'Totale': 0}
        finally:
            conn.close()

    def get_incassi_mensili(self):
        """Recupera gli incassi mensili divisi per tipo"""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            c.execute('''
            SELECT 
                COALESCE(SUM(costo_quota), 0) as totale_quote,
                COALESCE(SUM(costo_bar), 0) as totale_bar
            FROM soci 
            WHERE DATE_TRUNC('month', inizio_attivita) = DATE_TRUNC('month', CURRENT_DATE)
            ''')
            result = c.fetchone()
            return {
                'Quote': float(result[0]),
                'Bar': float(result[1])
            }
        except psycopg2.Error as e:
            print(f"Errore nel recupero degli incassi mensili: {e}")
            return {'Quote': 0, 'Bar': 0}
        finally:
            conn.close()

    def get_statistiche_quote(self):
        """Recupera le statistiche sull'utilizzo delle quote"""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            c.execute('''
            SELECT tipo_pesca, COUNT(*) as count
            FROM soci 
            WHERE stato != 'Terminato'
            GROUP BY tipo_pesca
            ''')
            result = c.fetchall()
            return {row[0]: row[1] for row in result}
        except psycopg2.Error as e:
            print(f"Errore nel recupero delle statistiche quote: {e}")
            return {}
        finally:
            conn.close()

    def get_all_eventi(self):
        """Recupera tutti gli eventi con i loro partecipanti"""
        conn = self.get_connection()
        c = conn.cursor(cursor_factory=DictCursor)
        try:
            # Prima recupera tutti gli eventi
            c.execute('''
            SELECT e.* FROM eventi e
            ORDER BY e.data ASC, e.ora ASC
            ''')

            eventi = []
            for row in c.fetchall():
                evento = dict(row)

                # Per ogni evento, recupera i suoi partecipanti
                c.execute('''
                SELECT id, nome, cognome, quota_versata 
                FROM eventi_partecipanti 
                WHERE evento_id = %s
                ''', (evento['id'],))

                partecipanti = c.fetchall()

                # Inizializza le liste per i partecipanti
                evento['partecipanti_ids'] = []
                evento['partecipanti_nomi'] = []
                evento['partecipanti_quote'] = []

                # Aggiungi i dettagli di ogni partecipante
                for p in partecipanti:
                    evento['partecipanti_ids'].append(p['id'])
                    evento['partecipanti_nomi'].append(f"{p['nome']} {p['cognome']}")
                    evento['partecipanti_quote'].append(p['quota_versata'])

                eventi.append(evento)

            return eventi
        except psycopg2.Error as e:
            print(f"Errore nel recupero degli eventi: {e}")
            return []
        finally:
            conn.close()

    def add_evento(self, titolo, data, ora, descrizione='', data_fine=None, ora_fine=None, max_partecipanti=None):
        """Aggiunge un nuovo evento"""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            c.execute('''
            INSERT INTO eventi (titolo, data, ora, descrizione, data_fine, ora_fine, max_partecipanti)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            ''', (titolo, data, ora, descrizione, data_fine, ora_fine, max_partecipanti))
            evento_id = c.fetchone()[0]
            conn.commit()
            return evento_id
        except psycopg2.Error as e:
            print(f"Errore nell'aggiunta dell'evento: {e}")
            return None
        finally:
            conn.close()

    def add_partecipante_evento(self, evento_id, nome, cognome, quota_versata):
        """Aggiunge un partecipante a un evento"""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            c.execute('''
            INSERT INTO eventi_partecipanti (evento_id, nome, cognome, quota_versata)
            VALUES (%s, %s, %s, %s)
            ''', (evento_id, nome, cognome, quota_versata))
            conn.commit()
            return True
        except psycopg2.Error as e:
            print(f"Errore nell'aggiunta del partecipante: {e}")
            return False
        finally:
            conn.close()

    def delete_evento(self, evento_id):
        """Elimina un evento"""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            c.execute('DELETE FROM eventi WHERE id = %s', (evento_id,))
            conn.commit()
            return True
        except psycopg2.Error as e:
            print(f"Errore nell'eliminazione dell'evento: {e}")
            return False
        finally:
            conn.close()

    def update_evento(self, evento_id, titolo, data, ora, descrizione, data_fine=None, ora_fine=None, max_partecipanti=None):
        """Aggiorna un evento esistente"""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            c.execute('''
            UPDATE eventi 
            SET titolo = %s, data = %s, ora = %s, descrizione = %s, 
                data_fine = %s, ora_fine = %s, max_partecipanti = %s
            WHERE id = %s
            ''', (titolo, data, ora, descrizione, data_fine, ora_fine, max_partecipanti, evento_id))
            conn.commit()
            return True
        except psycopg2.Error as e:
            print(f"Errore nell'aggiornamento dell'evento: {e}")
            return False
        finally:
            conn.close()

    def delete_soci(self, soci_ids):
        """Elimina definitivamente i soci specificati se sono in stato Terminato"""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            # Converte gli ID in una lista di interi
            soci_ids = [int(id) for id in soci_ids]

            # Verifica che tutti i soci siano in stato Terminato
            c.execute('''
            SELECT COUNT(*) 
            FROM soci 
            WHERE id = ANY(%s) AND stato != 'Terminato'
            ''', (soci_ids,))

            non_terminati = c.fetchone()[0]
            if non_terminati > 0:
                return False, "Possono essere eliminati solo i soci con stato Terminato"

            # Elimina i soci
            c.execute('DELETE FROM soci WHERE id = ANY(%s)', (soci_ids,))
            conn.commit()
            return True, "Soci eliminati con successo"
        except psycopg2.Error as e:
            print(f"Errore nell'eliminazione dei soci: {e}")
            return False, f"Errore durante l'eliminazione: {str(e)}"
        finally:
            conn.close()