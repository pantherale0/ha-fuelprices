"""Fuel Prices integration const."""

DOMAIN = "fuel_prices"
NAME = "Fuel Prices"

CONF_AREAS = "areas"
CONF_SOURCES = "sources"

CONF_STATE_VALUE = "state"

CONF_LOCATION = "location"

METERS_PER_MILE = 1609

# UK sources backed by the CMA open data scheme, removed in pyfuelprices 2026.10
REMOVED_CMA_SOURCES = frozenset({
    "Applegreen",
    "ascona",
    "asda",
    "bpuk",
    "essouk",
    "jet",
    "karanretail",
    "motoway",
    "motorfuelgroup",
    "rontec",
    "sainsburys",
    "sgnretail",
    "shelluk",
    "tesco",
})

# Removed or deprecated sources mapped to the source that replaces them
REPLACED_SOURCES: dict[str, str] = {
    **dict.fromkeys(REMOVED_CMA_SOURCES, "petrolprices"),
    "directlease": "anwbonderweg",
}

# Area keys left behind by the removed cheapest stations feature
REMOVED_AREA_KEYS = (
    "cheapest_stations",
    "cheapest_stations_count",
    "cheapest_stations_fuel_type",
)

# Repair issues raised by older versions for features that no longer exist
REMOVED_ISSUE_IDS = ("deprecate_directlease", "deprecate_cheapest_stations")
