![Holfy Logo](https://holfuy.com/image/logo/holfuy-logo.png)

# Home-Assistant Holfuy Integration

A Home Assistant integration providing live weather reports from Holfuy weather stations.

Before you can use this integration you need to obtain an API key from Holfuy. Please read the [Holfuy API](https://api.holfuy.com/live/) pages for getting one.


## Getting Started

### Installation
You can manually install this integration as an custom_component under Home Assistant or install it using [HACS](https://hacs.xyz/) (coming).

After installation you will need to restart HomeAssistant.

#### Manual installation
1. **Download** the `ha-hofluy` repository or folder.
2. **Copy** the `custom_components/holfuy` folder from the downloaded files.
3. **Paste** the `hofluy` folder into your Home Assistant's custom components directory: `<home_assistant_folder>/custom_components/holfuy`
4. **Restart** Home Assistant.

### Configuration
After installing the integration you still need to configure it:

1. Go to `Settings: Devices & services`
2. Click `Add Integration` and search for `Holfuy`
3. Enter your Holfuy API key

