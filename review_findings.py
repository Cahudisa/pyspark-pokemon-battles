"""
Quick summary of Gold layer findings — no Spark needed, just pandas + pyarrow
(both already in your conda environment).

Run from the project root:
    python review_findings.py
"""

import pandas as pd

pd.set_option("display.max_rows", 30)
pd.set_option("display.width", 120)

GOLD_PATH = "data/gold"


def section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


# 1 — Win rate by type
section("1. Win rate by type")
df = pd.read_parquet(f"{GOLD_PATH}/win_rate_by_type")
print(df.sort_values("win_rate_pct", ascending=False).to_string(index=False))

# 2 — Speed vs. type advantage
section("2. Does Speed matter more than type advantage?")
df = pd.read_parquet(f"{GOLD_PATH}/speed_vs_type_advantage")
order = ["immune", "resisted", "neutral", "super_effective"]
df["a_type_advantage"] = pd.Categorical(df["a_type_advantage"], categories=order, ordered=True)
print(df.sort_values(["a_type_advantage", "a_faster"], ascending=[True, False]).to_string(index=False))

# 3 — Legendary vs. non-legendary
section("3. Legendary vs. non-legendary win rate")
df = pd.read_parquet(f"{GOLD_PATH}/win_rate_by_legendary")
print(df.sort_values("legendary", ascending=False).to_string(index=False))

# 4 — Power creep by generation
section("4. Win rate by generation (power creep check)")
df = pd.read_parquet(f"{GOLD_PATH}/win_rate_by_generation")
print(df.sort_values("generation").to_string(index=False))

# 5 — Type matchup matrix vs. official chart
section("5. Type matchup matrix — top/bottom 10 by simulated win rate")
df = pd.read_parquet(f"{GOLD_PATH}/type_matchup_matrix")
df_sorted = df.sort_values("a_win_rate_pct", ascending=False)
print("Top 10 (A dominates B):")
print(df_sorted.head(10).to_string(index=False))
print("\nBottom 10 (A struggles against B):")
print(df_sorted.tail(10).to_string(index=False))

correlation = df["a_win_rate_pct"].corr(df["official_multiplier"])
print(f"\nCorrelation between simulated win rate and official type multiplier: {correlation:.3f}")
print("(Closer to 1.0 = the simulation's outcomes align with the real game's type chart)")

# 6 — Original (50k) vs. simulated (millions) comparison
section("6. Original dataset vs. large-scale simulation")
df = pd.read_parquet(f"{GOLD_PATH}/win_rate_comparison_original_vs_simulated")
print(df.sort_values("win_rate_pct_simulated", ascending=False).to_string(index=False))

print("\nDone.")
