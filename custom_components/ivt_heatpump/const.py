"""Constants for IVT Heat Pump integration."""

DOMAIN = "ivt_heatpump"
MANUFACTURER = "Bosch / IVT"

# Config keys
CONF_DEVICE_ID = "device_id"
CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_TOKEN_EXPIRES_AT = "token_expires_at"

# OAuth2 constants
POINTT_BASE_URL = "https://pointt-api.bosch-thermotechnology.com/pointt-api/api/v1/gateways/"
TOKEN_URL = "https://singlekey-id.com/auth/connect/token"
CLIENT_ID = "762162C0-FA2D-4540-AE66-6489F189FADC"
REDIRECT_URI = "com.bosch.tt.dashtt.pointt://app/login"
CODE_VERIFIER = "abcdefghijklmnopqrstuvwxyz0123456789abcdefghijklm"
SCOPES = [
    "openid", "email", "profile", "offline_access",
    "pointt.gateway.claiming", "pointt.gateway.removal",
    "pointt.gateway.list", "pointt.gateway.users",
    "pointt.gateway.resource.dashapp", "pointt.castt.flow.token-exchange",
    "bacon",
]

# Polling
DEFAULT_SCAN_INTERVAL = 60  # seconds

# ── Heating Circuit (HC) ────────────────────────────────────
# API paths (relative to /heatingCircuits/hc1/)
HC_ROOM_TEMP = "/heatingCircuits/hc1/roomtemperature"
HC_CURRENT_SETPOINT = "/heatingCircuits/hc1/currentRoomSetpoint"
HC_TEMP_OVERRIDE = "/heatingCircuits/hc1/temporaryRoomSetpoint"
HC_OPERATION_MODE = "/heatingCircuits/hc1/operationMode"
HC_ACTIVE_PROGRAM = "/heatingCircuits/hc1/activeSwitchProgram"
HC_STATUS = "/heatingCircuits/hc1/overallStatus"
HC_COMFORT2_TEMP = "/heatingCircuits/hc1/temperatureLevels/comfort2"
HC_ECO_TEMP = "/heatingCircuits/hc1/temperatureLevels/eco"
HC_MAX_FLOW_TEMP = "/heatingCircuits/hc1/maxFlowTemp"
HC_HEATING_TYPE = "/heatingCircuits/hc1/heatingType"
HC_CONTROL_TYPE = "/heatingCircuits/hc1/controlType"
HC_HEAT_COOL_MODE = "/heatingCircuits/hc1/heatCoolMode"
HC_SUWI_MODE = "/heatingCircuits/hc1/currentSuWiMode"
HC_SUWI_SWITCH = "/heatingCircuits/hc1/suWiSwitchMode"
HC_SUWI_THRESHOLD = "/heatingCircuits/hc1/suWiThreshold"

# HC temperature limits (from API)
HC_TEMP_MIN = 5.0
HC_TEMP_MAX = 30.0

# HC modes
HC_MODE_MANUAL = "manual"
HC_MODE_AUTO = "auto"

# ── Hot Water (DHW) ─────────────────────────────────────────
DHW_ACTUAL_TEMP = "/dhwCircuits/dhw1/actualTemp"
DHW_CURRENT_SETPOINT = "/dhwCircuits/dhw1/currentSetpoint"
DHW_OPERATION_MODE = "/dhwCircuits/dhw1/operationMode"
DHW_STATUS = "/dhwCircuits/dhw1/overallStatus"
DHW_CHARGE = "/dhwCircuits/dhw1/charge"
DHW_CHARGE_DURATION = "/dhwCircuits/dhw1/chargeDuration"
DHW_SINGLE_CHARGE_SETPOINT = "/dhwCircuits/dhw1/singleChargeSetpoint"
DHW_REDUCE_TEMP_ON_ALARM = "/dhwCircuits/dhw1/reduceTempOnAlarm"
DHW_TD_MODE = "/dhwCircuits/dhw1/tdMode"
DHW_TEMP_ECO = "/dhwCircuits/dhw1/temperatureLevels/eco"
DHW_TEMP_HIGH = "/dhwCircuits/dhw1/temperatureLevels/high"
DHW_TEMP_LOW = "/dhwCircuits/dhw1/temperatureLevels/low"
DHW_TEMP_OFF = "/dhwCircuits/dhw1/temperatureLevels/off"

# DHW modes (Bosch API values)
DHW_MODE_OFF = "Off"
DHW_MODE_ECO = "low"       # ECO+ in IVT app
DHW_MODE_LOW = "eco"       # ECO in IVT app
DHW_MODE_HIGH = "high"     # Comfort in IVT app
DHW_MODE_AUTO = "ownprogram"  # Auto/Schedule in IVT app

# DHW mode → temperature limits (from API)
DHW_TEMP_LIMITS = {
    DHW_MODE_ECO: {"min": 30.0, "max": 43.0},
    DHW_MODE_LOW: {"min": 30.0, "max": 48.0},
    DHW_MODE_HIGH: {"min": 30.0, "max": 47.0},
}

# ── Heat Sources ─────────────────────────────────────────────
HS_ACTUAL_MODULATION = "/heatSources/actualModulation"
HS_SUPPLY_TEMP = "/heatSources/actualSupplyTemperature"
HS_RETURN_TEMP = "/heatSources/returnTemperature"
HS_CH_STATUS = "/heatSources/chStatus"
HS_HEAT_DEMAND = "/heatSources/actualHeatDemand"
HS_NUM_STARTS = "/heatSources/numberOfStarts"
HS_TYPE = "/heatSources/hs1/type"
HS_HP_TYPE = "/heatSources/hs1/heatPumpType"
HS_STANDBY = "/heatSources/standbyMode"
HS_EM_STATUS = "/heatSources/emStatus"

# ── System ───────────────────────────────────────────────────
SYS_OUTDOOR_TEMP = "/system/sensors/temperatures/outdoor_t1"
SYS_DATETIME = "/system/dateTime"
SYS_BUS = "/system/bus"
SYS_BRAND = "/system/brand"
SYS_COUNTRY = "/system/country"

# ── Gateway ──────────────────────────────────────────────────
GW_FIRMWARE = "/gateway/versionFirmware"
GW_HARDWARE = "/gateway/versionHardware"
GW_DATETIME = "/gateway/dateTime"
GW_UUID = "/gateway/uuid"
GW_IP = "/gateway/wifi/ip/ipv4"
GW_MAC = "/gateway/wifi/mac"
GW_SSID = "/gateway/wifi/ssid"
GW_SERIAL = "/gateway/serialId"
GW_SW_PREFIX = "/gateway/swPrefix"
GW_TIMEZONE = "/gateway/tzInfo/timeZone"

# ── System (additional) ─────────────────────────────────────
SYS_TYPE = "/system/type"
SYS_INFO = "/system/info"

# ── Heat Source (per-source starts) ──────────────────────────
HS_HS1_STARTS = "/heatSources/hs1/numberOfStarts"

# ── Notifications ────────────────────────────────────────────
NOTIFICATIONS = "/notifications"

# ── Recordings (Energy Monitoring) ──────────────────────────
# Fetched at runtime — these are the endpoint paths
REC_TOTAL_COMPRESSOR = "/recordings/heatSources/emon/total/compressor"
REC_TOTAL_EHEATER = "/recordings/heatSources/emon/total/eheater"
REC_TOTAL_OUTPUT = "/recordings/heatSources/emon/total/outputProduced"
REC_CH_COMPRESSOR = "/recordings/heatSources/emon/ch/compressor"
REC_CH_EHEATER = "/recordings/heatSources/emon/ch/eheater"
REC_CH_OUTPUT = "/recordings/heatSources/emon/ch/outputProduced"
REC_DHW_COMPRESSOR = "/recordings/heatSources/emon/dhw/compressor"
REC_DHW_EHEATER = "/recordings/heatSources/emon/dhw/eheater"
REC_DHW_OUTPUT = "/recordings/heatSources/emon/dhw/outputProduced"
REC_COOLING_COMPRESSOR = "/recordings/heatSources/emon/cooling/compressor"
REC_COOLING_OUTPUT = "/recordings/heatSources/emon/cooling/outputProduced"
REC_SUPPLY_TEMP = "/recordings/heatSources/actualSupplyTemperature"

# ── Variable Tariff ──────────────────────────────────────────
VT_CH_OPTIMIZATION = "/system/variableTariff/ch/optimization"
VT_CH_HIGH_DELTA = "/system/variableTariff/ch/highPriceDelta"
VT_CH_LOW_DELTA = "/system/variableTariff/ch/lowPriceDelta"
VT_CH_MID_SETPOINT = "/system/variableTariff/ch/midPriceSetpoint"
VT_DHW_OPTIMIZATION = "/system/variableTariff/dhw/optimization"
VT_DHW_HIGH_ENABLE = "/system/variableTariff/dhw/highPriceEnable"
VT_DHW_LOW_ENABLE = "/system/variableTariff/dhw/lowPriceEnable"
