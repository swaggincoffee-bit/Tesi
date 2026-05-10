import pandas as pd
from datetime import timedelta


def load_csv(path, label=""):
    """Carica un CSV con encoding noto o provando encoding comuni."""
    ENCODING_MAP = {
        "SAP"    : "latin-1",
        "BEAM"   : "utf-8",
        "LETTURE": "utf-8",
    }
    encodings = [ENCODING_MAP[label]] if label in ENCODING_MAP else ["utf-8", "latin-1", "cp1252", "utf-8-sig"]
    for enc in encodings:
        try:
            df = pd.read_csv(path, sep=";", encoding=enc, dtype=str, low_memory=False)
            df.columns = df.columns.str.strip()
            if label:
                print(f"  {label}: {df.shape[0]:,} righe x {df.shape[1]} colonne  (encoding: {enc})")
            return df
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Impossibile leggere {path}.")


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
    Costruisce df_target (contatore x finestra) vettorizzato.

    Colonne risultanti: _key, finestra, t_start, t_end, silente
      silente=0 -> il contatore ha comunicato almeno una volta nella finestra
      silente=1 -> nessuna comunicazione (inclusi contatori senza alcuna lettura)
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


def feat_aggregate(df_target, df_anagrafica, df_lett_re=None):
    """
    Collassa il panel in cross-section aggregando le finestre per contatore.

    Aggiunge:
      pct_silente        -> proporzione di finestre silenti [0, 1]
      n_finestre         -> numero di finestre osservate
      silente_prevalente -> 1 se pct_silente > 0.5

    Se df_lett_re è fornito, aggiunge anche:
      pct_err         -> proporzione di letture con stato ERR per contatore
      diag_bit_00..15 -> 1 se almeno una lettura ha quel bit diagnostico attivo
    """
    from src.config import COL_STATO_LETT, COL_DIAGNOSTICA

    agg = (
        df_target.groupby("_key")["silente"]
        .agg(pct_silente="mean", n_finestre="count")
        .reset_index()
    )
    agg["silente_prevalente"] = (agg["pct_silente"] > 0.5).astype(int)
    df_cs = df_anagrafica.merge(agg, on="_key", how="left")

    if df_lett_re is not None:
        lett = df_lett_re.copy()

        # pct_err
        lett["is_err"] = (lett[COL_STATO_LETT].str.strip() == "ERR").astype(int)
        err_agg = lett.groupby("_key")["is_err"].mean().rename("pct_err").reset_index()

        # diag_bit_00..15
        diag = lett[["_key", COL_DIAGNOSTICA]].copy()
        diag[COL_DIAGNOSTICA] = diag[COL_DIAGNOSTICA].str.strip().str.zfill(16)
        for i in range(16):
            diag[f"diag_bit_{i:02d}"] = diag[COL_DIAGNOSTICA].str[i].eq("1").astype(int)
        diag_cols = [f"diag_bit_{i:02d}" for i in range(16)]
        diag_agg = diag.groupby("_key")[diag_cols].max().reset_index()

        df_cs = df_cs.merge(err_agg,  on="_key", how="left")
        df_cs = df_cs.merge(diag_agg, on="_key", how="left")
        df_cs["pct_err"] = df_cs["pct_err"].fillna(0)
        for col in diag_cols:
            df_cs[col] = df_cs[col].fillna(0).astype(int)

    return df_cs


def feat_engineer(df_cs, ref_date):
    """
    Aggiunge variabili numeriche e alias leggibili al dataframe cross-section.

    ref_date: data di riferimento per calcolare i giorni (usa DATA_MAX del dataset letture)

    Colonne aggiunte:
      anni_da_costruzione -> anni dalla costruzione al ref_date
      consumo_annuo       -> consumo annuo PDR numerico
      gg_da_installazione -> giorni dall'installazione al ref_date
      firmware_num        -> parte numerica della versione firmware
      gg_da_ult_com       -> giorni dall'ultima comunicazione al ref_date
      gg_da_ult_mis       -> giorni dall'ultima misura al ref_date
      costruttore         -> alias leggibile di COL_COSTRUTTORE
      modello             -> alias leggibile di COL_MODELLO
      tecnologia          -> alias leggibile di COL_TECN_COM
      comune              -> alias leggibile di COL_COMUNE
      accessibile         -> alias leggibile di COL_ACCESSIBILE
      telegestione        -> alias leggibile di COL_TELEGESTIONE
    """
    from src.config import (
        COL_ANNO_COSTR, COL_CONSUMO, COL_DATA_INST,
        COL_FIRMWARE, COL_ULT_COM, COL_ULT_MIS,
        COL_COSTRUTTORE, COL_MODELLO, COL_TECN_COM,
        COL_COMUNE, COL_ACCESSIBILE, COL_TELEGESTIONE,
    )

    df = df_cs.copy()

    df["anni_da_costruzione"] = ref_date.year - pd.to_numeric(df[COL_ANNO_COSTR], errors="coerce")

    df["consumo_annuo"] = pd.to_numeric(
        df[COL_CONSUMO].str.replace(",", "."), errors="coerce"
    )

    df["gg_da_installazione"] = (
        ref_date - pd.to_datetime(df[COL_DATA_INST], format="%d.%m.%Y", errors="coerce")
    ).dt.days

    df["firmware_num"] = pd.to_numeric(
        df[COL_FIRMWARE].str.extract(r"(\d+)")[0], errors="coerce"
    )

    df["gg_da_ult_com"] = (ref_date - parse_oracle_dates(df[COL_ULT_COM])).dt.days
    df["gg_da_ult_mis"] = (ref_date - parse_oracle_dates(df[COL_ULT_MIS])).dt.days

    df["costruttore"] = df[COL_COSTRUTTORE].fillna("N/A")
    df["modello"]     = df[COL_MODELLO].fillna("N/A")
    df["tecnologia"]  = df[COL_TECN_COM].fillna("N/A")
    df["comune"]      = df[COL_COMUNE].fillna("N/A")
    df["accessibile"] = df[COL_ACCESSIBILE].fillna("N/A")
    df["telegestione"]= df[COL_TELEGESTIONE].fillna("N/A")

    return df
