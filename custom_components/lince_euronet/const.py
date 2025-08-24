"""Constants for the Lince Euronet integration."""

from homeassistant.helpers.entity import EntityCategory

DOMAIN = "lince_euronet"

INGRESSI_COLUMNS = [
    "allarme_24h",
    "ingresso_aperto",
    "ingresso_escluso",
    "memoria_24h",
    "memoria_allarme",
]

SYSTEM_STATUS_SENSORS = [
    # (unique_id, name, temp index, bitmask)
    ("fail", "Guasto", 0, 16),
    ("allarme", "Allarme", 0, 4),
    ("fuse", "Fusibile Uscite", 3, 16),
    ("mains", "Rete 220V presente", 0, 1),
    ("charge_ext", "Stato di carica batteria esterna", 0, 32),
    ("charge_int", "Stato di carica batteria di Centrale", 0, 2),
    ("exp1", "Espansione 1", 8, 1),
    ("exp2", "Espansione 2", 8, 2),
    ("exp3", "Espansione 3", 8, 4),
    ("exp4", "Espansione 4", 8, 8),
    ("exp5", "Espansione 5", 8, 16),
    ("expr", "Espansione Radio", 8, 32),
    ("expc", "Conflitto Espansione Radio", 8, 64),
    ("tamper_int", "Sabotaggio Centrale", 0, 64),
    ("as", "Sabotaggio Allarme Ingresso", 0, 128),
    ("dual_bal", "Sabotaggio Ingressi", 9, 4),
    ("tamper_ext", "Sabotaggio Dispositivi su BUS", 2, 16),
    ("bus_fail", "Allarme Integrità BUS", 2, 32),
    ("tamper_intM", "Memoria Sabotaggio Centrale", 1, 1),
    ("asM", "Memoria Sabotaggio Allarme Ingresso", 1, 2),
    ("dual_balM", "Memoria Sabotaggio Ingressi", 9, 128),
    ("tamper_extM", "Memoria Sabotaggio Dispositivi su BUS", 2, 16),
    ("bus_failM", "Memoria Allarme integrità BUS", 1, 8),
    ("alarm", "Ingressi Aperti", 9, 2),
    ("esclusi", "Ingressi Esclusi", 9, 1),
]

NUMERIC_SYSTEM_SENSORS = [
    # (unique_id, name, temp_idx, conversion_fn, unit, device_class, entity_category)
    ("vbatt", "Tensione batteria", 4, lambda v: v / 100, "V", "voltage"),
    ("rev_sw", "Rel SW centrale", 5, lambda v: v / 100, None, None),
    ("vbus", "Tensione BUS", 6, lambda v: round(v / 183, 2), "V", "voltage"),
    ("temp", "Temperatura", 7, lambda v: round((v - 2000) / 12), "°C", "temperature"),
]

GSTATE_SYSTEM_SENSORS = [
    # (unique_id, name, char)
    ("G1", "Stato G1", "1"),
    ("G2", "Stato G2", "2"),
    ("G3", "Stato G3", "3"),
    ("Gext", "Stato Gext", "4"),
    ("Servizio", "Stato Servizio", "S"),
]
