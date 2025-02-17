import yfinance as yf
import math
from datetime import date, timedelta
import pandas as pd
import plotly.graph_objects as go

# -----------------------------------------------------------
# Gemeinsame Utility-Funktionen
# -----------------------------------------------------------
def calculate_atr(df, period=14):
    df = df.copy()
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR'] = df['TR'].rolling(window=period).mean()
    return df

def find_extreme_3days(df, mode):
    if len(df) < 3:
        return None, None
    cands = df.tail(3)
    if mode == "hoch":
        idx = cands['High'].idxmax()
    else:
        idx = cands['Low'].idxmin()
    row = cands.loc[idx]
    return idx, row

def plot_chart(df_plot, highlights, lb, ub):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df_plot.index,
        open=df_plot['Open'],
        high=df_plot['High'],
        low=df_plot['Low'],
        close=df_plot['Close'],
        name='Kerzen'
    ))
    fig.add_hline(y=lb, line=dict(color='black', width=2), annotation_text='lb')
    fig.add_hline(y=ub, line=dict(color='black', width=2), annotation_text='ub')
    for p in highlights:
        fig.add_hline(y=p, line=dict(width=1, dash='dot'), annotation_text=f"{p:.2f}")
    fig.update_layout(height=600, xaxis_rangeslider_visible=False)
    return fig

# -----------------------------------------------------------
# Vorjahr
# -----------------------------------------------------------
def load_data_year(ticker, year):
    start_date = f"{year}-01-01"
    end_date   = f"{year}-12-31"
    df = yf.download(ticker, start=start_date, end=end_date, interval='1d', progress=False)
    if df.empty:
        raise ValueError(f"Falsches Wertpapierkürzel oder keine Daten für Jahr {year}.")
    df.reset_index(inplace=True)
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    return df

def run_vorjahr_model(ticker, analysis_date, mode_choice, divider_val,
                      vol_sel, atr_period, databuf):
    """
    Logik:
      1) VJ-Daten laden, min/max bestimmen
      2) Schrittweite = (VJ-High - VJ-Low) / divider_val
      3) Erzeuge Sequence [VJ-Low + i*step ...]
      4) Lade Aktuelle Daten, bestimme Extrem-Kerze (3 Tage), ATR => Range [lb, ub]
      5) 'In-Range' = alle Sequenzwerte, die lb <= x <= ub (sort. desc)
      6) 4 Expansions in passender Richtung => start ab max(in-range) oder ub (bei 'hoch')
         / ab min(in-range) oder lb (bei 'tief'), in 4 * step-Schritten
      7) Zusammenführen & return
    """
    # 1) Vorjahres-Daten
    prev_year = analysis_date.year - 1
    df_vj = load_data_year(ticker, prev_year)
    vj_low = df_vj['Low'].min()
    vj_high = df_vj['High'].max()
    if vj_low is None or vj_high is None:
        raise ValueError("Keine validen High/Low im Vorjahr.")

    # 2) Schrittweite
    step_val = (vj_high - vj_low) / float(divider_val)
    step_val = round(step_val, 4)

    # 3) Sequence (ggf. bis 80 steps)
    max_steps = 80
    sequence = [round(vj_low + i * step_val, 4) for i in range(max_steps + 1)]

    # Aktuelle Daten laden
    total_days = databuf + atr_period + 3
    end_date = analysis_date
    start_date = end_date - timedelta(days=total_days)
    df_current = yf.download(ticker, start=start_date, end=end_date, interval='1d', progress=False)
    if df_current.empty:
        raise ValueError("Falsches Wertpapierkürzel oder keine aktuellen Daten (Vorjahr-Modell).")
    df_current.reset_index(inplace=True)
    df_current['Date'] = pd.to_datetime(df_current['Date'])
    df_current.set_index('Date', inplace=True)

    cutoff_date = analysis_date - timedelta(days=1)
    df_cut = df_current.loc[:cutoff_date]
    if df_cut.empty:
        raise ValueError("Keine Daten bis zum Vortag (Vorjahr-Modell).")

    # Extrem-Kerze
    extreme_date, extreme_row = find_extreme_3days(df_cut, mode_choice)
    if extreme_date is None:
        raise ValueError("Keine Extrem-Kerze (letzte 3 Tage) (Vorjahr).")

    # ATR
    df_cut = calculate_atr(df_cut, int(atr_period))
    curr_atr = df_cut['ATR'].iloc[-1]
    if math.isnan(curr_atr):
        raise ValueError("Nicht genug ATR-Daten im aktuellen Zeitraum (Vorjahr).")

    # Volatilität
    if vol_sel == "hoch":
        vol_factor = 1.5
    elif vol_sel == "gering":
        vol_factor = 0.5
    else:
        vol_factor = 1.0

    # Range
    basis = (extreme_row['High'] + extreme_row['Low']) / 2
    if mode_choice == "hoch":
        lb, ub = basis, basis + curr_atr * vol_factor
    else:
        lb, ub = basis - curr_atr * vol_factor, basis

    # 5) In-Range (desc)
    in_range = [x for x in sequence if lb <= x <= ub]
    in_range.sort(reverse=True)

    # 6) Expansions in passender Richtung (4 Werte)
    expansions = []
    if mode_choice == "hoch":
        if in_range:
            start_val = max(in_range)  # höchster In-Range-Wert
        else:
            start_val = ub  # Falls kein In-Range
        # Generiere 4 Werte in step_val-Schritten
        for i in range(1, 5):
            expansions.append(round(start_val + i * step_val, 4))
    else:  # mode_choice == "tief"
        if in_range:
            start_val = min(in_range)  # tiefster In-Range-Wert
        else:
            start_val = lb
        for i in range(1, 5):
            expansions.append(round(start_val - i * step_val, 4))

    # Sortierung absteigend
    expansions.sort(reverse=True)

    # Letzte 10 Tage & Chart
    df_chart = df_cut.tail(10)
    highlights = in_range + expansions
    fig = plot_chart(df_chart, highlights, lb, ub)

    results = {
        "vj_low": vj_low,
        "vj_high": vj_high,
        "divider_val": divider_val,
        "step_val": step_val,
        "basis": basis,
        "preise_inrange_vorjahr": in_range,
        "preise_ausserhalb_vorjahr": expansions,
        "df_vj": df_vj,
        "df_cut": df_cut,
        "figure": fig,
        "extreme_date": extreme_date,
        "atr": curr_atr,
        "lb": lb,
        "ub": ub
    }
    return results

# -----------------------------------------------------------
# Vormonat
# -----------------------------------------------------------
def load_data_range(ticker, start_date, end_date):
    df = yf.download(ticker, start=start_date, end=end_date, interval='1d', progress=False)
    if df.empty:
        raise ValueError("Falsches Wertpapierkürzel oder keine Daten (Vormonat).")
    df.reset_index(inplace=True)
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    return df

def get_previous_month_span(df, analysis_date):
    m = analysis_date.month
    y = analysis_date.year
    if m == 1:
        vm_year = y - 1
        vm_month = 12
    else:
        vm_year = y
        vm_month = m - 1
    df_vm = df[(df.index.year == vm_year) & (df.index.month == vm_month)]
    if df_vm.empty:
        return None, None, vm_year, vm_month
    return df_vm['Low'].min(), df_vm['High'].max(), vm_year, vm_month

def run_vormonat_model(ticker, analysis_date, mode_choice, divider_val,
                       vol_choice, atr_period, databuf):
    """
    Gleiche Logik wie Vorjahr:
      - Nur 4 Expansions in 'richtiger' Richtung
      - Step = (m_high - m_low) / divider_val
      - Start ab max(in_range) oder ub (bei 'hoch'),
        min(in_range) oder lb (bei 'tief')
    """
    total_days = databuf + atr_period + 3
    end_day = analysis_date
    start_day = end_day - timedelta(days=total_days)
    df_all = load_data_range(ticker, start_day, end_day)
    if df_all is None or df_all.empty:
        raise ValueError("Falsches Wertpapierkürzel oder keine Daten (Vormonat).")

    m_low, m_high, vm_year, vm_month = get_previous_month_span(df_all, analysis_date)
    if m_low is None or m_high is None:
        raise ValueError(f"Keine Daten für Vormonat {vm_month}.{vm_year}")

    cutoff = analysis_date - timedelta(days=1)
    df_cut = df_all.loc[:cutoff]
    if df_cut.empty:
        raise ValueError("Keine Daten bis zum Vortag (Vormonat).")

    extreme_date, extreme_row = find_extreme_3days(df_cut, mode_choice)
    if extreme_date is None:
        raise ValueError("Keine 3-Tage-Extremkerze gefunden (Vormonat).")

    df_cut = calculate_atr(df_cut, int(atr_period))
    curr_atr = df_cut['ATR'].iloc[-1]
    if math.isnan(curr_atr):
        raise ValueError("Nicht genug ATR-Daten (Vormonat).")

    if vol_choice == "hoch":
        vol_factor = 1.5
    elif vol_choice == "gering":
        vol_factor = 0.5
    else:
        vol_factor = 1.0

    basis = (extreme_row['High'] + extreme_row['Low']) / 2
    if mode_choice == "hoch":
        lb, ub = basis, basis + curr_atr * vol_factor
    else:
        lb, ub = basis - curr_atr * vol_factor, basis

    span = m_high - m_low
    if span <= 0:
        raise ValueError("Ungültige Spanne im Vormonat (<=0).")

    step_val = span / float(divider_val)
    step_val = round(step_val, 4)
    max_steps = 80
    sequence = [round(m_low + i * step_val, 4) for i in range(max_steps+1)]

    # 1) In-Range
    in_range = [x for x in sequence if lb <= x <= ub]
    in_range.sort(reverse=True)

    # 2) Expansions in passender Richtung (4 Werte)
    expansions = []
    if mode_choice == "hoch":
        # Starte ab höchstem In-Range Wert, sonst ab ub
        if in_range:
            start_val = max(in_range)
        else:
            start_val = ub
        for i in range(1, 5):
            expansions.append(round(start_val + i * step_val, 4))
    else:  # tief
        if in_range:
            start_val = min(in_range)
        else:
            start_val = lb
        for i in range(1, 5):
            expansions.append(round(start_val - i * step_val, 4))

    expansions.sort(reverse=True)

    df_chart = df_cut.tail(10)
    highlights = in_range + expansions
    fig = plot_chart(df_chart, highlights, lb, ub)

    results = {
        "vm_year": vm_year,
        "vm_month": vm_month,
        "m_low": m_low,
        "m_high": m_high,
        "divider_val": divider_val,
        "lb": lb,
        "ub": ub,
        "basis": basis,
        "preise_inrange_vormonat": in_range,
        "preise_ausserhalb_vormonat": expansions,
        "df": df_all,
        "df_cut": df_cut,
        "figure": fig,
        "extreme_date": extreme_date,
        "atr": curr_atr,
        "step_val": step_val
    }
    return results
