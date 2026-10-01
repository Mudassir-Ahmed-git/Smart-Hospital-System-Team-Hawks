"""Capacity forecasting with scikit-learn.

Model: Ridge regression on [time index, weekday sin/cos] fitted to daily mean occupancy %.
That captures a linear trend plus weekly seasonality, which is what hospital load mostly looks like
at this data volume. It is intentionally simple and explainable."""
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

MIN_DAYS = 4


def _features(days: pd.Series, t0: pd.Timestamp) -> np.ndarray:
    t = (days - t0).dt.days.to_numpy(dtype=float)
    dow = days.dt.dayofweek.to_numpy(dtype=float)
    return np.column_stack([t, np.sin(2 * np.pi * dow / 7), np.cos(2 * np.pi * dow / 7)])


def forecast_occupancy(history: pd.DataFrame, horizon: int = 3) -> dict:
    """history columns: date (datetime), occupancy (0-100). Returns forecast dict or {'ok': False}."""
    if history.empty:
        return {"ok": False, "reason": "no history"}
    df = history.copy()
    df["day"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
    daily = df.groupby("day", as_index=False)["occupancy"].mean().sort_values("day")
    if len(daily) < MIN_DAYS:
        return {"ok": False, "reason": f"need at least {MIN_DAYS} days of history, have {len(daily)}"}

    t0 = daily["day"].iloc[0]
    model = Ridge(alpha=1.0).fit(_features(daily["day"], t0), daily["occupancy"].to_numpy())
    last_day = daily["day"].iloc[-1]
    future_days = pd.Series(pd.date_range(last_day + pd.Timedelta(days=1), periods=horizon, freq="D"))
    preds = np.clip(model.predict(_features(future_days, t0)), 0, 100)

    # Baseline = the latest complete reading (mean of the last day), so "+20%" means vs. now.
    current = float(daily["occupancy"].iloc[-1])
    fitted = np.clip(model.predict(_features(daily["day"], t0)), 0, 100)
    residual_sd = float(np.std(daily["occupancy"].to_numpy() - fitted))
    return {
        "ok": True,
        "current": round(current, 1),
        "forecast": [{"date": d.date().isoformat(), "occupancyPct": round(float(p), 1)} for d, p in zip(future_days, preds)],
        "tomorrow": round(float(preds[0]), 1),
        "changePct": round((float(preds[0]) - current) / current * 100, 1) if current > 0 else 0.0,
        "uncertainty": round(residual_sd, 1),
        "daysOfHistory": int(len(daily)),
    }


def describe(bed_label: str, f: dict) -> tuple[str, str]:
    """(message, risk_level) in the style 'ICU demand may increase 20% tomorrow'."""
    if not f.get("ok"):
        return f"Not enough history to forecast {bed_label} demand yet.", "unknown"
    ch, tm = f["changePct"], f["tomorrow"]
    if abs(ch) < 3:
        msg = f"{bed_label} demand is expected to stay steady tomorrow (~{tm:.0f}% occupied)."
    elif ch > 0:
        msg = f"{bed_label} demand may increase {abs(ch):.0f}% tomorrow (to ~{tm:.0f}% occupied)."
    else:
        msg = f"{bed_label} demand may decrease {abs(ch):.0f}% tomorrow (to ~{tm:.0f}% occupied)."
    risk = "high" if tm >= 90 else "elevated" if tm >= 80 else "normal"
    return msg, risk
