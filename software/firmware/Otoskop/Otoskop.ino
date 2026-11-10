#include <Arduino.h>
#include <WiFi.h>
#include <SPI.h>
#include <SD.h>
#include <Preferences.h>
#include <esp_camera.h>
#include <esp_http_server.h>
#include <esp_arduino_version.h>
#include <driver/ledc.h>
#include <esp_mac.h>
#include <esp_heap_caps.h>
#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>
#include <atomic>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include "settings.h"
#include "photo_names.h"
#include "jpeg_dimensions.h"
#include "photo_buffer.h"

#if !defined(ARDUINO_XIAO_ESP32S3) || !defined(BOARD_HAS_PSRAM)
#error "Build requires XIAO_ESP32S3 and PSRAM=opi; use scripts/build.sh"
#endif
#if !ARDUINO_USB_CDC_ON_BOOT
#error "USB CDC on boot must be enabled"
#endif

static Preferences counterStore;
static SemaphoreHandle_t cameraMutex;
static httpd_handle_t webServer = nullptr, streamServer = nullptr;
static std::atomic<bool> cameraReady{false};
static bool sdReady = false, counterReady = false;
static String cameraMessage = "Kamera noch nicht initialisiert.";
static String sdMessage = "SD noch nicht initialisiert.";
static String serverMessage = "Streamserver noch nicht gestartet.";
static String lastSaved;
static String deviceName, deviceId;
static framesize_t photoSize = FRAMESIZE_VGA;
static uint16_t photoWidth = 0, photoHeight = 0;

static void initIdentity() {
  uint8_t mac[6] = {};
  esp_efuse_mac_get_default(mac);
  char id[18], suffix[8];
  snprintf(id, sizeof(id), "%02x:%02x:%02x:%02x:%02x:%02x", mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  snprintf(suffix, sizeof(suffix), "-%02X%02X%02X", mac[3], mac[4], mac[5]);
  deviceId = id;
  deviceName = String(AP_SSID) + suffix;
}
static uint64_t nextPhoto = 1;
static std::atomic<uint32_t> streamFailures{0};
static SemaphoreHandle_t lightMutex;
static bool lightReady = false;
static std::atomic<uint8_t> lightBrightness{0};
static uint32_t lightLastCommand = 0; // guarded by lightMutex
static String lightMessage = "Deaktiviert: LED-Verdrahtung und LIGHT_GPIO noch festlegen.";

// Use an explicit timer and channel, separate from the camera configuration.
static void initLight() {
  if (LIGHT_GPIO < 0) return;
  pinMode(LIGHT_GPIO, OUTPUT);
  digitalWrite(LIGHT_GPIO, LOW);
  lightMutex = xSemaphoreCreateMutex();
  if (!lightMutex) { lightMessage = "LED-Synchronisation fehlgeschlagen."; return; }
  ledc_timer_config_t timer = {};
  timer.speed_mode = LEDC_LOW_SPEED_MODE;
  timer.duty_resolution = LEDC_TIMER_8_BIT;
  timer.timer_num = LEDC_TIMER_1;
  timer.freq_hz = LIGHT_PWM_HZ;
  timer.clk_cfg = LEDC_AUTO_CLK;
  ledc_channel_config_t channel = {};
  channel.gpio_num = LIGHT_GPIO;
  channel.speed_mode = LEDC_LOW_SPEED_MODE;
  channel.channel = LEDC_CHANNEL_1;
  channel.intr_type = LEDC_INTR_DISABLE;
  channel.timer_sel = LEDC_TIMER_1;
  channel.duty = 0;
  if (ledc_timer_config(&timer) != ESP_OK || ledc_channel_config(&channel) != ESP_OK) {
    lightMessage = "LED-PWM konnte nicht gestartet werden.";
    return;
  }
  lightReady = true;
  lightMessage = "Bereit; automatische Abschaltung nach 10 s ohne Steuerbefehl.";
}

static bool writeLightLocked(uint8_t value) {
  const uint32_t duty = (uint32_t(value) * 255 + 50) / 100;
  if (ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_1, duty) != ESP_OK ||
      ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_1) != ESP_OK) return false;
  lightBrightness.store(value);
  lightLastCommand = millis();
  return true;
}

static void expireLight() {
  if (!lightReady || !lightBrightness.load()) return;
  if (xSemaphoreTake(lightMutex, pdMS_TO_TICKS(20)) != pdTRUE) return;
  if (lightBrightness.load() && uint32_t(millis() - lightLastCommand) >= LIGHT_TIMEOUT_MS)
    writeLightLocked(0);
  xSemaphoreGive(lightMutex);
}

static const char INDEX_HTML[] PROGMEM = R"HTML(<!doctype html>
<html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Otoskop · Kamera</title><style>
*{box-sizing:border-box}body{font:17px system-ui,sans-serif;background:#10232d;color:#edf5f7;margin:0;padding:24px}
main{max-width:880px;margin:auto}h1{margin:0 0 8px}p{line-height:1.5}small{color:#b6cbd3}
img{display:block;width:100%;min-height:220px;object-fit:contain;background:#07141b;border-radius:14px;margin:20px 0}
button{font:inherit;padding:13px 20px;margin:0 8px 12px 0;border:0;border-radius:8px;background:#66e0c7;color:#10232d;cursor:pointer}
button:disabled{opacity:.45;cursor:wait}.panel{background:#1a3441;padding:16px;border-radius:12px;white-space:pre-line;overflow-wrap:anywhere}
.error{color:#ffb5a9}#result{min-height:1.5em}
</style><main><h1>Otoskop</h1><small>Livebild 640 × 480 · Fotos in voller Sensorauflösung · microSD</small>
<img id="live" alt="Das Livebild wird geladen.">
<button id="photo" disabled>Foto auf SD speichern</button><button id="toggle">Livebild pausieren</button>
<p id="result" role="status" aria-live="polite"></p><div id="status" class="panel">Status wird geladen …</div>
<p><small>Fotos liegen im Ordner /photos auf der microSD-Karte. Karte nur bei ausgeschaltetem Board entfernen.</small></p></main>
<script>
const live=document.querySelector('#live'),photo=document.querySelector('#photo'),statusBox=document.querySelector('#status'),result=document.querySelector('#result'),toggle=document.querySelector('#toggle');
let running=true,busy=false,ready=false;
function start(){live.src='http://'+location.hostname+':81/stream?t='+Date.now()}
live.onerror=()=>{result.textContent='Livebild unterbrochen. Status prüfen und Livebild erneut starten.';result.className='error'};
toggle.onclick=()=>{running=!running;if(running)start();else live.removeAttribute('src');toggle.textContent=running?'Livebild pausieren':'Livebild starten'};
async function refresh(){if(busy)return;try{const r=await fetch('/status',{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);const s=await r.json();
ready=s.camera_ok&&s.sd_ok;photo.disabled=busy||!ready;
statusBox.textContent='Kamera: '+s.camera+'\nSD: '+s.sd+'\nStream: '+s.stream+'\nStream-Aufnahmefehler: '+s.stream_failures+(s.last_saved?'\nLetztes Foto: '+s.last_saved:'');
statusBox.className='panel'+(ready?'':' error');if(!s.camera_ok)live.removeAttribute('src');
}catch(e){photo.disabled=true;statusBox.textContent='Board nicht erreichbar: '+e.message;statusBox.className='panel error'}}
photo.onclick=async()=>{busy=true;photo.disabled=true;result.className='';result.textContent='Foto wird gespeichert …';try{
const r=await fetch('/capture',{method:'POST'});const s=await r.json();if(!r.ok)throw Error(s.error||'HTTP '+r.status);
result.textContent='Gespeichert: '+s.path+' · '+s.width+' × '+s.height+' ('+s.bytes+' Bytes)';
}catch(e){result.className='error';result.textContent=e.message}finally{busy=false;await refresh()}};
start();refresh();setInterval(refresh,3000);
</script></html>)HTML";

static String jsonQuote(const String &value) {
  String out = "\"";
  for (size_t i = 0; i < value.length(); ++i) {
    const unsigned char c = value[i];
    if (c == '"' || c == '\\') { out += '\\'; out += char(c); }
    else if (c < 0x20) { char escape[7]; snprintf(escape, sizeof(escape), "\\u%04x", c); out += escape; }
    else out += char(c);
  }
  return out + '"';
}

static esp_err_t sendJson(httpd_req_t *req, const char *status, const String &json) {
  httpd_resp_set_status(req, status);
  httpd_resp_set_type(req, "application/json; charset=utf-8");
  httpd_resp_set_hdr(req, "Cache-Control", "no-store");
  return httpd_resp_send(req, json.c_str(), json.length());
}

static esp_err_t sendError(httpd_req_t *req, const char *status, const String &message) {
  Serial.println(message);
  return sendJson(req, status, "{\"error\":" + jsonQuote(message) + "}");
}

static void initCamera() {
  if (!cameraMutex) { cameraMessage = "Kein Speicher für Kamera-Synchronisation."; return; }
  if (!psramFound()) { cameraMessage = "PSRAM fehlt. PSRAM=opi prüfen und Board neu starten."; return; }
  camera_config_t config = {};
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = CAM_D0; config.pin_d1 = CAM_D1;
  config.pin_d2 = CAM_D2; config.pin_d3 = CAM_D3;
  config.pin_d4 = CAM_D4; config.pin_d5 = CAM_D5;
  config.pin_d6 = CAM_D6; config.pin_d7 = CAM_D7;
  config.pin_xclk = CAM_XCLK; config.pin_pclk = CAM_PCLK;
  config.pin_vsync = CAM_VSYNC; config.pin_href = CAM_HREF;
  config.pin_sccb_sda = CAM_SDA; config.pin_sccb_scl = CAM_SCL;
  config.pin_pwdn = -1; config.pin_reset = -1;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  // Allocate buffers at maximum resolution first. The driver clamps this to
  // the detected sensor's native maximum (OV2640 / OV3660 / OV5640).
  config.frame_size = FRAMESIZE_5MP;
  config.jpeg_quality = PHOTO_QUALITY;
  config.fb_count = 2;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.grab_mode = CAMERA_GRAB_LATEST;
  const esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    cameraMessage = "Kamera nicht gestartet: " + String(esp_err_to_name(err)) +
                    ". Sense-Erweiterung und Kamera-Flachbandkabel bei ausgeschaltetem Board prüfen.";
    return;
  }
  sensor_t *sensor = esp_camera_sensor_get();
  camera_sensor_info_t *info = sensor ? esp_camera_sensor_get_info(&sensor->id) : nullptr;
  if (!info || !info->support_jpeg) {
    cameraMessage = "Kamerasensor unterstützt keine JPEG-Fotos. Kamera prüfen.";
    esp_camera_deinit();
    return;
  }
  photoSize = info->max_size;
  photoWidth = resolution[photoSize].width;
  photoHeight = resolution[photoSize].height;
  if (sensor->set_framesize(sensor, STREAM_SIZE) != 0 ||
      sensor->set_quality(sensor, STREAM_QUALITY) != 0) {
    cameraMessage = "Livebild-Auflösung konnte nicht eingestellt werden. Board neu starten.";
    esp_camera_deinit();
    return;
  }
  cameraReady = true;
  cameraMessage = String("Bereit, ") + info->name + "; Live 640 × 480, Foto " +
                  String(photoWidth) + " × " + String(photoHeight) + "; Sensor-ID 0x" + String(sensor->id.PID, HEX) +
                  ", PSRAM " + String(ESP.getPsramSize() / (1024 * 1024)) + " MB";
}

static void initSD() {
  SPI.begin(SD_SCK, SD_MISO, SD_MOSI, SD_CS);
  if (!SD.begin(SD_CS, SPI, SD_SPI_HZ, "/sd", 5, false)) {
    sdMessage = "Karte nicht eingebunden. FAT32-microSD bis 32 GB und Sitz der Sense-Erweiterung prüfen; danach neu starten.";
    return;
  }
  if (SD.cardType() == CARD_NONE) { sdMessage = "Keine microSD-Karte erkannt. Karte einsetzen und neu starten."; return; }
  if (!SD.exists("/photos") && !SD.mkdir("/photos")) { sdMessage = "Ordner /photos nicht anlegbar. Karte voll oder Dateisystem beschädigt."; return; }
  File dir = SD.open("/photos");
  if (!dir || !dir.isDirectory()) { sdMessage = "/photos ist kein lesbarer Ordner."; return; }
  counterReady = counterStore.begin("otoskop", false);
  if (!counterReady) { sdMessage = "Persistenter Fotozähler (NVS) nicht verfügbar. Neustart erforderlich."; return; }
  uint32_t highest = counterStore.getUInt("last", 0);
  File entry = dir.openNextFile();
  while (entry) {
    uint32_t number;
    if (parsePhotoNumber(entry.name(), number) && number > highest) highest = number;
    entry.close();
    entry = dir.openNextFile();
  }
  dir.close();
  nextPhoto = uint64_t(highest) + 1;
  sdReady = true;
  sdMessage = "Bereit, " + String(SD.cardSize() / (1024 * 1024)) + " MB; Ordner /photos";
}

static esp_err_t indexHandler(httpd_req_t *req) {
  httpd_resp_set_type(req, "text/html; charset=utf-8");
  httpd_resp_set_hdr(req, "Cache-Control", "no-store");
  return httpd_resp_send(req, INDEX_HTML, HTTPD_RESP_USE_STRLEN);
}

// All SD state and NVS operations belong to the port-80 HTTP server task.
static esp_err_t statusHandler(httpd_req_t *req) {
  String json = "{\"api_version\":2,\"snapshot_supported\":true,\"high_res_photo_supported\":true,\"camera_ok\":" + String(cameraReady ? "true" : "false") +
                ",\"stream_width\":640,\"stream_height\":480,\"photo_width\":" + String(photoWidth) +
                ",\"photo_height\":" + String(photoHeight) +
                ",\"device_id\":" + jsonQuote(deviceId) + ",\"device_name\":" + jsonQuote(deviceName) +
                ",\"firmware_version\":" + jsonQuote(FIRMWARE_VERSION) +
                ",\"sd_ok\":" + String(sdReady ? "true" : "false") +
                ",\"stream_ok\":" + String(streamServer ? "true" : "false") +
                ",\"led_supported\":" + String(lightReady ? "true" : "false") +
                ",\"led_brightness\":" + String(lightBrightness.load()) +
                ",\"led\":" + jsonQuote(lightMessage) +
                ",\"camera\":" + jsonQuote(cameraMessage) + ",\"sd\":" + jsonQuote(sdMessage) +
                ",\"stream\":" + jsonQuote(serverMessage) + ",\"last_saved\":" + jsonQuote(lastSaved) +
                ",\"stream_failures\":" + String(streamFailures.load()) + "}";
  return sendJson(req, "200 OK", json);
}

static esp_err_t lightHandler(httpd_req_t *req) {
  if (!lightReady) return sendError(req, "503 Service Unavailable", lightMessage);
  char query[40], value[5];
  if (httpd_req_get_url_query_str(req, query, sizeof(query)) != ESP_OK ||
      httpd_query_key_value(query, "brightness", value, sizeof(value)) != ESP_OK)
    return sendError(req, "400 Bad Request", "brightness muss eine ganze Zahl von 0 bis 100 sein.");
  unsigned brightness = 0;
  const size_t length = strlen(value);
  if (length == 0 || length > 3)
    return sendError(req, "400 Bad Request", "Ungültige LED-Helligkeit.");
  for (size_t i = 0; i < length; ++i) {
    if (value[i] < '0' || value[i] > '9')
      return sendError(req, "400 Bad Request", "Ungültige LED-Helligkeit.");
    brightness = brightness * 10 + unsigned(value[i] - '0');
  }
  if (brightness > 100) return sendError(req, "400 Bad Request", "LED-Helligkeit muss zwischen 0 und 100 liegen.");
  if (xSemaphoreTake(lightMutex, pdMS_TO_TICKS(100)) != pdTRUE)
    return sendError(req, "503 Service Unavailable", "LED-Steuerung beschäftigt.");
  const bool ok = writeLightLocked(static_cast<uint8_t>(brightness));
  xSemaphoreGive(lightMutex);
  if (!ok) return sendError(req, "500 Internal Server Error", "LED-PWM konnte nicht aktualisiert werden.");
  return sendJson(req, "200 OK", "{\"led_brightness\":" + String(brightness) + "}");
}

// Both PC and SD photos use the native sensor maximum. Restore preview mode
// on every path, then release the camera before network or SD I/O.
static bool takePhoto(Photo &photo, String &error) {
  if (!cameraReady) { error = cameraMessage; return false; }
  if (xSemaphoreTake(cameraMutex, pdMS_TO_TICKS(5000)) != pdTRUE) {
    error = "Kamera beschäftigt. Erneut versuchen.";
    return false;
  }
  sensor_t *sensor = esp_camera_sensor_get();
  const bool selected = sensor && sensor->set_quality(sensor, PHOTO_QUALITY) == 0 &&
                        sensor->set_framesize(sensor, photoSize) == 0;
  if (selected) {
    // Two buffers can still contain the old mode or a frame crossing the
    // register update. Discard both; inspect JPEG bytes on subsequent frames.
    for (unsigned attempt = 0; attempt < 6; ++attempt) {
      camera_fb_t *fb = esp_camera_fb_get();
      if (!fb) { error = "Keine Kameraaufnahme erhalten. Board neu starten."; break; }
      const bool valid = attempt >= 2 && fb->format == PIXFORMAT_JPEG &&
                         jpegHasSize(fb->buf, fb->len, photoWidth, photoHeight) &&
                         fb->len >= 4 && fb->buf[fb->len - 2] == 0xff && fb->buf[fb->len - 1] == 0xd9;
      if (valid) {
        photo.data = static_cast<uint8_t *>(heap_caps_malloc(fb->len, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT));
        if (photo.data) { memcpy(photo.data, fb->buf, fb->len); photo.length = fb->len; }
        else error = "Zu wenig PSRAM für das Foto. Board neu starten.";
      }
      esp_camera_fb_return(fb);
      if (valid) break;
    }
    if (!photo.length && !error.length())
      error = "Kamera liefert noch kein vollständiges Foto in maximaler Auflösung. Erneut versuchen.";
  } else error = "Fotoauflösung konnte nicht eingestellt werden.";
  // Do not short-circuit: attempt both restoration operations even on failure.
  const bool sizeRestored = sensor && sensor->set_framesize(sensor, STREAM_SIZE) == 0;
  const bool qualityRestored = sensor && sensor->set_quality(sensor, STREAM_QUALITY) == 0;
  if (!sizeRestored || !qualityRestored) {
    cameraMessage = "Livebild konnte nach der Aufnahme nicht wiederhergestellt werden. Board neu starten.";
    cameraReady = false;
    error = cameraMessage;
  }
  xSemaphoreGive(cameraMutex);
  return photo.length && sizeRestored && qualityRestored;
}

// Direct JPEG capture for the desktop app; independent of microSD and NVS.
static esp_err_t snapshotHandler(httpd_req_t *req) {
  Photo photo;
  String error;
  if (!takePhoto(photo, error)) return sendError(req, "503 Service Unavailable", error);
  httpd_resp_set_type(req, "image/jpeg");
  httpd_resp_set_hdr(req, "Cache-Control", "no-store");
  return httpd_resp_send(req, reinterpret_cast<const char *>(photo.data), photo.length);
}

// Reserve the number in NVS before creating the file. O_EXCL prevents truncating
// an existing file even if NVS was cleared or the card was exchanged.
static int reservePhoto(char *sdPath, size_t sdPathSize, String &error) {
  while (nextPhoto <= UINT32_MAX) {
    const uint32_t number = static_cast<uint32_t>(nextPhoto++);
    if (counterStore.putUInt("last", number) != sizeof(uint32_t)) {
      error = "Fotozähler konnte nicht dauerhaft gespeichert werden."; return -1;
    }
    snprintf(sdPath, sdPathSize, "/photos/IMG_%010lu.jpg", static_cast<unsigned long>(number));
    const String fullPath = String("/sd") + sdPath;
    const int fd = open(fullPath.c_str(), O_WRONLY | O_CREAT | O_EXCL, 0666);
    if (fd >= 0) return fd;
    if (errno != EEXIST) {
      error = "Fotodatei nicht anlegbar: " + String(strerror(errno)) + ". SD-Karte und freien Platz prüfen.";
      return -1;
    }
  }
  error = "Fotozähler ausgeschöpft (4294967295).";
  return -1;
}

static esp_err_t captureHandler(httpd_req_t *req) {
  if (!cameraReady) return sendError(req, "503 Service Unavailable", cameraMessage);
  if (!sdReady || !counterReady) return sendError(req, "503 Service Unavailable", sdMessage);
  Photo photo;
  String error;
  if (!takePhoto(photo, error)) return sendError(req, "503 Service Unavailable", error);
  char path[40] = {};
  const int fd = reservePhoto(path, sizeof(path), error);
  const size_t length = photo.length;
  bool saved = fd >= 0;
  if (saved) {
    size_t offset = 0;
    while (offset < length) {
      const ssize_t count = write(fd, photo.data + offset, length - offset);
      if (count < 0 && errno == EINTR) continue;
      if (count <= 0) { saved = false; break; }
      offset += static_cast<size_t>(count);
    }
    if (fsync(fd) != 0) saved = false;
    if (close(fd) != 0) saved = false;
    if (!saved) error = "JPEG nicht vollständig gespeichert. SD voll, entfernt oder Schreibfehler. Karte bei ausgeschaltetem Board prüfen.";
    // A failed partial file is intentionally retained; its number is never reused.
  }
  if (!saved) {
    sdReady = false; sdMessage = error + " Anschließend Board neu starten.";
    return sendError(req, "507 Insufficient Storage", sdMessage);
  }
  lastSaved = path;
  Serial.printf("Foto gespeichert: %s (%u Bytes)\n", path, static_cast<unsigned>(length));
  return sendJson(req, "201 Created", "{\"path\":" + jsonQuote(path) + ",\"bytes\":" + String(length) +
                  ",\"width\":" + String(photoWidth) + ",\"height\":" + String(photoHeight) + "}");
}

static esp_err_t streamHandler(httpd_req_t *req) {
  if (!cameraReady) return sendError(req, "503 Service Unavailable", cameraMessage);
  httpd_resp_set_type(req, "multipart/x-mixed-replace;boundary=otoskop_frame");
  httpd_resp_set_hdr(req, "Cache-Control", "no-store");
  esp_err_t result = ESP_OK;
  while (WiFi.softAPgetStationNum() > 0) {
    if (xSemaphoreTake(cameraMutex, pdMS_TO_TICKS(40000)) != pdTRUE) { result = ESP_FAIL; break; }
    if (!cameraReady) { xSemaphoreGive(cameraMutex); result = ESP_FAIL; break; }
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb || fb->format != PIXFORMAT_JPEG) {
      if (fb) esp_camera_fb_return(fb);
      xSemaphoreGive(cameraMutex);
      streamFailures.fetch_add(1);
      Serial.println("Stream: Kamera liefert kein JPEG. Livebild neu starten; ggf. Board neu starten.");
      result = ESP_FAIL; break;
    }
    // A high-resolution frame can remain queued after a photo. Never send it
    // through the low-resolution live feed, regardless of the driver's metadata.
    if (!jpegHasSize(fb->buf, fb->len, 640, 480)) {
      esp_camera_fb_return(fb);
      xSemaphoreGive(cameraMutex);
      vTaskDelay(pdMS_TO_TICKS(10));
      continue;
    }
    char header[128];
    const int headerLength = snprintf(header, sizeof(header),
      "--otoskop_frame\r\nContent-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n", static_cast<unsigned>(fb->len));
    result = httpd_resp_send_chunk(req, header, headerLength);
    if (result == ESP_OK) result = httpd_resp_send_chunk(req, reinterpret_cast<const char *>(fb->buf), fb->len);
    if (result == ESP_OK) result = httpd_resp_send_chunk(req, "\r\n", 2);
    esp_camera_fb_return(fb);
    xSemaphoreGive(cameraMutex);
    if (result != ESP_OK) break;
    vTaskDelay(pdMS_TO_TICKS(40)); // Let pending photo requests acquire the mutex.
  }
  // Returning failure makes httpd close the socket after a broken MJPEG response.
  return result == ESP_OK ? httpd_resp_send_chunk(req, nullptr, 0) : result;
}

static bool registerRoute(httpd_handle_t server, const char *uri, httpd_method_t method, esp_err_t (*handler)(httpd_req_t *)) {
  httpd_uri_t route = {};
  route.uri = uri; route.method = method; route.handler = handler;
  return httpd_register_uri_handler(server, &route) == ESP_OK;
}

static void startServers() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = 81; config.ctrl_port = 32769;
  config.stack_size = 8192; config.send_wait_timeout = 2; config.recv_wait_timeout = 5;
  if (httpd_start(&streamServer, &config) == ESP_OK && registerRoute(streamServer, "/stream", HTTP_GET, streamHandler))
    serverMessage = "Bereit auf Port 81 (ein aktives Livebild)";
  else {
    if (streamServer) { httpd_stop(streamServer); streamServer = nullptr; }
    serverMessage = "Streamserver konnte nicht starten. Board neu starten.";
  }
  // Start the control server last: all status strings are now initialized.
  config.server_port = 80; config.ctrl_port = 32768;
  config.lru_purge_enable = true;
  if (httpd_start(&webServer, &config) != ESP_OK ||
      !registerRoute(webServer, "/", HTTP_GET, indexHandler) ||
      !registerRoute(webServer, "/status", HTTP_GET, statusHandler) ||
      !registerRoute(webServer, "/snapshot", HTTP_POST, snapshotHandler) ||
      !registerRoute(webServer, "/led", HTTP_POST, lightHandler) ||
      !registerRoute(webServer, "/capture", HTTP_POST, captureHandler))
    Serial.println("FEHLER: Webserver nicht vollständig gestartet. Board neu starten.");
}

void setup() {
  Serial.begin(115200);
  delay(500); // No while(!Serial): stand-alone operation without a USB host.
  Serial.printf("\nOtoskop | Arduino-ESP32 %s\n", ESP_ARDUINO_VERSION_STR);
  initIdentity();
  cameraMutex = xSemaphoreCreateMutex();
  initCamera(); Serial.println(cameraMessage);
  initLight(); Serial.println(lightMessage);
  initSD(); Serial.println(sdMessage);
  WiFi.mode(WIFI_AP);
  const IPAddress ip(192, 168, 4, 1), mask(255, 255, 255, 0);
  if (!WiFi.softAPConfig(ip, ip, mask) || !WiFi.softAP(deviceName.c_str(), AP_PASSWORD, AP_CHANNEL, false, 2)) {
    Serial.println("FEHLER: WLAN-Access-Point konnte nicht starten. Stromversorgung prüfen und neu starten.");
    return;
  }
  startServers();
  Serial.printf("WLAN: %s | Passwort: %s | http://192.168.4.1\n", deviceName.c_str(), AP_PASSWORD);
  Serial.println(serverMessage);
}

void loop() { expireLight(); delay(50); }
