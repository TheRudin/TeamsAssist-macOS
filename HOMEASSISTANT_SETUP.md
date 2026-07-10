# Microsoft Teams Home Assistant Integration Guide

This guide describes how to configure Home Assistant to work with **TeamsAssist (macOS)** and how to use the sensors for automations.

## 1. Setup Sensors in Home Assistant

Add the following configuration to your Home Assistant `configuration.yaml` file (or equivalent packages directory).

```yaml
# Input Text Helpers to receive states from the macOS script
input_text:
  teams_status:
    name: Microsoft Teams status
    icon: mdi:microsoft-teams
  teams_activity:
    name: Microsoft Teams activity
    icon: mdi:phone-off

# Template Sensors to display the values neatly in your UI
sensor:
  - platform: template
    sensors:
      teams_status: 
        friendly_name: "Microsoft Teams status"
        value_template: "{{states('input_text.teams_status')}}"
        icon_template: "{{state_attr('input_text.teams_status','icon')}}"
        unique_id: sensor.teams_status
      teams_activity:
        friendly_name: "Microsoft Teams activity"
        value_template: "{{states('input_text.teams_activity')}}"
        unique_id: sensor.teams_activity
```

After adding this code, **restart Home Assistant** to create the entities.

## 2. Sensor States and Mappings

### Teams Status (`sensor.teams_status`)
This sensor displays your current presence status. 
- **Available** (Green status)
- **Busy** (Red status)
- **On the phone** (Red status)
- **Away** / **Be right back** (Yellow status)
- **Do not disturb** / **Presenting** / **Focusing** (Red/Purple status)
- **In a meeting** (Red status)
- **Offline** (Grey status - Teams is closed)

### Teams Activity (`sensor.teams_activity`)
This sensor shows call activity:
- **In a call**
- **Not in a call**

---

## 3. Automation Example

Below is an automation example that turns a status light **Red** when you are in a meeting or busy, **Yellow** when away, **Green** when available, and **Off** when offline.

```yaml
alias: Office Status Light Automations
description: Updates office light color based on Microsoft Teams presence
trigger:
  - platform: state
    entity_id: sensor.teams_status
condition: []
action:
  - choose:
      # RED: Busy / In Meeting / Do Not Disturb
      - conditions:
          - condition: template
            value_template: >-
              {{ states('sensor.teams_status') in ['Busy', 'On the phone', 'In a meeting', 'Do not disturb', 'Presenting', 'Focusing'] }}
        sequence:
          - service: light.turn_on
            target:
              entity_id: light.office_status_light
            data:
              rgb_color: [255, 0, 0]
              brightness: 255

      # YELLOW: Away / Be right back
      - conditions:
          - condition: template
            value_template: >-
              {{ states('sensor.teams_status') in ['Away', 'Be right back'] }}
        sequence:
          - service: light.turn_on
            target:
              entity_id: light.office_status_light
            data:
              rgb_color: [255, 150, 0]
              brightness: 150

      # GREEN: Available
      - conditions:
          - condition: state
            entity_id: sensor.teams_status
            state: Available
        sequence:
          - service: light.turn_on
            target:
              entity_id: light.office_status_light
            data:
              rgb_color: [0, 255, 0]
              brightness: 255

      # OFF: Offline
      - conditions:
          - condition: state
            entity_id: sensor.teams_status
            state: Offline
        sequence:
          - service: light.turn_off
            target:
              entity_id: light.office_status_light
    default: []
mode: single
```

## 4. Troubleshooting Entities in Home Assistant

If your sensors are not updating:
1. Check the background logs on your Mac: `cat ~/Documents/Teams\ Assistant/Scripts/teams_status.log`.
2. Check the error logs on your Mac: `cat ~/Documents/Teams\ Assistant/Scripts/teams_status.err`.
3. Verify that your Long-Lived Access Token and Home Assistant URL are correct in your local `settings.json` file.
