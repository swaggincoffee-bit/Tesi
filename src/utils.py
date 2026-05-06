import pandas as pd
from datetime import timedelta


def load_csv(path, label=""):
    """Carica un CSV provando encoding comuni (utf-8, latin-1, cp1252)."""
    for enc in ["utf-8", "latin-1", "cp1252", "utf-8-sig"]:
        try:
            df = pd.read_csv(path, sep=";", encoding=enc, dtype=str, low_memory=False)
            df.columns = df.columns.str.strip()
            if label:
                print(f"  ✅ {label}: {df.shape[0]:,} righe × {df.shape[1]} colonne  (encoding: {enc})")
            return df
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Impossibile leggere {path} con nessun encoding provato.")


def parse_oracle_dates(series):
    """Converte date Oracle (es. '16-DEC-25 12.00.00...') in datetime."""
    return pd.to_datetime(
        series.str.strip().str.split(" ").str[0],
        format="%d-%b-%y",
        errors="coerce",
    )


def build_windows(data_min, data_max, window_days=3):
    """Restituisce lista di tuple (t_start, t_end) che coprono [data_min, data_max]."""
    finestre, t = [], data_min
    while t <= data_max:
        finestre.append((t, t + timedelta(days=window_days - 1)))
        t += timedelta(days=window_days)
    return finestre


def build_target(df_lett_re, df_anagrafica, finestre):
    """
    Costruisce df_target (contatore × finestra) vettorizzato.

    Colonne risultanti: _key, finestra, t_start, t_end, silente
      silente=0 → il contatore ha comunicato almeno una volta nella finestra
      silente=1 → nessuna comunicazione (inclusi contatori senza alcuna lettura)
    """
    bins = [ts for ts, _ in finestre] + [finestre[-1][1] + timedelta(days=1)]

    lett = df_lett_re.copy()
    lett["finestra"] = pd.cut(
        lett["data_lettura"], bins=bins,
        labels=range(1, len(finestre) + 1), right=False,
    ).astype("Int64")

    comunicati = (
        lett.dropna(subset=["finestra"])
        .drop_duplicates(subset=["_key", "finestra"])[["_key", "finestra"]]
        .assign(silente=0)
    )

    meta = pd.DataFrame({
        "finestra": range(1, len(finestre) + 1),
        "t_start":  [ts for ts, _ in finestre],
        "t_end":    [te for _, te in finestre],
    })

    idx = pd.MultiIndex.from_product(
        [df_anagrafica["_key"].values, range(1, len(finestre) + 1)],
        names=["_key", "finestra"],
    )
    df_target = pd.DataFrame(index=idx).reset_index()
    df_target = df_target.merge(comunicati, on=["_key", "finestra"], how="left")
    df_target["silente"] = df_target["silente"].fillna(1).astype(int)
    df_target = df_target.merge(meta, on="finestra", how="left")
    return df_target


def feat_aggregate(df_target, df_anagrafica):
    """
    Collassa il panel in cross-section aggregando le finestre per contatore.

    Aggiunge:
      pct_silente         → proporzione di finestre silenti [0, 1]
      silente_prevalente  → 1 se pct_silente > 0.5  (target per A2/C1)
    """
    agg = (
        df_target.groupby("_key")["silente"]
        .agg(pct_silente="mean", n_finestre="count")
        .reset_index()
    )
    agg["silente_prevalente"] = (agg["pct_silente"] > 0.5).astype(int)
    return df_anagrafica.merge(agg, on="_key", how="left")
