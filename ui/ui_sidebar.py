import streamlit as st
from datetime import date

def get_sidebar_inputs():
    # Session State für Button
    if "start_button_pressed" not in st.session_state:
        st.session_state["start_button_pressed"] = False

    if st.sidebar.button("Berechnen"):
        st.session_state["start_button_pressed"] = True

    # HIER jetzt Deine Inputs
    ticker = st.sidebar.text_input("Wertpapier (Ticker)", "BTC-USD")

    analysis_date = st.sidebar.date_input(
        label="Gesuchtes Datum",
        value=date.today(),
        help="Datum für die Analyse..."
    )

    mode_choice = st.sidebar.radio(
        label="Suchmodus",
        options=["hoch", "tief"],
        index=0,
        help="Art der gesuchten Preisprojektion."

    )
    volatility = st.sidebar.radio(
        label="Volatilität",
        options=["normal", "hoch"],
        index=0,
        help="ATR-Faktor: normal=1.0, hoch=1.5"
    )

    atr_period = st.sidebar.number_input(
        label="ATR-Periode (Tage)",
        value=14,
        min_value=1,
        help="Anzahl Tage für die ATR-Berechnung."
    )

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

    big_rhythm_options = ["0,36", "3,6", "36", "360", "3600"]
    big_rhythm = st.sidebar.selectbox(
        "Großer Rhythmus",
        options=big_rhythm_options,
        index=3,
        help="Auswahl des großen Teilers (z.B. 360)"
    )

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

    # GANZ AM ENDE: return
    return {
        "ticker": ticker,
        "analysis_date": analysis_date,
        "mode_choice": mode_choice,
        "atr_period": atr_period,
        "vj_divider": vj_divider,
        "vm_divider": vm_divider,
        "big_rhythm": big_rhythm,
        "small_div": small_div,
        "start_button": st.session_state["start_button_pressed"]
    }
