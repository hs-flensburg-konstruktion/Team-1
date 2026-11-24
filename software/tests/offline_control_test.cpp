#include <assert.h>
#include "../firmware/Otoskop/offline_control.h"

int main() {
  BootSelector normal(0, false);
  assert(normal.update(10000, true) == BootMode::Offline);
  BootSelector early(0, true);
  assert(early.update(4999, false) == BootMode::Pending);
  assert(early.update(5029, false) == BootMode::Offline);
  assert(early.update(15000, true) == BootMode::Offline);
  BootSelector wifi(100, true);
  assert(wifi.update(5100, true) == BootMode::Pending); // release is required
  assert(wifi.update(5100, false) == BootMode::Pending);
  assert(wifi.update(5129, false) == BootMode::Pending);
  assert(wifi.update(5130, false) == BootMode::Wifi);
  BootSelector bounce(0, true);
  bounce.update(20, false);
  assert(bounce.update(25, true) == BootMode::Pending);
  bounce.update(5000, false);
  assert(bounce.update(5030, false) == BootMode::Wifi);
  const uint32_t start = UINT32_MAX - 3000;
  BootSelector wrap(start, true);
  wrap.update(start + 5000U, false);
  assert(wrap.update(start + 5030U, false) == BootMode::Wifi);

  ShutterButton button;
  button.reset(0, true); // held at boot: never capture
  assert(!button.update(6000, true, true));
  assert(!button.update(6001, false, true));
  assert(!button.update(6031, false, true)); // arm on release
  assert(!button.update(6100, true, true));
  assert(!button.update(6110, false, true)); // bounce
  assert(!button.update(6115, true, true));
  assert(!button.update(6144, true, true));
  assert(button.update(6145, true, true));
  assert(!button.update(20000, true, true)); // holding cannot retrigger
  // A new press while busy, still held at the end, is discarded.
  button.reset(20001, true);
  assert(!button.update(20050, true, true));
  button.update(20060, false, true);
  button.update(20090, false, true);
  button.update(20100, true, true);
  assert(button.update(20130, true, true));
  button.update(20200, false, false);
  button.update(20230, false, false);
  button.update(20300, true, false);
  assert(!button.update(20330, true, false));
  assert(!button.update(20400, true, true));
  button.reset(20500, false);
  button.update(20530, false, true);
  button.update(20540, true, false);
  assert(!button.update(20570, true, false)); // fault cannot capture
}
