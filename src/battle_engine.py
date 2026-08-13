"""
Battle engine: type effectiveness, damage formula, and single-battle simulation
for the PySpark Pokemon Battle Analytics project.

This encodes a simplified version of the mainline Pokemon games' damage formula.
Simplifications are documented inline: this dataset only has base stats, not
individual moves, so assumptions were made to keep the simulation game-accurate
in spirit while being computable from the data we actually have.

Usage: designed to be called from a PySpark UDF (see notebooks/03_battle_simulation.ipynb),
but every function here is plain Python with no Spark dependency, so it can also
be unit tested or run standalone.
"""

import random

# Official type effectiveness chart (attacker type -> {defender type: multiplier}).
# 2.0 = super effective, 0.5 = not very effective, 0.0 = no effect. Omitted = 1.0 (normal).
TYPE_CHART = {
    "Normal":   {"Rock": 0.5, "Ghost": 0.0, "Steel": 0.5},
    "Fire":     {"Fire": 0.5, "Water": 0.5, "Grass": 2.0, "Ice": 2.0, "Bug": 2.0, "Rock": 0.5, "Dragon": 0.5, "Steel": 2.0},
    "Water":    {"Fire": 2.0, "Water": 0.5, "Grass": 0.5, "Ground": 2.0, "Rock": 2.0, "Dragon": 0.5},
    "Electric": {"Water": 2.0, "Electric": 0.5, "Grass": 0.5, "Ground": 0.0, "Flying": 2.0, "Dragon": 0.5},
    "Grass":    {"Fire": 0.5, "Water": 2.0, "Grass": 0.5, "Poison": 0.5, "Ground": 2.0, "Flying": 0.5, "Bug": 0.5, "Rock": 2.0, "Dragon": 0.5, "Steel": 0.5},
    "Ice":      {"Fire": 0.5, "Water": 0.5, "Grass": 2.0, "Ice": 0.5, "Ground": 2.0, "Flying": 2.0, "Dragon": 2.0, "Steel": 0.5},
    "Fighting": {"Normal": 2.0, "Ice": 2.0, "Poison": 0.5, "Flying": 0.5, "Psychic": 0.5, "Bug": 0.5, "Rock": 2.0, "Ghost": 0.0, "Dark": 2.0, "Steel": 2.0, "Fairy": 0.5},
    "Poison":   {"Grass": 2.0, "Poison": 0.5, "Ground": 0.5, "Rock": 0.5, "Ghost": 0.5, "Steel": 0.0, "Fairy": 2.0},
    "Ground":   {"Fire": 2.0, "Electric": 2.0, "Grass": 0.5, "Poison": 2.0, "Flying": 0.0, "Bug": 0.5, "Rock": 2.0, "Steel": 2.0},
    "Flying":   {"Electric": 0.5, "Grass": 2.0, "Fighting": 2.0, "Bug": 2.0, "Rock": 0.5, "Steel": 0.5},
    "Psychic":  {"Fighting": 2.0, "Poison": 2.0, "Psychic": 0.5, "Dark": 0.0, "Steel": 0.5},
    "Bug":      {"Fire": 0.5, "Grass": 2.0, "Fighting": 0.5, "Poison": 0.5, "Flying": 0.5, "Psychic": 2.0, "Ghost": 0.5, "Dark": 2.0, "Steel": 0.5, "Fairy": 0.5},
    "Rock":     {"Fire": 2.0, "Ice": 2.0, "Fighting": 0.5, "Ground": 0.5, "Flying": 2.0, "Bug": 2.0, "Steel": 0.5},
    "Ghost":    {"Normal": 0.0, "Psychic": 2.0, "Ghost": 2.0, "Dark": 0.5},
    "Dragon":   {"Dragon": 2.0, "Steel": 0.5, "Fairy": 0.0},
    "Dark":     {"Fighting": 0.5, "Psychic": 2.0, "Ghost": 2.0, "Dark": 0.5, "Fairy": 0.5},
    "Steel":    {"Fire": 0.5, "Water": 0.5, "Electric": 0.5, "Ice": 2.0, "Rock": 2.0, "Steel": 0.5, "Fairy": 2.0},
    "Fairy":    {"Fire": 0.5, "Fighting": 2.0, "Poison": 0.5, "Dragon": 2.0, "Dark": 2.0, "Steel": 0.5},
}

ALL_TYPES = [
    "Normal", "Fire", "Water", "Electric", "Grass", "Ice", "Fighting", "Poison",
    "Ground", "Flying", "Psychic", "Bug", "Rock", "Ghost", "Dragon", "Dark",
    "Steel", "Fairy",
]


def type_effectiveness(attack_type: str, defend_type_1: str, defend_type_2: str) -> float:
    """Multiply effectiveness against each of the defender's types (dual-type stacking)."""
    chart = TYPE_CHART.get(attack_type, {})
    mult_1 = chart.get(defend_type_1, 1.0)
    mult_2 = 1.0
    if defend_type_2 and defend_type_2 != "None":
        mult_2 = chart.get(defend_type_2, 1.0)
    return mult_1 * mult_2


def calculate_damage(attacker: dict, defender: dict, rng: random.Random) -> int:
    """
    Simplified mainline-games damage formula:
        damage = (((2*level/5 + 2) * power * A/D) / 50 + 2) * modifier

    See module docstring for the assumptions behind level/power/STAB/attack-stat choice.
    """
    LEVEL = 50
    POWER = 60
    STAB = 1.5

    use_special = attacker["sp_atk"] > attacker["attack"]
    eff_attack = attacker["sp_atk"] if use_special else attacker["attack"]
    eff_defense = defender["sp_def"] if use_special else defender["defense"]
    eff_defense = max(eff_defense, 1)  # guard against division by zero on edge-case data

    type_mult = type_effectiveness(attacker["type_1"], defender["type_1"], defender["type_2"])

    base = (((2 * LEVEL / 5 + 2) * POWER * eff_attack / eff_defense) / 50) + 2

    random_roll = rng.uniform(0.85, 1.0)
    is_crit = rng.random() < (1 / 16)
    crit_mult = 1.5 if is_crit else 1.0

    damage = base * STAB * type_mult * random_roll * crit_mult
    return max(0, int(damage))


def simulate_battle(pokemon_a: dict, pokemon_b: dict, seed: int, max_turns: int = 100) -> dict:
    """
    Simulate one full turn-based battle between two Pokemon, until one faints.

    Turn order: higher Speed attacks first, fixed for the whole battle; ties broken
    randomly (documented simplification — no move data means no priority-changing effects).

    Returns: {"winner_id", "turns", "faster_pokemon_won"}
    """
    rng = random.Random(seed)

    hp = {pokemon_a["pokemon_id"]: pokemon_a["hp"], pokemon_b["pokemon_id"]: pokemon_b["hp"]}

    if pokemon_a["speed"] > pokemon_b["speed"]:
        first, second = pokemon_a, pokemon_b
    elif pokemon_b["speed"] > pokemon_a["speed"]:
        first, second = pokemon_b, pokemon_a
    else:
        first, second = (pokemon_a, pokemon_b) if rng.random() < 0.5 else (pokemon_b, pokemon_a)

    turns = 0
    while turns < max_turns:
        turns += 1

        for attacker, defender in ((first, second), (second, first)):
            dmg = calculate_damage(attacker, defender, rng)
            hp[defender["pokemon_id"]] -= dmg
            if hp[defender["pokemon_id"]] <= 0:
                return {
                    "winner_id": attacker["pokemon_id"],
                    "turns": turns,
                    "faster_pokemon_won": attacker["pokemon_id"] == first["pokemon_id"],
                }

    # Fallback for the rare double-immunity case: higher remaining HP wins, no infinite loop
    winner_id = max(hp, key=lambda pid: hp[pid])
    return {"winner_id": winner_id, "turns": turns, "faster_pokemon_won": winner_id == first["pokemon_id"]}


if __name__ == "__main__":
    # Quick sanity check — run with: python src/battle_engine.py
    pikachu = {"pokemon_id": 1, "name": "Pikachu", "type_1": "Electric", "type_2": "None",
               "hp": 35, "attack": 55, "defense": 40, "sp_atk": 50, "sp_def": 50, "speed": 90}
    charizard = {"pokemon_id": 2, "name": "Charizard", "type_1": "Fire", "type_2": "Flying",
                 "hp": 78, "attack": 84, "defense": 78, "sp_atk": 109, "sp_def": 85, "speed": 100}

    result = simulate_battle(pikachu, charizard, seed=42)
    print(f"Pikachu vs Charizard (seed=42): {result}")
