import streamlit as st
from datetime import date

def get_sidebar_inputs():
    st.sidebar.header("Eingaben & Einstellungen")

    # 1) Session-State für den Button anlegen, damit der Wert "True" erhalten bleibt
    #    bei weiteren Re-Runs.
    if "start_button_pressed" not in st.session_state:
        st.session_state["start_button_pressed"] = False

    # 2) Wertpapier (Yahoo-Kürzel)
    ticker = st.sidebar.text_input(
        label="Wertpapier (Yahoo-Kürzel)",
        value="BTC-USD",
        help="Beispiel: BTC-USD, TSLA, AAPL, etc. (Yahoo Finance Kürzel)"
    )

    # 3) Gesuchtes Datum
    analysis_date = st.sidebar.date_input(
        label="Gesuchtes Datum",
        value=date.today(),
        help="Datum für die Analyse (z.B. aktueller Tag oder Vergangenheitsdatum)."
    )

    # 4) Suchmodus: hoch oder tief
    mode_choice = st.sidebar.radio(
        label="Suchmodus",
        options=["hoch", "tief"],
        index=0
    )

    # 5) Volatilität
    volatility = st.sidebar.radio(
        label="Volatilität",
        options=["normal", "hoch"],
        index=0
    )

    # 6) ATR-Periode (Tage)
    atr_period = st.sidebar.number_input(
        label="ATR-Periode (Tage)",
        value=14,
        min_value=1,
        help="Anzahl Tage zur Berechnung der ATR (Average True Range)."
    )

    # 7) Teiler-Auswahl für Vorjahr und Vormonat (8 oder 16)
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

    # 8) Großer Rhythmus (z.B. 0,36 bis 3600)
    big_rhythm_options = ["0,36", "3,6", "36", "360", "3600"]
    big_rhythm = st.sidebar.selectbox(
        "Großer Rhythmus",
        options=big_rhythm_options,
        index=3,
        help="Auswahl des großen Teilers: 0,36 / 3,6 / 36 / 360 / 3600"
    )

    # 9) Kleiner Teiler – rechnerisch abhängig vom großen Rhythmus
    BASE_SMALL_DIVS = [180.0, 90.0, 45.0, 22.5, 11.25, 5.625]
    try:
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

    # 10) Berechnen-Button: Setzt das Session-State-Flag True
    if st.sidebar.button(
        "Berechnen",
        help="Bitte zuerst alle Eingaben abschließen, dann klicken."
    ):
        st.session_state["start_button_pressed"] = True

    # Debug-Ausgabe in der Sidebar
    st.sidebar.write("DEBUG - start_button_pressed =", st.session_state["start_button_pressed"])

    # 11) Gesamtes Dictionary zurückgeben
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
        # Der wichtige Unterschied: Wir liefern jetzt den Session-State-Wert zurück.
        "start_button": st.session_state["start_button_pressed"]
    }
