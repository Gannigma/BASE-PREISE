import streamlit as st
from datetime import timedelta

# Import der UI-Module
from ui.ui_sidebar import get_sidebar_inputs
from ui.ui_display import display_results

# Import der Berechnungs-Module
from calculations.calc_360 import run_360_model
from calculations.calc_vormonat_vorjahr_fix import run_vorjahr_model, run_vormonat_model

def main():
    st.title("Gannigma App für Base: Preise")
    
    # Eingaben aus der Sidebar holen
    inputs = get_sidebar_inputs()
    
    # Warten, bis der Benutzer auf "Berechnen" klickt
    if not inputs["start_button"]:
        st.info("Bitte alle Eingaben in der Sidebar vornehmen und auf 'Berechnen' klicken.")
        return

    # Werte aus den Sidebar-Eingaben extrahieren
    ticker = inputs["ticker"]
    analysis_date = inputs["analysis_date"]
    mode_choice = inputs["mode_choice"]
    volatility = inputs["volatility"]
    atr_period = inputs["atr_period"]
    big_rhythm = inputs["big_rhythm"]
    small_div = inputs["small_div"]
    vj_divider = inputs["vj_divider"]  # Teiler Vorjahr
    vm_divider = inputs["vm_divider"]  # Teiler Vormonat

    data_buffer = 2000  # ca. 5 Jahre

    try:
        # 1) 360°-Modell
        result_360 = run_360_model(
            ticker=ticker,
            analysis_date=analysis_date,
            mode_choice=mode_choice,
            volatility_choice=volatility,
            main_rhythm=big_rhythm,
            selected_small_div=small_div,
            atr_period=atr_period,
            data_buffer=data_buffer
        )

        # 2) Vorjahr
        result_vorjahr = run_vorjahr_model(
            ticker=ticker,
            analysis_date=analysis_date,
            mode_choice=mode_choice,
            divider_val=vj_divider,
            vol_sel=volatility,
            atr_period=atr_period,
            databuf=data_buffer
        )

        # 3) Vormonat
        result_vormonat = run_vormonat_model(
            ticker=ticker,
            analysis_date=analysis_date,
            mode_choice=mode_choice,
            divider_val=vm_divider,
            vol_choice=volatility,
            atr_period=atr_period,
            databuf=data_buffer
        )
    except ValueError as ve:
        # Falsches Kürzel oder keine Daten
        st.error(str(ve))
        return
    except Exception as e:
        st.error(f"Fehler bei der Berechnung: {e}")
        return

    # Basisdaten für die Anzeige (z.B. aus 360°-Ergebnis)
    basisdaten = {
        "analysis_date": analysis_date,
        "vortageskerze": result_360.get("extreme_date", "n/a"),
        "atr_value": result_360.get("atr", None),
        "range_unten": result_360.get("lb", None),
        "range_oben": result_360.get("ub", None),
        "mode_choice": mode_choice
    }

    # In-Range & Expansionswerte (360°)
    inrange_360 = result_360.get("in_range_vals", [])
    expansions_360 = result_360.get("expansions_vals", [])

    # In-Range & Expansionswerte (Vorjahr)
    inrange_vorjahr = result_vorjahr.get("preise_inrange_vorjahr", [])
    expansions_vorjahr = result_vorjahr.get("preise_ausserhalb_vorjahr", [])

    # In-Range & Expansionswerte (Vormonat)
    inrange_vormonat = result_vormonat.get("preise_inrange_vormonat", [])
    expansions_vormonat = result_vormonat.get("preise_ausserhalb_vormonat", [])

    # Chart-Daten: z.B. aus 360°-Result
    df_chart = result_360.get("df_chart", None)
    # Falls df_chart existiert, prüfen wir, ob es leer ist:
    if df_chart is not None and not df_chart.empty:
        df_chart = df_chart.tail(10)
    else:
        df_chart = None

    # Gesamtergebnisse für ui_display
    ergebnisse = {
        # 360°
        "preise_inrange_360": inrange_360,
        "preise_ausserhalb_360": expansions_360,
        # Vorjahr
        "preise_inrange_vorjahr": inrange_vorjahr,
        "preise_ausserhalb_vorjahr": expansions_vorjahr,
        # Vormonat
        "preise_inrange_vormonat": inrange_vormonat,
        "preise_ausserhalb_vormonat": expansions_vormonat,
        # Chart
        "df_chart": df_chart,
        # Datencheck
        "vj_high": result_vorjahr.get("vj_high"),
        "vj_low": result_vorjahr.get("vj_low"),
        "vj_range": None,
        "vj_teiler": result_vorjahr.get("divider_val"),
        "vj_schritt": result_vorjahr.get("step_val"),

        "vm_high": result_vormonat.get("m_high"),
        "vm_low": result_vormonat.get("m_low"),
        "vm_range": None,
        "vm_teiler": result_vormonat.get("divider_val"),
        "vm_schritt": result_vormonat.get("step_val")
    }

    # Range-Berechnungen
    if ergebnisse["vj_high"] and ergebnisse["vj_low"]:
        ergebnisse["vj_range"] = ergebnisse["vj_high"] - ergebnisse["vj_low"]
    if ergebnisse["vm_high"] and ergebnisse["vm_low"]:
        ergebnisse["vm_range"] = ergebnisse["vm_high"] - ergebnisse["vm_low"]

    display_results(ticker, basisdaten, ergebnisse, volatility, big_rhythm, small_div)


if __name__ == '__main__':
    main()
