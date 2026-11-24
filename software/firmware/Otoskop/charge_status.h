#pragma once
#include <stdint.h>

enum class ChargeState { NoUsb, Unknown, Charging, Full };

// The nCHG node is loaded by its existing on-board LED + 10k resistor.
// External 10k/10k dividers, no external capacitors. High nCHG ADC readings
// are therefore around 1V, not half of the USB voltage. Compare levels with
// hysteresis; positive charging/completion timing is still required.
static constexpr unsigned CHARGE_ACTIVE_MAX_MV = 400;
static constexpr unsigned CHARGE_INACTIVE_MIN_MV = 650;

inline unsigned medianMillivolts5(const unsigned *values) {
  unsigned sorted[5];
  for (unsigned i = 0; i < 5; ++i) {
    unsigned j = i;
    while (j && sorted[j-1] > values[i]) { sorted[j] = sorted[j-1]; --j; }
    sorted[j] = values[i];
  }
  return sorted[2];
}

enum class SenseLevel { Unknown, Low, High };

// Accept valid level transitions only after 20ms of stability. Ambiguous
// levels need 100ms before invalidating the previous value. No RC required.
class StableSense {
  SenseLevel stable_ = SenseLevel::Unknown, candidate_ = SenseLevel::Unknown;
  uint32_t changed_ = 0;
  bool initialized_ = false;
public:
  void reset() { stable_ = candidate_ = SenseLevel::Unknown; initialized_ = false; }
  SenseLevel update(uint32_t now, SenseLevel value) {
    if (!initialized_ || candidate_ != value) {
      initialized_ = true; candidate_ = value; changed_ = now;
    }
    const uint32_t duration = value == SenseLevel::Unknown ? 100 : 20;
    if (uint32_t(now - changed_) >= duration) stable_ = candidate_;
    return stable_;
  }
};

// SGM40567: 160ms active per 1280ms while charging, then 51.2s active at
// completion. Off alone, power-on with a full battery, and missing battery
// are not sufficient evidence of a full charge.
class ChargeMonitor {
  ChargeState state_ = ChargeState::Unknown;
  SenseLevel level_ = SenseLevel::Unknown;
  StableSense usbInput_, chargeInput_;
  bool usb_ = false, sampled_ = false, pulse_ = false, observed_ = false;
  uint32_t sampleAt_ = 0, levelAt_ = 0, usbAt_ = 0, pulseAt_ = 0, validAt_ = 0;
  unsigned pulses_ = 0;

  void forget() {
    level_ = SenseLevel::Unknown; pulse_ = observed_ = false; pulses_ = 0;
    state_ = ChargeState::Unknown;
  }
public:
  ChargeState state() const { return state_; }
  ChargeState update(uint32_t now, unsigned usbMv, unsigned chargeMv) {
    const bool gap = sampled_ && uint32_t(now - sampleAt_) > 100;
    sampled_ = true; sampleAt_ = now;
    if (gap) { usbInput_.reset(); chargeInput_.reset(); usb_ = false; forget(); }
    const SenseLevel rawUsb = usbMv < 800 ? SenseLevel::Low :
        usbMv >= 1800 && usbMv <= 2900 ? SenseLevel::High : SenseLevel::Unknown;
    const SenseLevel usbLevel = usbInput_.update(now, rawUsb);
    if (usbLevel != SenseLevel::High) {
      usb_ = false; forget();
      if (usbLevel == SenseLevel::Low) state_ = ChargeState::NoUsb;
      return state_;
    }
    if (!usb_) { usb_ = true; usbAt_ = now; forget(); chargeInput_.reset(); }
    const SenseLevel rawCharge = chargeMv <= CHARGE_ACTIVE_MAX_MV ? SenseLevel::Low :
        chargeMv >= CHARGE_INACTIVE_MIN_MV && chargeMv <= 2900 ? SenseLevel::High : SenseLevel::Unknown;
    const SenseLevel incoming = chargeInput_.update(now, rawCharge);
    if (uint32_t(now - usbAt_) < 500) return state_;
    if (incoming == SenseLevel::Unknown) { forget(); return state_; }
    if (level_ == SenseLevel::Unknown) { level_ = incoming; levelAt_ = now; return state_; }
    if (incoming != level_) {
      if (level_ == SenseLevel::Low) {
        const uint32_t width = now - levelAt_;
        if (width >= 80 && width <= 300) {
          const uint32_t period = levelAt_ - pulseAt_;
          pulses_ = pulse_ && period >= 1000 && period <= 1560 ? (pulses_ < 3 ? pulses_ + 1 : 3) : 1;
          pulse_ = true; pulseAt_ = levelAt_; validAt_ = now;
          if (pulses_ >= 3) { observed_ = true; state_ = ChargeState::Charging; }
        } else if (state_ != ChargeState::Full) {
          pulse_ = observed_ = false; pulses_ = 0; state_ = ChargeState::Unknown;
        }
      }
      level_ = incoming; levelAt_ = now;
    }
    if (level_ == SenseLevel::Low && observed_ &&
        uint32_t(levelAt_ - validAt_) <= 1800 && uint32_t(now - levelAt_) >= 5000)
      state_ = ChargeState::Full;
    if (state_ != ChargeState::Full && level_ == SenseLevel::High &&
        observed_ && uint32_t(now - validAt_) > 4000) {
      pulse_ = observed_ = false; pulses_ = 0; state_ = ChargeState::Unknown;
    }
    return state_;
  }
};

inline bool chargeLed(ChargeState state, uint32_t elapsed, bool ready) {
  const uint32_t phase = elapsed % 5000;
  switch (state) {
    case ChargeState::Charging: return phase < 100;
    case ChargeState::Full: return phase < 100 || (phase >= 200 && phase < 300);
    case ChargeState::Unknown: return false;
    case ChargeState::NoUsb: return ready;
  }
  return false;
}

inline bool photoSuccessLed(uint32_t elapsed) {
  return elapsed < 100 || (elapsed >= 250 && elapsed < 350);
}

inline bool statusLed(ChargeState state, uint32_t elapsed, bool ready,
                      bool busy, bool success, uint32_t successElapsed) {
  if (success) return photoSuccessLed(successElapsed);
  if (busy) return false;
  return chargeLed(state, elapsed, ready);
}

inline const char *chargeStateName(ChargeState state) {
  switch (state) {
    case ChargeState::Charging: return "charging";
    case ChargeState::Full: return "full";
    case ChargeState::Unknown: return "unknown";
    case ChargeState::NoUsb: return "no_usb";
  }
  return "unknown";
}
