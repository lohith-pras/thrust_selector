"""
Data models for thruster selection system.
"""

from dataclasses import dataclass


@dataclass
class Thruster:
    """Represents an electric propulsion thruster."""

    id: str
    name: str
    manufacturer: str
    type: str
    thrust_mN: float
    isp_s: float
    power_W: float
    mass_kg: float
    trl: int
    thrust_efficiency: float
    propellant: str

    @property
    def thrust_N(self) -> float:
        """Thrust in Newtons."""
        return self.thrust_mN / 1000.0

    def __repr__(self) -> str:
        return (
            f"Thruster({self.name}, {self.type}, "
            f"T={self.thrust_mN}mN, Isp={self.isp_s}s, "
            f"P={self.power_W}W)"
        )


@dataclass
class MissionRequirements:
    """Mission constraints and requirements."""

    delta_v_ms: float  # Required delta-v in m/s
    satellite_dry_mass_kg: float  # Satellite mass without propulsion
    available_power_W: float  # Power budget for propulsion
    mass_budget_kg: float  # Total mass constraint
    min_trl: int = 6  # Minimum technology readiness level
    max_duty_cycle: float = 3.0  # Max power ratio for duty cycling

    def __repr__(self) -> str:
        return (
            f"Mission(Δv={self.delta_v_ms}m/s, "
            f"P={self.available_power_W}W, "
            f"M_budget={self.mass_budget_kg}kg)"
        )


@dataclass
class ThrusterPerformance:
    """Performance metrics for a thruster-mission combination."""

    thruster: Thruster
    propellant_mass_kg: float
    total_mass_kg: float
    mission_duration_days: float
    num_burns_estimate: int
    fuel_ratio_percent: float
    is_feasible: bool
    infeasibility_reasons: list[str]

    # Scoring components
    mass_score: float
    time_score: float
    combined_score: float

    def __repr__(self) -> str:
        status = "✓ FEASIBLE" if self.is_feasible else "✗ INFEASIBLE"
        return (
            f"{status}: {self.thruster.name} - "
            f"Propellant: {self.propellant_mass_kg:.2f}kg, "
            f"Duration: {self.mission_duration_days:.1f}d, "
            f"Score: {self.combined_score:.2f}"
        )
