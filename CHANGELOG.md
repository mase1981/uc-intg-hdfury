# Changelog

All notable changes to the HDFury Integration will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.1] - 2026-01-22

### Added
- **Sensor Entities**: Added comprehensive sensor support for real-time device monitoring
  - Connection Status sensor - Shows device connection state
  - Firmware Version sensor - Displays current firmware version
  - Current Input sensor - Shows selected input source
  - EDID Mode sensor - Displays active EDID configuration
  - HDR Mode sensor - Shows HDR status and mode
  - HDCP Mode sensor - Displays HDCP version in use
  - OLED Display Status sensor - Shows OLED on/off state
  - Autoswitch Status sensor - Shows autoswitch on/off state
  - Color Space sensor - Displays active color space mode
  - Deep Color sensor - Shows active bit depth
- All commands now available as simple commands for activity setup

### Fixed
- **Reboot Button Visibility**: Fixed reboot and hotplug buttons always visible on System page (was conditionally hidden)
- Sensor state updates properly synchronized with device state changes

### Updated
- **ucapi Library**: Updated from 0.3.1 to 0.5.1 for sensor support
- **min_core_api**: Updated requirement to 0.5.1 for sensor compatibility

## [0.4.0] - 2026-01-22

### Added
- **Reboot Command**: Added device reboot functionality (was missing from previous versions)
- **Factory Reset Commands**: Added factory reset modes 1, 2, and 3
- **Hotplug Command**: Added hotplug event trigger for source devices
- **TX Audio Mute**: Added mute/unmute control for TX0 and TX1 audio outputs
- **Analog Audio Controls**: Added volume, bass, and treble control for analog outputs
- **TX Plus5 Voltage Control**: Added TX0/TX1 plus5 voltage control
- **HTPC Mode Commands**: Added HTPC mode control for ports 0-3
- **OLED Controls**: Added OLED page selection (0-4) and fade timer control (0-255 seconds)
- **CEC Logical Address**: Added CEC logical address configuration (video/audio)
- **AVI Controls**: Added AVI custom and disable commands
- **Structured Exception Classes**: Added HDFuryConnectionError and HDFuryCommandError for better error handling
- **Comprehensive Unit Tests**: Added test suite for client, models, and core functionality
- **System UI Page**: Added reboot and hotplug buttons to remote system page

### Improved
- **Reconnection Logic**: Implemented exponential backoff for connection recovery (5s → 10s → 30s → 60s → 300s)
- **Race Condition Protection**: Added entities_ready flag to prevent race conditions on startup
- **Connection Health**: Enhanced health monitoring with automatic recovery on connection loss
- **Configuration Reload**: Added configuration reload on Remote reconnect for better reboot survival
- **Error Handling**: Better exception handling throughout the codebase
- **Command Timeout**: Improved timeout handling with retry logic

### Fixed
- Connection stability issues with better retry mechanisms
- Entity subscription timing issues with race condition protection
- Missing commands that were in VRRooM specification but not implemented

### Technical Improvements
- Added initialization_lock for thread-safe entity setup
- Improved logging with detailed reconnection attempt tracking
- Enhanced command queue management
- Better async/await patterns for connection management
- Modernized codebase to match latest integration patterns from successful integrations

## [0.3.7] - Previous Release

- Initial stable release with basic HDFury device support
- Support for VRRooM, VERTEX, VERTEX2, DIVA, Maestro, ARCANA2, and Dr.HDMI 8K
- Basic EDID management
- HDR and color space controls
- CEC and eARC controls
- Media player and remote entities
