# SDAC Elia
Custom component for Home Assistant HACS to fetch Belgian SDAC prices. The prices are stored in sensors that can be used for automation purposes.
This component is built for quarterly hour prices.
No API key is needed to fetch the data.

## Pricing context
All prices are expressed in €/MWh. No VAT or distribution network costs are added to the shown prices.

## Sensors
This component adds the following sensors to Home Assistant:
- Elia SDAC current price: shows the current sdac price and stores the sdac prices of today and tomorrow in its atributes
- Custom electricity price (Optional): custom formula applied to sdac price, needs to be configured
- Custom injection tariff (Optional): custom formula for injection tariff applied to sdac price, needs to be configured

## Installation
Installing the custom component can be done with [HACS](https://hacs.xyz) by searching for "SDAC Elia".

OR

It can be installed manually by downloading the [latest release](https://github.com/milanhin/sdac_elia/releases) and copying the `sdac_elia` folder into to your Home Assistant `config/custom_components` folder.

## Configuration
Configuration is done through the UI by going to settings -> integrations -> add the SDAC Elia integration.
To add the custom sensors, tick the boxes of the sensor you'd like to configure.
For each custom sensor, two parameters are required. These two typically make up a price formula.
The config parameters for each sensor are called:
- custom_price
  - price_factor
  - fixed_price
- custom_injection_tariff
  - injection_tariff_factor
  - fixed_injection_price

of which the factor is the multiplicator for the sdac (EPEX) price and the fixed price is the commission added to the formula, typically described as: $\mathbf{A \cdot \mathrm{EPEX} \pm B}$ where A is the factor and B is the fixed cost. An example:

In the case of Ecopower's formulae (as of dec-2025):
- electricity price: 0.00102 * EPEX_DA + 0.004 [€/kWh]
- injection tariff: 0.00098 * EPEX_DA - 0.015 [€/kWh]

These formulae do not include network costs (NL: nettarieven). It is possible to include those network costs by adding them to the fixed cost parameter.
Note: the formula is expressed in €/kWh and should be configured this way as well, while the EPEX price is expressed in €/MWh.

## Graph with pricing forecast
A graph can be shown with the [ApexChart Graph Card](https://github.com/RomRider/apexcharts-card). 
The lovelace code (based on [hass-entso-e](https://github.com/JaccoR/hass-entso-e)) for this graph is:
```
type: custom:apexcharts-card
graph_span: 24h
span:
  start: day
now:
  show: true
  label: Now
header:
  show: true
  title: Elia SDAC prices of today (€/Mwh)
yaxis:
  - decimals: 2
series:
  - entity: sensor.elia_sdac_current_price
    stroke_width: 2
    float_precision: 3
    type: column
    opacity: 1
    color: ""
    data_generator: |
      return entity.attributes.prices.map((entry) => { 
      return [new Date(entry.time), entry.price];
      });
```
And would result in:\
![SDAC prices forecast plot](https://github.com/milanhin/sdac_elia/blob/main/assets/forecast_plot.png)
