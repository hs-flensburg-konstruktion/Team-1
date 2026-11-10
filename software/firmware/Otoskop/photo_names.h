#pragma once
#include <stdint.h>
#include <string.h>

// Only accept our exact basename. Ignore other files, subdirectories and overflow.
inline bool parsePhotoNumber(const char *name, uint32_t &number) {
  const char *base = strrchr(name, '/');
  base = base ? base + 1 : name;
  if (strlen(base) != 18 || strncmp(base, "IMG_", 4) != 0 ||
      strcmp(base + 14, ".jpg") != 0) return false;
  uint64_t value = 0;
  for (int i = 4; i < 14; ++i) {
    if (base[i] < '0' || base[i] > '9') return false;
    value = value * 10 + (base[i] - '0');
  }
  if (value == 0 || value > UINT32_MAX) return false;
  number = static_cast<uint32_t>(value);
  return true;
}
