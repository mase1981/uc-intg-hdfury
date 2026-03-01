# HDFury Integration for Unfolded Circle Remote

[![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-hdfury?style=flat-square)](https://github.com/mase1981/uc-intg-hdfury/releases)
![License](https://img.shields.io/badge/license-MPL--2.0-blue?style=flat-square)
[![GitHub issues](https://img.shields.io/github/issues/mase1981/uc-intg-hdfury?style=flat-square)](https://github.com/mase1981/uc-intg-hdfury/issues)
[![Community Forum](https://img.shields.io/badge/community-forum-blue?style=flat-square)](https://unfolded.community/)
[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Downloads](https://img.shields.io/github/downloads/mase1981/uc-intg-hdfury/total?style=flat-square)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=flat-square)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg?style=flat-square)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA&style=flat-square)](https://github.com/sponsors/mase1981)

Control HDFury HDMI devices from your Unfolded Circle Remote with persistent TCP connection, automatic reconnection, and real-time status monitoring.

---

## Support Development

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-pink?style=for-the-badge&logo=github)](https://github.com/sponsors/mase1981)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/mmiyara)

---

## Supported Devices

| Model | Port | Inputs | Features |
|-------|------|--------|----------|
| VRRooM 8K | 2222 | 4 HDMI | EDID, HDR, CEC, eARC, Matrix |
| VERTEX2 | 2220 | 4 HDMI | EDID, HDR, CEC, Scale, Color Space |
| VERTEX | 2220 | 2 (Top/Bot) | EDID, HDR, CEC, Scale, Color Space |
| DIVA | 2210 | 4 HDMI | EDID, HDR, CEC, LED Control |
| Maestro | 2200 | 4 HDMI | EDID, HDR, CEC, eARC |
| ARCANA2 | 2222 | Passthrough | Audio Modes, Scale Modes |
| Dr.HDMI 8K | 2201 | Passthrough | EDID, Output Resolution |

---

## Sensors

Real-time monitoring of video and audio signals.

| Sensor | Description |
|--------|-------------|
| Current Input | Active HDMI input selection |
| Video Input | Input signal info (resolution, HDR, refresh) |
| Audio RX | Audio input format |
| TX0 Output | Output 0 video signal |
| TX0 Sink | Output 0 connected display |
| TX0 Audio | Output 0 audio format |
| TX1 Output | Output 1 video signal |
| TX1 Sink | Output 1 connected display |
| TX1 Audio | Output 1 audio format |

---

## Select Entities

Dropdown controls for device configuration.

| Select | Description | Models |
|--------|-------------|--------|
| Input | HDMI input selection | All multi-input |
| EDID Mode | AutoMix, Custom, Fixed, Copy | Most |
| HDCP | Auto, 1.4, 2.2 | Most |
| EDID Audio | Stereo, 5.1, Full, Native | Most |
| eARC Force | Auto, eARC, Manual, HDMI | VRRooM, VERTEX2, DIVA, Maestro |
| ARC Force | Auto, ARC, HDMI | VERTEX2, DIVA, Maestro |
| Scale Mode | Auto, Custom, None, Advanced | VERTEX2, VERTEX, DIVA, Maestro, ARCANA2 |
| Audio Mode | Display, eARC, Both | ARCANA2 |
| LED Mode | Off, Follow, Static, Blinking, Pulsating, Rotating | DIVA |
| Color Space | Auto, RGB, YCbCr 4:4:4, YCbCr 4:2:2 | VERTEX2, VERTEX, DIVA, Maestro |
| Deep Color | Auto, 8-bit, 10-bit, 12-bit | VERTEX2, VERTEX, DIVA, Maestro |
| Output Resolution | Auto, 4K60, 4K30, 1080p, 720p | Dr.HDMI 8K |

---

## Remote Commands

Available through remote entity UI pages.

| Command | Description |
|---------|-------------|
| Input Selection | Switch HDMI inputs |
| HDR Custom On/Off | Enable/disable custom HDR metadata |
| HDR Disable On/Off | Block HDR passthrough |
| CEC On/Off | Enable/disable CEC |
| OLED On/Off | Control front panel display |
| Autoswitch On/Off | Automatic input switching |
| Hotplug | Trigger EDID re-negotiation |
| Reboot | Restart device |

---

## Installation

### Option 1: Remote Web Interface (Recommended)

1. Download the latest `.tar.gz` from [Releases](https://github.com/mase1981/uc-intg-hdfury/releases)
2. Open Remote web interface → **Settings** → **Integrations**
3. Click **Upload** and select the downloaded file
4. Configure: Select model, enter IP address
5. Done - entities are created automatically

### Option 2: Docker

**Image:** `ghcr.io/mase1981/uc-intg-hdfury:latest`

**Docker Compose:**
```yaml
services:
  uc-intg-hdfury:
    image: ghcr.io/mase1981/uc-intg-hdfury:latest
    container_name: uc-intg-hdfury
    network_mode: host
    volumes:
      - ./config:/data
    environment:
      - UC_CONFIG_HOME=/data
      - UC_INTEGRATION_HTTP_PORT=9029
      - UC_INTEGRATION_INTERFACE=0.0.0.0
    restart: unless-stopped
```

**Docker Run:**
```bash
docker run -d \
  --name uc-intg-hdfury \
  --network host \
  -v ./config:/data \
  -e UC_CONFIG_HOME=/data \
  -e UC_INTEGRATION_HTTP_PORT=9029 \
  -e UC_INTEGRATION_INTERFACE=0.0.0.0 \
  --restart unless-stopped \
  ghcr.io/mase1981/uc-intg-hdfury:latest
```

**Requirements:**
- HDFury device on same network
- IP Interrupts enabled on device
- Static IP recommended

---

## License

Mozilla Public License 2.0 (MPL-2.0)

## Links

- [GitHub Issues](https://github.com/mase1981/uc-intg-hdfury/issues)
- [UC Community Forum](https://unfolded.community/)
- [Discord](https://discord.gg/zGVYf58)
- [HDFury Support](https://www.hdfury.com/support/)

---

**Made with care for the Unfolded Circle and HDFury communities**
