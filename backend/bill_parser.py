import re
from typing import Any, Dict

# UK National Grid carbon intensity factor (2024)
CARBON_FACTOR = 0.197  # kg CO₂ per kWh


# ─── PROVIDER DETECTION ────────────────────────────────────────────────────────

def detect_provider(text: str) -> str:
    lower = text.lower()
    if "scottish power" in lower or "scottishpower" in lower:
        return "Scottish Power"
    if "british gas" in lower or "britishgas" in lower:
        return "British Gas"
    if "octopus energy" in lower or "octopus" in lower:
        return "Octopus Energy"
    if "e.on next" in lower or " e.on" in lower or "e-on" in lower or "\neon " in lower:
        return "E.ON Next"
    if "utilita" in lower:
        return "Utilita"
    if "npower" in lower or "n-power" in lower:
        return "nPower"
    if "edf energy" in lower or "edf" in lower:
        return "EDF Energy"
    if "ovo energy" in lower or " ovo " in lower:
        return "OVO Energy"
    if "shell energy" in lower:
        return "Shell Energy"
    if "bulb energy" in lower or " bulb " in lower:
        return "Bulb Energy"
    if "so energy" in lower:
        return "So Energy"
    return "Unknown"


# ─── SHARED REGEX HELPERS ──────────────────────────────────────────────────────

def _find_amount(text: str) -> float | None:
    patterns = [
        r"(?:total\s+)?(?:amount\s+)?(?:due|to\s+pay|payable)[^£\d]{0,20}£?\s*([0-9]+\.[0-9]{2})",
        r"please\s+pay[^£\d]{0,10}£?\s*([0-9]+\.[0-9]{2})",
        r"£\s*([0-9]+\.[0-9]{2})",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                pass
    return None


def _find_kwh(text: str) -> int | None:
    m = re.search(
        r"(?:total\s+)?(?:electricity|gas)?\s*(?:used|usage|consumption)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*kWh",
        text, re.IGNORECASE,
    )
    if not m:
        m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*kWh", text, re.IGNORECASE)
    if m:
        try:
            return int(float(m.group(1)))
        except ValueError:
            pass
    return None


def _find_unit_rate(text: str) -> float | None:
    m = re.search(r"unit\s+rate[:\s]*([0-9]+\.?[0-9]*)\s*p", text, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


def _find_standing_charge(text: str) -> float | None:
    m = re.search(r"standing\s+charge[:\s]*([0-9]+\.?[0-9]*)\s*p", text, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


def _find_meter_serial(text: str) -> str | None:
    m = re.search(
        r"(?:meter\s+(?:serial|number|no)|MPAN|MSN)[:\s#]*([A-Z0-9]{6,20})",
        text, re.IGNORECASE,
    )
    return m.group(1).strip() if m else None


def _find_date(text: str, label_pattern: str) -> str | None:
    m = re.search(
        label_pattern + r"[:\s]*([0-9]{1,2}\s+\w+\s+20[0-9]{2})",
        text, re.IGNORECASE,
    )
    return m.group(1).strip() if m else None


# ─── SCOTTISH POWER ───────────────────────────────────────────────────────────

def parse_scottish_power(text: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}

    m = re.search(r"Account\s+number[:\s]*([\d ]{6,})", text, re.IGNORECASE)
    if m:
        data["account_number"] = m.group(1).strip()

    m = re.search(
        r"amount to pay[^£0-9]*£?\s*([0-9]+\.[0-9]{2})", text, re.IGNORECASE
    )
    if not m:
        m = re.search(r"£\s*([0-9]+\.[0-9]{2})", text)
    if m:
        try:
            data["amount_due"] = float(m.group(1))
        except ValueError:
            pass

    d = _find_date(text, r"Bill\s+date")
    if d:
        data["bill_date"] = d

    d = _find_date(text, r"Pay\s+by")
    if d:
        data["due_date"] = d

    kwh = _find_kwh(text)
    if kwh:
        data["usage_kwh"] = kwh

    ur = _find_unit_rate(text)
    if ur:
        data["unit_rate"] = ur

    sc = _find_standing_charge(text)
    if sc:
        data["standing_charge"] = sc

    ms = _find_meter_serial(text)
    if ms:
        data["meter_serial"] = ms

    m = re.search(r"tariff[:\s]+(.{3,50}?)(?:\n|  |$)", text, re.IGNORECASE)
    if m:
        data["tariff_name"] = m.group(1).strip()

    return data


# ─── BRITISH GAS ──────────────────────────────────────────────────────────────

def parse_british_gas(text: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}

    m = re.search(
        r"(?:account\s*(?:no|number|#)[:\s]*|A/C\s*[:\s]+)([\d\s]{6,15})",
        text, re.IGNORECASE,
    )
    if m:
        data["account_number"] = m.group(1).strip()

    amt = _find_amount(text)
    if amt:
        data["amount_due"] = amt

    d = _find_date(text, r"(?:bill|invoice|statement)\s+date")
    if not d:
        # Try same-line match using MULTILINE anchor
        m2 = re.search(r"^Bill\s+date[:\s]+([0-9]{1,2}\s+\w+\s+20[0-9]{2})", text, re.IGNORECASE | re.MULTILINE)
        if m2:
            d = m2.group(1).strip()
    if not d:
        # Try "Covering: X – DATE" pattern — end date of covering period is bill date
        m3 = re.search(r"Covering[:\s]+[^\n]*?[–\-]\s*([0-9]{1,2}\s+\w+\s+20[0-9]{2})", text, re.IGNORECASE)
        if m3:
            d = m3.group(1).strip()
    if d:
        data["bill_date"] = d

    d = _find_date(text, r"(?:pay(?:ment)?\s+(?:by|due|date)|due\s+date)")
    if d:
        data["due_date"] = d

    kwh = _find_kwh(text)
    if kwh:
        data["usage_kwh"] = kwh

    ur = _find_unit_rate(text)
    if ur:
        data["unit_rate"] = ur

    sc = _find_standing_charge(text)
    if sc:
        data["standing_charge"] = sc

    ms = _find_meter_serial(text)
    if ms:
        data["meter_serial"] = ms

    m = re.search(r"tariff[:\s]+(.{3,50}?)(?:\n|  |$)", text, re.IGNORECASE)
    if m:
        data["tariff_name"] = m.group(1).strip()

    return data


# ─── OCTOPUS ENERGY ───────────────────────────────────────────────────────────

_OCTOPUS_TARIFFS = [
    "Agile Octopus", "Go Octopus", "Octopus Go",
    "Flexible Octopus", "Octopus Tracker", "Intelligent Octopus",
    "Cosy Octopus", "Octopus Flux",
]


def parse_octopus_energy(text: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}

    m = re.search(r"(?:account[:\s]*)(A-[A-Z0-9]{6,10})", text, re.IGNORECASE)
    if not m:
        m = re.search(r"\b(A-[A-Z0-9]{6,10})\b", text)
    if m:
        data["account_number"] = m.group(1).strip()

    amt = _find_amount(text)
    if amt:
        data["amount_due"] = amt

    d = _find_date(text, r"(?:invoice|bill|statement)\s+date")
    if not d:
        dates = re.findall(r"\b([0-9]{1,2}\s+\w+\s+20[0-9]{2})\b", text)
        if dates:
            d = dates[0]
    if d:
        data["bill_date"] = d

    kwh = _find_kwh(text)
    if kwh:
        data["usage_kwh"] = kwh

    for tariff in _OCTOPUS_TARIFFS:
        if tariff.lower() in text.lower():
            data["tariff_name"] = tariff
            break

    ur = _find_unit_rate(text)
    if ur:
        data["unit_rate"] = ur

    sc = _find_standing_charge(text)
    if sc:
        data["standing_charge"] = sc

    ms = _find_meter_serial(text)
    if ms:
        data["meter_serial"] = ms

    return data


# ─── E.ON ─────────────────────────────────────────────────────────────────────

def parse_eon(text: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}

    m = re.search(r"(?:account[:\s]*)([\d]{8,12})", text, re.IGNORECASE)
    if m:
        data["account_number"] = m.group(1).strip()

    amt = _find_amount(text)
    if amt:
        data["amount_due"] = amt

    d = _find_date(text, r"(?:bill|invoice)\s+date")
    if d:
        data["bill_date"] = d

    d = _find_date(text, r"(?:pay(?:ment)?\s+(?:by|due|date)|due\s+date)")
    if d:
        data["due_date"] = d

    kwh = _find_kwh(text)
    if kwh:
        data["usage_kwh"] = kwh

    ur = _find_unit_rate(text)
    if ur:
        data["unit_rate"] = ur

    sc = _find_standing_charge(text)
    if sc:
        data["standing_charge"] = sc

    ms = _find_meter_serial(text)
    if ms:
        data["meter_serial"] = ms

    m = re.search(r"tariff[:\s]+(.{3,50}?)(?:\n|  |$)", text, re.IGNORECASE)
    if m:
        data["tariff_name"] = m.group(1).strip()

    return data


# ─── OVO ENERGY ───────────────────────────────────────────────────────────────

def parse_ovo_energy(text: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}

    m = re.search(r"(?:account[:\s]*)([\d]{6,12})", text, re.IGNORECASE)
    if m:
        data["account_number"] = m.group(1).strip()

    amt = _find_amount(text)
    if amt:
        data["amount_due"] = amt

    d = _find_date(text, r"(?:bill|statement|invoice)\s+date")
    if d:
        data["bill_date"] = d

    d = _find_date(text, r"(?:pay(?:ment)?\s+(?:by|due)|due\s+date)")
    if d:
        data["due_date"] = d

    kwh = _find_kwh(text)
    if kwh:
        data["usage_kwh"] = kwh

    ur = _find_unit_rate(text)
    if ur:
        data["unit_rate"] = ur

    sc = _find_standing_charge(text)
    if sc:
        data["standing_charge"] = sc

    ms = _find_meter_serial(text)
    if ms:
        data["meter_serial"] = ms

    m = re.search(r"(?:plan|tariff)[:\s]+(.{3,50}?)(?:\n|  |$)", text, re.IGNORECASE)
    if m:
        data["tariff_name"] = m.group(1).strip()

    return data


# ─── EDF ENERGY ───────────────────────────────────────────────────────────────

def parse_edf_energy(text: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}

    m = re.search(
        r"(?:account\s*(?:no|number|#|reference)[:\s]*)([\d\s]{6,15})",
        text, re.IGNORECASE,
    )
    if m:
        data["account_number"] = m.group(1).strip()

    amt = _find_amount(text)
    if amt:
        data["amount_due"] = amt

    d = _find_date(text, r"(?:bill|invoice|statement)\s+date")
    if d:
        data["bill_date"] = d

    d = _find_date(text, r"(?:pay(?:ment)?\s+(?:by|due)|due\s+date)")
    if d:
        data["due_date"] = d

    kwh = _find_kwh(text)
    if kwh:
        data["usage_kwh"] = kwh

    ur = _find_unit_rate(text)
    if ur:
        data["unit_rate"] = ur

    sc = _find_standing_charge(text)
    if sc:
        data["standing_charge"] = sc

    ms = _find_meter_serial(text)
    if ms:
        data["meter_serial"] = ms

    m = re.search(r"(?:tariff|product)[:\s]+(.{3,50}?)(?:\n|  |$)", text, re.IGNORECASE)
    if m:
        data["tariff_name"] = m.group(1).strip()

    return data


# ─── NPOWER ───────────────────────────────────────────────────────────────────

def parse_npower(text: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}

    m = re.search(
        r"(?:account\s*(?:no|number|#)?[:\s]+)([\d\s]{6,15})",
        text, re.IGNORECASE,
    )
    if m:
        data["account_number"] = m.group(1).strip()

    amt = _find_amount(text)
    if amt:
        data["amount_due"] = amt

    d = _find_date(text, r"(?:bill|statement)\s+date")
    if d:
        data["bill_date"] = d

    d = _find_date(text, r"(?:pay(?:ment)?\s+(?:by|due)|due\s+date|payment\s+date)")
    if d:
        data["due_date"] = d

    kwh = _find_kwh(text)
    if kwh:
        data["usage_kwh"] = kwh

    ur = _find_unit_rate(text)
    if ur:
        data["unit_rate"] = ur

    sc = _find_standing_charge(text)
    if sc:
        data["standing_charge"] = sc

    ms = _find_meter_serial(text)
    if ms:
        data["meter_serial"] = ms

    m = re.search(r"tariff[:\s]+(.{3,50}?)(?:\n|  |$)", text, re.IGNORECASE)
    if m:
        data["tariff_name"] = m.group(1).strip()

    return data


# ─── EON NEXT ─────────────────────────────────────────────────────────────────

def parse_eon_next(text: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}

    m = re.search(r"(?:account\s*(?:no|number|ref)?[:\s]+)([\w\s\-]{5,20})", text, re.IGNORECASE)
    if m:
        data["account_number"] = m.group(1).strip()

    amt = _find_amount(text)
    if amt:
        data["amount_due"] = amt

    d = _find_date(text, r"(?:bill|statement|invoice)\s+date")
    if d:
        data["bill_date"] = d

    d = _find_date(text, r"(?:pay(?:ment)?\s+(?:by|due)|due\s+date)")
    if d:
        data["due_date"] = d

    kwh = _find_kwh(text)
    if kwh:
        data["usage_kwh"] = kwh

    ur = _find_unit_rate(text)
    if ur:
        data["unit_rate"] = ur

    sc = _find_standing_charge(text)
    if sc:
        data["standing_charge"] = sc

    ms = _find_meter_serial(text)
    if ms:
        data["meter_serial"] = ms

    # E.ON Next tariff names often include "Next Flex" / "Next Fixed"
    m = re.search(r"(?:tariff|plan)[:\s]+(E\.?ON\s+Next\s+[A-Za-z\s]{2,30}|[A-Za-z\s]{3,40}?)(?:\n|  |$)",
                  text, re.IGNORECASE)
    if m:
        data["tariff_name"] = m.group(1).strip()

    return data


# ─── UTILITA ──────────────────────────────────────────────────────────────────

def parse_utilita(text: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}

    m = re.search(r"(?:account\s*(?:no|number|ref)?[:\s]+)([\d\s]{6,18})", text, re.IGNORECASE)
    if m:
        data["account_number"] = m.group(1).strip()

    amt = _find_amount(text)
    if amt:
        data["amount_due"] = amt

    d = _find_date(text, r"(?:bill|statement)\s+date")
    if d:
        data["bill_date"] = d
    else:
        # Utilita often uses "Issued:" or "Generated:"
        d = _find_date(text, r"(?:issued|generated)[:\s]+")
        if d:
            data["bill_date"] = d

    d = _find_date(text, r"(?:pay(?:ment)?\s+(?:by|due)|due\s+date)")
    if d:
        data["due_date"] = d

    kwh = _find_kwh(text)
    if kwh:
        data["usage_kwh"] = kwh

    ur = _find_unit_rate(text)
    if ur:
        data["unit_rate"] = ur

    sc = _find_standing_charge(text)
    if sc:
        data["standing_charge"] = sc

    # Utilita uses MPAN/MPRN instead of meter serial
    mpan = re.search(r"(?:MPAN|MPRN|meter\s+point)[:\s]+([\d\s]{10,21})", text, re.IGNORECASE)
    if mpan:
        data["meter_serial"] = mpan.group(1).strip()
    else:
        ms = _find_meter_serial(text)
        if ms:
            data["meter_serial"] = ms

    m = re.search(r"tariff[:\s]+(.{3,50}?)(?:\n|  |$)", text, re.IGNORECASE)
    if m:
        data["tariff_name"] = m.group(1).strip()

    return data


# ─── SHELL ENERGY ─────────────────────────────────────────────────────────────

def parse_shell_energy(text: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}

    m = re.search(r"(?:account\s*(?:no|number|ref)?[:\s]+)([\w\d\-]{5,20})", text, re.IGNORECASE)
    if m:
        data["account_number"] = m.group(1).strip()

    amt = _find_amount(text)
    if amt:
        data["amount_due"] = amt

    d = _find_date(text, r"(?:bill|statement|invoice)\s+date")
    if d:
        data["bill_date"] = d

    d = _find_date(text, r"(?:pay(?:ment)?\s+(?:by|due)|due\s+date|direct\s+debit)")
    if d:
        data["due_date"] = d

    kwh = _find_kwh(text)
    if kwh:
        data["usage_kwh"] = kwh

    ur = _find_unit_rate(text)
    if ur:
        data["unit_rate"] = ur

    sc = _find_standing_charge(text)
    if sc:
        data["standing_charge"] = sc

    ms = _find_meter_serial(text)
    if ms:
        data["meter_serial"] = ms

    # Shell Energy tariff names often follow "Shell Energy <name> Tariff"
    m = re.search(r"(?:tariff|product|plan)[:\s]+(.{3,60}?)(?:\n|  |$)", text, re.IGNORECASE)
    if m:
        data["tariff_name"] = m.group(1).strip()

    return data


# ─── GENERIC FALLBACK ─────────────────────────────────────────────────────────

def parse_generic(text: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}

    amt = _find_amount(text)
    if amt:
        data["amount_due"] = amt

    dates = re.findall(r"\b([0-9]{1,2}\s+\w+\s+20[0-9]{2})\b", text)
    if dates:
        data["bill_date"] = dates[0]
    if len(dates) > 1:
        data["due_date"] = dates[1]

    kwh = _find_kwh(text)
    if kwh:
        data["usage_kwh"] = kwh

    ur = _find_unit_rate(text)
    if ur:
        data["unit_rate"] = ur

    sc = _find_standing_charge(text)
    if sc:
        data["standing_charge"] = sc

    ms = _find_meter_serial(text)
    if ms:
        data["meter_serial"] = ms

    m = re.search(r"tariff[:\s]+(.{3,50}?)(?:\n|  |$)", text, re.IGNORECASE)
    if m:
        data["tariff_name"] = m.group(1).strip()

    return data


# ─── MAIN ENTRY POINT ─────────────────────────────────────────────────────────

_PARSERS = {
    "Scottish Power": parse_scottish_power,
    "British Gas":    parse_british_gas,
    "Octopus Energy": parse_octopus_energy,
    "E.ON Next":      parse_eon_next,
    "OVO Energy":     parse_ovo_energy,
    "EDF Energy":     parse_edf_energy,
    "nPower":         parse_npower,
    "Utilita":        parse_utilita,
    "Shell Energy":   parse_shell_energy,
}


def parse_bill(text: str) -> Dict[str, Any]:
    provider = detect_provider(text)
    result: Dict[str, Any] = {"provider": provider}

    parser = _PARSERS.get(provider, parse_generic)
    result.update(parser(text))

    if result.get("usage_kwh"):
        result["carbon_kg"] = round(result["usage_kwh"] * CARBON_FACTOR, 2)

    return result
