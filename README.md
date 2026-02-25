# IVT Heat Pump — Home Assistant Integration

A clean, standalone Home Assistant custom component for **IVT / Bosch heat pumps** using the **PoinTT OAuth2 API** (cloud, via K30 gateway).

Built specifically for IVT heat pumps — no generic abstractions, no database JSON configs. Direct API calls, readable code.

## Features

### Climate (Heating Circuit)
- **Modes:** Heat (manual) / Auto (schedule)
- **Temperature control:** 5–30°C via temporaryRoomSetpoint
- **Presets:** Comfort / ECO (schedule temperature levels)
- **Attributes:** room temp, setpoint, active program A/B, summer/winter mode

### Water Heater (Hot Water)
- **Modes:** Off / ECO+ / ECO / Comfort / Auto
- **Temperature:** per-mode setpoints (each mode has its own range)
- **Extra Hot Water:** start/stop charge, configurable duration & setpoint
- **Away mode:** maps to Extra Hot Water charge

### Sensors (30+ sensors)
- **Temperatures:** outdoor, room, supply, return, DHW, all setpoints
- **Status:** heating status, DHW status, heat demand, compressor modulation
- **Heat pump:** type, starts count, standby mode
- **Energy monitoring:** compressor, e-heater, and heat output for CH/DHW/total

### Number Controls (adjustable settings)
- Heating comfort & ECO levels
- Max flow temperature
- Summer/winter threshold
- DHW temperature levels (ECO, ECO+, Comfort)
- Extra hot water setpoint & duration
- Variable tariff settings

### Switches
- Reduce DHW temp on alarm
- Tariff optimization (CH & DHW)

### Buttons
- Start / Stop Extra Hot Water charge

## Installation

### HACS (recommended)
1. Add this repository as a custom repository in HACS
2. Install "IVT Heat Pump"
3. Restart Home Assistant
4. Add integration via Settings → Integrations

### Manual
Copy `custom_components/ivt_heatpump/` to your HA `custom_components/` directory.

## Setup

### Option 1: Manual token entry
If you already have tokens (e.g. from the bosch-thermostat-client-python `tokens.json`):
1. Enter your Device ID (gateway serial number)
2. Paste access_token, refresh_token

### Option 2: OAuth login
1. Enter Device ID
2. Open the provided OAuth URL in a browser
3. Log in with your Bosch SingleKey ID
4. Paste the callback redirect URL

## API Endpoints Used

| Endpoint | Description |
|---|---|
| `/heatingCircuits/hc1/*` | Heating circuit control |
| `/dhwCircuits/dhw1/*` | Hot water circuit control |
| `/heatSources/*` | Heat pump status & diagnostics |
| `/system/sensors/temperatures/*` | System temperature sensors |
| `/recordings/heatSources/emon/*` | Energy consumption history |
| `/system/variableTariff/*` | Dynamic electricity tariff |

## Requirements

- IVT heat pump with K30 gateway
- Bosch PoinTT cloud account (Bosch HomeCom app)
- Home Assistant 2024.1+

## License

MIT
