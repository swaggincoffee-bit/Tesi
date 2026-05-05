# Tesi — Analisi Predittiva Contatori Gas (Reggio Emilia)

Modelli statistici e ML per la previsione del silenzio radio dei contatori smart gas G4/G6 in provincia di Reggio Emilia.

---

## Struttura del repository

```
├── 00_preparazione_dati/
│   ├── 01_Preparazione_dati.ipynb       ← v1 originale
│   └── 01_Preparazione_dati_v2.ipynb    ← v2 corretta (usa questa)
│
├── A_cross_section/
│   ├── A1_OLS.ipynb
│   └── A2_Logit.ipynb
│
├── B_panel/
│   ├── B1_FE_OLS.ipynb
│   ├── B2_RE_GLS.ipynb
│   ├── B3_Conditional_Logit.ipynb
│   └── B4_Mixed_Logit.ipynb
│
└── C_machine_learning/
    ├── C1_RandomForest.ipynb
    └── C2_GradientBoosting.ipynb
```

---

## Classificazione dei modelli

### Famiglia A — Cross-section
Una riga per contatore. Il dataset panel viene collassato aggregando le 6 finestre per contatore.

| Modello | Descrizione | Var. statiche | Var. dinamiche |
|---------|-------------|:---:|:---:|
| **A1** OLS | `pct_silente_i = β₀ + β·X_i + ε_i` — baseline | ✅ | aggregate |
| **A2** Logit | `P(silente_prev=1) = σ(β₀ + β·X_i)` — odds ratio | ✅ | aggregate |

---

### Famiglia B — Panel
Una riga per contatore × finestra. Sfrutta la dimensione temporale.

| Modello | Descrizione | Var. statiche | Var. dinamiche | Eterogeneità |
|---------|-------------|:---:|:---:|:---:|
| **B1** FE OLS | Within estimator — demeaning | ✗ | ✅ | controllata |
| **B2** RE GLS | Random effects — Hausman test | ✅ | ✅ | N(0,σ²) |
| **B3** Cond. Logit | Condizionato sulla somma | ✗ | ✅ | controllata |
| **B4** Mixed Logit | Integrazione numerica | ✅ | ✅ | N(0,σ²) |

---

### Famiglia C — Machine Learning
Approccio non parametrico su cross-section o panel.

| Modello | Descrizione |
|---------|-------------|
| **C1** Random Forest | Dataset collassato, permutation importance |
| **C2** Gradient Boosting | XGBoost/LightGBM — opzionale |

---

## Sequenza logica

```
Step 1 — Baseline     Step 2 — Rigore stat.    Step 3 — ML
──────────────────    ─────────────────────    ──────────────
A1 OLS          →     B1/B2 Panel OLS    →     C1 Random Forest
A2 Logit        →     B3/B4 Panel Logit  →     confronto finale
```

---

## Dataset

- **Parco contatori RE**: 226,702 contatori (merge SAP × BEAM)
- **Letture**: 298,745 righe — 16 giorni (6–22 dic 2025)
- **Finestre**: 6 finestre da 3 giorni
- **Target**: silente=1 se il contatore non ha comunicato in una finestra
- **Sbilanciamento**: 85.9% silenti / 14.1% comunicanti
