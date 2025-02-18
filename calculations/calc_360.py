import yfinance as yf
import math
from datetime import timedelta
import pandas as pd
import plotly.graph_objects as go

def load_data_daily(ticker, start_date, end_date):
    """
    Holt die Kursdaten via yfinance.
    Wenn df leer ist => ValueError mit entsprechender Fehlermeldung.
    """
    df = yf.download(ticker, start=start_date, end=end_date, interval='1d', progress=False)

    # Debug-Ausgabe
    import streamlit as st
    st.write("DEBUG - Rohdaten von yfinance (calc_360):")
    st.dataframe(df.head(10))  # zeigt die ersten 10 Zeilen
    st.dataframe(df.tail(10))  # zeigt die letzten 10 Zeilen

if df.empty:
    raise ValueError("Keine Daten...")

    if df.empty:
        raise ValueError(f"Falsches Wertpapierkürzel oder keine Daten gefunden (360). [{ticker}]")
    df.reset_index(inplace=True)
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    return df

def find_extreme_day(df, mode):
    """
    Sucht aus den letzten 3 Kerzen diejenige mit dem höchsten High (mode='hoch')
    oder dem tiefsten Low (mode='tief').
    Gibt (Datum, Zeilen-Objekt) zurück oder (None, None) bei zu wenig Daten.
    """
    if len(df) < 3:
        return None, None
    cands = df.tail(3)
    if mode == "hoch":
        idx = cands['High'].idxmax()
    else:
        idx = cands['Low'].idxmin()
    row = cands.loc[idx]
    return idx, row

def calculate_atr(df, period=14):
    """
    Standard-ATR-Berechnung (Simple Rolling).
    """
    df = df.copy()
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = (df['High'] - df['Close'].shift(1)).abs()
    df['L-PC'] = (df['Low'] - df['Close'].shift(1)).abs()
    df['TR']   = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR']  = df['TR'].rolling(window=period).mean()
    return df

def run_360_model(ticker, analysis_date, mode_choice,
                  volatility_choice, main_rhythm,
                  selected_small_div, atr_period, data_buffer):
    """
    Implementiert das "360°"-Preismodell nach folgendem Prinzip:
      1) Berechne [lb, ub] = ATR-Range (Basis: Extrem-Kerze der letzten 3 Tage, plus Volatilitätsfaktor).
      2) Erzeuge eine Liste (steps) aus reinen 360°-Schritten, die bei 0 beginnt und in Abständen
         von 'selected_small_div' bis zu einer hohen Obergrenze (z.B. 100.000) geht.
      3) "In-Range" = alle Werte in 'steps', die in [lb, ub] liegen (sortiert absteigend).
      4) Expansions = 4 Werte oberhalb von ub (bei "hoch") oder unterhalb von lb (bei "tief")
         - wir nehmen die "nächsten" 4 in aufsteigender Reihenfolge und sortieren sie am Ende absteigend.
    """
    # 1) Daten laden
    total_days = data_buffer + atr_period + 5
    end_date = analysis_date
    start_date = end_date - timedelta(days=total_days)

    # Yahoo-Download
    df = load_data_daily(ticker, start_date, end_date)
    real_cutoff = analysis_date - timedelta(days=1)
    df_cut = df.loc[:real_cutoff].copy()
    if df_cut is not None and not df_cut.empty:
        raise ValueError("Keine Daten bis zum Vortag (360).")

    # 2) Bestimme Extrem-Kerze & ATR
    extreme_date, extreme_row = find_extreme_day(df_cut, mode_choice)
    if extreme_date is None or extreme_row is None:
        raise ValueError("Keine Extrem-Kerze (3 Handelstage) (360).")

    df_cut = calculate_atr(df_cut, int(atr_period))
    curr_atr = df_cut['ATR'].iloc[-1]
    if math.isnan(curr_atr):
        raise ValueError("Nicht genug Daten für ATR (360).")

    # 3) Range [lb, ub]
    if volatility_choice == "hoch":
        vol_factor = 1.5
    elif volatility_choice == "gering":
        vol_factor = 0.5
    else:
        vol_factor = 1.0

    basis = (extreme_row['High'] + extreme_row['Low']) / 2
    if mode_choice == "hoch":
        lb = basis
        ub = basis + curr_atr * vol_factor
    else:
        lb = basis - curr_atr * vol_factor
        ub = basis

    # lb & ub runden
    lb = round(lb, 4)
    ub = round(ub, 4)

    # 4) Erzeuge die 360°-Schritte ab 0 => steps
    #    Bis z.B. 100000 (anpassbar, aber sollte genügen für Öl, BTC, etc.)
    #    Du kannst bei sehr hohen Kursen (z.B. 3600) auch auf 999999 erhöhen
    steps = []
    val = 0.0
    max_val = 500000.0
    while val <= max_val:
        steps.append(round(val, 4))
        val += selected_small_div  # z.B. 22.5, 45, etc.

    # 5) In-Range = [x for x in steps if lb <= x <= ub], absteigend
    in_range_vals = [x for x in steps if x >= lb and x <= ub]
    in_range_vals.sort(reverse=True)

    # 6) Expansions: je nach Modus 4 Werte ober- bzw. unterhalb
    expansions_vals = []
    if mode_choice == "hoch":
        # next 4 Schritte oberhalb ub (kleinste > ub, dann next, next...) => absteigend sortieren
        bigger_candidates = [x for x in steps if x > ub]
        bigger_candidates.sort()  # aufsteigend
        # nimm die ersten 4
        expansions_vals = bigger_candidates[:4]
        expansions_vals.sort(reverse=True)
    else:
        # "tief" => 4 Werte unter lb
        smaller_candidates = [x for x in steps if x < lb]
        # sortiert absteigend => wir nehmen die ersten 4
        smaller_candidates.sort(reverse=True)
        expansions_vals = smaller_candidates[:4]
        # expansions_vals sind jetzt 4 absteigend => passt

    # 7) Chart (letzte 10 Kerzen)
    df_chart = df_cut.tail(10)

    # Rückgabe
    results = {
        "df_cut": df_cut,
        "df_chart": df_chart,
        "extreme_date": extreme_date,
        "atr": round(curr_atr, 4),
        "lb": lb,
        "ub": ub,
        "in_range_vals": in_range_vals,
        "expansions_vals": expansions_vals,
        "basis": round(basis, 4)
    }
    return results
