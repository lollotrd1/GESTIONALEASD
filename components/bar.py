import streamlit as st
from data_manager import DataManager

def gestione_bar():
    st.subheader("Gestione Bar")
    
    # Inizializzazione DataManager
    dm = DataManager()
    
    # Layout a colonne
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Menu Prodotti")
        
        # Form per aggiungere nuovo prodotto
        with st.expander("Aggiungi Nuovo Prodotto"):
            with st.form("nuovo_prodotto"):
                nome_prodotto = st.text_input("Nome Prodotto")
                prezzo = st.number_input("Prezzo", min_value=0.0, step=0.5)
                submitted = st.form_submit_button("Aggiungi Prodotto")
                
                if submitted and nome_prodotto and prezzo > 0:
                    # TODO: Implementare l'aggiunta del prodotto
                    st.success(f"Prodotto {nome_prodotto} aggiunto con successo!")
        
        # TODO: Implementare la lista dei prodotti
    
    with col2:
        st.markdown("### Registra Ordine")
        # TODO: Implementare il form per registrare un nuovo ordine
        
        # Selezione socio
        st.selectbox("Seleziona Socio", ["TODO: Lista Soci"])
        
        # Selezione prodotto e quantità
        st.selectbox("Seleziona Prodotto", ["TODO: Lista Prodotti"])
        st.number_input("Quantità", min_value=1, value=1)
        
        if st.button("Registra Ordine"):
            # TODO: Implementare la registrazione dell'ordine
            pass

if __name__ == "__main__":
    gestione_bar()
