"""
Thruster selection and ranking logic.
"""

import json
from pathlib import Path
from typing import List
from .models import Thruster, MissionRequirements, ThrusterPerformance
from .calculator import evaluate_thruster


def load_thrusters(data_path: str = "data/thrusters.json") -> List[Thruster]:
    """
    Load thruster catalog from JSON file.

    Args:
        data_path: Path to JSON file

    Returns:
        List of Thruster objects
    """
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Thruster data not found: {data_path}")

    with open(path, "r") as f:
        data = json.load(f)

    if "thrusters" not in data or not isinstance(data["thrusters"], list):
        raise ValueError("Invalid thruster catalog: missing 'thrusters' list")

    thrusters = [Thruster(**item) for item in data["thrusters"]]
    return thrusters


def select_thrusters(
    requirements: MissionRequirements,
    thrusters: List[Thruster],
    mass_weight: float = 0.4,
    time_weight: float = 0.6,
    show_infeasible: bool = False,
) -> List[ThrusterPerformance]:
    """
    Evaluate all thrusters and rank by combined score.

    Args:
        requirements: Mission requirements
        thrusters: List of candidate thrusters
        mass_weight: Weight for mass optimization (0-1)
        time_weight: Weight for time optimization (0-1)
        show_infeasible: Include infeasible options in results

    Returns:
        Sorted list of ThrusterPerformance (best first)
    """
    results = []

    for thruster in thrusters:
        performance = evaluate_thruster(
            thruster, requirements, mass_weight, time_weight
        )

        if show_infeasible or performance.is_feasible:
            results.append(performance)

    # Sort by combined score (lower is better)
    results.sort(key=lambda x: x.combined_score)

    return results


def print_results(
    results: List[ThrusterPerformance],
    requirements: MissionRequirements,
    verbose: bool = False,
):
    """
    Pretty-print selection results.

    Args:
        results: Evaluated thruster performances
        requirements: Mission requirements used
        verbose: Show detailed metrics
    """
    print("\n" + "=" * 80)
    print("THRUSTER SELECTION RESULTS")
    print("=" * 80)
    print(f"\n📋 Mission Requirements:")
    print(f"   • Delta-v: {requirements.delta_v_ms} m/s")
    print(f"   • Satellite dry mass: {requirements.satellite_dry_mass_kg} kg")
    print(f"   • Available power: {requirements.available_power_W} W")
    print(f"   • Mass budget: {requirements.mass_budget_kg} kg")
    print(f"   • Minimum TRL: {requirements.min_trl}")

    feasible = [r for r in results if r.is_feasible]
    infeasible = [r for r in results if not r.is_feasible]

    print(f"\n📊 Summary: {len(feasible)} feasible, {len(infeasible)} infeasible")

    if feasible:
        print("\n" + "=" * 80)
        print("✓ FEASIBLE THRUSTERS (ranked by combined score)")
        print("=" * 80)

        for i, perf in enumerate(feasible, 1):
            print(f"\n{i}. {perf.thruster.name} ({perf.thruster.type})")
            print(f"   Manufacturer: {perf.thruster.manufacturer}")
            print(
                f"   Score: {perf.combined_score:.3f} "
                f"(mass: {perf.mass_score:.3f}, time: {perf.time_score:.3f})"
            )
            print(
                f"   Thrust: {perf.thruster.thrust_mN} mN  |  "
                f"Isp: {perf.thruster.isp_s} s  |  "
                f"Power: {perf.thruster.power_W} W  |  "
                f"TRL: {perf.thruster.trl}"
            )
            print(
                f"   Thruster mass: {perf.thruster.mass_kg:.3f} kg  |  "
                f"Propellant: {perf.propellant_mass_kg:.3f} kg  |  "
                f"Total: {perf.total_mass_kg:.3f} kg"
            )
            print(
                f"   Mission duration: {perf.mission_duration_days:.1f} days "
                f"({perf.mission_duration_days/30:.1f} months)"
            )
            print(
                f"   Fuel ratio: {perf.fuel_ratio_percent:.1f}%  |  "
                f"Est. burns: {perf.num_burns_estimate:,}"
            )

            if verbose:
                print(f"   Propellant type: {perf.thruster.propellant}")

    if infeasible:
        print("\n" + "=" * 80)
        print("✗ INFEASIBLE THRUSTERS")
        print("=" * 80)

        for perf in infeasible:
            print(f"\n• {perf.thruster.name} ({perf.thruster.type})")
            print(f"  Reasons:")
            for reason in perf.infeasibility_reasons:
                print(f"    - {reason}")

    print("\n" + "=" * 80 + "\n")
