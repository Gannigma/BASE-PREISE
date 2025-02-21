# calc_360.py

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
    print(f"[DEBUG calc_360] load_data_daily(ticker={ticker}, start={start_date}, end={end_date})")
    df = yf.download(
        ticker,
        start=start_date,
        end=end_date,
        interval='1d',
        progress=False,
        auto_adjust=False  # oder True, je nach Bedarf
    )

    # -------------------------------------------
    # NEUE ZEILEN: MultiIndex-Spalten entfernen
    # -------------------------------------------
    if isinstance(df.columns, pd.MultiIndex):
        print("[DEBUG calc_360] Detected MultiIndex columns. Dropping level=1.")
        df.columns = df.columns.droplevel(1)

    if df.empty:
        raise ValueError(f"Falsches Wertpapierkürzel oder keine Daten (360) für {ticker}!")

    # Index anpassen
    df.reset_index(inplace=True)
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)

    return df


def find_extreme_day(df, mode):
    """
    Sucht aus den letzten 3 Kerzen diejenige
    mit dem höchsten High (mode='hoch')
    oder dem tiefsten Low (mode='tief').
    Gibt (Datum, Zeilen-Objekt) zurück
    oder (None, None) bei zu wenig Daten.

    Das Problem: idxmax()/idxmin() kann mehrere Zeilen liefern,
    wenn es ein exaktes High/Low in mehr als einer Zeile gibt.
    Dann wird row ein DataFrame statt einer Series.
    """
    if len(df) < 3:
        return None, None

    cands = df.tail(3)
    print("[DEBUG] cands:\n", cands)

    if mode == "hoch":
        idx = cands['High'].idxmax()
    else:
        idx = cands['Low'].idxmin()

    print("[DEBUG] idx returned from idxmax/idxmin:", idx)

    # row kann ein einzelnes Series-Objekt ODER ein ganzer DataFrame sein
    row = cands.loc[idx]

    if isinstance(row, pd.DataFrame):
        print("[DEBUG] row is a DataFrame mit shape:", row.shape,
              "- wir nehmen die erste Zeile davon.")
        row = row.iloc[0]

    print("[DEBUG] row shape:", getattr(row, "shape", None))
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


def run_360_model(
    ticker,
    analysis_date,
    mode_choice,
    volatility_choice,
    main_rhythm,
    selected_small_div,
    atr_period,
    data_buffer
):
    """
    Implementiert das "360°"-Preismodell:
      1) ATR-Range [lb, ub] über Extrem-Kerze (letzte 3 Tage) + Volatilitätsfaktor
      2) 360°-Liste ab 0 in Schritten von 'selected_small_div' bis max_val
      3) In-Range = alle Werte in [lb, ub], absteigend sortiert
      4) 4 Expansions oberhalb (hoch) oder unterhalb (tief) der Range
    """
    print(f"[DEBUG calc_360] run_360_model("
          f"ticker={ticker}, date={analysis_date}, mode={mode_choice}, "
          f"volatility={volatility_choice}, big_rhythm={main_rhythm}, "
          f"small_div={selected_small_div}, atr_period={atr_period}, data_buffer={data_buffer})")

    # 1) Daten laden
    total_days = data_buffer + atr_period + 5
    end_date = analysis_date
    start_date = end_date - timedelta(days=total_days)

    df = load_data_daily(ticker, start_date, end_date)

    # real_cutoff => wir wollen nur Daten bis zum Vortag
    real_cutoff = analysis_date - timedelta(days=1)

    # Anstatt df.loc[:real_cutoff], explizit filtern:
    df_cut = df[df.index <= pd.to_datetime(real_cutoff)].copy()
    print(f"[DEBUG calc_360] df_cut shape = {df_cut.shape}")

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
        # Fallback
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

    # 4) 360°-Schritte
    steps = []
    val = 0.0
    max_val = 500000.0
    while val <= max_val:
        steps.append(round(val, 4))
        val += selected_small_div

    # In-Range = [lb, ub]
    in_range_vals = [x for x in steps if (x >= lb and x <= ub)]
    in_range_vals.sort(reverse=True)

    # Expansions: 4 Werte ober- oder unterhalb
    expansions_vals = []
    if mode_choice == "hoch":
        bigger_candidates = [x for x in steps if x > ub]
        bigger_candidates.sort()
        expansions_vals = bigger_candidates[:4]
        expansions_vals.sort(reverse=True)
    else:
        smaller_candidates = [x for x in steps if x < lb]
        smaller_candidates.sort(reverse=True)
        expansions_vals = smaller_candidates[:4]

    # 5) Letzte 10 Kerzen im Chart
    df_chart = df_cut.tail(10)
    print("[DEBUG calc_360] df_chart shape =", df_chart.shape)

    results = {
        "df_cut": df_cut,
        "df_chart": df_chart,
        "extreme_date": extreme_date,
        "atr": round(curr_atr, 4),
        "lb": lb,
        "ub": ub,
        "in_range_vals": in_range_vals,
        "expansions_vals": expansions_vals,
        "basis": round(basis, 4),
    }
    print("[DEBUG calc_360] run_360_model completed.")
    return results
