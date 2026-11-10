#include "../firmware/Otoskop/jpeg_dimensions.h"
#include <assert.h>
#include <vector>

static std::vector<uint8_t> jpeg(uint16_t w, uint16_t h, uint8_t sof = 0xc0) {
  return {0xff, 0xd8, 0xff, 0xe0, 0, 4, 0, 0,
          0xff, sof, 0, 11, 8, uint8_t(h >> 8), uint8_t(h),
          uint8_t(w >> 8), uint8_t(w), 1, 1, 0x11, 0, 0xff, 0xd9};
}

int main() {
  uint16_t w, h;
  for (const auto &size : {std::vector<uint16_t>{640, 480}, {1600, 1200}, {2048, 1536}, {2592, 1944}}) {
    for (uint8_t sof : {0xc0, 0xc1, 0xc2}) {
      auto data = jpeg(size[0], size[1], sof);
      assert(jpegDimensions(data.data(), data.size(), w, h));
      assert(w == size[0] && h == size[1]);
      assert(jpegHasSize(data.data(), data.size(), size[0], size[1]));
      assert(!jpegHasSize(data.data(), data.size(), 320, 240));
      for (size_t n = 0; n < 21; ++n)
        assert(!jpegDimensions(data.data(), n, w, h));
    }
  }
  // A queued preview must never satisfy a full-resolution photo request.
  auto preview = jpeg(640, 480), photo = jpeg(2048, 1536);
  assert(!jpegHasSize(preview.data(), preview.size(), 2048, 1536));
  assert(!jpegHasSize(photo.data(), photo.size(), 640, 480));
  for (uint8_t marker : {0xc4, 0xc8, 0xcc, 0xda, 0xd9, 0x00}) {
    auto data = jpeg(640, 480, marker);
    assert(!jpegDimensions(data.data(), data.size(), w, h));
  }
  for (uint8_t length : {0, 1, 0xff}) {
    auto data = photo;
    data[5] = length;
    assert(!jpegDimensions(data.data(), data.size(), w, h));
  }
  assert(!jpegDimensions(nullptr, 100, w, h));
  auto zero = jpeg(0, 480);
  assert(!jpegDimensions(zero.data(), zero.size(), w, h));
  // Marker padding and standalone markers are legal before SOF.
  photo.insert(photo.begin() + 2, {0xff, 0x01, 0xff});
  assert(jpegHasSize(photo.data(), photo.size(), 2048, 1536));
}
