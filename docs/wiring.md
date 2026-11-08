# Wiring

BCM GPIO numbering, as used by `gpiozero`/`lgpio` and `drivers.yaml`. IN3/IN4 moved from 20/21 to 26/16 on 2026-11-08.

| Signal | GPIO | L298N |
| --- | --- | --- |
| ENA (left PWM) | 12 | ENA |
| IN1 (left dir A) | 5 | IN1 |
| IN2 (left dir B) | 6 | IN2 |
| ENB (right PWM) | 13 | ENB |
| IN3 (right dir A) | 26 | IN3 |
| IN4 (right dir B) | 16 | IN4 |

## Power

- Pi: 5 V 3 A power bank.
- Motors: separate 2×18650 pack → kill switch → L298N 12V input.
- **Common ground:** L298N GND to Pi GND, pin 34.
- L298N 5 V jumper **on**; the +5 V terminal is **not connected**.
- **ENA/ENB jumpers removed** — otherwise the channels are hard-enabled and PWM does
  nothing.
- MPU6050 on 3.3 V (pin 1), I2C bus 1, address `0x68`.

## Safety

- The motor battery switch is the kill switch. Software cannot override a stuck
  L298N channel; only removing power can.
- Keep the L298N heatsink clear; stalls at 0.35 dead zone still heat the driver.
- Before any live motor test: wheels off the ground, robot restrained, someone
  watching.
