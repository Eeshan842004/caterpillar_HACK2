import math
from typing import Any

import numpy as np


def compute_baseline_minutes(
    profile: dict[str, Any],
    task_type_name: str,
    material: str,
    quantity: float,
    job_efficiency_override: float | None = None,
) -> float | None:
    """Computes baseline task duration in minutes per technical spec §8.6.1.

    tt = profile task type; mat = task.material
    rate_per_hour =
      linear | area | count : tt.rate_per_hour[mat] ?? tt.rate_per_hour.any
      bucket                : bucket_capacity_m3 * fill_factor[mat] * (tt.cycles_per_hour_override ?? cycles_per_hour)
      haul                  : payload_t * 60 / cycle_min_default
    if rate missing or quantity <= 0 -> null
    job_efficiency = site.job_efficiency_override ?? profile.job_efficiency  # default 0.8333
    baseline_min = quantity / (rate_per_hour * job_efficiency) * 60
    """
    if quantity <= 0:
        return None

    task_types = {tt["task_type"]: tt for tt in profile.get("task_types", [])}
    if task_type_name not in task_types:
        return None

    tt = task_types[task_type_name]
    rate_model = tt.get("rate_model")
    rate_constants = profile.get("rate_constants", {})

    rate_per_hour = None
    if rate_model in ("linear", "area", "count"):
        rates = tt.get("rate_per_hour", {})
        rate_per_hour = rates.get(material)
        if rate_per_hour is None:
            rate_per_hour = rates.get("any")
    elif rate_model == "bucket":
        bucket_cap = rate_constants.get("bucket_capacity_m3", 1.0)
        fill_factors = rate_constants.get("fill_factor", {})
        fill = fill_factors.get(material, 1.0)
        cycles = tt.get("cycles_per_hour_override") or rate_constants.get("cycles_per_hour", 100)
        rate_per_hour = bucket_cap * fill * cycles
    elif rate_model == "haul":
        payload = rate_constants.get("payload_t", 90.0)
        cycle_min = rate_constants.get("cycle_min_default", 12.0)
        rate_per_hour = payload * (60.0 / cycle_min)

    if rate_per_hour is None or rate_per_hour <= 0:
        return None

    job_eff = (
        job_efficiency_override
        if job_efficiency_override is not None
        else profile.get("job_efficiency", 0.8333)
    )
    if job_eff <= 0:
        return None

    baseline_min = (quantity / (rate_per_hour * job_eff)) * 60.0
    return round(baseline_min, 4)


def compute_task_effects(
    effects_config: dict[str, Any],
    skill_level: str,
    experience_months: int,
    weather: str,
    visibility: str,
    temp_band: str,
    time_of_day: str,
    congestion: str,
    machine_age_years: int,
    material: str,
    is_wind_sensitive: bool = False,
    task_type: str = "",
    operator_effect: float = 0.0,
    site_effect: float = 0.0,
    noise: float = 0.0,
    effect_scale: float = 1.0,
) -> tuple[float, list[tuple[str, float]]]:
    """Computes total log-scale effects for a task.

    actual_active = baseline * exp(sum(effects) + operator_effect + site_effect + noise)
    Returns:
        (total_multiplier, breakdown_of_factors)
    """
    skill_cfg = effects_config.get("skill", {})
    exp_cfg = effects_config.get("experience", {})
    wx_cfg = effects_config.get("weather", {})
    vis_cfg = effects_config.get("visibility", {})
    temp_cfg = effects_config.get("temperature_band", {})
    tod_cfg = effects_config.get("time_of_day", {})
    cong_cfg = effects_config.get("congestion", {})
    age_cfg = effects_config.get("machine_age", {})
    mat_cfg = effects_config.get("material", {})

    factors = []

    # 1. Skill
    skill_val = skill_cfg.get(skill_level, 0.0)
    factors.append(("skill", skill_val))

    # 2. Experience
    exp_coef = exp_cfg.get("coef", -0.06)
    exp_anchor = exp_cfg.get("anchor_log_months", 3.0)
    plateau = exp_cfg.get("plateau_months")
    months_eff = min(experience_months, plateau) if plateau else experience_months
    exp_val = exp_coef * (math.log1p(months_eff) - exp_anchor)
    factors.append(("experience", exp_val))

    # 3. Weather
    wx_val = wx_cfg.get(weather, 0.0)
    if weather == "windy" and is_wind_sensitive:
        wx_val += wx_cfg.get("windy_sensitive_extra", 0.20)
    factors.append(("weather", wx_val))

    # 4. Visibility
    vis_val = vis_cfg.get(visibility, 0.0)
    factors.append(("visibility", vis_val))

    # 5. Temperature band
    temp_val = temp_cfg.get(temp_band, 0.0)
    factors.append(("temperature_band", temp_val))

    # 6. Time of day
    tod_val = tod_cfg.get(time_of_day, 0.0)
    factors.append(("time_of_day", tod_val))

    # 7. Congestion
    cong_val = cong_cfg.get(congestion, 0.0)
    factors.append(("congestion", cong_val))

    # 8. Machine age
    age_coef = age_cfg.get("coef_per_year", 0.012)
    age_val = age_coef * max(0, machine_age_years)
    factors.append(("machine_age", age_val))

    # 9. Material
    mat_val = mat_cfg.get(material, 0.0)
    factors.append(("material", mat_val))

    # 10. Interactions (only when both conditions hold)
    ix_cfg = effects_config.get("interactions", {})
    ix_val = 0.0
    if weather == "rain" and material == "clay" and task_type == "trenching":
        ix_val += ix_cfg.get("rain_clay_trenching", 0.0)
    if skill_level == "beginner" and time_of_day == "night":
        ix_val += ix_cfg.get("beginner_night", 0.0)
    if skill_level == "beginner" and weather == "rain":
        ix_val += ix_cfg.get("beginner_rain", 0.0)
    if congestion == "high" and task_type.startswith("haul"):
        ix_val += ix_cfg.get("high_congestion_haul", 0.0)
    factors.append(("interactions", ix_val))

    # Scale deterministic effects and random components
    scaled_effects_sum = sum(val for _, val in factors) * effect_scale
    scaled_operator_effect = operator_effect * effect_scale
    scaled_site_effect = site_effect * effect_scale

    total_log_effect = scaled_effects_sum + scaled_operator_effect + scaled_site_effect + noise
    multiplier = math.exp(total_log_effect)

    # Return multiplier and unscaled factor percentages for contributions/logging
    factor_breakdown = [(name, round(val * effect_scale, 4)) for name, val in factors]
    return multiplier, factor_breakdown


def sample_task_noise(rng: np.random.Generator, baseline_min: float, noise_cfg: dict[str, Any]) -> float:
    """Heteroscedastic, heavy-tailed log-scale noise (see config `noise_variance`)."""
    sigma = noise_cfg.get("sigma", 0.10) + noise_cfg.get("small_task_extra_sigma", 0.0) * math.exp(
        -baseline_min / max(1.0, noise_cfg.get("small_task_scale_min", 40))
    )
    noise = float(rng.normal(0, sigma))
    if rng.random() < noise_cfg.get("disruption_prob", 0.0):
        noise += float(
            rng.uniform(noise_cfg.get("disruption_min", 0.25), noise_cfg.get("disruption_max", 0.6))
        )
    return noise
