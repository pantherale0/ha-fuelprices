# Cheapest Fuel Price Sensor based on a device tracker

This YAML configuration creates a sensor in Home Assistant that displays the price of diesel fuel (B7, this will vary depending on country / data source) at the nearest fuel stations to a given device tracker. It uses the `fuel_prices.find_fuels` action to retrieve this data.

The template sensors will update every time HA has started, or whenever your device tracker state changes.

Radius is defined in meters, so you can use whatever unit you would like (miles, km, etc) as long as it is converted to meters.

Change `sensor.device_tracker_here` to another device tracker.

## Configuration

This configuration should be placed within your `configuration.yaml` file under the `template` section.

```yaml
- trigger:
    - platform: state
      entity_id:
        - sensor.device_tracker_here
      attribute: longitude
    - platform: state
      entity_id:
        - sensor.device_tracker_here
      attribute: latitude
    - platform: homeassistant
      event: start
  action:
    - variables:
        fuel_type: B7
        lat: |
          {{ state_attr('sensor.device_tracker_here', 'latitude') | float }}
        long: |
          {{ state_attr('sensor.device_tracker_here', 'longitude') | float }}
        radius: |
          {{ 5 * 1609.34 }} # 5 miles converted to meters
    - service: fuel_prices.find_fuels
      data:
        location:
          latitude: |
            {{ lat }}
          longitude: |
            {{ long }}
          radius: |
            {{ radius }}
        type: |
          {{ fuel_type }}
      response_variable: data
  sensor:
    - name: Device Tracker Cheapest Fuel Station
      unique_id: Device Tracker Cheapest Fuel Station
      state: |
        {{ data['fuels'][0].available_fuels[fuel_type] | float }}
      availability: |
        {{ data['fuels'] | count > 0 }}
      state_class: total
      device_class: monetary
      unit_of_measurement: |
        {{ data['fuels'][0].currency }}
      attributes:
        other_stations: |
          {{ data }}
        latitude: |
          {{ data['fuels'][0].latitude }}
        longitude: |
          {{ data['fuels'][0].longitude }}
        name: |
          {{ data['fuels'][0].name }}
        station: |
          {{ data['fuels'][0] }}
```
