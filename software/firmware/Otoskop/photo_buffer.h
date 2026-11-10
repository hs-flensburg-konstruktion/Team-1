#pragma once
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

struct Photo {
  uint8_t *data = nullptr;
  size_t length = 0;
  ~Photo() { free(data); }
  Photo() = default;
  Photo(const Photo &) = delete;
  Photo &operator=(const Photo &) = delete;
};
