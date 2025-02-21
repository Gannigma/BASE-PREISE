# ui_display.py

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

def format_price(value: float) -> str:
    """
    Formatiert Zahlen nach deutschen Regeln
    """
    if value is None:
        return "n/a"

    if abs(value) < 5:
        decimals = 4
    elif abs(value) < 100:
        decimals = 2
    else:
        decimals = 0

    pattern = f"{{:,.{decimals}f}}"
    temp_str = pattern.format(value)
    temp_str = temp_str.replace(",", "X").replace(".", ",").replace("X", ".")
    return temp_str

def display_results(ticker, basisdaten, ergebnisse, volatility, big_rhythm, small_div):
    # --------------------------------------------------
    # BLOCK 1: BASISDATEN
    # --------------------------------------------------
    st.subheader("Block 1: Basisdaten")
    colA, colB, colC = st.columns(3)
    with colA:
        st.write(f"**Wertpapier** : {ticker}")
        st.write(f"**Analysedatum** : {basisdaten.get('analysis_date', '')}")
        st.write(f"**Vortageskerze** : {basisdaten.get('vortageskerze', 'n/a')}")
    with colB:
        atr_val = basisdaten.get('atr_value', None)
        lb_val  = basisdaten.get('range_unten', None)
        ub_val  = basisdaten.get('range_oben', None)

        st.write(f"**ATR** : {format_price(atr_val) if atr_val is not None else 'n/a'}")
        st.write(f"**Bereich unten** : {format_price(lb_val) if lb_val is not None else 'n/a'}")
        st.write(f"**Bereich oben** : {format_price(ub_val) if ub_val is not None else 'n/a'}")
    with colC:
        st.write(f"**Volatilität** : {volatility}")
        st.write(f"**Modus (Hoch/Tief)** : {basisdaten.get('mode_choice', '')}")
        st.write(f"**360 Hauptrhythmus** : {big_rhythm}")
        st.write(f"**360 Teiler** : {small_div}")

    st.markdown("---")

    # --------------------------------------------------
    # BLOCK 2: IN-RANGE-WERTE
    # --------------------------------------------------
    st.subheader("Block 2: In-Range-Werte")
    st.write("Hier sehen wir die Preise innerhalb der ATR-Reihe in 3 Spalten : 360°, Vormonat, Vorjahr")

    inrange_360 = ergebnisse.get("preise_inrange_360", [])
    inrange_vormonat = ergebnisse.get("preise_inrange_vormonat", [])
    inrange_vorjahr = ergebnisse.get("preise_inrange_vorjahr", [])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<h4 style='color:blue;'>360°</h4>", unsafe_allow_html=True)
        for preis in inrange_360:
            p_str = format_price(preis)
            st.markdown(f"<p style='color:blue; font-weight:bold;'>{p_str}</p>", unsafe_allow_html=True)

    with col2:
        st.markdown("<h4 style='color:blue;'>Vormonat</h4>", unsafe_allow_html=True)
        for preis in inrange_vormonat:
            p_str = format_price(preis)
            st.markdown(f"<p style='color:blue; font-weight:bold;'>{p_str}</p>", unsafe_allow_html=True)

    with col3:
        st.markdown("<h4 style='color:blue;'>Vorjahr</h4>", unsafe_allow_html=True)
        for preis in inrange_vorjahr:
            p_str = format_price(preis)
            st.markdown(f"<p style='color:blue; font-weight:bold;'>{p_str}</p>", unsafe_allow_html=True)

    st.markdown("---")

    # --------------------------------------------------
    # BLOCK 3: CHART (10 Vortageskerzen)
    # --------------------------------------------------
    st.subheader("Block 3: Börsenchart (10 Vortageskerzen)")
    df_chart = ergebnisse.get("df_chart")
    if df_chart is not None and not df_chart.empty:
        fig = go.Figure(data=[go.Candlestick(
            x=df_chart.index,
            open=df_chart['Open'],
            high=df_chart['High'],
            low=df_chart['Low'],
            close=df_chart['Close'],
            name="OHLC"
        )])

        lb_val = basisdaten.get("range_unten")
        ub_val = basisdaten.get("range_oben")
        if lb_val is not None:
            fig.add_hline(y=lb_val, line=dict(color="black", dash="dash"),
                          annotation_text="Range-Untergrenze")
        if ub_val is not None:
            fig.add_hline(y=ub_val, line=dict(color="black", dash="dash"),
                          annotation_text="Range-Obergrenze")

        inrange_360 = ergebnisse.get("preise_inrange_360", [])
        inrange_vorjahr = ergebnisse.get("preise_inrange_vorjahr", [])
        inrange_vormonat = ergebnisse.get("preise_inrange_vormonat", [])

        for preis in inrange_360:
            fig.add_hline(y=preis, line=dict(color="green"), annotation_text="360°")
        for preis in inrange_vorjahr:
            fig.add_hline(y=preis, line=dict(color="red"), annotation_text="Vorjahr")
        for preis in inrange_vormonat:
            fig.add_hline(y=preis, line=dict(color="blue"), annotation_text="Vormonat")

        fig.update_layout(
            height=500,
            xaxis_rangeslider_visible=False,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Keine Chart-Daten vorhanden oder DataFrame leer.")

    st.markdown("---")

    # --------------------------------------------------
    # BLOCK 4: LEGENDE
    # --------------------------------------------------
    st.subheader("Block 4: Legende")
    st.markdown(
        """
        <p>
        <strong>Farbliche Zuordnung der Linien im Diagramm:</strong><br>
        <span style='color:green;'>■ 360°</span> | 
        <span style='color:blue;'>■ Vormonat</span> | 
        <span style='color:red;'>■ Vorjahr</span> | 
        <span style='color:black;'>■ ATR Range (gestrichelt)</span>
        </p>
        """,
        unsafe_allow_html=True
    )
    st.markdown("---")

    # --------------------------------------------------
    # BLOCK 5: EXPANSIONSWERTE
    # --------------------------------------------------
    st.subheader("Block 5: Expansionswerte (außerhalb des Bereichs)")
    st.write("Die folgenden Werte liegen außerhalb des ATR-Bereichs. Es werden jeweils 4 Werte aufgelistet.")

    out_360 = ergebnisse.get("preise_ausserhalb_360", [])
    out_vm  = ergebnisse.get("preise_ausserhalb_vormonat", [])
    out_vj  = ergebnisse.get("preise_ausserhalb_vorjahr", [])

    colX, colY, colZ = st.columns(3)
    with colX:
        st.markdown("<h4 style='color:green;'>360°</h4>", unsafe_allow_html=True)
        for preis in out_360:
            p_str = format_price(preis)
            st.markdown(f"<p style='color:green; font-weight:bold;'>{p_str}</p>", unsafe_allow_html=True)

    with colY:
        st.markdown("<h4 style='color:green;'>Vormonat</h4>", unsafe_allow_html=True)
        for preis in out_vm:
            p_str = format_price(preis)
            st.markdown(f"<p style='color:green; font-weight:bold;'>{p_str}</p>", unsafe_allow_html=True)

    with colZ:
        st.markdown("<h4 style='color:green;'>Vorjahr</h4>", unsafe_allow_html=True)
        for preis in out_vj:
            p_str = format_price(preis)
            st.markdown(f"<p style='color:green; font-weight:bold;'>{p_str}</p>", unsafe_allow_html=True)

    st.markdown("---")

    # --------------------------------------------------
    # BLOCK 6: DATENCHECK – zuerst Vormonat, dann Vorjahr
    # --------------------------------------------------
    st.subheader("Block 6: Datencheck (Vormonat / Vorjahr)")
    st.write("""
        Hier werden die grundlegenden Daten (z.B. Hoch/Tief, Range, 
        angewandte Teiler etc.) für Vormonat und Vorjahr übersichtlich dargestellt.
    """)

    vj_high = ergebnisse.get("vj_high")
    vj_low  = ergebnisse.get("vj_low")
    vj_range = ergebnisse.get("vj_range")
    vj_teiler = ergebnisse.get("vj_teiler")
    vj_schritt = ergebnisse.get("vj_schritt")

    vm_high = ergebnisse.get("vm_high")
    vm_low  = ergebnisse.get("vm_low")
    vm_range = ergebnisse.get("vm_range")
    vm_teiler = ergebnisse.get("vm_teiler")
    vm_schritt = ergebnisse.get("vm_schritt")

    col_vm, col_vj = st.columns(2)

    with col_vm:
        st.markdown("#### Vormonat")
        if vm_high is None and vm_low is None:
            st.write("Keine Daten für Vormonat gefunden.")
        else:
            st.write(f"**Hoch** : {format_price(vm_high) if vm_high else 'n/a'}")
            st.write(f"**Tief** : {format_price(vm_low) if vm_low else 'n/a'}")
            st.write(f"**Range** : {format_price(vm_range) if vm_range else 'n/a'}")
            st.write(f"**Teiler** : {vm_teiler if vm_teiler else 'n/a'}")
            st.write(f"**Schrittweite** : {format_price(vm_schritt) if vm_schritt else 'n/a'}")

    with col_vj:
        st.markdown("#### Vorjahr")
        if vj_high is None and vj_low is None:
            st.write("Keine Daten für Vorjahr gefunden.")
        else:
            st.write(f"**Hoch** : {format_price(vj_high) if vj_high else 'n/a'}")
            st.write(f"**Tief** : {format_price(vj_low) if vj_low else 'n/a'}")
            st.write(f"**Range** : {format_price(vj_range) if vj_range else 'n/a'}")
            st.write(f"**Teiler** : {vj_teiler if vj_teiler else 'n/a'}")
            st.write(f"**Schrittweite** : {format_price(vj_schritt) if vj_schritt else 'n/a'}")

    st.markdown("---")
