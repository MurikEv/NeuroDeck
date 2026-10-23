# NeuroDeck hardware notes

## Board and display

- Board: Radxa Zero 3W
- Display: ST7796 SPI, 320x480
- SPI overlay: `spidev` on `spi3m1` over CS0
- SPI device: `/dev/spidev3.0` (bus 3, chip select 0)
- SPI settings used by the working test: mode 0, 24 MHz, RGB565
- Display service v1 boot/status text is hardware-verified.
- The current migration stage mirrors the existing 480x320 PyQt UI to the
  320x480 SPI panel while retaining HDMI as a recovery path.

## Display wiring

| Display signal | Radxa physical pin | Mapping |
| --- | ---: | --- |
| VCC | 2 | +5V |
| GND | 6 | GND |
| SCK | 23 | SPI clock |
| SDI / MOSI | 19 | SPI MOSI |
| LCD_CS | 24 | SPI CS0 |
| LCD_RST | 22 | `gpiochip3` line 17 |
| LCD_RS / DC | 32 | `gpiochip3` line 18 |
| LED | 4 | +5V |

Not used yet: SDO/MISO, CTP_INT, and SD_CS.

## GPIO mapping from `gpioinfo`

- PIN_22 -> `gpiochip3` line 17 (LCD_RST)
- PIN_32 -> `gpiochip3` line 18 (LCD_RS/DC)
- PIN_23 -> `gpiochip4` line 18 (SPI SCK)
- PIN_19 -> `gpiochip4` line 19 (SPI MOSI)
- PIN_21 -> `gpiochip4` line 21
- PIN_24 -> `gpiochip4` line 22 (SPI CS0)

Display service GPIO constants:

- `GPIO_CHIP = "gpiochip3"`
- `RST_LINE = 17`
- `DC_LINE = 18`
- `SPI_BUS = 3`
- `SPI_DEVICE = 0`

## Color inversion fix

This panel shows inverted colors. Every logical RGB565 color must be inverted
exactly once before transmission:

```python
color = color ^ 0xFFFF
```

Keep this workaround in both fill and drawing paths.

## Qt UI mirror

- The existing PyQt UI is already designed for 480x320 landscape.
- The mirror renders that canvas, rotates it in software, converts it to
  big-endian RGB565, and sends it through the display service.
- Default software rotation is 90 degrees. If the image is upside down, test
  270 degrees without changing code:

  ```bash
  sudo env NEURODECK_SPI_ROTATION=270 ./venv/bin/python main.py
  ```

- To keep only the verified boot/status screen while diagnosing mirror issues:

  ```bash
  sudo env NEURODECK_SPI_MIRROR=0 ./venv/bin/python main.py
  ```

- Capture is limited to four checks per second. Unchanged frames are skipped,
  and the SPI worker keeps only the newest pending frame so the Qt UI thread
  does not wait for a full-screen SPI transfer.
- HDMI remains enabled during this validation stage. Headless Qt/offscreen
  mode comes only after frame orientation and refresh behavior work reliably.
- Touch v1 uses the same `NEURODECK_SPI_ROTATION` value as the mirror so image
  rotation and pointer coordinates stay in sync.

## Capacitive touch v1

- Module matches the LCDWiki MSP3526/FT6336U family. Its chip identity has not
  been read yet; compatible coordinate registers and address are verified.
- OS: Debian 12 Bookworm, kernel `6.1.84-10-rk2410-nocsf`.
- Overlay: `rk3568-i2c5-m0.dtbo`, enabled using rsetup while retaining the
  existing camera and SPI overlays.
- Device: `/dev/i2c-5`, address `0x38` (confirmed after releasing CTP_RST).
- Pinmux: physical pin 29 = GPIO3_B3 / line 11 = I2C5_SCL_M0;
  physical pin 31 = GPIO3_B4 / line 12 = I2C5_SDA_M0.
- The display-side CTP_SDA/SCL measure about 4.8 V. Do not connect them directly
  to Radxa GPIO. A four-channel bidirectional level converter is installed.

| Converter terminal | Connection |
| --- | --- |
| HVcc | Shared display +5 V supply |
| LVcc | Radxa physical pin 1, +3.3 V |
| GND | Radxa physical pin 9; common ground with the display |
| H1 | Display CTP_SDA |
| L1 | Radxa physical pin 31, I2C5 SDA |
| H2 | Display CTP_SCL |
| L2 | Radxa physical pin 29, I2C5 SCL |
| H3 | Display CTP_RST |
| L3 | Radxa physical pin 11, gpiochip3 line 1 |
| H4 / L4 | Unused; CTP_INT is disconnected |

- CTP_RST measured 0.1 V when left floating, preventing the controller from
  responding. The service requests RST low, waits 50 ms, drives it high, waits
  500 ms, and retains the GPIO request throughout operation.
- Polling uses native Linux I2C_RDWR combined transfers every 20 ms in a worker;
  there is no new Python package dependency. The existing gpiod v1 API is kept.
- At 90-degree mirror rotation, UI coordinates are `(raw_y, 319 - raw_x)`.
  At 270 degrees, they are `(479 - raw_y, raw_x)`.
- Measured native coordinates, in displayed corner order: top-left `(314, 38)`,
  top-right `(287, 451)`, bottom-right `(50, 444)`, bottom-left `(46, 34)`.
- One finger is supported. A second finger, invalid sample, read error or page
  change cancels the current press. Moving outside a button and lifting does
  not open that application. Double taps are translated for existing Qt views.
- `services/touch_service.py` injects pointer events into the existing Qt UI;
  full UI touch operation still requires validation on the Radxa.
- To disable touch independently while testing:

  ```bash
  sudo env NEURODECK_TOUCH=0 ./venv/bin/python main.py
  ```

- Stop the standalone GPIO/I2C tests before launching NeuroDeck: only one
  process can own the reset GPIO. Keep the existing HDMI session for now.

## Current status

- Display: the color test in `display_test_working.py` is working. Red, green,
  blue, and white fill correctly with the RGB565 inversion fix.
- Boot display: `NEURODECK`, `BOOTING...`, and `UI READY` are confirmed working
  on the target display.
- Full PyQt mirror: confirmed working on the Radxa; HDMI remains enabled.
- Touch transport: address 0x38 and corner coordinates confirmed working.
- Touch-to-Qt input: implemented and tested offline; target UI validation pending.
- Camera: `/dev/video0` is working. `fswebcam` is not recommended; use
  GStreamer or OpenCV for camera capture.
