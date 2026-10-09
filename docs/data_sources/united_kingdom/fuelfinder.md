# Fuel Finder Provider Set Up

## Background

Fuel Finder is the UK Government service that replaced the CMA open data scheme, where each retailer (Asda, Tesco, Shell and so on) published its own price feed. Those retailer feeds have been removed from this integration.

Fuel Finder requires your own API client ID and client secret, and requests must come from a UK IP address. If you do not want to register for API access, use the PetrolPrices data source instead, which requires no setup.

## Migrating from the CMA data sources

If you previously used any of the CMA retailer data sources (Applegreen, Ascona, Asda, BP, Esso, Jet, Karan Retail, Moto, Motor Fuel Group, Rontec, Sainsbury's, SGN Retail, Shell or Tesco), the integration replaces them with PetrolPrices automatically when you upgrade. The entities created by the removed data sources are deleted, and new entities are created for the stations returned by PetrolPrices.

No action is needed unless you would prefer to use Fuel Finder.

## Retrieving Your API Credentials

1. **Register for API access** by following the instructions on [GOV.UK](https://www.gov.uk/guidance/access-the-latest-fuel-prices-and-forecourt-data-via-api-or-email).

1. **Note down your client ID and client secret** once your access has been approved.

## Configuring the data source

1. In Home Assistant, go to **Settings** -> **Devices & services** -> **Fuel Prices** and click **Configure**.

1. Select **Configure data collector sources**.

1. Add **GB: fuelfinder** to the list of data sources and submit.

1. **Enter your client ID and client secret** when prompted.

1. Select **Complete re-configuration**. The integration reloads and starts collecting data from Fuel Finder.

If the credentials are later found to be missing or invalid, Fuel Finder is disabled and a repair issue is raised in **Settings** -> **Repairs**. Repeat the steps above to re-enter them.
