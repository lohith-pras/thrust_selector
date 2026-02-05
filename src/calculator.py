"""
Core physics calculations for thruster performance.
"""

import math
from .models import Thruster, MissionRequirements, ThrusterPerformance


# Physical constants
G0 = 9.81  # Standard gravity (m/s²)
SECONDS_PER_DAY = 86400


def calculate_propellant_mass(
    delta_v_ms: float, isp_s: float, dry_mass_kg: float
) -> float:
    """
    Calculate required propellant mass using Tsiolkovsky equation.

    Δv = Isp × g₀ × ln(m_initial / m_final)
    m_propellant = m_dry × (exp(Δv / (Isp × g₀)) - 1)

    Args:
        delta_v_ms: Required delta-v in m/s
        isp_s: Specific impulse in seconds
        dry_mass_kg: Dry mass (satellite + thruster) in kg

    Returns:
        Required propellant mass in kg
    """
    if isp_s <= 0 or dry_mass_kg <= 0:
        return float("inf")

    mass_ratio = math.exp(delta_v_ms / (isp_s * G0))
    return dry_mass_kg * (mass_ratio - 1)


def calculate_mission_duration(
    thrust_N: float, isp_s: float, propellant_kg: float
) -> float:
    """
    Estimate mission duration using momentum equation.

    t_mission = (Δm × v_e) / Thrust
    where v_e = Isp × g₀

    Args:
        thrust_N: Thrust in Newtons
        isp_s: Specific impulse in seconds
        propellant_kg: Propellant mass in kg

    Returns:
        Mission duration in days
    """
    if thrust_N <= 0 or isp_s <= 0 or propellant_kg <= 0:
        return float("inf")

    exhaust_velocity = isp_s * G0  # m/s
    duration_seconds = (propellant_kg * exhaust_velocity) / thrust_N
    return duration_seconds / SECONDS_PER_DAY


def calculate_mass_breakdown(
    thruster: Thruster, requirements: MissionRequirements
) -> tuple[float, float, float, float]:
    """
    Calculate dry mass, propellant mass, total mass, and fuel ratio.

    Returns:
        (dry_mass_with_thruster, propellant_mass, total_mass, fuel_ratio)
    """
    dry_mass_with_thruster = requirements.satellite_dry_mass_kg + thruster.mass_kg
    propellant_mass = calculate_propellant_mass(
        requirements.delta_v_ms, thruster.isp_s, dry_mass_with_thruster
    )
    total_mass = dry_mass_with_thruster + propellant_mass
    fuel_ratio = (propellant_mass / total_mass) if total_mass > 0 else float("inf")

    return dry_mass_with_thruster, propellant_mass, total_mass, fuel_ratio


def estimate_number_of_burns(
    mission_duration_days: float, thruster_power_W: float, available_power_W: float
) -> int:
    """
    Estimate number of thruster firings based on duty cycle.

    If thruster power > available power, assume 2 burns per orbit.
    Otherwise, continuous operation (1 long burn per maneuver phase).

    Args:
        mission_duration_days: Total mission time
        thruster_power_W: Thruster power requirement
        available_power_W: Available spacecraft power

    Returns:
        Estimated number of discrete burns
    """
    # Assume ~15 orbits per day for LEO
    orbits_per_day = 15
    total_orbits = mission_duration_days * orbits_per_day

    if thruster_power_W > available_power_W:
        # Duty cycling: 2 burns per orbit (at nodes)
        return int(total_orbits * 2)
    else:
        # Continuous operation: fewer, longer burns
        return max(1, int(total_orbits / 10))


def check_feasibility(
    thruster: Thruster, requirements: MissionRequirements
) -> tuple[bool, list[str]]:
    """
    Check if thruster meets mission feasibility constraints.

    Args:
        thruster: Thruster to evaluate
        requirements: Mission requirements

    Returns:
        (is_feasible, list_of_reasons_if_not)
    """
    reasons = []

    # TRL check
    if thruster.trl < requirements.min_trl:
        reasons.append(f"TRL {thruster.trl} < minimum {requirements.min_trl}")

    # Power check (with duty cycle allowance)
    max_acceptable_power = requirements.available_power_W * requirements.max_duty_cycle
    if thruster.power_W > max_acceptable_power:
        reasons.append(
            f"Power {thruster.power_W}W exceeds "
            f"{requirements.max_duty_cycle}x duty cycle limit "
            f"({max_acceptable_power}W)"
        )

    if thruster.isp_s <= 0:
        reasons.append("Specific impulse must be positive")

    if thruster.thrust_N <= 0:
        reasons.append("Thrust must be positive")

    # Calculate required propellant
    _, propellant_mass, total_mass, fuel_ratio = calculate_mass_breakdown(
        thruster, requirements
    )

    # Mass budget check
    if total_mass > requirements.mass_budget_kg:
        reasons.append(
            f"Total mass {total_mass:.2f}kg > "
            f"budget {requirements.mass_budget_kg}kg"
        )

    # Check for unrealistic propellant ratios (>50%)
    if fuel_ratio > 0.5:
        reasons.append(f"Fuel ratio {fuel_ratio*100:.1f}% too high (>50%)")

    return (len(reasons) == 0, reasons)


def evaluate_thruster(
    thruster: Thruster,
    requirements: MissionRequirements,
    mass_weight: float = 0.4,
    time_weight: float = 0.6,
) -> ThrusterPerformance:
    """
    Fully evaluate a thruster for the given mission.

    Args:
        thruster: Thruster to evaluate
        requirements: Mission requirements
        mass_weight: Weight for mass in scoring (0-1)
        time_weight: Weight for time in scoring (0-1)

    Returns:
        Complete performance evaluation
    """
    # Calculate masses
    _, propellant_mass, total_mass, fuel_ratio = calculate_mass_breakdown(
        thruster, requirements
    )

    # Calculate duration
    mission_duration = calculate_mission_duration(
        thruster.thrust_N, thruster.isp_s, propellant_mass
    )

    # Estimate burns
    num_burns = estimate_number_of_burns(
        mission_duration, thruster.power_W, requirements.available_power_W
    )

    # Fuel ratio
    fuel_ratio = fuel_ratio * 100

    # Feasibility check
    is_feasible, reasons = check_feasibility(thruster, requirements)

    # Scoring (normalize by typical values)
    # Lower is better for both
    mass_score = total_mass / requirements.mass_budget_kg
    time_score = mission_duration / 365  # Normalize to 1 year
    combined_score = mass_weight * mass_score + time_weight * time_score

    return ThrusterPerformance(
        thruster=thruster,
        propellant_mass_kg=propellant_mass,
        total_mass_kg=total_mass,
        mission_duration_days=mission_duration,
        num_burns_estimate=num_burns,
        fuel_ratio_percent=fuel_ratio,
        is_feasible=is_feasible,
        infeasibility_reasons=reasons,
        mass_score=mass_score,
        time_score=time_score,
        combined_score=combined_score,
    )
