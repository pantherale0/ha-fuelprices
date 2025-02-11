# Installation

1. Add the repository to HACS
1. Install integration
1. Follow prompts to configure integration

## Configuration Parameters

The main configuration entry point is provided via a configuration flow. Using a `configuration.yaml` file to configure is not supported and will not be added in the future following Home Assistant's own design principles

### Area Configuration Options

| Option                      | Description                                                                                                                                                                                          | Type                               | Default |
|-----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------|---------|
| `name`                      | (Required) The name of the area.                                                                                                                                                                      | Text                      | None    |
| `radius`                    | (Required) The radius of the area in miles.                                                                                                                                                            | Number (miles) | 5.0     |
| `latitude`                  | (Required, with `longitude`) The latitude of the center of the area. Must be used with `longitude`.                                                                                                    | Latitude                 | None    |
| `longitude`                 | (Required, with `latitude`) The longitude of the center of the area. Must be used with `latitude`.                                                                                                   | Longitude                | None    |
| `cheapest_sensors`          | (Optional) A boolean value to determine whether cheapest sensors should be created for this area.                                                                                                     | Flag                   | False   |
| `cheapest_sensors_count`    | (Required, with `cheapest_sensors`) The number of cheapest sensors to create. Only used if `cheapest_sensors` is true.                                                                                                         | Number (Min: 1, Max: 10, Step: 1) | 5       |
| `cheapest_sensors_fuel_type` | (Required, with `cheapest_sensors`) The fuel type for which the cheapest sensors should be created. Only used if `cheapest_sensors` is true. | Text                      | ""      |

### System Configuration Options

| Option        | Description                                                                                                                                                                                                              | Type                                      | Default |
|---------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------|---------|
| `sources`     | (Required) A list of data sources (fuel price providers) to use. If not provided, the integration will attempt to determine the data source based on your Home Assistant configuration's country setting. | Dropdown, Multiple      | None    |
| `timeout`     | (Optional) The timeout in seconds for requests to the data sources.                                                                                                                                                         | Number (Box, Unit: s, Min: 5, Max: 60) | 30    |
| `scan_interval` | (Optional) The interval in minutes between updates of the fuel prices.                                                                                                                                                    | Number (Box, Unit: m, Min: 360, Max: 1440) | 1440    |
| `state_value` | (Optional) The attribute to use for the state of the fuel price sensors. Used to select which piece of information from the source data is shown as the sensor's value (e.g., name, B7, E5, address). | Text | name |