import yfinance as yf
import math
from datetime import timedelta
import pandas as pd
import plotly.graph_objects as go

def load_data_daily(ticker, start_date, end_date):
    """
    Holt die Kursdaten via yfinance.
    Falls das heruntergeladene DataFrame leer ist,
    werfen wir einen ValueError.
    """
    df = yf.download(ticker, start=start_date, end=end_date, interval='1d', progress=False)
    if df.empty:
        raise ValueError(f"Falsches Wertpapierkürzel oder keine Daten (360) für {ticker}!")
    # Index anpassen
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
    # tail(3) => die letzten 3 Zeilen
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
    df['L-PC'] = (df['Low']  - df['Close'].shift(1)).abs()
    df['TR']   = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR']  = df['TR'].rolling(window=period).mean()
    return df

def run_360_model(ticker, analysis_date, mode_choice,
                  volatility_choice, main_rhythm,
                  selected_small_div, atr_period, data_buffer):
    """
    Implementiert das "360°"-Preismodell nach deinem Prompt:
      1) ATR-Range [lb, ub] über Extrem-Kerze (letzte 3 Tage) + Volatilitätsfaktor
      2) 360°-Liste ab 0 in Schritten von 'selected_small_div' bis max_val
      3) In-Range = alle Werte in [lb, ub], absteigend sortiert
      4) 4 Expansions oberhalb (hoch) oder unterhalb (tief) der Range
    """
    # 1) Daten laden
    total_days = data_buffer + atr_period + 5
    end_date = analysis_date
    start_date = end_date - timedelta(days=total_days)

    df = load_data_daily(ticker, start_date, end_date)

    # real_cutoff = analysis_date - 1 Tag
    real_cutoff = analysis_date - timedelta(days=1)

    # Filter: alles bis inklusive real_cutoff
    df_cut = df.loc[:real_cutoff].copy()

    # Falls df_cut leer => Kein passender Handelstag
    if df_cut.empty:
        raise ValueError("Keine Daten bis zum Vortag (360).")

    # 2) Extrem-Kerze & ATR
    extreme_date, extreme_row = find_extreme_day(df_cut, mode_choice)
    if extreme_date is None or extreme_row is None:
        raise ValueError("Keine Extrem-Kerze (3 Handelstage) (360).")

    df_cut = calculate_atr(df_cut, int(atr_period))
    curr_atr = df_cut['ATR'].iloc[-1]
    if math.isnan(curr_atr):
        raise ValueError("Nicht genug Daten für ATR (360).")

    # Volatilitätsfaktor
    if volatility_choice == "hoch":
        vol_factor = 1.5
    elif volatility_choice == "normal":
        vol_factor = 1.0
    else:
        # Falls du doch mal "gering" unterstützt, setze hier 0.5
        # oder wie du es definieren möchtest.
        vol_factor = 1.0

    # 3) Range [lb, ub] berechnen
    basis = (extreme_row['High'] + extreme_row['Low']) / 2
    if mode_choice == "hoch":
        lb = basis
        ub = basis + curr_atr * vol_factor
    else:
        lb = basis - curr_atr * vol_factor
        ub = basis

    lb = round(lb, 4)
    ub = round(ub, 4)

    # 4) 360°-Schritte (von 0 bis max_val)
    steps = []
    val = 0.0
    max_val = 500000.0
    while val <= max_val:
        steps.append(round(val, 4))
        val += selected_small_div

    # In-Range = [lb, ub]
    in_range_vals = [x for x in steps if lb <= x <= ub]
    in_range_vals.sort(reverse=True)

    # Expansions: 4 Werte ober- oder unterhalb
    expansions_vals = []
    if mode_choice == "hoch":
        bigger_candidates = [x for x in steps if x > ub]
        bigger_candidates.sort()  # aufsteigend
        expansions_vals = bigger_candidates[:4]
        expansions_vals.sort(reverse=True)
    else:
        smaller_candidates = [x for x in steps if x < lb]
        smaller_candidates.sort(reverse=True)
        expansions_vals = smaller_candidates[:4]

    # 5) Letzte 10 Kerzen im Chart
    df_chart = df_cut.tail(10)

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
