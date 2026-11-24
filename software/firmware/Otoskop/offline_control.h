#pragma once
#include <stdint.h>

enum class BootMode { Pending, Offline, Wifi };

// Selection is evaluated only once, before camera/network startup. Releasing
// before the threshold cannot be turned into a long hold by release debounce.
class BootSelector {
  uint32_t started_, released_ = 0;
  bool releasing_ = false;
  BootMode mode_;
public:
  BootSelector(uint32_t now, bool pressed)
      : started_(now), mode_(pressed ? BootMode::Pending : BootMode::Offline) {}
  BootMode update(uint32_t now, bool pressed) {
    if (mode_ != BootMode::Pending) return mode_;
    if (pressed) releasing_ = false;
    else if (!releasing_) { releasing_ = true; released_ = now; }
    else if (uint32_t(now - released_) >= 30)
      mode_ = uint32_t(released_ - started_) >= 5000 ? BootMode::Wifi : BootMode::Offline;
    return mode_;
  }
};

// One debounced press, then a release is required. Presses during a busy cycle
// are discarded, including a press that is still held when the cycle ends.
class ShutterButton {
  bool raw_ = false, stable_ = false, armed_ = false;
  uint32_t changed_ = 0;
public:
  void reset(uint32_t now, bool pressed) {
    raw_ = stable_ = pressed; changed_ = now; armed_ = false;
  }
  bool update(uint32_t now, bool pressed, bool ready) {
    if (!ready) armed_ = false;
    if (pressed != raw_) { raw_ = pressed; changed_ = now; }
    if (uint32_t(now - changed_) < 30) return false;
    if (stable_ != raw_) {
      stable_ = raw_;
      if (stable_) {
        const bool fire = ready && armed_;
        armed_ = false;
        return fire;
      }
    }
    if (!stable_ && ready) armed_ = true;
    return false;
  }
};
