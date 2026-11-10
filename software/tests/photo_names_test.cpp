#include "../firmware/Otoskop/photo_names.h"
#include <assert.h>

int main() {
  uint32_t n = 0;
  assert(parsePhotoNumber("IMG_0000000001.jpg", n) && n == 1);
  assert(parsePhotoNumber("/photos/IMG_0000000042.jpg", n) && n == 42);
  assert(parsePhotoNumber("IMG_4294967295.jpg", n) && n == UINT32_MAX);
  assert(!parsePhotoNumber("IMG_4294967296.jpg", n));
  assert(!parsePhotoNumber("IMG_9999999999.jpg", n));
  assert(!parsePhotoNumber("IMG_0000000000.jpg", n));
  assert(!parsePhotoNumber("IMG_0000000001.jpg.bak", n));
  assert(!parsePhotoNumber("IMG_0000000001.tmp", n));
  assert(!parsePhotoNumber("IMG_00000000a1.jpg", n));
  assert(!parsePhotoNumber("IMG_1.jpg", n));
  assert(!parsePhotoNumber("", n));
}
