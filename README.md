# Electric Propulsion Thruster Selection Tool

Command-line tool for selecting electric propulsion thrusters for small satellite missions.

## Quick Start

```bash
python main.py --delta-v 800 --sat-mass 12 --power 30 --budget 18
```

## Features

- Physics-based evaluation using Tsiolkovsky equation
- Filters by power, mass, and TRL constraints
- Ranks by propellant efficiency vs. mission duration
- Includes 10 real thrusters (Hall, ion, FEEP, electrospray, resistojets, PPT)

## Usage

```bash
# Basic usage
python main.py --delta-v 800 --sat-mass 12 --power 30 --budget 18

# Show all options
python main.py --delta-v 800 --sat-mass 12 --power 30 --budget 18 --show-all

# Adjust optimization weights
python main.py --delta-v 800 --sat-mass 12 --power 30 --budget 18 --mass-weight 0.2 --time-weight 0.8
```

## Arguments

**Required**: `--delta-v` (m/s), `--sat-mass` (kg), `--power` (W), `--budget` (kg)

**Optional**: `--min-trl` (default: 6), `--duty-cycle` (default: 3.0), `--mass-weight` (default: 0.4), `--time-weight` (default: 0.6), `--show-all`, `--verbose`, `--data`

## Scoring Methodology

Thrusters are ranked using a weighted economic model from [Lascombes et al., 2019]:

```python
score = w_mass × (total_mass / budget) + w_time × (duration / year)
```

**Why these two metrics?**

- Reflects real mission economics: launch costs (mass) + operations costs (time)
- Isp is implicitly captured: higher Isp → less propellant → lower mass score

**Default weights**: 40% mass, 60% time

**Customize via CLI**:

```bash
# Prioritize mass savings
python main.py ... --mass-weight 0.7 --time-weight 0.3

# Prioritize mission speed
python main.py ... --mass-weight 0.3 --time-weight 0.7
```

**Reference**: Paper 2, Section IV.B.3, Equation (3)

## Scaling to Larger Catalogs

**For 100+ thrusters**: Replace JSON with SQLite for indexed queries and faster filtering.

**For richer criteria**: Extend `MissionRequirements` to include thermal constraints (max temp, dissipation), attitude control (disturbance torque), reliability metrics (lifetime, MTBF), and operational factors (propellant availability, GSE). Add performance curves for throttling and multi-mode thrusters.

**For broader reach**: Migrate CLI from argparse → Click (better UX, validation) → FastAPI/Flask web app (multi-user, visualization, batch processing). Core `calculator.py` and `selector.py` modules remain reusable across all interfaces.

## References

- O'Reilly, D., et al. (2021). "Electric Propulsion Methods for Small Satellites: A Review." _Aerospace_, 8(1), 22.
- Lascombes, P., et al. (2019). "Electric Propulsion for Small Satellites: A Case Study." _36th IEPC_.

---

**Author**: Lohith Tarikere Prasanna (loh.t.prasanna@fau.de)
