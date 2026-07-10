# Microsoft Teams Home Assistant Integration Guide

This guide details how to configure sensors, write robust automations, and build dashboard cards to utilize **TeamsAssist (macOS)** data inside Home Assistant.

---

## 1. Sensor Configuration (`configuration.yaml`)

Add this configuration to your Home Assistant setup (typically in `configuration.yaml` or a dedicated package file).

```yaml
# Input Text Helpers to receive states from the macOS script
input_text:
  teams_status:
    name: Microsoft Teams status
    icon: mdi:microsoft-teams
  teams_activity:
    name: Microsoft Teams activity
    icon: mdi:phone-off

# Template Sensors to format values and attributes for the UI
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

# Binary Sensor to monitor if the macOS background daemon is active
binary_sensor:
  - platform: template
    sensors:
      teams_monitoring:
        friendly_name: "Microsoft Teams Monitoring"
        value_template: "{{ is_state('binary_sensor.teams_monitoring', 'on') }}"
        device_class: connectivity
        unique_id: binary_sensor.teams_monitoring
```

*Note: Restart Home Assistant after adding these sensors to activate them.*

---

## 2. Lovelace Dashboard UI Example

Add a custom dashboard card to show your active Teams status on your home tablet or dashboard.

```yaml
type: entities
title: Workspace Status
show_header_toggle: false
entities:
  - entity: sensor.teams_status
    name: Presence
  - entity: sensor.teams_activity
    name: Call Activity
  - entity: binary_sensor.teams_monitoring
    name: Daemon Online Status
```

---

## 3. Automation Examples

### Example A: Status Light Color Automation
This automation adjusts the color of a smart light based on your presence. It turns **Red** for calls/meetings, **Green** when available, **Yellow** when away, and **Off** when offline.

```yaml
alias: "Teams: Update Office Status Light Color"
description: "Changes light color based on Microsoft Teams presence"
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
              rgb_color: [255, 30, 10]
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
              rgb_color: [252, 150, 0]
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
              rgb_color: [0, 255, 10]
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

### Example B: Auto-Off Status Light when Daemon Stops
To prevent the status light from staying lit (e.g. when you turn off your Mac or close your laptop), this automation turns off the light when the connection to the daemon is lost.

```yaml
alias: "Teams: Turn Off Light when Daemon is Offline"
description: "Turns off status light if TeamsAssist daemon stops running"
trigger:
  - platform: state
    entity_id: binary_sensor.teams_monitoring
    to: "off"
action:
  - service: light.turn_off
    target:
      entity_id: light.office_status_light
mode: single
```

---

## 4. Troubleshooting Status Synced Entities

If the state changes are not showing in Home Assistant:
1. **Check the REST API Connection**: Open a terminal on your Mac and test connection with:
   ```bash
   curl -X GET -H "Authorization: Bearer <your_token>" <your_ha_url>/api/
   ```
   If successful, it will return a JSON message containing `"message": "API running."`.
2. **Review Daemon Logs**:
   - `cat ~/Documents/Teams\ Assistant/Scripts/teams_status.log` (Check logs for successful POST events).
   - `cat ~/Documents/Teams\ Assistant/Scripts/teams_status.err` (Check for network exceptions or invalid tokens).
