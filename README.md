# SDAC Elia
Custom component for Home Assistant to fetch Belgian SDAC prices. The prices are stored in sensors that can be used for automation purposes.
This component is built for quarterly hour prices.
No API key is needed to fetch the data.

## Pricing context
All prices are expressed in €/MWh. No VAT or distribution network costs are added to the shown prices.

## Sensors
This component adds the following sensors to Home Assistant:
- Elia SDAC current price: shows the current sdac price and stores the forecast in its atributes
- Ecopower electricity price: price formula of Ecopower applied to sdac price
- Ecopower injection tariff: injection tariff formula of Ecopower applied to sdac price
- Custom electricity price (Optional): custom formula applied to sdac price (meant for other suppliers than ecopower), needs to be configured
- Custom injection tariff (Optional): custom formula for injection tariff applied to sdac price (meant for other suppliers than ecopower), needs to be configured

## Configuration
To add the integration without custom sensors, with only the ecopower price and injection tariff sensors, the following entry should be added to the configuration.yaml file:
```
sensor:
  - platform: sdac_elia
```
Note that the "sensor" entry can only be in the file once. If it is already in the configuration file, the platform entry line should be added alongside the other already existing entries.

To get the optional custom sensors, two parameters are required per sensor. These two typically make up a price formula.
The config parameters for each sensor are called:
- custom_price
  - price_factor
  - fixed_price
- custom_injection_tariff
  - injection_tariff_factor
  - fixed_injection_price

In the case of Ecopower's formulae:
- elektrcity price: 0.00102 * EPEX_DA + 0.004 [€/kWh]
- injection tariff: 0.00098 * EPEX_DA - 0.015 [€/kWh]
  
Note: the formula is expressed in €/kWh and should be configured this way as well.
In the configuration.yaml file of Home Assistant, this would be configured as:

```
sensor:
  - platform: sdac_elia
    custom_price:
      price_factor: 0.00102
      fixed_price: 0.004
    custom_injection_tariff:
      injection_tariff_factor: 0.00098
      fixed_injection_price: 0.015
```
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
