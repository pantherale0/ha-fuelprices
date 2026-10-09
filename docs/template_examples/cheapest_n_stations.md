# Cheapest Fuel Price Sensors

This YAML configuration creates three sensors in Home Assistant showing the three cheapest fuel stations near your home for a single fuel type. It uses the `fuel_prices.find_fuels` action to retrieve the data and the `zone.home` zone for the search coordinates.

The sensors update when Home Assistant starts and every 12 hours.

## Before you start

Change these variables to suit your setup:

| Variable | Description |
| --- | --- |
| `fuel_type` | The fuel to search for, such as `B7` (diesel) or `E10` (unleaded). Fuel types vary by country and data source, check the `available_fuels` attribute of one of your fuel station sensors. |
| `source` | The data source to search, such as `petrolprices`, `fuelfinder`, `anwbonderweg` or `tankerkoenig`. It must be one of the sources configured in the integration. Setting this avoids a reverse geocoding lookup on every search, which is rate limited and is the most common cause of empty results. Use `any` to search every configured source. |
| `radius_miles` | The search radius in miles. It is converted to meters for the action. |
| `zone` | The zone to search around. |

Also change `unit_of_measurement` to match the currency of your data source, for example `EUR/L`.

## Configuration

This configuration should be placed within your `configuration.yaml` file under the `template` section.

```yaml
- triggers:
    - trigger: homeassistant
      event: start
    - trigger: time_pattern
      hours: /12
  variables:
    fuel_type: B7
    source: petrolprices
    radius_miles: 5
    zone: zone.home
  conditions:
    - condition: template
      value_template: >
        {{ state_attr(zone, 'latitude') is number
           and state_attr(zone, 'longitude') is number }}
  actions:
    - action: fuel_prices.find_fuels
      continue_on_error: true
      data:
        location:
          latitude: "{{ state_attr(zone, 'latitude') }}"
          longitude: "{{ state_attr(zone, 'longitude') }}"
          radius: "{{ radius_miles * 1609.34 }}"
        type: "{{ fuel_type }}"
        source: "{{ source }}"
      response_variable: data
  sensor:
    - name: Home Cheapest Fuel Station 1
      unique_id: home_cheapest_fuel_station_1
      variables:
        index: 0
      availability: &availability >
        {{ data is defined and data.fuels | count > index }}
      state: &state "{{ data.fuels[index].cost }}"
      unit_of_measurement: GBP/L
      state_class: measurement
      icon: mdi:gas-station
      attributes: &attributes
        name: "{{ data.fuels[index].name }}"
        brand: "{{ data.fuels[index].brand }}"
        address: "{{ data.fuels[index].address }}"
        postal_code: "{{ data.fuels[index].postal_code }}"
        latitude: "{{ data.fuels[index].latitude }}"
        longitude: "{{ data.fuels[index].longitude }}"
        distance: "{{ data.fuels[index].distance }}"
        fuel_type: "{{ fuel_type }}"
        last_updated: "{{ data.fuels[index].last_updated }}"
    - name: Home Cheapest Fuel Station 2
      unique_id: home_cheapest_fuel_station_2
      variables:
        index: 1
      availability: *availability
      state: *state
      unit_of_measurement: GBP/L
      state_class: measurement
      icon: mdi:gas-station
      attributes: *attributes
    - name: Home Cheapest Fuel Station 3
      unique_id: home_cheapest_fuel_station_3
      variables:
        index: 2
      availability: *availability
      state: *state
      unit_of_measurement: GBP/L
      state_class: measurement
      icon: mdi:gas-station
      attributes: *attributes
```

## Notes

- If the search fails (for example the source is not configured, or a data source is temporarily unavailable), the sensors become unavailable until the next successful search instead of keeping stale prices.
- To add more sensors, copy the last sensor and increase `index` by one.
- The `monetary` device class is intentionally not used, Home Assistant reserves it for amounts of money rather than prices per unit.
