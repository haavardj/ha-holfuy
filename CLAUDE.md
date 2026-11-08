# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Home Assistant custom integration (domain `holfuy`) that polls the Holfuy live API
and exposes weather-station readings as sensor entities. Distributed through HACS
(`hacs.json`) or by copying `custom_components/holfuy/` into a Home Assistant config
directory.

The HTTP client lives in a separate repo and PyPI package,
[pyholfuy](https://github.com/haavardj/pyholfuy) (import name `holfuy`). Changes to
request parameters, units, timeouts or error handling belong there, followed by a
release and a bump of the pin in `manifest.json` (`requirements`) and `pyproject.toml`.

## Commands

Dev dependencies are a PEP 735 dependency group in `pyproject.toml` (use `uv`):

```sh
uv sync                                   # .venv with homeassistant, pyholfuy, stubs, ruff, pyright
uv run ruff check custom_components       # lint
uv run ruff format custom_components      # format
uv run pyright                            # type check (pyproject points pyright at .venv)
```

There are no tests. CI (`.github/workflows/validate.yml`) runs HACS validation and
hassfest on push, PR and nightly; hassfest checks `manifest.json` (keys must stay in
alphabetical order after `domain` and `name`) and `strings.json`.

## Architecture

One config entry = one Holfuy API key. The key gives access to a set of stations;
the integration discovers them (`s=all`), it does not ask for station IDs.

- `coordinator.py`: `HolfuyDataUpdateCoordinator` calls `HolfuyService.fetch_data()`
  every 5 minutes with the library defaults (newest reading, °C, m/s) and reshapes the
  response into `{station_id: {"Name", "Temperature", "Pressure", "RelativeHumidity",
  "Wind", "WindGust", "WindBearing"}}`. It also sets `available_station_ids`.
  The library returns `None` on HTTP, network and JSON errors instead of raising;
  the coordinator turns that into `{}`, so a failed fetch does not raise `UpdateFailed`.
- `__init__.py`: builds service + coordinator, runs the first refresh, stores the
  coordinator in `config_entry.runtime_data` (`HolfuyWeatherData`), forwards to the
  sensor platform.
- `sensor.py`: creates one `HolfuySensor` per (station, `SENSOR_TYPES` entry) from
  `available_station_ids` at setup time; stations that appear later need a reload.
  Each `HolfuySensorDescription.key` must match a key in the coordinator's per-station
  dict. Missing data reads as `None` (unknown). One HA device per station, identified
  by `(DOMAIN, station_id)`.
- `config_flow.py`: single user step asking for the API key.

Unique IDs are `f"{station_name}-{key}".lower()`, so renaming a station on Holfuy
changes entity IDs.

## Gotchas

- Home Assistant loads UI text for custom integrations from `translations/*.json` only;
  `strings.json` is not read at runtime. Keep `translations/en.json` identical to
  `strings.json`, write plain text (no `[%key:…%]` references, which only core's build
  resolves), and add every new key to `nb.json` too.
- `const.py` holds unused leftovers (`ATTR_MAP`, `SCAN_INTERVAL`, `CONF_STATION_ID`).
- `entry["wind"]` in the coordinator raises `KeyError` if any station lacks wind data,
  failing the update for all stations.
- The coordinator wraps the call in a 10 s `async_timeout` (deprecated; use
  `asyncio.timeout`), shorter than the library's own 30 s.
- `async_update_entry` in `__init__.py` is never registered as an update listener, and
  `cleanup_old_device` targets a device this integration never creates.
- Versions: `manifest.json` 0.2.0, `pyproject.toml` 0.1. Library pin is
  `pyholfuy==0.1.0` in the manifest and `pyholfuy>=0.1` in `pyproject.toml`; PyPI has 0.2.
