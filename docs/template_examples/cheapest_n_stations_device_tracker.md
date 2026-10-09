# Cheapest Fuel Price Sensor based on a device tracker

This YAML configuration creates a sensor in Home Assistant showing the cheapest fuel station near a device tracker (or person) for a single fuel type. It uses the `fuel_prices.find_fuels` action to retrieve the data.

The sensor updates when Home Assistant starts and every 15 minutes, as long as the tracker has a location. It deliberately does not update on every location change, as GPS trackers can report several updates a minute which would flood the data sources with searches.

## Before you start

Change these variables to suit your setup:

| Variable | Description |
| --- | --- |
| `tracker` | The `device_tracker` or `person` entity to search around. It must have `latitude` and `longitude` attributes. |
| `fuel_type` | The fuel to search for, such as `B7` (diesel) or `E10` (unleaded). Fuel types vary by country and data source, check the `available_fuels` attribute of one of your fuel station sensors. |
| `source` | The data source to search, such as `petrolprices`, `fuelfinder`, `anwbonderweg` or `tankerkoenig`. It must be one of the sources configured in the integration. Setting this avoids a reverse geocoding lookup on every search, which is rate limited and is the most common cause of empty results. Use `any` if you travel between countries, but expect occasional empty results. |
| `radius_miles` | The search radius in miles. It is converted to meters for the action. |

Also change `unit_of_measurement` to match the currency of your data source, for example `EUR/L`.

## Configuration

This configuration should be placed within your `configuration.yaml` file under the `template` section.

```yaml
- triggers:
    - trigger: homeassistant
      event: start
    - trigger: time_pattern
      minutes: /15
  variables:
    tracker: device_tracker.my_phone
    fuel_type: B7
    source: petrolprices
    radius_miles: 5
  conditions:
    - condition: template
      value_template: >
        {{ state_attr(tracker, 'latitude') is number
           and state_attr(tracker, 'longitude') is number }}
  actions:
    - action: fuel_prices.find_fuels
      continue_on_error: true
      data:
        location:
          latitude: "{{ state_attr(tracker, 'latitude') }}"
          longitude: "{{ state_attr(tracker, 'longitude') }}"
          radius: "{{ radius_miles * 1609.34 }}"
        type: "{{ fuel_type }}"
        source: "{{ source }}"
      response_variable: data
  sensor:
    - name: Device Tracker Cheapest Fuel Station
      unique_id: device_tracker_cheapest_fuel_station
      availability: >
        {{ data is defined and data.fuels | count > 0 }}
      state: "{{ data.fuels[0].cost }}"
      unit_of_measurement: GBP/L
      state_class: measurement
      icon: mdi:gas-station
      attributes:
        name: "{{ data.fuels[0].name }}"
        brand: "{{ data.fuels[0].brand }}"
        address: "{{ data.fuels[0].address }}"
        postal_code: "{{ data.fuels[0].postal_code }}"
        latitude: "{{ data.fuels[0].latitude }}"
        longitude: "{{ data.fuels[0].longitude }}"
        distance: "{{ data.fuels[0].distance }}"
        fuel_type: "{{ fuel_type }}"
        last_updated: "{{ data.fuels[0].last_updated }}"
        stations_found: "{{ data.fuels | count }}"
```

## Notes

- If the tracker has no location (for example it is unavailable), the search is skipped and the sensor keeps its last value.
- If the search fails (for example the source is not configured, or a data source is temporarily unavailable), the sensor becomes unavailable until the next successful search instead of showing a stale price.
- Only a summary of the cheapest station is stored. Storing the full search results as an attribute can exceed Home Assistant's 16 KB attribute limit, which stops the state from being recorded. Use the `fuel_prices.find_fuels` action directly if you need every result.
- The `monetary` device class is intentionally not used, Home Assistant reserves it for amounts of money rather than prices per unit.
