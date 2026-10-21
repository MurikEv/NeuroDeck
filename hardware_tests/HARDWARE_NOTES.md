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

Not used yet: SDO/MISO, CTP_SCL, CTP_RST, CTP_SDA, CTP_INT, and SD_CS.

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
- Touch is a separate next phase. The CTP controller, voltage, I2C bus/address,
  reset/interrupt GPIO mapping, and coordinate orientation must be identified
  before connecting or implementing it.

## Current status

- Display: the color test in `display_test_working.py` is working. Red, green,
  blue, and white fill correctly with the RGB565 inversion fix.
- Boot display: `NEURODECK`, `BOOTING...`, and `UI READY` are confirmed working
  on the target display.
- Full PyQt mirror: implemented as a transitional mode; hardware orientation
  and refresh behavior still need validation on the Radxa.
- Camera: `/dev/video0` is working. `fswebcam` is not recommended; use
  GStreamer or OpenCV for camera capture.
