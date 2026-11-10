#pragma once

// WPA2 access point. Change the password before sharing the device.
static constexpr char AP_SSID[] = "Otoskop";
static constexpr char AP_PASSWORD[] = "Otoskop-2026";
static constexpr char FIRMWARE_VERSION[] = "1.5.0";
static constexpr framesize_t STREAM_SIZE = FRAMESIZE_VGA;
static constexpr int STREAM_QUALITY = 12;
static constexpr int PHOTO_QUALITY = 10; // Lower means better quality; no upscaling.
static constexpr uint8_t AP_CHANNEL = 6;
static constexpr uint32_t SD_SPI_HZ = 4000000;

// Official Seeed Sense pinout, also CAMERA_MODEL_XIAO_ESP32S3 in Espressif's example.
static constexpr int CAM_D0 = 15, CAM_D1 = 17, CAM_D2 = 18, CAM_D3 = 16;
static constexpr int CAM_D4 = 14, CAM_D5 = 12, CAM_D6 = 11, CAM_D7 = 48;
static constexpr int CAM_XCLK = 10, CAM_PCLK = 13, CAM_VSYNC = 38, CAM_HREF = 47;
static constexpr int CAM_SDA = 40, CAM_SCL = 39;
static constexpr int SD_CS = 21, SD_SCK = 7, SD_MISO = 8, SD_MOSI = 9;
// GPIO21 is shared with the board LED: do not drive LED_BUILTIN when using SD.

// External AO3400A gate on XIAO D0 (ESP GPIO1), as wired in the schematic.
// Set to -1 for builds with the light output disabled.
static constexpr int LIGHT_GPIO = 1;
static constexpr uint32_t LIGHT_PWM_HZ = 20000;
static constexpr uint32_t LIGHT_TIMEOUT_MS = 10000;
static_assert(LIGHT_GPIO == -1 || (LIGHT_GPIO >= 1 && LIGHT_GPIO <= 6) ||
              LIGHT_GPIO == 43 || LIGHT_GPIO == 44,
              "LIGHT_GPIO must be a free XIAO GPIO: 1..6, 43 or 44");
