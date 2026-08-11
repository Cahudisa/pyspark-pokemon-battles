# PySpark Pokémon Battle Analytics ⚡

> A distributed ETL pipeline that simulates millions of Pokémon battles using PySpark and the game's real damage formula, then analyzes the results with a medallion architecture (Bronze → Silver → Gold).

---

## 🎯 Business Questions Answered
- Which type has the highest real win rate across all matchups (not just the theoretical type chart)?
- Does speed (who attacks first) matter more than raw stats or type advantage?
- Do legendary Pokémon actually win significantly more often, or is that a myth?
- Is there a "power creep" effect — do Pokémon from newer generations perform better in combat?
- How closely does the official type effectiveness chart match simulated battle outcomes?

---

## 🏗️ Architecture

```
Kaggle CSVs (pokemon.csv, combats.csv)
      │
      ▼
 Bronze Layer          → Raw ingestion, no transformations
      │
      ▼
 Silver Layer          → Cleaning, type casting, standardization
      │
      ▼
 Battle Simulation      → PySpark-distributed Monte Carlo simulation:
 (PySpark)                every Pokémon vs. every Pokémon, using the
                          game's real damage formula, run multiple
                          times per matchup to account for crit/miss/
                          damage-roll randomness → millions of rows
      │
      ▼
  Gold Layer            → Win rates, type matchup matrix, generation
                          trends — business metrics ready for BI
      │
      ▼
 Power BI Dashboard     → Interactive battle analytics report
```

---

## 📊 Data Sources

| Dataset | Source |
|---|---|
| Pokémon stats (~800 Pokémon: type, base stats, generation, legendary flag) | [Kaggle — Pokemon: Weedle's Cave](https://www.kaggle.com/datasets/terminus7/pokemon-challenge) |
| Original simulated combats (~50,000 battles) | Same dataset as above (`combats.csv`) |
| Large-scale simulated combats (millions of rows) | Generated in this project via PySpark, using the games's real damage formula and type effectiveness table |

> Raw CSV files are not included in this repo. Download them manually from the link above and place them in `data/bronze/`.

---

## 🛠️ Stack

| Layer | Tools |
|---|---|
| Distributed processing | PySpark, Spark SQL |
| Environment | Conda (Python 3.10, OpenJDK 17, PySpark 3.5.1) |
| Storage | Parquet (Bronze → Silver → Gold) |
| Orchestration | Jupyter Notebooks |
| Business Intelligence | Power BI |
| Version Control | Git, GitHub |

---

## ⚙️ How to Run Locally

### 1. Clone the repo
```bash
git clone https://github.com/Cahudisa/pyspark-pokemon-battles.git
cd pyspark-pokemon-battles
```

### 2. Create and activate the Conda environment
```bash
conda env create -f environment.yml
conda activate pyspark-pokemon-battles
```

### 3. Set up Hadoop winutils (Windows only)
PySpark needs `winutils.exe` and `hadoop.dll` to write files on Windows:

1. Download both files from [cdarlint/winutils](https://github.com/cdarlint/winutils) (folder `hadoop-3.3.5/bin/`)
2. Place them in `tools/hadoop/bin/`
3. Configure the environment variable (scoped to this Conda env only):
   ```bash
   conda env config vars set HADOOP_HOME=<full-path-to-project>\tools\hadoop -n pyspark-pokemon-battles
   ```
4. Add `tools\hadoop\bin` to the env's PATH via an activate script (see `docs/` or project notes) so the `.dll` loads correctly.
5. Reactivate and verify:
   ```bash
   conda deactivate
   conda activate pyspark-pokemon-battles
   python test_spark.py
   ```

### 4. Download the dataset
Download `pokemon.csv` and `combats.csv` from Kaggle and place them in `data/bronze/`.

### 5. Run the notebooks in order
```
01_bronze_ingest.ipynb        → raw ingestion
02_silver_transform.ipynb     → cleaning and standardization
03_battle_simulation.ipynb    → distributed Monte Carlo battle simulation
04_gold_metrics.ipynb         → business metrics for Power BI
```

---

## 👤 Author
**Carlos Díaz** — Data Engineer
[GitHub](https://github.com/Cahudisa)
