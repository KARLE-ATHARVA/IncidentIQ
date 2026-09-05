from datetime import datetime, timezone
from pathlib import Path
import sys
from uuid import uuid4


# Allow `python test_detection_manual.py` when run from `backend/`.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from backend.app.services.detection import (
    DetectionConfig,
    DetectionStatus,
    detect_anomaly,
)


service_id = uuid4()
metric_event_id = uuid4()
observed_at = datetime.now(timezone.utc)


# ---------------------------------------------------------
# Shared historical baseline
# ---------------------------------------------------------

historical_values = [
    100,
    102,
    98,
    101,
    99,
    103,
    100,
    101,
    99,
    102,
]


# =========================================================
# TEST 1 — Normal value
# =========================================================

normal_result = detect_anomaly(
    service_id=service_id,
    metric_event_id=metric_event_id,
    metric_name="checkout_latency",
    current_value=101,
    observed_at=observed_at,
    historical_values=historical_values,
    recent_values=[
        100,
        101,
        99,
        102,
    ],
)


print("\n--- NORMAL TEST ---")
print("Status:", normal_result.status)
print("Baseline:", normal_result.baseline_value)
print("Z-score:", normal_result.z_score)
print("Robust Z-score:", normal_result.robust_z_score)
print("Percentage deviation:", normal_result.percentage_deviation)
print("Direction:", normal_result.direction)
print("Anomalous observations:", normal_result.anomalous_observations)
print("Detection method:", normal_result.detection_method)
print("Explanation:", normal_result.explanation)


# =========================================================
# TEST 2 — Sustained anomaly
# =========================================================

anomaly_result = detect_anomaly(
    service_id=service_id,
    metric_event_id=metric_event_id,
    metric_name="checkout_latency",
    current_value=165,
    observed_at=observed_at,
    historical_values=historical_values,
    recent_values=[
        150,
        155,
        160,
    ],
)


print("\n--- SUSTAINED ANOMALY TEST ---")
print("Status:", anomaly_result.status)
print("Baseline:", anomaly_result.baseline_value)
print("Z-score:", anomaly_result.z_score)
print("Robust Z-score:", anomaly_result.robust_z_score)
print("Percentage deviation:", anomaly_result.percentage_deviation)
print("Direction:", anomaly_result.direction)
print("Anomalous observations:", anomaly_result.anomalous_observations)
print("Detection method:", anomaly_result.detection_method)
print("Explanation:", anomaly_result.explanation)


# =========================================================
# TEST 3 — Single transient spike
# =========================================================

transient_result = detect_anomaly(
    service_id=service_id,
    metric_event_id=metric_event_id,
    metric_name="checkout_latency",
    current_value=150,
    observed_at=observed_at,
    historical_values=historical_values,
    recent_values=[
        100,
        101,
        99,
        102,
    ],
)


print("\n--- TRANSIENT SPIKE TEST ---")
print("Status:", transient_result.status)
print("Baseline:", transient_result.baseline_value)
print("Z-score:", transient_result.z_score)
print("Robust Z-score:", transient_result.robust_z_score)
print("Percentage deviation:", transient_result.percentage_deviation)
print("Direction:", transient_result.direction)
print("Anomalous observations:", transient_result.anomalous_observations)
print("Detection method:", transient_result.detection_method)
print("Explanation:", transient_result.explanation)


# =========================================================
# TEST 4 — Insufficient historical data
# =========================================================

insufficient_result = detect_anomaly(
    service_id=service_id,
    metric_event_id=metric_event_id,
    metric_name="checkout_latency",
    current_value=150,
    observed_at=observed_at,
    historical_values=[
        100,
        101,
        99,
    ],
    recent_values=[
        100,
        101,
        99,
    ],
)


print("\n--- INSUFFICIENT DATA TEST ---")
print("Status:", insufficient_result.status)
print("Explanation:", insufficient_result.explanation)


# =========================================================
# TEST 5 — Zero variance
# =========================================================

zero_variance_result = detect_anomaly(
    service_id=service_id,
    metric_event_id=metric_event_id,
    metric_name="stable_latency",
    current_value=165,
    observed_at=observed_at,
    historical_values=[
        100,
        100,
        100,
        100,
        100,
        100,
        100,
        100,
        100,
        100,
    ],
    recent_values=[
        150,
        155,
        160,
    ],
)


print("\n--- ZERO VARIANCE TEST ---")
print("Status:", zero_variance_result.status)
print("Baseline:", zero_variance_result.baseline_value)
print("Standard deviation:", zero_variance_result.standard_deviation)
print("Median:", zero_variance_result.median)
print("MAD:", zero_variance_result.mad)
print("Z-score:", zero_variance_result.z_score)
print("Robust Z-score:", zero_variance_result.robust_z_score)
print("Direction:", zero_variance_result.direction)
print("Anomalous observations:", zero_variance_result.anomalous_observations)
print("Detection method:", zero_variance_result.detection_method)
print("Explanation:", zero_variance_result.explanation)


# =========================================================
# TEST 6 — Zero baseline
# =========================================================

zero_baseline_result = detect_anomaly(
    service_id=service_id,
    metric_event_id=metric_event_id,
    metric_name="error_count",
    current_value=10,
    observed_at=observed_at,
    historical_values=[
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    ],
    recent_values=[
        10,
        10,
        10,
    ],
)


print("\n--- ZERO BASELINE TEST ---")
print("Status:", zero_baseline_result.status)
print("Baseline:", zero_baseline_result.baseline_value)
print("Percentage deviation:", zero_baseline_result.percentage_deviation)
print("Z-score:", zero_baseline_result.z_score)
print("Robust Z-score:", zero_baseline_result.robust_z_score)
print("Direction:", zero_baseline_result.direction)
print("Anomalous observations:", zero_baseline_result.anomalous_observations)
print("Detection method:", zero_baseline_result.detection_method)
print("Explanation:", zero_baseline_result.explanation)


# =========================================================
# TEST 7 — Negative values
# =========================================================

negative_result = detect_anomaly(
    service_id=service_id,
    metric_event_id=metric_event_id,
    metric_name="temperature_delta",
    current_value=-150,
    observed_at=observed_at,
    historical_values=[
        -100,
        -102,
        -98,
        -101,
        -99,
        -103,
        -100,
        -101,
        -99,
        -102,
    ],
    recent_values=[
        -150,
        -155,
        -160,
    ],
)


print("\n--- NEGATIVE VALUES TEST ---")
print("Status:", negative_result.status)
print("Baseline:", negative_result.baseline_value)
print("Z-score:", negative_result.z_score)
print("Robust Z-score:", negative_result.robust_z_score)
print("Percentage deviation:", negative_result.percentage_deviation)
print("Direction:", negative_result.direction)
print("Anomalous observations:", negative_result.anomalous_observations)
print("Detection method:", negative_result.detection_method)
print("Explanation:", negative_result.explanation)


# =========================================================
# TEST 8 — Invalid configuration
# =========================================================

print("\n--- INVALID CONFIGURATION TEST ---")

try:
    invalid_config = DetectionConfig(
        persistence_window=0,
    )

    detect_anomaly(
        service_id=service_id,
        metric_event_id=metric_event_id,
        metric_name="checkout_latency",
        current_value=101,
        observed_at=observed_at,
        historical_values=historical_values,
        recent_values=[],
        config=invalid_config,
    )

    print("ERROR: Invalid configuration was accepted.")

except ValueError as error:
    print("Correctly rejected invalid configuration.")
    print("Error:", error)