# Data scraper for Duolingo
Adds multiple sensors with information/statistics grabbed from Duolingo account

## Installation

### Requirements:

1. Install this component by copying [these files](https://github.com/Makhuta/homeassistant-duolingo/tree/main/custom_components/duolingo) to `custom_components/duolingo/`.
2. **You will need to restart after installation for the component to start working.**

### Adding new device

To add the **Duolingo Scraper** integration to your Home Assistant, use this My button:

<a href="https://my.home-assistant.io/redirect/config_flow_start?domain=duolingo" class="my badge" target="_blank"><img src="https://my.home-assistant.io/badges/config_flow_start.svg"></a>

<details><summary style="list-style: none"><h3><b style="cursor: pointer">Manual configuration steps</b></h3></summary>

If the above My button doesn’t work, you can also perform the following steps manually:

- Browse to your Home Assistant instance.

- Go to [Settings > Devices & Services](https://my.home-assistant.io/redirect/integrations/).

- In the bottom right corner, select the [Add Integration button.](https://my.home-assistant.io/redirect/config_flow_start?domain=duolingo)

- From the list, select **Duolingo Scraper**.

- Follow the instructions on screen to complete the setup.

</details>

## Note

The users will be viewed from the JWT token point of view meaning that you might not see some datas when parsing other users with the same token.

### How to get the JWT token?

The JWT token is unique per user and will be different based on for whom you will be logged as in your browser. You can get the JWT token by opening following:

Developer tools -> Go to the Console -> Insert the following command

```javascript
document.cookie.match(new RegExp('(^| )jwt_token=([^;]+)'))[0].slice(11)
```

Inside the Console is your unique JWT token, you can copy it and use it in HomeAssistant.

PS. If your JWT token don't work make sure to not copy the brackets \" or \' from Console (they are there only to define the type of the return value which is in this case string)

| Wrong | Right |
| - | - |
| 'YOUR_TOKEN' | YOUR_TOKEN |