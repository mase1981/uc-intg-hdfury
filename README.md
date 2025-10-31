# HDFury Integration for Unfolded Circle Remote

![hdfury](https://img.shields.io/badge/hdfury-multimodel-red)
[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-hdfury)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/mase1981/uc-intg-hdfury/total)
![License](https://img.shields.io/badge/license-MPL--2.0-blue)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA)](https://github.com/sponsors/mase1981/button)


> **Control multiple HDFury HDMI devices with the Unfolded Circle Remote 2/3**

Full integration for HDFury devices providing dual-entity control with media player and advanced remote functionality. Supports 7 different HDFury models with model-specific features and dynamic UI generation.

---

## 📺 Supported Devices

This integration supports the following HDFury models with automatic feature detection:

| Model | Status | Default Port | Inputs | Key Features |
|-------|--------|--------------|--------|--------------|
| **VRRooM 8K** | ✅ Fully Tested | 2222 | 4 HDMI | EDID, HDR, CEC, eARC |
| **VERTEX2** | ✅ Supported | 2220 | 4 HDMI | EDID, HDR, CEC, Scale modes |
| **VERTEX** | ✅ Supported | 2220 | 2 (Top/Bottom) | EDID, HDR, CEC, Scale modes |
| **DIVA** | ✅ Supported | 2210 | 4 HDMI | EDID, HDR, CEC, LED controls |
| **Maestro** | ✅ Supported | 2200 | 4 HDMI | EDID, HDR, CEC, eARC |
| **ARCANA2** | ✅ Supported | 2222 | Passthrough | Audio modes, Scale modes |
| **Dr.HDMI 8K** | ✅ Supported | 2201 | Passthrough | EDID management |

**Each model automatically configures with appropriate features and UI pages based on its capabilities.**

---

## ✨ Features

### Universal Features
- ✅ **Model Selection** - Choose your specific HDFury device during setup
- ✅ **Auto-Configuration** - Default ports and features set automatically
- ✅ **Dynamic UI** - Remote pages adapt to device capabilities
- ✅ **Dual Entity System** - Media Player + Remote Control entities

### Media Player Entity
- ✅ **Input Switching** - HDMI input selection (model-dependent)
- ✅ **State Monitoring** - Real-time device status
- ✅ **Activity Integration** - Seamless activity support
- ✅ **Now Playing Info** - Current input/output display

### Remote Control Entity
- ✅ **Adaptive UI Pages** - Only shows supported features
- ✅ **EDID Management** - Mode and audio source control (most models)
- ✅ **HDR Control** - Custom HDR and disable toggles (most models)
- ✅ **Scale Modes** - Video scaling options (VERTEX2, VERTEX, DIVA, Maestro, ARCANA2)
- ✅ **Audio Modes** - Audio routing control (ARCANA2)
- ✅ **CEC Management** - Engine control and eARC forcing (most models)
- ✅ **System Settings** - OLED, autoswitch, HDCP mode (model-dependent)

---

## 📋 Requirements

- **Unfolded Circle Remote Two** or **Remote 3** (firmware 1.6.0+)
- **HDFury Device** (any supported model)
- **Network Connectivity** between Remote and HDFury device
- **HDFury Configuration**: IP INTERRUPTS must be **ON** (enabled by default)

---

## 🚀 Installation

### Method 1: Remote Web Configurator (Recommended)

1. Download the latest `uc-intg-hdfury-X.X.X-aarch64.tar.gz` from [Releases](https://github.com/mase1981/uc-intg-hdfury/releases)
2. Open your Unfolded Circle **Web Configurator** (http://remote-ip/)
3. Navigate to **Integrations** → **Add Integration**
4. Click **Upload Driver**
5. Select the downloaded `.tar.gz` file
6. Follow the on-screen setup wizard

### Method 2: Docker Run (One-Line Command)
```bash
docker run -d --name uc-intg-hdfury --restart unless-stopped --network host -v $(pwd)/data:/data -e UC_CONFIG_HOME=/data -e UC_INTEGRATION_INTERFACE=0.0.0.0 -e UC_INTEGRATION_HTTP_PORT=9029 -e UC_DISABLE_MDNS_PUBLISH=false ghcr.io/mase1981/uc-intg-hdfury:latest
```

### Method 3: Docker Compose

Create a `docker-compose.yml` file:
```yaml
version: '3.8'

services:
  hdfury-integration:
    image: ghcr.io/mase1981/uc-intg-hdfury:latest
    container_name: uc-intg-hdfury
    restart: unless-stopped
    network_mode: host
    volumes:
      - ./data:/data
    environment:
      - UC_CONFIG_HOME=/data
      - UC_INTEGRATION_INTERFACE=0.0.0.0
      - UC_INTEGRATION_HTTP_PORT=9029
      - UC_DISABLE_MDNS_PUBLISH=false
```

Then run:
```bash
docker-compose up -d
```

### Method 4: Python (Development)
```bash
# Clone repository
git clone https://github.com/mase1981/uc-intg-hdfury.git
cd uc-intg-hdfury

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run integration
python uc_intg_hdfury/driver.py
```

---

## ⚙️ Configuration

### Step 1: Configure HDFury Device

**Enable IP Control:**
1. Access HDFury device web interface or OSD menu
2. Navigate to **Network Settings** or **IP Control**
3. Enable **IP INTERRUPTS** (set to **ON**)
4. Note the **Port** (varies by model - see table above)
5. Note the device **IP Address**

**Network Requirements:**
- ✅ HDFury device must be on same network as UC Remote
- ✅ No firewall blocking telnet communication on configured port
- ✅ For advanced networks (UniFi, pfSense): ensure telnet traffic allowed

### Step 2: Setup in Remote Configurator

1. In the UC Remote web configurator, go to **Integrations**
2. Find **HDFury Controls** and click **Configure**
3. **Select your device model** from the dropdown:
   - VRRooM
   - VERTEX2
   - VERTEX
   - DIVA
   - Maestro
   - ARCANA2
   - Dr.HDMI 8K
4. Enter device information:
   - **IP Address**: Your HDFury device IP
   - **Port**: Auto-filled based on model (can be customized)
5. Click **Submit**
6. Integration will verify connection and create entities

**Note:** The port field auto-fills with the default for your selected model, but can be changed if your device uses a custom port.

---

## 🎮 Usage

### Entities Created

For each HDFury device, **two entities** are created:

#### 1️⃣ Media Player Entity
- **Entity ID**: `hdfury-{ip}`
- **Name**: `HDFury {Model}`
- **Type**: Media Player

**Features (model-dependent):**
- Input source selection (HDMI 0-3, or Top/Bottom for VERTEX)
- Current status display
- Activity integration
- Real-time state updates

#### 2️⃣ Remote Control Entity
- **Entity ID**: `hdfury-{ip}-remote`
- **Name**: `HDFury {Model} Controls`
- **Type**: Remote

**Features:**
- Dynamic UI pages based on device capabilities
- Model-specific control options
- Organized by feature category

### Adding to Activities

1. Create or edit an **Activity**
2. Add the **HDFury {Model}** (Media Player) entity
3. Configure input switching for activity start
4. Set default HDMI input if desired
5. Use the **HDFury {Model} Controls** (Remote) entity for advanced settings

### Control Pages by Model

The integration automatically creates UI pages based on your device's capabilities:

#### Sources Page (VRRooM, VERTEX2, VERTEX, DIVA, Maestro)
Direct selection of HDMI inputs:
- **VRRooM/VERTEX2/DIVA/Maestro**: HDMI 0-3 buttons
- **VERTEX**: Top and Bottom buttons

#### EDID Page (Most models)
EDID management controls:
- **EDID Mode**: automix, custom, fixed, copy options (varies by model)
- **Audio Source**: stereo, 5.1, full, and model-specific options

#### Scale Page (VERTEX2, VERTEX, DIVA, Maestro, ARCANA2)
Video scaling options:
- **VERTEX2/VERTEX/DIVA/Maestro**: auto, custom, none
- **ARCANA2**: Extensive 4K scaling modes including HDR/SDR variants

#### Audio Page (ARCANA2 only)
Audio routing control:
- **Audio Mode**: display, earc, both

#### HDR Page (Most models)
HDR metadata control:
- **Custom HDR**: ON/OFF - Output custom HDR metadata
- **Disable HDR**: ON/OFF - Stop all HDR metadata

#### CEC/eARC Page (VRRooM, VERTEX2, DIVA, Maestro)
Audio return and control:
- **CEC Engine**: ON/OFF - Enable/disable CEC
- **eARC Force Mode**: auto, earc, hdmi (varies by model)

#### System Page (Model-dependent)
Device settings (availability varies):
- **OLED Display**: ON/OFF - Control front panel
- **Autoswitch**: ON/OFF - Automatic input switching
- **HDCP Mode**: auto, 1.4 - HDCP version control

---

## 🔧 Troubleshooting

### Connection Issues During Setup

**Problem**: Setup fails with "Could not connect" or timeout

**Solutions:**
1. ✅ Verify HDFury device is powered on
2. ✅ Confirm IP address is correct
3. ✅ Check IP INTERRUPTS is enabled (ON)
4. ✅ Verify port number matches your device model
5. ✅ Test telnet manually: `telnet <ip> <port>`
6. ✅ Check firewall/router not blocking telnet traffic
7. ✅ Ensure HDFury and UC Remote on same network/VLAN

### Wrong Model Selected

**Problem**: Integration doesn't work correctly or shows wrong features

**Solution:**
1. Delete the device from integration
2. Re-add and select the correct model from dropdown
3. Verify model selection matches your physical device

### Commands Not Executing

**Problem**: Buttons show success but device doesn't respond

**Solutions:**
1. ✅ Check OLED display on device for command confirmation
2. ✅ Verify device firmware is up to date
3. ✅ Restart HDFury device
4. ✅ Restart integration in UC Remote web configurator
5. ✅ For Docker: check logs with `docker logs uc-intg-hdfury`

### Entity Shows Unavailable

**Problem**: Entity appears unavailable after Remote restart

**Solutions:**
1. ✅ Wait 30-60 seconds for automatic reconnection
2. ✅ Check HDFury device is still reachable on network
3. ✅ Verify IP address hasn't changed (set static IP on device)
4. ✅ Restart integration from web configurator
5. ✅ Check integration logs for connection errors

### Docker Container Issues

**Problem**: Docker container not starting or crashing

**Solutions:**
1. ✅ Check container logs: `docker logs uc-intg-hdfury`
2. ✅ Verify network mode is set to `host`
3. ✅ Ensure port 9029 is not in use by another service
4. ✅ Check volume permissions for `./data` directory
5. ✅ Pull latest image: `docker pull ghcr.io/mase1981/uc-intg-hdfury:latest`

### Missing UI Pages

**Problem**: Expected control pages don't appear

**Solution:** This is normal behavior. The integration only shows UI pages for features your specific device supports. For example:
- ARCANA2 won't show Sources page (passthrough device)
- Dr.HDMI 8K won't show HDR or CEC pages
- Check the feature matrix above for your model's capabilities

---

## ⚠️ Known Limitations

| Limitation | Explanation | Workaround |
|-----------|-------------|------------|
| **Single device per integration instance** | Each HDFury device requires separate setup | Run multiple integration instances if needed |
| **No output power control** | Most HDFury devices are designed to stay powered on | Use device-specific power features if available |
| **Status polling disabled** | To prevent device overload during activities | Commands update state immediately |
| **Model-specific features** | Some settings only apply to certain models | Integration automatically hides unsupported features |
| **No automatic model detection** | User must select correct model during setup | Refer to device label or documentation |

---

## 🗃️ Architecture

### Integration Components
```
uc-intg-hdfury/
├── uc_intg_hdfury/
│   ├── __init__.py           # Package initialization with version
│   ├── config.py             # Configuration management with persistence
│   ├── device.py             # Device abstraction and state management
│   ├── driver.py             # Main integration driver
│   ├── hdfury_client.py      # Telnet communication client
│   ├── media_player.py       # Media Player entity implementation
│   ├── models.py             # Model configurations and feature definitions
│   └── remote.py             # Remote Control entity with dynamic UI
├── driver.json               # Integration metadata
├── pyproject.toml            # Python project configuration
├── requirements.txt          # Runtime dependencies
├── Dockerfile                # Docker container build
├── docker-compose.yml        # Docker Compose configuration
├── LICENSE                   # MPL-2.0 license
└── README.md                 # This file
```

### Dependencies

- **ucapi** (>=0.3.1) - Unfolded Circle Integration API
- **pyee** (~=9.0.4) - Event emitter for async patterns
- **certifi** - SSL certificate verification

---

## 💨‍💻 Development

### Building From Source
```bash
# Clone repository
git clone https://github.com/mase1981/uc-intg-hdfury.git
cd uc-intg-hdfury

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Build distribution package
python -m build

# Output: dist/uc-intg-hdfury-X.X.X.tar.gz
```

### Contributing

Contributions are welcome! Please follow these guidelines:

1. 🍴 Fork the repository
2. 🌿 Create a feature branch (`git checkout -b feature/amazing-feature`)
3. 💾 Commit your changes (`git commit -m 'Add amazing feature'`)
4. 📤 Push to the branch (`git push origin feature/amazing-feature`)
5. 🎉 Open a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Use type hints where applicable
- Add docstrings to all functions and classes
- Keep line length to 100 characters
- Use absolute imports only

---

## 🙏 Credits & Acknowledgments

### Integration Development
- **Author**: [Meir Miyara](https://www.linkedin.com/in/meirmiyara/)

### Libraries & References
- **Unfolded Circle**: [Integration Python Library](https://github.com/unfoldedcircle/integration-python-library)
- **HDFury**: For their excellent HDMI processing devices

### Community
- **Unfolded Circle Community**: For testing and feedback
- **HDFury Community**: For device specifications and command reference

---

## 💖 Support the Project

If you find this integration useful, please consider:

- ⭐ **Star this repository** on GitHub
- 🐛 **Report issues** to help improve the integration
- 💡 **Share feedback** in discussions
- 📖 **Contribute** documentation or code improvements

### Sponsor

If you'd like to support continued development:

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-pink?logo=github)](https://github.com/sponsors/mase1981)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support-yellow?logo=buy-me-a-coffee)](https://www.buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-Support-blue?logo=paypal)](https://www.paypal.com/paypalme/mmiyara)

---

## 📞 Support & Community

### Getting Help

- 📋 **Issues**: [GitHub Issues](https://github.com/mase1981/uc-intg-hdfury/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/mase1981/uc-intg-hdfury/discussions)
- 🎮 **Discord**: [Unfolded Circle Discord](https://discord.gg/zGVYf58)
- 🌐 **UC Community**: [Unfolded Circle Forum](https://unfoldedcircle.com/community)

### Reporting Issues

When reporting issues, please include:

1. Integration version (v0.3.0+)
2. **HDFury device model** (VRRooM, VERTEX2, etc.)
3. UC Remote firmware version
4. Detailed description of the problem
5. Relevant log excerpts (from web configurator or Docker logs)

---

## 📜 License

This project is licensed under the **Mozilla Public License 2.0** (MPL-2.0).

See the [LICENSE](LICENSE) file for full details.
```
Copyright (c) 2025 Meir Miyara

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
```

---

## 🚨 Disclaimer

This is an independent integration and is not officially affiliated with, endorsed by, or supported by HDFury or Unfolded Circle.

---

<div align="center">

**Enjoy controlling your HDFury devices with your Unfolded Circle Remote!** 🎉

Made with ❤️ by [Meir Miyara](https://www.linkedin.com/in/meirmiyara/)

</div>
