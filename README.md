# HDFury Integration for Unfolded Circle Remote

![hdfury](https://img.shields.io/badge/hdfury-vrroom-red)
[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-hdfury)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/mase1981/uc-intg-hdfury/total)
![License](https://img.shields.io/badge/license-MPL--2.0-blue)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA)](https://github.com/sponsors/mase1981/button)


> **Control HDFury HDMI matrix devices like the VRRooM with the Unfolded Circle Remote 2/3**

Full integration for HDFury devices providing dual-entity control with media player and advanced remote functionality.

---

## 📺 Supported Devices

This integration is tested and verified with:

- ✅ **HDFury 8k VRRooM** - Fully Tested

**Note:** While this integration was developed for the 8k VRRooM, it may work with other IP-controllable HDFury models. Compatibility with other models is not guaranteed.

---

## ✨ Features

### Media Player Entity
- ✅ **Power Control** - TX0 output on/off
- ✅ **Input Switching** - 4 HDMI input selection
- ✅ **State Monitoring** - Real-time device status
- ✅ **Activity Integration** - Seamless activity support
- ✅ **Now Playing Info** - Current input/output display

### Remote Control Entity
- ✅ **Multi-Page UI** - 5 custom control pages
- ✅ **EDID Management** - Mode and audio source control
- ✅ **HDR Control** - Custom HDR and disable toggles
- ✅ **CEC Management** - Engine control and eARC forcing
- ✅ **System Settings** - OLED, autoswitch, HDCP mode

---

## 📋 Requirements

- **Unfolded Circle Remote Two** or **Remote 3** (firmware 1.6.0+)
- **HDFury Device** (8k VRRooM verified)
- **Network Connectivity** between Remote and HDFury device
- **HDFury Configuration**: IP INTERRUPTS must be **ON** (default port: 2222)

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
4. Note the **Port** (default: 2222)
5. Note the device **IP Address**

**Network Requirements:**
- ✅ HDFury device must be on same network as UC Remote
- ✅ No firewall blocking telnet communication on configured port
- ✅ For advanced networks (UniFi, pfSense): ensure telnet traffic allowed

### Step 2: Setup in Remote Configurator

1. In the UC Remote web configurator, go to **Integrations**
2. Find **HDFury Controls** and click **Configure**
3. Enter device information:
   - **IP Address**: Your HDFury device IP
   - **Port**: Telnet port (default: 2222)
4. Click **Submit**
5. Integration will verify connection and create entities

---

## 🎮 Usage

### Entities Created

For each HDFury device, **two entities** are created:

#### 1️⃣ Media Player Entity
- **Entity ID**: `hdfury-{ip}`
- **Name**: `HDFury VRRooM`
- **Type**: Media Player

**Features:**
- Power control (TX0 output)
- Input source selection (4 HDMI inputs)
- Current status display
- Activity integration

#### 2️⃣ Remote Control Entity
- **Entity ID**: `hdfury-{ip}-remote`
- **Name**: `HDFury VRRooM Controls`
- **Type**: Remote

**Features:**
- Five custom UI pages:
  - **Sources**: Direct HDMI input selection (0-3)
  - **EDID**: Mode control + Automix audio source
  - **HDR/AVI**: Custom HDR and disable toggles
  - **CEC/eARC**: CEC engine + eARC force mode
  - **System**: OLED display, autoswitch, HDCP mode

### Adding to Activities

1. Create or edit an **Activity**
2. Add the **HDFury VRRooM** (Media Player) entity
3. Configure power on/off commands
4. Set default HDMI input if desired
5. Use the **HDFury VRRooM Controls** (Remote) entity for advanced settings

### Control Pages

#### Sources Page
Direct selection of HDMI inputs:
- **HDMI 0** through **HDMI 3** buttons

#### EDID Page
EDID management controls:
- **EDID Mode**: automix, custom, fixed, copytx0, copytx1
- **Automix Audio Source**: stereo, 5.1, full, audioout, earcout

#### HDR/AVI Page
HDR metadata control:
- **Custom HDR**: ON/OFF - Output custom HDR metadata
- **Disable HDR**: ON/OFF - Stop all HDR metadata

#### CEC/eARC Page
Audio return and control:
- **CEC Engine**: ON/OFF - Enable/disable CEC
- **eARC Force Mode**: auto, earc, hdmi

#### System Page
Device settings:
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
4. ✅ Verify port number (default: 2222)
5. ✅ Test telnet manually: `telnet <ip> <port>`
6. ✅ Check firewall/router not blocking telnet traffic
7. ✅ Ensure HDFury and UC Remote on same network/VLAN

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

---

## ⚠️ Known Limitations

| Limitation | Explanation | Workaround |
|-----------|-------------|------------|
| **Single device per integration instance** | Each HDFury device requires separate setup | Run multiple integration instances if needed |
| **No output power control** | VRRooM is designed to stay powered on | Use TX0 power output control instead |
| **Status polling disabled** | To prevent device overload during activities | Commands update state immediately |
| **Advanced features device-specific** | Some settings may not apply to all models | Test features with your specific model |

---

## 🏗️ Architecture

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
│   └── remote.py             # Remote Control entity implementation
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

## 👨‍💻 Development

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

1. Integration version
2. HDFury device model
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

**Enjoy controlling your HDFury device with your Unfolded Circle Remote!** 🎉

Made with ❤️ by [Meir Miyara](https://www.linkedin.com/in/meirmiyara/)

</div>
