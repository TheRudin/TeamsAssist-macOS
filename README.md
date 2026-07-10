# TeamsAssist



# Introduction
We're working a lot at our home office these days. Several people already found inventive solutions to make working in the home office more comfortable. One of these ways is to automate activities in your home automatation system based on your status on Microsoft Teams.

Microsoft provides the status of your account that is used in Teams via the Graph API. To access the Graph API, your organization needs to grant consent for the organization so everybody can read their Teams status. Since my organization didn't want to grant consent, I needed to find a workaround, which I found in monitoring the Teams client logfile for certain changes.

This script makes use of two sensors that are created in Home Assistant up front:
* sensor.teams_status
* sensor.teams_activity

sensor.teams_status displays the availability status of your Teams client. sensor.teams_activity shows if you are in a call or not based on system power assertions (for New Teams) or logs (for Classic Teams).

# Important
This solution is created to work with Home Assistant on macOS. It uses a Python script that runs in the background as a launch agent.

# Requirements
* Create the three Teams sensors in the Home Assistant configuration.yaml file

```yaml
input_text:
  teams_status:
    name: Microsoft Teams status
    icon: mdi:microsoft-teams
  teams_activity:
    name: Microsoft Teams activity
    icon: mdi:phone-off

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
* Generate a Long-lived access token ([see HA documentation](https://developers.home-assistant.io/docs/auth_api/#long-lived-access-token))
* Copy and temporarily save the token somewhere you can find it later
* Restart Home Assistant to have the new sensors added
* Edit the `Scripts/settings.json` file and:
  * Replace `<Insert token>` with the token you generated
  * Replace `<HA URL>` with the URL to your Home Assistant server (e.g., `http://homeassistant.local:8123`)
  * Adjust language or entity settings if needed
* Register and start the background agent using:
  ```bash
  python3 Scripts/setup_launchagent.py
  ```

To stop and uninstall the background agent at any time, run:
```bash
python3 Scripts/setup_launchagent.py --uninstall
```

After completing the steps above, start your Teams client and verify if the status and activity is updated as expected. You can check the background logs in `Scripts/teams_status.log` or error logs in `Scripts/teams_status.err`.

# BluePrint

[![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FHassassistant%2FTeamsAssist%2Fblob%2Fmain%2FAutomation%2Fteams-light.yaml) 

Changes the color of a light based on your Teams status.

