# HDFury VRROOM Integration for Unfolded Circle

This is a custom integration for the Unfolded Circle Remote family that allows for IP control of HDFury VRROOM devices.
![Version](https://img.shields.io/badge/version-0.1.20-green)
![License](https://img.shields.io/badge/license-MPL--2.0-orange)
 [![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA)](https://github.com/sponsors/mase1981/button)


This integration creates two distinct entities on your remote:
* A **MediaPlayer** entity, this is used to determine the state of the device and for inclusion in activities. Additionally it will showcase input output relevant dynamic data.
* A **Remote** entity, which provides a custom UI with pages and buttons for direct control of the device's advanced features.

**NOTE:** This integration was developed and tested against an HDFury 8k VRRooM. While it may work with other IP-controllable HDFury models, it has only been verified with the 8k VRRooM. 

## Features

* **IP Control:** No need for IR emitters. Control your HDFury device directly over your local network.
* **Input Switching:** Directly select any of the 4 HDMI inputs.
* **Advanced Remote UI:** A multi-page remote entity provides control over:
    * **EDID:** Control EDID mode and Automix audio sources.
    * **HDR/AVI:** Toggle custom and disabled HDR metadata flags.
    * **CEC/eARC:** Toggle the CEC engine and set the eARC force mode.
    * **System:** Control the OLED display, autoswitching, and HDCP mode.
* **State Polling:** The integration polls the device after every command to keep the remote's UI updated.
* **Resilient Connection:** Automatically reconnects to the device if the connection is lost.
* **Persistent Configuration:** Remembers your device's IP address between restarts.

## Prerequisites

* HDfury Device **must** be connected to same local network as your unfolded circle remote.
* HDFury **IP INTERRUPTS** config must be set to **on**, you can define whichever port you want, integration will ask you for the port during setup. 
* If you are using advanced network equipment (similar to UDM [Unifi]) Make sure you are **not** blocking that port or telnet communication. 

## Installation

### Option 1: `tar.gz` File (Recommended for most users)
1.  Navigate to the [**Releases**](https://github.com/mase1981/uc-intg-hdfury/releases) page for this repository.
2.  Download the latest `uc-intg-hdfury-<version>-aarch64.tar.gz` file from the Assets section.
3.  Open a web browser and navigate to your Unfolded Circle remote's IP address to access the web configurator.
4.  Go to **Settings** -> **Integrations**.
5.  Click the "UPLOAD" button and select the `.tar.gz` file you just downloaded.

### Option 2: Docker
For users running Docker (e.g., on a Synology NAS), you can deploy this integration as a container.

**Docker Compose (Recommended):**
Use the `docker-compose.yml` file in this repository. Update the `volumes` section to match a path on your host machine where you want to store the configuration file. Then run:

    docker-compose up -d

**Docker Run (Single Command for SSH):**
Replace `/path/on/your/host/config` with an actual path on your machine (e.g., `/volume1/docker/hdfury/config`).

    docker run -d --restart=unless-stopped --net=host -v /path/on/your/host/config:/app/uc_intg_hdfury/config --name hdfury-integration mase1981/uc-intg-hdfury:latest

## Configuration

1.  After installation, go to **Settings** -> **Integrations** on your remote and click **+ ADD INTEGRATION**.
2.  Select **HDFury Controls** from the list.
3.  Follow the on-screen prompts to enter the **IP Address** and **Port** of your HDFury device.
4.  Once setup is complete, two new entities will be available to add to your remote's user interface.

> **Important Note on Entities (READ CAREFULLY):**
> * **`HDFury VRRooM Controls`:** Add this entity to your UI. It contains the custom pages with all the control buttons.
> * **`HDFury VRRooM` (MediaPlayer):** This entity is primarily for status and for use in Activities. You can add it to your UI for basic source selection and to see the current input/output status.

## For Developers

To run this integration locally for development or debugging:

1.  Clone the repository:

        git clone https://github.com/mase1981/uc-intg-hdfury.git
        cd uc-intg-hdfury

2.  Create and activate a Python virtual environment:

        python -m venv .venv
        # On Windows
        .venv\Scripts\activate

3.  Install the required dependencies using Poetry:

        pip install poetry
        poetry install

4.  Run the integration driver:

        python -m uc_intg_hdfury.driver

The driver will now be discoverable by your Unfolded Circle remote on the local network.

## Acknowledgements

* **The Unfolded Circle Team** for creating a fantastic product and providing the [ucapi library](https://github.com/unfoldedcircle/integration-python-library) for developers.
