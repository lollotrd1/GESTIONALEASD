from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from data_manager import DataManager
import os
import plotly.graph_objs as go
import plotly.utils
import json
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
from flask import send_file

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
dm = DataManager()

# Aggiungi la funzione zip al contesto globale di Jinja2
app.jinja_env.globals.update(zip=zip)

@app.route('/')
def index():
    stats = dm.get_stats_soci()
    soci = dm.get_soci_by_stato(None)  # Ottiene tutti i soci
    tariffe = dm.get_all_quote()
    prodotti_bar = dm.get_all_prodotti_bar()
    return render_template('index.html', stats=stats, soci=soci, tariffe=tariffe, prodotti_bar=prodotti_bar)

@app.route('/soci/<stato>')
def lista_soci(stato):
    soci = dm.get_soci_by_stato(stato if stato != 'tutti' else None)
    stats = dm.get_stats_soci()
    return render_template('soci.html', soci=soci, stats=stats, stato_filtro=stato)


@app.route('/pesca/aggiungi-socio', methods=['POST'])
def aggiungi_socio():
    nome_cognome = request.form.get('nome_cognome')
    quota = request.form.get('quota')
    note = request.form.get('note', '')
    prodotti = request.form.getlist('prodotti[]')
    quantita = request.form.getlist('quantita[]')

    if not nome_cognome:
        flash('Il nome del socio è obbligatorio', 'error')
        return redirect(url_for('index'))

    try:
        # Aggiungi il socio e ottieni l'ID
        socio_id = dm.add_socio(nome_cognome, quota, note)

        if socio_id:
            # Aggiungi i prodotti bar se presenti
            for prod_id, qty in zip(prodotti, quantita):
                if prod_id:  # Skip empty selections
                    dm.add_prodotto_to_socio(socio_id, int(prod_id), int(qty))

            flash('Socio aggiunto con successo!', 'success')
        else:
            flash('Errore durante l\'aggiunta del socio', 'error')
    except Exception as e:
        flash(f'Errore durante l\'aggiunta del socio: {str(e)}', 'error')

    return redirect(url_for('index'))

@app.route('/pesca/quote', methods=['GET'])
def pesca_quote():
    quote = dm.get_all_quote()
    return render_template('quote.html', quote=quote)

@app.route('/pesca/quote/add', methods=['POST'])
def add_quota():
    nome = request.form.get('nome')
    prezzo = float(request.form.get('prezzo', 0))
    tipo = request.form.get('tipo')

    if dm.add_quota(nome, prezzo, tipo):
        flash('Quota aggiunta con successo!', 'success')
    else:
        flash('Errore durante l\'aggiunta della quota', 'error')

    return redirect(url_for('pesca_quote'))

@app.route('/pesca/quote/edit/<int:quota_id>', methods=['POST'])
def edit_quota(quota_id):
    nome = request.form.get('nome')
    prezzo = float(request.form.get('prezzo', 0))
    tipo = request.form.get('tipo')

    if dm.update_quota(quota_id, nome, prezzo, tipo):
        return jsonify({
            'success': True,
            'message': 'Quota aggiornata con successo!'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Errore durante l\'aggiornamento della quota'
        })

@app.route('/pesca/quote/delete/<int:quota_id>', methods=['POST'])
def delete_quota(quota_id):
    if dm.delete_quota(quota_id):
        flash('Quota eliminata con successo!', 'success')
    else:
        flash('Errore durante l\'eliminazione della quota', 'error')

    return redirect(url_for('pesca_quote'))

@app.route('/bar/prodotti')
def bar_prodotti():
    prodotti = dm.get_all_prodotti_bar()
    return render_template('bar_prodotti.html', prodotti=prodotti)

@app.route('/bar/prodotti/add', methods=['POST'])
def add_prodotto_bar():
    nome = request.form.get('nome')
    prezzo = float(request.form.get('prezzo', 0))
    categoria = request.form.get('categoria')

    if dm.add_prodotto_bar(nome, prezzo, categoria):
        flash('Prodotto aggiunto con successo!', 'success')
    else:
        flash('Errore durante l\'aggiunta del prodotto', 'error')

    return redirect(url_for('bar_prodotti'))

@app.route('/bar/prodotti/edit/<int:prodotto_id>', methods=['POST'])
def edit_prodotto_bar(prodotto_id):
    nome = request.form.get('nome')
    prezzo = float(request.form.get('prezzo', 0))
    categoria = request.form.get('categoria')

    if dm.update_prodotto_bar(prodotto_id, nome, prezzo, categoria):
        return jsonify({
            'success': True,
            'message': 'Prodotto aggiornato con successo!'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Errore durante l\'aggiornamento del prodotto'
        })

@app.route('/bar/prodotti/delete/<int:prodotto_id>', methods=['POST'])
def delete_prodotto_bar(prodotto_id):
    if dm.delete_prodotto_bar(prodotto_id):
        flash('Prodotto eliminato con successo!', 'success')
    else:
        flash('Errore durante l\'eliminazione del prodotto', 'error')

    return redirect(url_for('bar_prodotti'))

@app.route('/gestione-socio/')
@app.route('/gestione-socio/<int:socio_id>')
def gestione_socio(socio_id=None):
    soci_attivi = dm.get_soci_by_stato('Attivo')
    quote = dm.get_all_quote()
    prodotti_bar = dm.get_all_prodotti_bar()
    socio_selezionato = None

    if socio_id:
        for socio in soci_attivi:
            if socio['id'] == socio_id:
                socio_selezionato = socio
                break

    return render_template('gestione_socio.html', 
                         soci_attivi=soci_attivi,
                         socio_selezionato=socio_selezionato,
                         quote=quote,
                         prodotti_bar=prodotti_bar)

@app.route('/gestione-socio/<int:socio_id>/update-quota', methods=['POST'])
def update_quota_socio(socio_id):
    quota = request.form.get('quota')
    if dm.update_quota_socio(socio_id, quota):
        flash('Quota aggiornata con successo!', 'success')
    else:
        flash('Errore durante l\'aggiornamento della quota', 'error')
    return redirect(url_for('gestione_socio', socio_id=socio_id))

@app.route('/gestione-socio/<int:socio_id>/update-note', methods=['POST'])
def update_note_socio(socio_id):
    note = request.form.get('note')
    if dm.update_note_socio(socio_id, note):
        flash('Note aggiornate con successo!', 'success')
    else:
        flash('Errore durante l\'aggiornamento delle note', 'error')
    return redirect(url_for('gestione_socio', socio_id=socio_id))

@app.route('/gestione-socio/<int:socio_id>/add-prodotto', methods=['POST'])
def add_prodotto_socio(socio_id):
    try:
        if request.is_json:
            data = request.get_json()
            prodotto_id = data.get('prodotto_id')
            quantita = int(data.get('quantita', 1))
        else:
            prodotto_id = request.form.get('prodotto_id')
            quantita = int(request.form.get('quantita', 1))

        if not prodotto_id:
            response = {'success': False, 'message': 'Prodotto non specificato'}
            return jsonify(response) if request.is_json else redirect(url_for('index'))

        success = dm.add_prodotto_to_socio(socio_id, prodotto_id, quantita)

        if success:
            message = 'Prodotto aggiunto con successo!'
            if not request.is_json:
                flash(message, 'success')
            response = {'success': True, 'message': message}
        else:
            message = 'Errore durante l\'aggiunta del prodotto'
            if not request.is_json:
                flash(message, 'error')
            response = {'success': False, 'message': message}

        return jsonify(response) if request.is_json else redirect(url_for('index'))

    except Exception as e:
        message = f'Errore durante l\'aggiunta del prodotto: {str(e)}'
        if not request.is_json:
            flash(message, 'error')
        return jsonify({'success': False, 'message': message}), 500

@app.route('/gestione-socio/<int:socio_id>/update-stato', methods=['POST'])
def update_stato_socio(socio_id):
    """Aggiorna lo stato di un socio, supporta sia form che JSON requests"""
    try:
        if request.is_json:
            # Per richieste AJAX/Fetch
            data = request.get_json()
            stato = data.get('stato')
        else:
            # Per form submissions tradizionali
            stato = request.form.get('stato')

        if not stato:
            response = {'success': False, 'message': 'Stato non specificato'}
            return jsonify(response) if request.is_json else redirect(url_for('index'))

        success = dm.update_stato_socio(socio_id, stato)

        if success:
            message = 'Stato aggiornato con successo!'
            if not request.is_json:
                flash(message, 'success')
            response = {'success': True, 'message': message}
        else:
            message = 'Errore durante l\'aggiornamento dello stato'
            if not request.is_json:
                flash(message, 'error')
            response = {'success': False, 'message': message}

        return jsonify(response) if request.is_json else redirect(url_for('index'))

    except Exception as e:
        message = f'Errore durante l\'aggiornamento dello stato: {str(e)}'
        if not request.is_json:
            flash(message, 'error')
        return jsonify({'success': False, 'message': message}), 500

@app.route('/report/giornaliero')
def report_giornaliero():
    incassi = dm.get_incassi_giornalieri()

    # Crea il grafico a torta
    labels = list(incassi.keys())
    values = list(incassi.values())

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        textinfo='percent+value',
        hovertemplate="€%{value:.2f}<br>%{percent}<br>%{label}<extra></extra>"
    )])

    fig.update_layout(
        title='Incassi Giornalieri',
        showlegend=True
    )

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    totale = sum(values)

    return render_template('report_giornaliero.html', 
                         graphJSON=graphJSON,
                         incassi=incassi,
                         totale=totale)

@app.route('/report/mensile')
def report_mensile():
    incassi = dm.get_incassi_mensili()

    # Crea il grafico a torta
    labels = list(incassi.keys())
    values = list(incassi.values())

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        textinfo='percent+value',
        hovertemplate="€%{value:.2f}<br>%{percent}<br>%{label}<extra></extra>"
    )])

    fig.update_layout(
        title='Incassi Mensili',
        showlegend=True
    )

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    totale = sum(values)

    return render_template('report_mensile.html', 
                         graphJSON=graphJSON,
                         incassi=incassi,
                         totale=totale)

@app.route('/report/statistiche')
def report_statistiche():
    statistiche = dm.get_statistiche_quote()

    # Crea il grafico a torta
    labels = list(statistiche.keys())
    values = list(statistiche.values())

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        textinfo='percent+value',
        hovertemplate="%{value} soci<br>%{percent}<br>%{label}<extra></extra>"
    )])

    fig.update_layout(
        title='Distribuzione Quote Attive',
        showlegend=True
    )

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    totale = sum(values)

    return render_template('report_statistiche.html', 
                         graphJSON=graphJSON,
                         statistiche=statistiche,
                         totale=totale)

@app.route('/report')
def report_unificato():
    # Recupera i dati per tutti i report
    incassi_giornalieri = dm.get_incassi_giornalieri()
    incassi_mensili = dm.get_incassi_mensili()
    statistiche = dm.get_statistiche_quote()

    # Crea il grafico a torta per incassi giornalieri
    labels_giornalieri = list(incassi_giornalieri.keys())
    values_giornalieri = list(incassi_giornalieri.values())
    fig_giornaliero = go.Figure(data=[go.Pie(
        labels=labels_giornalieri,
        values=values_giornalieri,
        textinfo='percent+value',
        hovertemplate="€%{value:.2f}<br>%{percent}<br>%{label}<extra></extra>"
    )])
    fig_giornaliero.update_layout(
        title='Incassi Giornalieri',
        showlegend=True,
        height=300
    )

    # Crea il grafico a torta per incassi mensili
    labels_mensili = list(incassi_mensili.keys())
    values_mensili = list(incassi_mensili.values())
    fig_mensile = go.Figure(data=[go.Pie(
        labels=labels_mensili,
        values=values_mensili,
        textinfo='percent+value',
        hovertemplate="€%{value:.2f}<br>%{percent}<br>%{label}<extra></extra>"
    )])
    fig_mensile.update_layout(
        title='Incassi Mensili',
        showlegend=True,
        height=300
    )

    # Crea il grafico a torta per le statistiche quote
    labels_quote = list(statistiche.keys())
    values_quote = list(statistiche.values())
    fig_quote = go.Figure(data=[go.Pie(
        labels=labels_quote,
        values=values_quote,
        textinfo='percent+value',
        hovertemplate="%{value} soci<br>%{percent}<br>%{label}<extra></extra>"
    )])
    fig_quote.update_layout(
        title='Distribuzione Quote Attive',
        showlegend=True,
        height=300
    )

    return render_template('report_unificato.html',
                         incassi_giornalieri=incassi_giornalieri,
                         incassi_mensili=incassi_mensili,
                         statistiche=statistiche,
                         totale_giornaliero=sum(incassi_giornalieri.values()),
                         totale_mensile=sum(incassi_mensili.values()),
                         totale_quote=sum(statistiche.values()),
                         graph_giornaliero=json.dumps(fig_giornaliero, cls=plotly.utils.PlotlyJSONEncoder),
                         graph_mensile=json.dumps(fig_mensile, cls=plotly.utils.PlotlyJSONEncoder),
                         graph_quote=json.dumps(fig_quote, cls=plotly.utils.PlotlyJSONEncoder))

@app.route('/eventi')
def eventi():
    eventi = dm.get_all_eventi()
    return render_template('eventi.html', eventi=eventi)

@app.route('/eventi/aggiungi', methods=['POST'])
def aggiungi_evento():
    titolo = request.form.get('titolo')
    data = request.form.get('data')
    ora = request.form.get('ora')
    data_fine = request.form.get('data_fine')
    ora_fine = request.form.get('ora_fine')
    max_partecipanti = request.form.get('max_partecipanti')
    descrizione = request.form.get('descrizione', '')

    if max_partecipanti:
        try:
            max_partecipanti = int(max_partecipanti)
        except ValueError:
            max_partecipanti = None

    evento_id = dm.add_evento(titolo, data, ora, descrizione, data_fine, ora_fine, max_partecipanti)
    if evento_id:
        flash('Evento aggiunto con successo!', 'success')
    else:
        flash('Errore durante l\'aggiunta dell\'evento', 'error')

    return redirect(url_for('eventi'))

@app.route('/eventi/partecipanti/<int:evento_id>')
def get_partecipanti(evento_id):
    """Restituisce l'HTML della lista partecipanti per l'aggiornamento asincrono"""
    eventi = dm.get_all_eventi()
    evento = next((e for e in eventi if e['id'] == evento_id), None)
    if not evento:
        return ''

    return render_template('partecipanti_list.html', evento=evento)

@app.route('/eventi/partecipante/<int:evento_id>', methods=['POST'])
def aggiungi_partecipante(evento_id):
    nome_cognome = request.form.get('nome_cognome')
    quota_versata = 'quota_versata' in request.form

    if not nome_cognome:
        return jsonify({'success': False, 'message': 'Il nome del partecipante è obbligatorio'})

    # Divide il nome e cognome
    parti = nome_cognome.split(' ', 1)
    nome = parti[0]
    cognome = parti[1] if len(parti) > 1 else ''

    if dm.add_partecipante_evento(evento_id, nome, cognome, quota_versata):
        return jsonify({'success': True, 'message': 'Partecipante aggiunto con successo!'})
    else:
        return jsonify({'success': False, 'message': 'Errore durante l\'aggiunta del partecipante'})

@app.route('/eventi/elimina/<int:evento_id>', methods=['POST'])
def elimina_evento(evento_id):
    if dm.delete_evento(evento_id):
        return jsonify({'success': True, 'message': 'Evento eliminato con successo!'})
    else:
        return jsonify({'success': False, 'message': 'Errore durante l\'eliminazione dell\'evento'})

@app.route('/eventi/modifica/<int:evento_id>', methods=['POST'])
def modifica_evento(evento_id):
    titolo = request.form.get('titolo')
    data = request.form.get('data')
    ora = request.form.get('ora')
    data_fine = request.form.get('data_fine')
    ora_fine = request.form.get('ora_fine')
    max_partecipanti = request.form.get('max_partecipanti')
    descrizione = request.form.get('descrizione', '')

    if max_partecipanti:
        try:
            max_partecipanti = int(max_partecipanti)
        except ValueError:
            max_partecipanti = None

    if dm.update_evento(evento_id, titolo, data, ora, descrizione, data_fine, ora_fine, max_partecipanti):
        return jsonify({'success': True, 'message': 'Evento modificato con successo!'})
    else:
        return jsonify({'success': False, 'message': 'Errore durante la modifica dell\'evento'})

@app.route('/eventi/quota/<int:evento_id>/<int:partecipante_id>', methods=['POST'])
def toggle_quota(evento_id, partecipante_id):
    """Toggle lo stato della quota per un partecipante"""
    data = request.get_json()
    quota_versata = data.get('quota_versata', False)

    try:
        conn = dm.get_connection()
        c = conn.cursor()
        c.execute('''
        UPDATE eventi_partecipanti 
        SET quota_versata = %s
        WHERE evento_id = %s AND id = %s
        ''', (quota_versata, evento_id, partecipante_id))
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Stato quota aggiornato con successo!'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Errore durante l\'aggiornamento della quota: {str(e)}'
        })

@app.route('/eventi/contatore/<int:evento_id>')
def get_contatore(evento_id):
    """Restituisce il numero di partecipanti per un evento"""
    eventi = dm.get_all_eventi()
    evento = next((e for e in eventi if e['id'] == evento_id), None)
    if not evento:
        return jsonify({'count': 0})

    return jsonify({
        'count': len(evento['partecipanti_nomi']),
        'max_partecipanti': evento['max_partecipanti']
    })


@app.route('/report/reset/<tipo>', methods=['POST'])
def reset_report(tipo):
    """Reset a specific report type"""
    try:
        conn = dm.get_connection()
        c = conn.cursor()

        if tipo == 'giornaliero':
            # Reset daily income
            c.execute('''
            UPDATE soci 
            SET costo_quota = 0, costo_bar = 0 
            WHERE DATE(inizio_attivita) = CURRENT_DATE
            ''')
        elif tipo == 'mensile':
            # Reset monthly income
            c.execute('''
            UPDATE soci 
            SET costo_quota = 0, costo_bar = 0 
            WHERE DATE_TRUNC('month', inizio_attivita) = DATE_TRUNC('month', CURRENT_DATE)
            ''')
        elif tipo == 'quote':
            # Reset active quotes statistics
            c.execute('''
            UPDATE soci 
            SET tipo_pesca = 'Nessuna'
            WHERE stato != 'Terminato'
            ''')

        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'Report {tipo} resettato con successo!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Errore durante il reset del report: {str(e)}'})

@app.route('/report/download/<tipo>')
def download_report(tipo):
    """Generate and download a PDF report"""
    # Create a buffer for the PDF
    buffer = BytesIO()

    # Create the PDF object
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Add title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )

    if tipo == 'giornaliero':
        title = 'Report Incassi Giornalieri'
        data = dm.get_incassi_giornalieri()
        totale = sum(data.values())
    elif tipo == 'mensile':
        title = 'Report Incassi Mensili'
        data = dm.get_incassi_mensili()
        totale = sum(data.values())
    else:  # quote
        title = 'Report Statistiche Quote'
        data = dm.get_statistiche_quote()
        totale = sum(data.values())

    elements.append(Paragraph(title, title_style))

    # Add date
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=20
    )
    current_date = datetime.now().strftime('%d/%m/%Y %H:%M')
    elements.append(Paragraph(f'Generato il: {current_date}', date_style))
    elements.append(Spacer(1, 20))

    # Create table data
    table_data = [['Tipo', 'Valore']]
    for key, value in data.items():
        if tipo in ['giornaliero', 'mensile']:
            formatted_value = f'€{value:.2f}'
        else:
            formatted_value = f'{value} soci'
        table_data.append([key, formatted_value])

    # Add total row
    if tipo in ['giornaliero', 'mensile']:
        total_text = f'€{totale:.2f}'
    else:
        total_text = f'{totale} soci'
    table_data.append(['Totale', total_text])

    # Create table
    table = Table(table_data, colWidths=[4*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)

    # Build PDF
    doc.build(elements)

    # Prepare response
    buffer.seek(0)
    return send_file(
        buffer,
        download_name=f'report_{tipo}_{datetime.now().strftime("%Y%m%d")}.pdf',
        as_attachment=True,
        mimetype='application/pdf'
    )

@app.route('/api/statistiche')
def api_statistiche():
    """API endpoint per ottenere le statistiche dei soci"""
    try:
        stats = dm.get_stats_soci()
        return jsonify({
            'success': True,
            'attivi': stats.attivi,
            'in_pausa': stats.in_pausa,
            'terminati': stats.terminati
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Errore durante il recupero delle statistiche: {str(e)}'
        }), 500

@app.route('/api/socio/<int:socio_id>/costi')
def api_costi_socio(socio_id):
    """API endpoint per ottenere i costi aggiornati di un socio"""
    try:
        conn = dm.get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT costo_quota, costo_bar
            FROM soci
            WHERE id = %s
        ''', (socio_id,))
        result = c.fetchone()
        conn.close()

        if result:
            costo_quota, costo_bar = result
            return jsonify({
                'success': True,
                'costo_quota': float(costo_quota or 0),
                'costo_bar': float(costo_bar or 0),
                'totale': float((costo_quota or 0) + (costo_bar or 0))
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Socio non trovato'
            }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Errore durante il recupero dei costi: {str(e)}'
        }), 500

@app.route('/elimina-soci', methods=['POST'])
def elimina_soci():
    """Elimina definitivamente i soci selezionati"""
    try:
        data = request.get_json()
        soci_ids = data.get('soci_ids', [])

        if not soci_ids:
            return jsonify({
                'success': False,
                'message': 'Nessun socio selezionato per l\'eliminazione'
            }), 400

        success, message = dm.delete_soci(soci_ids)
        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Errore durante l\'eliminazione: {str(e)}'
        }), 500

@app.route('/api/incassi')
def api_incassi():
    """API endpoint per ottenere il totale degli incassi dei soci terminati"""
    try:
        incassi = dm.get_incassi_giornalieri()
        return jsonify({
            'success': True,
            'Totale': float(incassi.get('Totale', 0)) #Handle case where 'Totale' might be missing
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Errore durante il recupero degli incassi: {str(e)}'
        }), 500

@app.route('/profilo')
def profilo():
    """Pagina del profilo utente"""
    return render_template('profilo.html')

@app.route('/impostazioni')
def impostazioni():
    """Pagina delle impostazioni"""
    return render_template('impostazioni.html')

@app.route('/logout')
def logout():
    """Route per il logout"""
    # TODO: Implementare la logica di logout quando verrà aggiunta l'autenticazione
    flash('Logout effettuato con successo', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Utilizziamo la porta fornita dall'ambiente o 5000 come fallback
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)