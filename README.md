# HDFury Integration for Unfolded Circle Remote 2/3

Control your HDFury HDMI processing devices directly from your Unfolded Circle Remote 2 or Remote 3 with comprehensive device control, **model-specific features**, **dynamic UI generation**, and **advanced EDID/HDR management**.

![HDFury](https://img.shields.io/badge/HDFury-Multi--Model-red)
[![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-hdfury?style=flat-square)](https://github.com/mase1981/uc-intg-hdfury/releases)
![License](https://img.shields.io/badge/license-MPL--2.0-blue?style=flat-square)
[![GitHub issues](https://img.shields.io/github/issues/mase1981/uc-intg-hdfury?style=flat-square)](https://github.com/mase1981/uc-intg-hdfury/issues)
[![Community Forum](https://img.shields.io/badge/community-forum-blue?style=flat-square)](https://unfolded.community/)
[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/mase1981/uc-intg-hdfury/total?style=flat-square)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=flat-square)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg?style=flat-square)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA&style=flat-square)](https://github.com/sponsors/mase1981)


## Features

This integration provides comprehensive control of HDFury HDMI processing devices through native telnet/IP protocol, delivering seamless integration with your Unfolded Circle Remote for complete HDMI management and video processing control.

---
## ❤️ Support Development ❤️

If you find this integration useful, consider supporting development:

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-pink?style=for-the-badge&logo=github)](https://github.com/sponsors/mase1981)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/mmiyara)

Your support helps maintain this integration. Thank you! ❤️
---

## 📺 Supported Devices

This integration supports the following HDFury models with automatic feature detection:

| Model | Status | Default Port | Inputs | Key Features |
|-------|--------|--------------|--------|--------------|
| **VRRooM 8K** | ✅ Fully Tested | 2222 | 4 HDMI | EDID, HDR, CEC, eARC, Analog Audio |
| **VERTEX2** | ✅ Supported | 2220 | 4 HDMI | EDID, HDR, CEC, Scale, Matrix (2 outputs) |
| **VERTEX** | ✅ Supported | 2220 | 2 (Top/Bottom) | EDID, HDR, CEC, Scale, Matrix (2 outputs) |
| **DIVA** | ✅ Supported | 2210 | 4 HDMI | EDID, HDR, CEC, LED controls, Analog Audio |
| **Maestro** | ✅ Supported | 2200 | 4 HDMI | EDID, HDR, CEC, eARC, Analog Audio |
| **ARCANA2** | ✅ Supported | 2222 | Passthrough | Audio modes, Scale modes, Advanced HDR |
| **Dr.HDMI 8K** | ✅ Supported | 2201 | Passthrough | EDID management, Resolution control |

**Each model automatically configures with appropriate features and UI pages based on its capabilities.**

---

### 🎛️ **HDMI Input Control**

#### **Input Switching**
- **HDMI Inputs** - Select from available HDMI inputs (model-dependent)
- **Matrix Routing** - Route inputs to multiple outputs (VERTEX2, VERTEX)
- **Source Selection** - Visual source selection in media player entity
- **Activity Integration** - Seamless input switching in activities

#### **Hotplug Control**
- **Hotplug Event** - Trigger EDID re-negotiation for connected sources
- **Connection Management** - Force source device reconnection
- **EDID Refresh** - Resolve EDID handshake issues

### 🎨 **EDID Management**

#### **EDID Modes**
Control EDID behavior per input:
- **AutoMix** - Automatic EDID mixing
- **Custom** - User-defined EDID
- **Fixed** - Fixed EDID tables
- **Copy** - Copy EDID from outputs
- **EDID Slots** - Load/save custom EDID configurations

#### **EDID Audio Configuration**
- **Stereo** - 2.0 audio capability
- **5.1 Surround** - 5.1 audio formats
- **7.1 Surround** - 7.1 audio formats (VERTEX)
- **Full** - All audio formats
- **Custom** - Custom audio EDID

### 🌈 **HDR & Color Management**

#### **HDR Control**
- **Custom HDR** - Output custom HDR metadata
- **Disable HDR** - Stop all HDR metadata passthrough
- **HDR Modes** - HDR10, HLG control options

#### **Color Space**
- **Auto** - Automatic color space detection
- **RGB** - RGB 4:4:4
- **YCbCr 4:4:4** - Component 4:4:4
- **YCbCr 4:2:2** - Component 4:2:2
- **YCbCr 4:2:0** - Component 4:2:0 (for 4K60 HDR)

#### **Deep Color**
- **Auto** - Automatic bit depth
- **8-bit** - Standard color depth
- **10-bit** - Enhanced color depth
- **12-bit** - Maximum color depth

### 📐 **Video Scaling & Processing**

#### **Scale Modes** (VERTEX2, VERTEX, DIVA, Maestro)
- **Auto** - Automatic scaling
- **Custom** - Custom scaling settings
- **None** - No scaling (passthrough)

#### **Advanced Scaling** (ARCANA2)
- **Down to TX1** - Downscale to output 1
- **FRL TMDS** - Fixed Rate Link TMDS mode
- **Audio Only** - Audio extraction mode
- **4K60 444 8-bit** - Specific format modes with HDR/SDR variants

#### **Output Resolution**
- **Auto** - Automatic resolution
- **4K60/4K30** - 4K output modes
- **1080p60/1080p30** - 1080p output modes
- **720p60** - 720p output mode

### 🔊 **Audio Management**

#### **CEC Control**
- **CEC Engine** - Enable/disable CEC functionality
- **CEC Logical Address** - Configure as video or audio device
- **ARC Force** - Control Audio Return Channel modes
- **eARC Force** - Control Enhanced Audio Return Channel modes

#### **Audio Routing** (ARCANA2)
- **Display Mode** - Audio to display
- **eARC Mode** - Audio to eARC output
- **Both Mode** - Audio to both outputs

#### **Analog Audio** (VRRooM, DIVA, Maestro)
- **Volume Control** - Analog output volume (-30dB to +10dB)
- **Bass Control** - Bass adjustment (-10dB to +10dB)
- **Treble Control** - Treble adjustment (-10dB to +10dB)

#### **TX Audio Mute** (Matrix Models)
- **TX0 Mute** - Mute output 1 audio
- **TX1 Mute** - Mute output 2 audio
- **Independent Control** - Per-output audio control

### ⚙️ **System Settings**

#### **Device Management**
- **Reboot** - Restart HDFury device
- **Factory Reset** - Reset to factory defaults (modes 1, 2, 3)
- **Firmware Info** - Check firmware version
- **Device Info** - Query device status

#### **Display Control**
- **OLED Display** - Enable/disable front panel OLED
- **OLED Page** - Select OLED page (0-4)
- **OLED Fade** - Set OLED fade timer (0-255 seconds)

#### **HDCP Management**
- **Auto Mode** - Automatic HDCP negotiation
- **HDCP 1.4** - Force HDCP 1.4
- **HDCP 2.2** - Force HDCP 2.2 (VERTEX)

#### **Advanced Features**
- **Autoswitch** - Automatic input switching
- **TX Plus5** - +5V voltage control per output
- **HTPC Mode** - HTPC mode per input
- **AVI Custom/Disable** - AVI InfoFrame control

### **Protocol Requirements**

- **Protocol**: HDFury Telnet/IP Control
- **Port**: Model-specific (2200-2222, see table above)
- **IP Interrupts**: Must be enabled (ON) in device settings
- **Network Access**: Device must be on same local network
- **Connection**: Persistent TCP connection with automatic reconnection
- **Timeout Handling**: Exponential backoff retry (5s → 10s → 30s → 60s → 300s)

### **Network Requirements**

- **Local Network Access** - Integration requires same network as HDFury device
- **Telnet Protocol** - TCP telnet communication on configured port
- **Static IP Recommended** - Device should have static IP or DHCP reservation
- **Firewall** - Must allow telnet traffic on device port

## Installation

### Option 1: Remote Web Interface (Recommended)
1. Navigate to the [**Releases**](https://github.com/mase1981/uc-intg-hdfury/releases) page
2. Download the latest `uc-intg-hdfury-<version>-aarch64.tar.gz` file
3. Open your remote's web interface (`http://your-remote-ip`)
4. Go to **Settings** → **Integrations** → **Add Integration**
5. Click **Upload** and select the downloaded `.tar.gz` file

### Option 2: Docker (Advanced Users)

The integration is available as a pre-built Docker image from GitHub Container Registry:

**Image**: `ghcr.io/mase1981/uc-intg-hdfury:latest`

**Docker Compose:**
```yaml
services:
  uc-intg-hdfury:
    image: ghcr.io/mase1981/uc-intg-hdfury:latest
    container_name: uc-intg-hdfury
    network_mode: host
    volumes:
      - </local/path>:/data
    environment:
      - UC_CONFIG_HOME=/data
      - UC_INTEGRATION_HTTP_PORT=9029
      - UC_INTEGRATION_INTERFACE=0.0.0.0
      - PYTHONPATH=/app
    restart: unless-stopped
```

**Docker Run:**
```bash
docker run -d --name uc-hdfury --restart unless-stopped --network host -v hdfury-config:/app/config -e UC_CONFIG_HOME=/app/config -e UC_INTEGRATION_INTERFACE=0.0.0.0 -e UC_INTEGRATION_HTTP_PORT=9029 -e PYTHONPATH=/app ghcr.io/mase1981/uc-intg-hdfury:latest
```

## Configuration

### Step 1: Prepare Your HDFury Device

**IMPORTANT**: HDFury device must be powered on, connected to network, and have IP Interrupts enabled before adding the integration.

#### Verify IP Control:
1. Access device OSD menu or web interface
2. Navigate to **Network Settings** → **IP Control**
3. Enable **IP INTERRUPTS** (set to **ON**)
4. Note the **Port** number (defaults vary by model)
5. Note the device **IP Address**

#### Network Setup:
- **Wired Connection**: Recommended for stability
- **Static IP**: Recommended via DHCP reservation
- **Firewall**: Allow telnet traffic on device port
- **Network Isolation**: Must be on same subnet as Remote

### Step 2: Setup Integration

1. After installation, go to **Settings** → **Integrations**
2. The HDFury integration should appear in **Available Integrations**
3. Click **"Configure"** to begin setup:

#### **Configuration:**
- **Select Model**: Choose your HDFury device model from dropdown
- **IP Address**: Enter device IP (e.g., 192.168.1.100)
- **Port**: Auto-filled based on model (can be customized)
- Click **Complete Setup**

#### **Connection Test:**
- Integration verifies device connectivity
- Telnet connection established
- Setup fails if device unreachable or IP Interrupts disabled

4. Integration will create entities:
   - **Media Player**: `hdfury-[ip]`
   - **Remote**: `hdfury-[ip]-remote`

## Using the Integration

### Media Player Entity

The media player entity provides input control:

- **Power State**: Device availability monitoring
- **Input Selection**: Dropdown with available HDMI inputs
- **Source Names**: Model-specific input naming
  - VRRooM/VERTEX2/DIVA/Maestro: HDMI 0-3
  - VERTEX: Top/Bottom
  - ARCANA2/Dr.HDMI: No input selection (passthrough)
- **Activity Integration**: Seamless activity input switching

### Remote Entity

The remote entity provides comprehensive control with **dynamic UI pages** based on device capabilities:

#### **Sources Page** (Multi-input models)
Direct HDMI input selection buttons

#### **EDID Page** (Most models)
- EDID mode selection
- Audio format configuration
- EDID slot management

#### **Scale Page** (VERTEX2, VERTEX, DIVA, Maestro, ARCANA2)
Video scaling mode control

#### **Audio Page** (ARCANA2)
Audio routing configuration

#### **HDR Page** (Most models)
- Custom HDR control
- HDR disable toggle
- Color space selection
- Deep color modes

#### **CEC/eARC Page** (VRRooM, VERTEX2, DIVA, Maestro)
- CEC engine control
- ARC/eARC force modes
- CEC logical address

#### **System Page** (Model-dependent)
- OLED display control
- Autoswitch toggle
- HDCP mode selection
- Reboot button
- Hotplug trigger

## Credits

- **Developer**: Meir Miyara
- **HDFury**: Premium HDMI processing devices
- **Unfolded Circle**: Remote 2/3 integration framework (ucapi)
- **Protocol**: HDFury Telnet/IP Control Protocol
- **Community**: Testing and feedback from UC and HDFury communities

## License

This project is licensed under the Mozilla Public License 2.0 (MPL-2.0) - see LICENSE file for details.

## Support & Community

- **GitHub Issues**: [Report bugs and request features](https://github.com/mase1981/uc-intg-hdfury/issues)
- **UC Community Forum**: [General discussion and support](https://unfolded.community/)
- **Discord**: [Unfolded Circle Discord](https://discord.gg/zGVYf58)
- **Developer**: [Meir Miyara](https://www.linkedin.com/in/meirmiyara)
- **HDFury Support**: [Official HDFury Support](https://www.hdfury.com/support/)

---

**Made with ❤️ for the Unfolded Circle and HDFury Communities**

**Thank You**: Meir Miyara
