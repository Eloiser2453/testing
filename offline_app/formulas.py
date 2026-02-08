from __future__ import annotations

from typing import Dict, Iterable

SEGMENT_VARS = [f"SEG_{index}" for index in range(1, 7)]

VARIABLES: Iterable[str] = [
    "EXAM_DATE",
    "PATIENT_NAME",
    "PATIENT_AGE",
    "DIAGNOSIS",
    "RHYTHM",
    "REFERRAL",
    "PAYMENT_TYPE",
    "DEVICE",
    "LV_KDR",
    "LV_KSR",
    "LV_EDV",
    "LV_ESV",
    "LV_EF",
    "LV_IVS",
    "LV_PW",
    "LV_MASS",
    "LV_REL_WALL",
    "RV_BASE",
    "RV_MID",
    "RV_TAPSE",
    "LA_AP",
    "LA_VOL",
    "RA_AP",
    "RA_VOL",
    "AO_ROOT",
    "AO_ASC",
    "PA_DIAMETER",
    "IVC_DIAMETER",
    "MV_VE",
    "MV_VMAX",
    "MV_REGURG",
    "MV_GRADE",
    "AV_VMAX",
    "AV_GRAD",
    "AV_REGURG",
    "AV_GRADE",
    "TV_VE",
    "TV_VMAX",
    "TV_REGURG",
    "TV_GRADE",
    "PV_VMAX",
    "PV_GRAD",
    "PV_REGURG",
    "PV_GRADE",
    "REPORT_TEXT",
    "CONCLUSION_TEXT",
    "DOCTOR_NAME",
]

VARIABLES = list(VARIABLES) + SEGMENT_VARS

DEFAULT_VALUES: Dict[str, str] = {name: name for name in VARIABLES}


def compute_values() -> Dict[str, str]:
    """
    Replace this function with your own logic.

    Return a dictionary where keys are variable names (from VARIABLES) and
    values are the calculated results. By default we keep variable names as
    placeholder values so the sheet acts as a template.
    """
    return DEFAULT_VALUES.copy()
