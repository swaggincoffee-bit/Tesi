from pathlib import Path

ROOT         = Path(__file__).parent.parent
DATA_RAW     = ROOT / "data" / "raw"
DATA_PROC    = ROOT / "data" / "processed"
OUT_FIGURES  = ROOT / "outputs" / "figures"
OUT_TABLES   = ROOT / "outputs" / "tables"

# ── SAP ───────────────────────────────────────────────────────────────────────
COL_PROV         = "04IND - Provincia (cod)"
COL_COMUNE       = "04IND - Comune (cod)"
COL_CAP          = "04IND - CAP (cod)"
COL_ACCESSIBILE  = "03IMPS - STec - Accessibile (cod)"
COL_TELEGESTIONE = "03IMPS - Stato telegestione (cod)"
COL_CONSUMO      = "03IMPS - Operandi - Cons.Anno PDR (desc)"
COL_DATA_INST    = "11MDEF - Installazione(dta)"
COL_COSTRUTTORE  = "11MDEF - Costruttore (cod)"
COL_ANNO_COSTR   = "11MDEF - Anno Costruzione (cod)"
COL_MATERIALE    = "11MDEF - Materiale (cod)"
KEY_SAP          = "11MDEF - Numero Serie (cod)"

# ── BEAM ──────────────────────────────────────────────────────────────────────
KEY_BEAM     = "MATRICOLA CONTATORE"
COL_MODELLO  = "MODELLO CONTATORE"
COL_FIRMWARE = "VERSIONE FIRMWARE"
COL_TECN_COM = "Tecnologia di comunicazione"
COL_ULT_COM  = "Data ultima comunicazione"
COL_ULT_MIS  = "Data ultima misura"

# ── LETTURE ───────────────────────────────────────────────────────────────────
KEY_LETT        = "Matricola Contatore"
COL_DATA_LETT   = "Data lettura"
COL_STATO_LETT  = "Stato lettura"
COL_DIAGNOSTICA = "Diagnostica Contatore"

# ── Parametri pipeline ────────────────────────────────────────────────────────
PROV_TARGET = "Reggio nell'Emilia"
WINDOW_DAYS = 3

# ── Nomi file parquet ─────────────────────────────────────────────────────────
FNAME_ANAGRAFICA = "df_anagrafica.parquet"
FNAME_LETT_RE    = "df_lett_re.parquet"
FNAME_TARGET     = "df_target.parquet"
FNAME_CS         = "df_cs.parquet"
