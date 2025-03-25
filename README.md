# Fuel Prices

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
![Install Stats][stats]
[![License][license-shield]](LICENSE)

![Project Maintenance][maintenance-shield]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]

_Integration to integrate with [pyfuelprices][pyfuelprices]._

**This integration will set up the following platforms.**

| Platform | Description                                                                  |
| -------- | ---------------------------------------------------------------------------- |
| `sensor` | Optional entities for fuel stations, attributes will contain fuel price data |

## Installation

### Manual

1. Download latest release
1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. Extract downloaded release into `custom_components` directory (folder)
1. Restart Home Assistant
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Fuel Prices"

### HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=pantherale0&category=integration&repository=ha-fuelprices)

1. Open HACS on your HA instance.
1. Copy the repository URL: [https://github.com/pantherale0/ha-fuelprices](https://github.com/pantherale0/ha-fuelprices).
1. In the HACS menu (3 dots in the top right corner), choose "Custom repositories."
1. Paste the copied URL into the repository field.
1. Set the Type as "Integration."
1. Click "Add."
1. Restart Home Assistant.
1. In the HA UI, go to "Configuration" -> "Integrations," click "+," and search for "Fuel Prices."

## Privacy notice

This integration relies entirely on cloud services, alongside this a few libraries are used to geocode provided coordinates into location data for certain providers such as GasBuddy or TankerKoenig.

For reverse geocoding a mix of Nominatim (https://nominatim.org/) and these-united-states (https://pypi.org/project/these-united-states/). This is done to improve performance, for example, looking up provided coordinates with Nominatim will allow us to restrict the fuel station search to data providers available in only that country.

Similar to this, this integration will use these-united-states to retrieve the state of given coordinates, and finally Nominatim is also used to retrieve the nearest postcode for the TankerKoenig data source.

## Configuration

A new configuration parameter was introduced in 2024.6.0 that allows you to specify what state to display within Home Assistant. By default this is name, however it can be changed to a value of your liking after setup by clicking `Configure` followed by `Configure data collection sources`. This parameter is called `State to show on the created sensors`.

This value must be set to a fuel price key (available under `Available Fuels` for the produced sensor entities). In the UK this can be reliably set to E5 or B7, however if you set to SDV, a large number of fuel stations either do not stock this or do not provide this data. In this case the integration will default back to the fuel station name but this may create warnings / errors in your logs. Currently this cannot be configured by area.

## Configuration is done in the UI

<!---->

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

---

[pyfuelprices]: https://github.com/pantherale0/pyfuelprices
[buymecoffee]: https://www.buymeacoffee.com/pantherale0
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/pantherale0/ha-fuelprices.svg?style=for-the-badge
[stats]: https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=integration%20usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.fuel_prices.total&style=for-the-badge
[commits]: https://github.com/pantherale0/ha-fuelprices/commits/main
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/pantherale0/ha-fuelprices.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40pantherale0-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/pantherale0/ha-fuelprices.svg?style=for-the-badge
[releases]: https://github.com/pantherale0/ha-fuelprices/releases
