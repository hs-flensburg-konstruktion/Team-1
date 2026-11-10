#pragma once
#include <stddef.h>
#include <stdint.h>

// Queued frames may carry the driver's new dimensions but still contain an old
// JPEG. Always check the SOF header before selecting a photo or streaming it.
static inline bool jpegDimensions(const uint8_t *data, size_t size,
                                  uint16_t &width, uint16_t &height) {
  width = height = 0;
  if (!data || size < 4 || data[0] != 0xff || data[1] != 0xd8) return false;
  size_t pos = 2;
  while (pos < size) {
    if (data[pos++] != 0xff) return false;
    while (pos < size && data[pos] == 0xff) ++pos;
    if (pos >= size) return false;
    const uint8_t marker = data[pos++];
    if (marker == 0xda || marker == 0xd9 || marker == 0x00) return false;
    if (marker == 0x01 || (marker >= 0xd0 && marker <= 0xd7)) continue;
    if (size - pos < 2) return false;
    const size_t length = (size_t(data[pos]) << 8) | data[pos + 1];
    if (length < 2 || length > size - pos) return false;
    const bool sof = marker >= 0xc0 && marker <= 0xcf &&
                     marker != 0xc4 && marker != 0xc8 && marker != 0xcc;
    if (sof) {
      if (length < 8) return false;
      height = (uint16_t(data[pos + 3]) << 8) | data[pos + 4];
      width = (uint16_t(data[pos + 5]) << 8) | data[pos + 6];
      return width && height;
    }
    pos += length;
  }
  return false;
}

static inline bool jpegHasSize(const uint8_t *data, size_t size,
                              uint16_t width, uint16_t height) {
  uint16_t actualWidth, actualHeight;
  return jpegDimensions(data, size, actualWidth, actualHeight) &&
         actualWidth == width && actualHeight == height;
}
