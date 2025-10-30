# HDFury Integration for Unfolded Circle Remote

[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-hdfury)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/mase1981/uc-intg-hdfury/total)
![License](https://img.shields.io/badge/license-MPL--2.0-blue)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA)](https://github.com/sponsors/mase1981/button)

Control HDFury HDMI matrix devices like the VRRooM with your Unfolded Circle Remote.

---

## Features

- **IP Control**: Direct network communication without IR emitters
- **Dual Entity System**: 
  - **MediaPlayer Entity**: For device state and activity integration
  - **Remote Entity**: Multi-page custom UI for advanced control
- **Input Switching**: Direct selection of 4 HDMI inputs
- **Advanced Controls**:
  - EDID mode and audio source management
  - HDR metadata flag toggles
  - CEC engine control
  - eARC force mode settings
  - System settings (OLED, autoswitch, HDCP)
- **Resilient Connection**: Automatic reconnection handling
- **Persistent Configuration**: Device settings saved between restarts

---

## Compatibility

**Tested Hardware:**
- HDFury 8k VRRooM

**Note:** This integration was developed and tested against an HDFury 8k VRRooM. While it may work with other IP-controllable HDFury models, compatibility is only verified with the 8k VRRooM.

---

## Prerequisites

Before installing this integration, ensure:

1. **Network Requirements**:
   - HDFury device connected to same local network as UC Remote
   - No firewall blocking telnet communication on the configured port

2. **HDFury Device Configuration**:
   - **IP INTERRUPTS** must be set to **ON** in device settings
   - Note the port number (default: 2222)
   - For advanced network equipment (e.g., UniFi), ensure telnet traffic is not blocked

---

## Installation

### Option 1: Direct Installation via tar.gz (Recommended)

1. Download the latest `uc-intg-hdfury-<version>-aarch64.tar.gz` from the [Releases](https://github.com/mase1981/uc-intg-hdfury/releases) page
2. Open your UC Remote's web configurator (navigate to Remote's IP address)
3. Go to **Settings** → **Integrations**
4. Click **UPLOAD** and select the downloaded `.tar.gz` file
5. The integration will install automatically

### Option 2: Docker Deployment

For users running Docker (NAS devices, home servers, etc.):

#### Using Docker Compose (Recommended)

1. Create a `docker-compose.yml` file:

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

2. Run: `docker-compose up -d`

#### Using Docker CLI

```bash
docker run -d \
  --name uc-intg-hdfury \
  --restart unless-stopped \
  --network host \
  -v ./data:/data \
  -e UC_CONFIG_HOME=/data \
  -e UC_INTEGRATION_INTERFACE=0.0.0.0 \
  -e UC_INTEGRATION_HTTP_PORT=9029 \
  -e UC_DISABLE_MDNS_PUBLISH=false \
  ghcr.io/mase1981/uc-intg-hdfury:latest
```

---

## Configuration

1. After installation, open your UC Remote's web configurator
2. Navigate to **Settings** → **Integrations**
3. Click **+ ADD INTEGRATION**
4. Select **HDFury Controls** from the available integrations
5. Follow the setup wizard:
   - Enter your HDFury device's **IP Address**
   - Enter the **Port** (default: 2222)
6. Click **Next** to complete setup

The integration will discover your device and create two entities.

---

## Entities

### 1. HDFury VRRooM (MediaPlayer Entity)

**Purpose:** Device state monitoring and activity integration

**Features:**
- Current source display
- Input/output status information
- Activity integration support
- Basic source selection

**Usage:** Add to your UC Remote UI for quick status view and source switching

---

### 2. HDFury VRRooM Controls (Remote Entity)

**Purpose:** Advanced device control via custom multi-page UI

**Pages:**

#### Sources
- Direct selection of 4 HDMI inputs

#### EDID
- **EDID Mode**: automix, custom, fixed, copytx0, copytx1
- **Automix Audio Source**: stereo, 5.1, full, audioout, earcout

#### HDR/AVI
- **Custom HDR**: ON/OFF toggle
- **Disable HDR**: ON/OFF toggle

#### CEC/eARC
- **CEC Engine**: ON/OFF control
- **eARC Force Mode**: auto, earc, hdmi

#### System
- **OLED Display**: ON/OFF control
- **Autoswitch**: ON/OFF toggle
- **HDCP Mode**: auto, 1.4

**Usage:** Add to your UC Remote UI for comprehensive device control

---

## Using with Activities

The MediaPlayer entity integrates seamlessly with UC Remote activities:

1. Create a new activity or edit an existing one
2. Add the **HDFury VRRooM** MediaPlayer entity
3. Configure source selection for automatic input switching
4. The integration will handle power state and source changes

---

## Troubleshooting

### Device Not Found During Setup

- Verify HDFury device is on the same network
- Check IP INTERRUPTS is enabled in HDFury settings
- Confirm no firewall is blocking the telnet port
- Try accessing device via telnet manually: `telnet <ip> <port>`

### Connection Issues After Setup

- Check network connectivity to HDFury device
- Restart the integration via Settings → Integrations
- For Docker deployment, check container logs: `docker logs uc-intg-hdfury`
- Verify HDFury device hasn't changed IP address

### Commands Not Working

- Ensure latest firmware on HDFury device
- Check OLED display for command confirmation
- Review integration logs in UC Remote web configurator
- For Docker: `docker logs uc-intg-hdfury`

### Entity Not Appearing on Remote

- Confirm entity is added in UC Remote configuration
- Try removing and re-adding the entity
- Restart UC Remote if needed

---

## Development

### Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/mase1981/uc-intg-hdfury.git
cd uc-intg-hdfury
```

2. Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the integration:
```bash
python -m uc_intg_hdfury.driver
```

The driver will now be discoverable on your local network.

### Building from Source

#### Using Docker

```bash
docker build -t uc-intg-hdfury .
docker run --network host -v ./data:/data uc-intg-hdfury
```

#### Creating Distribution Package

Requires the UC Remote build environment. See [build.yml](.github/workflows/build.yml) for details.

---

## Environment Variables

When running via Docker, the following environment variables are available:

| Variable | Default | Description |
|----------|---------|-------------|
| `UC_CONFIG_HOME` | `/data` | Configuration storage directory |
| `UC_INTEGRATION_INTERFACE` | `0.0.0.0` | Network interface to bind to |
| `UC_INTEGRATION_HTTP_PORT` | `9029` | HTTP port for integration API |
| `UC_DISABLE_MDNS_PUBLISH` | `false` | Disable mDNS discovery |

---

## Technical Details

### Architecture

- **Language**: Python 3.9+
- **Framework**: Unfolded Circle API (ucapi)
- **Communication**: Telnet/IP control
- **Connection**: Async with automatic reconnection
- **State Management**: Event-driven updates

### Dependencies

- `ucapi>=0.3.1` - Unfolded Circle integration library
- `pyee~=9.0.4` - Event emitter for async patterns
- `certifi` - SSL certificate handling

### File Structure

```
uc-intg-hdfury/
├── .github/workflows/
│   └── build.yml           # CI/CD pipeline
├── uc_intg_hdfury/
│   ├── __init__.py         # Package initialization
│   ├── config.py           # Configuration management
│   ├── device.py           # Device abstraction
│   ├── driver.py           # Integration driver
│   ├── hdfury_client.py    # HDFury communication
│   ├── media_player.py     # MediaPlayer entity
│   └── remote.py           # Remote entity
├── docker-compose.yml      # Docker Compose config
├── Dockerfile              # Docker build instructions
├── driver.json             # Integration metadata
├── pyproject.toml          # Python project config
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## Support

- **Issues**: [GitHub Issues](https://github.com/mase1981/uc-intg-hdfury/issues)
- **Discord**: [Unfolded Circle Community](https://discord.gg/zGVYf58)
- **Documentation**: [UC Integration Docs](https://github.com/unfoldedcircle/integration-python-library)

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## Acknowledgements

- **Unfolded Circle Team** for the excellent UC Remote platform and integration library
- **HDFury** for their HDMI processing devices

---

## License

This project is licensed under the Mozilla Public License 2.0 (MPL-2.0). See LICENSE file for details.

---

## Disclaimer

This is an independent integration and is not officially affiliated with, endorsed by, or supported by HDFury or Unfolded Circle.