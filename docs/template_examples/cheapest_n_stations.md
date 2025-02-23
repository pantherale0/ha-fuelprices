# Cheapest Fuel Price Sensor

This YAML configuration creates a set of sensors in Home Assistant that display the price of diesel fuel (B7, this will vary depending on country / data source) at the nearest fuel stations to your home. It uses the `fuel_prices.find_fuels` service to retrieve this data and the defined `zone.home` to get the search co-oridinates.

The template sensors will update every time HA has started, or every 12 hours.

Radius is defined in meters, so you can use whatever unit you would like (miles, km, etc) as long as it is converted to meters.

Change `zone.home` to another zone (or device tracker).

## Configuration

This configuration should be placed within your `configuration.yaml` file under the `template` section.

```yaml
- trigger:
    - platform: homeassistant
      event: start
    - platform: time_pattern
      hours: /12
  action:
    - variables:
        fuel_type: B7
        lat: |
          {{ state_attr('zone.home', 'latitude') }}
        long: |
          {{ state_attr('zone.home', 'longitude') }}
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
    - name: Home Nearest Fuel Station 1
      unique_id: Home Nearest Fuel Station 1
      state: |
        {{ data['fuels'][0].available_fuels[fuel_type] | float }}
      availability: |
        {{ data['fuels'] | count > 0 }}
      state_class: total
      device_class: monetary
      unit_of_measurement: |
        {{ data['fuels'][0].currency }}
      attributes:
        latitude: |
          {{ data['fuels'][0].latitude }}
        longitude: |
          {{ data['fuels'][0].longitude }}
        name: |
          {{ data['fuels'][0].name }}
        station: |
          {{ data['fuels'][0] }}
    - name: Home Nearest Fuel Station 2
      unique_id: Home Nearest Fuel Station 2
      state: |
        {{ data['fuels'][1].available_fuels[fuel_type] | float }}
      availability: |
        {{ data['fuels'] | count > 1 }}
      state_class: total
      device_class: monetary
      unit_of_measurement: |
        {{ data['fuels'][0].currency }}
      attributes:
        latitude: |
          {{ data['fuels'][1].latitude }}
        longitude: |
          {{ data['fuels'][1].longitude }}
        name: |
          {{ data['fuels'][1].name }}
        station: |
          {{ data['fuels'][1] }}
    - name: Home Nearest Fuel Station 3
      unique_id: Home Nearest Fuel Station 3
      state: |
        {{ data['fuels'][2].available_fuels[fuel_type] | float }}
      availability: |
        {{ data['fuels'] | count > 2 }}
      state_class: total
      device_class: monetary
      unit_of_measurement: |
        {{ data['fuels'][0].currency }}
      attributes:
        latitude: |
          {{ data['fuels'][2].latitude }}
        longitude: |
          {{ data['fuels'][2].longitude }}
        name: |
          {{ data['fuels'][2].name }}
        station: |
          {{ data['fuels'][2] }}
```
