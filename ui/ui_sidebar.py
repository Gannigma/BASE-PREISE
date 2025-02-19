# ui_sidebar.py

import streamlit as st
from datetime import date

def get_sidebar_inputs():
    st.sidebar.header("Eingaben & Einstellungen")
    
    # 1) Wertpapier (Yahoo-Kürzel)
    ticker = st.sidebar.text_input(
        label="Wertpapier (Yahoo-Kürzel)",
        value="BTC-USD",
        help="Beispiel: BTC-USD, TSLA, AAPL, etc. (Yahoo Finance Kürzel)"
    )
    
    # 2) Gesuchtes Datum
    analysis_date = st.sidebar.date_input(
        label="Gesuchtes Datum",
        value=date.today(),
        help="Datum für die Analyse (z.B. aktueller Tag oder Vergangenheitsdatum)."
    )
    
    # 3) Suchmodus: hoch oder tief
    mode_choice = st.sidebar.radio(
        label="Suchmodus",
        options=["hoch", "tief"],
        index=0
    )
    
    # 4) Volatilität
    #  Falls du nur "hoch" oder "normal" möchtest, entfernen wir "gering".
    #  Wenn du "gering" doch brauchst, nimm sie einfach wieder rein.
    volatility = st.sidebar.radio(
        label="Volatilität",
        options=["normal", "hoch"],
        index=0
    )
    
    # 5) ATR-Periode (Tage)
    atr_period = st.sidebar.number_input(
        label="ATR-Periode (Tage)",
        value=14,
        min_value=1,
        help="Anzahl Tage zur Berechnung der ATR (Average True Range)."
    )
    
    # 6) Teiler-Auswahl für Vorjahr und Vormonat
    #    Nur 8 oder 16 laut deinen Vorgaben
    vj_divider = st.sidebar.radio(
        label="Teiler Vorjahr",
        options=[8, 16],
        index=1,
        help="Teiler für das Vorjahr (8 oder 16)."
    )
    vm_divider = st.sidebar.radio(
        label="Teiler Vormonat",
        options=[8, 16],
        index=1,
        help="Teiler für den Vormonat (8 oder 16)."
    )
    
    # 7) Großer Rhythmus (z.B. 0,36 bis 3600)
    big_rhythm_options = ["0,36", "3,6", "36", "360", "3600"]
    big_rhythm = st.sidebar.selectbox(
        "Großer Rhythmus",
        options=big_rhythm_options,
        index=3,
        help="Auswahl des großen Teilers: 0,36 / 3,6 / 36 / 360 / 3600"
    )
    
    # 8) Kleiner Teiler – rechnerisch abhängig vom großen Rhythmus
    BASE_SMALL_DIVS = [180.0, 90.0, 45.0, 22.5, 11.25, 5.625]
    try:
        # big_rhythm kommt im Format "0,36" – also erst Komma ersetzen durch Punkt
        factor = float(big_rhythm.replace(',', '.')) / 360.0
    except:
        factor = 1.0
    scaled_divs = [round(d * factor, 4) for d in BASE_SMALL_DIVS]
    small_div = st.sidebar.selectbox(
        "Kleiner Teiler",
        options=scaled_divs,
        index=2,
        help="Skalierter Wert basierend auf dem großen Rhythmus."
    )
    
    # 9) Berechnen-Button
    start_button = st.sidebar.button(
        "Berechnen",
        help="Bitte zuerst alle Eingaben abschließen, dann klicken.")
    st.sidebar.write("DEBUG - start_button =", start_button)

    
    # 10) Dictionary mit allen Eingaben zurückgeben
    return {
        "ticker": ticker,
        "analysis_date": analysis_date,
        "mode_choice": mode_choice,
        "volatility": volatility,
        "atr_period": atr_period,
        "vj_divider": vj_divider,
        "vm_divider": vm_divider,
        "big_rhythm": big_rhythm,
        "small_div": small_div,
        "start_button": start_button
    }
