#include <assert.h>
#include "../firmware/Otoskop/charge_status.h"

static void sample(ChargeMonitor &m, uint32_t from, uint32_t to, unsigned usb, unsigned chg) {
  for (uint32_t elapsed = 0; elapsed <= uint32_t(to-from); elapsed += 10)
    m.update(from + elapsed, usb, chg);
}

int main() {
  ChargeMonitor m;
  assert(m.update(0, 0, 0) == ChargeState::Unknown);
  sample(m, 10, 30, 0, 0);
  assert(m.state() == ChargeState::NoUsb);
  sample(m, 40, 60000, 2500, 1000); // LED off / already full / missing battery
  assert(m.state() == ChargeState::Unknown);
  sample(m, 60010, 60040, 0, 0);
  sample(m, 60050, 120050, 2500, 100); // permanently active without charging history
  assert(m.state() == ChargeState::Unknown);

  // Realistic 160 ms / 1280 ms pulse stream with one ambiguous edge sample.
  ChargeMonitor charging;
  for (uint32_t now = 0; now < 7000; now += 10) {
    unsigned phase = now % 1280;
    charging.update(now, 2500, phase == 160 ? 500 : phase < 160 ? 100 : 1000);
  }
  assert(charging.state() == ChargeState::Charging);
  sample(charging, 7000, 13000, 2500, 100);
  assert(charging.state() == ChargeState::Full);
  sample(charging, 13010, 80000, 2500, 1000); // full retained when LED turns off
  assert(charging.state() == ChargeState::Full);
  sample(charging, 80010, 80040, 0, 0);
  assert(charging.state() == ChargeState::NoUsb);
  sample(charging, 80050, 90000, 2500, 1000);
  assert(charging.state() == ChargeState::Unknown); // no stale full after reconnect

  // Disappearance of charging pulses alone must never mean full.
  ChargeMonitor stopped;
  for (uint32_t now = 0; now < 7000; now += 10)
    stopped.update(now, 2500, now % 1280 < 160 ? 100 : 1000);
  sample(stopped, 7000, 15000, 2500, 1000);
  assert(stopped.state() == ChargeState::Unknown);

  // Unsupported blink timings and transient glitches do not qualify as charge.
  ChargeMonitor bad;
  for (uint32_t now = 0; now < 12000; now += 10)
    bad.update(now, 2500, now % 500 < 20 ? 100 : 1000);
  assert(bad.state() == ChargeState::Unknown);
  sample(bad, 12000, 12120, 2500, 500);
  assert(bad.state() == ChargeState::Unknown);
  sample(bad, 12130, 12250, 1600, 1000);
  assert(bad.state() == ChargeState::Unknown);
  sample(bad, 12260, 12380, 3100, 1000);
  assert(bad.state() == ChargeState::Unknown);

  // Scheduling gaps invalidate decoding; camera operations must be sampled
  // independently, rather than accidentally counting a missed pulse as full.
  ChargeMonitor gap;
  for (uint32_t now = 0; now < 7000; now += 10)
    gap.update(now, 2500, now % 1280 < 160 ? 100 : 1000);
  gap.update(14000, 2500, 100);
  sample(gap, 14010, 20000, 2500, 100);
  assert(gap.state() == ChargeState::Unknown);

  ChargeMonitor wrap;
  const uint32_t start = UINT32_MAX - 6000;
  for (uint32_t elapsed = 0; elapsed < 7000; elapsed += 10)
    wrap.update(start + elapsed, 2500, elapsed % 1280 < 160 ? 100 : 1000);
  sample(wrap, start + 7000, start + 13000, 2500, 100);
  assert(wrap.state() == ChargeState::Full);
  sample(wrap, start + 13010, start + 13990, 2500, 1000);
  for (uint32_t elapsed = 14000; elapsed < 22000; elapsed += 10)
    wrap.update(start + elapsed, 2500, (elapsed-14000)%1280 < 160 ? 100 : 1000);
  assert(wrap.state() == ChargeState::Charging); // charger restarted after full


  // No capacitor: five-sample medians reject two outliers. 10ms glitches in
  // entire bursts must not detach USB or distort the charger pulse stream.
  ChargeMonitor noisy;
  for (uint32_t now = 0; now < 14000; now += 10) {
    const unsigned phase = now % 1280;
    const unsigned chg = now < 7000 ? (phase < 160 ? 220 : 1000) : 220;
    const unsigned usbValues[5] = {0, 2400, 2500, 2600, 4095};
    const unsigned chgValues[5] = {0, chg-50, chg, chg+50, 4095};
    unsigned usb = medianMillivolts5(usbValues);
    unsigned charge = medianMillivolts5(chgValues);
    if (now % 190 == 0) usb = 0;
    if (now % 230 == 0) charge = chg < 400 ? 1000 : 220;
    noisy.update(now, usb, charge);
    if (now == 6900) assert(noisy.state() == ChargeState::Charging);
  }
  assert(noisy.state() == ChargeState::Full);
  // Loaded nCHG highs need not approach half of VBUS. Verify detection with
  // low/high margins from the divider calculation and conservative ADC error.
  ChargeMonitor loaded;
  for (uint32_t now = 0; now < 7000; now += 10)
    loaded.update(now, 2350, now % 1280 < 160 ? 355 : 725);
  assert(loaded.state() == ChargeState::Charging);
  // Repeating short isolated spikes without real charge pulses cannot
  // manufacture a charging history or completion.
  ChargeMonitor spikes;
  for (uint32_t now = 0; now < 20000; now += 10)
    spikes.update(now, 2500, now % 180 == 0 ? 200 : 1000);
  assert(spikes.state() == ChargeState::Unknown);
  StableSense stable;
  assert(stable.update(0, SenseLevel::High) == SenseLevel::Unknown);
  assert(stable.update(20, SenseLevel::High) == SenseLevel::High);
  stable.update(30, SenseLevel::Low);
  assert(stable.update(40, SenseLevel::High) == SenseLevel::High);
  stable.update(50, SenseLevel::Unknown);
  assert(stable.update(149, SenseLevel::Unknown) == SenseLevel::High);
  assert(stable.update(150, SenseLevel::Unknown) == SenseLevel::Unknown);

  for (unsigned t = 0; t < 15000; ++t) {
    assert(chargeLed(ChargeState::Charging,t,false) == (t%5000 < 100));
    assert(chargeLed(ChargeState::Full,t,false) == (t%5000 < 100 || (t%5000>=200 && t%5000<300)));
    assert(!chargeLed(ChargeState::Unknown,t,true));
    assert(chargeLed(ChargeState::NoUsb,t,true));
    assert(!chargeLed(ChargeState::NoUsb,t,false));
  }
  assert(photoSuccessLed(0)); assert(!photoSuccessLed(100));
  assert(photoSuccessLed(250)); assert(!photoSuccessLed(350));
  // Charging/full indications cannot light during a photo; the finite save
  // acknowledgement overrides the periodic pattern and then returns to it.
  assert(!statusLed(ChargeState::Full, 0, true, true, false, 0));
  assert(statusLed(ChargeState::Charging, 2000, true, true, true, 0));
  assert(!statusLed(ChargeState::Full, 0, true, true, true, 150));
  assert(statusLed(ChargeState::Charging, 2000, true, true, true, 250));
  assert(statusLed(ChargeState::Full, 250, false, false, false, 500));
}
