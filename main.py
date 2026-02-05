#!/usr/bin/env python3
"""
Thruster Selection CLI
Simple command-line tool for selecting electric propulsion thrusters.
"""
import argparse
from src.models import MissionRequirements
from src.selector import load_thrusters, select_thrusters, print_results


def main():
    parser = argparse.ArgumentParser(
        description="Select optimal electric propulsion thruster for your mission",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic orbit raise (12U CubeSat)
  python main.py --delta-v 800 --sat-mass 12 --power 30 --budget 18

  # LEO to GEO transfer (50kg satellite)
  python main.py --delta-v 4000 --sat-mass 45 --power 100 --budget 55

  # Show all options including infeasible
  python main.py --delta-v 800 --sat-mass 12 --power 30 --budget 18 --show-all

  # Prioritize mission speed over mass
  python main.py --delta-v 800 --sat-mass 12 --power 30 --budget 18 \\
                 --mass-weight 0.2 --time-weight 0.8
        """,
    )

    # Required arguments
    parser.add_argument(
        "--delta-v",
        type=float,
        required=True,
        help="Required delta-v in m/s (e.g., 800 for 500→1200km orbit raise)",
    )
    parser.add_argument(
        "--sat-mass",
        type=float,
        required=True,
        help="Satellite dry mass in kg (without propulsion system)",
    )
    parser.add_argument(
        "--power",
        type=float,
        required=True,
        help="Available power for propulsion in Watts",
    )
    parser.add_argument(
        "--budget",
        type=float,
        required=True,
        help="Total mass budget in kg (satellite + thruster + propellant)",
    )

    # Optional arguments
    parser.add_argument(
        "--min-trl",
        type=int,
        default=6,
        help="Minimum Technology Readiness Level (default: 6)",
    )
    parser.add_argument(
        "--duty-cycle",
        type=float,
        default=3.0,
        help="Max power ratio for duty cycling (default: 3.0)",
    )
    parser.add_argument(
        "--mass-weight",
        type=float,
        default=0.4,
        help="Weight for mass optimization, 0-1 (default: 0.4)",
    )
    parser.add_argument(
        "--time-weight",
        type=float,
        default=0.6,
        help="Weight for time optimization, 0-1 (default: 0.6)",
    )
    parser.add_argument(
        "--show-all", action="store_true", help="Show infeasible thrusters too"
    )
    parser.add_argument("--verbose", action="store_true", help="Show detailed metrics")
    parser.add_argument(
        "--data",
        type=str,
        default="data/thrusters.json",
        help="Path to thruster catalog JSON (default: data/thrusters.json)",
    )

    args = parser.parse_args()

    # Validate inputs
    if args.delta_v < 0:
        parser.error("Delta-v must be zero or positive")
    if args.sat_mass <= 0:
        parser.error("Satellite mass must be positive")
    if args.power <= 0:
        parser.error("Power must be positive")
    if args.budget <= 0:
        parser.error("Mass budget must be positive")

    # Validate and normalize weights
    if not (0 <= args.mass_weight <= 1 and 0 <= args.time_weight <= 1):
        parser.error("Weights must be between 0 and 1")
    weight_sum = args.mass_weight + args.time_weight
    if weight_sum <= 0:
        parser.error("At least one of the weights must be positive")
    mass_weight = args.mass_weight / weight_sum
    time_weight = args.time_weight / weight_sum

    # Create mission requirements
    requirements = MissionRequirements(
        delta_v_ms=args.delta_v,
        satellite_dry_mass_kg=args.sat_mass,
        available_power_W=args.power,
        mass_budget_kg=args.budget,
        min_trl=args.min_trl,
        max_duty_cycle=args.duty_cycle,
    )

    # Load thrusters
    try:
        thrusters = load_thrusters(args.data)
        print(f"✓ Loaded {len(thrusters)} thrusters from catalog")
    except (FileNotFoundError, ValueError) as e:
        print(f"✗ Error: {e}")
        return 1

    # Evaluate and rank
    results = select_thrusters(
        requirements,
        thrusters,
        mass_weight=mass_weight,
        time_weight=time_weight,
        show_infeasible=args.show_all,
    )

    # Display results
    print_results(results, requirements, verbose=args.verbose)

    return 0


if __name__ == "__main__":
    exit(main())
