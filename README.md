# DMI pollen integration for Home Assistant

This integration retrieves the pollen data for Danmarks Meteorologiske Institut (Denmark's governmental Weather provider).

[!] **This implementation uses an unofficial API and it may change in the future**

DMI is in the works of making all there data free via DMI open data project. This is not done yet.

## Installation

1. Download zip file and extrat it into the `custom_components` folder in your config folder. If it does not exist, then create it.
2. Add `dmi_pollen`in your `configuration.yaml` file. See below:
```yaml
sensor:
  - platform: dmi_pollen
```
3. Restart your HA installation.
4. Now you should see two different sensors. `sensor.dmi_pollen_kobenhaven` and `sensor.dmi_pollen_viborg`.

Note: There is only two measurement stations in denmark. One in Københaven(Copenhagen) and one in Viborg.

## Usage

Readings are listed as attributes, and the state of the sensors is a calculated severity.
```yaml
birk: 0
bynke: 0
el: 697
elm: 0
græs: 0
hassel: 8
severity: mange
forecast: >-
  For i morgen, torsdag d. 11. marts 2021, ventes et højt antal ellepollen
  (flere end 50) samt et lavt antal hasselpollen (færre end 5)
applicable_date: onsdag den 10. marts 2021
source: 'Kilde: Astma-Allergi Danmark og DMI'
friendly_name: DMI Pollen Viborg
icon: 'mdi:flower-poppy'
```

## Important to know

New information is only released once a day, at about 15.00 GMT+1 (Local danish time).

## Bugs

If you run into a bug, or you have a good idea, submit a issue or even better, make a PR for it. :smile:

