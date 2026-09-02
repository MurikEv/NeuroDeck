# NeuroDeck hardware notes

## Board and display

- Board: Radxa Zero 3W
- Display: ST7796 SPI, 320x480
- SPI overlay: `spidev` on `spi3m1` over CS0
- SPI device: `/dev/spidev3.0` (bus 3, chip select 0)
- SPI settings used by the working test: mode 0, 24 MHz, RGB565
- Display service v1 is status-only. The main PyQt UI remains on HDMI.

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

## Current status

- Display: the color test in `display_test_working.py` is working. Red, green,
  blue, and white fill correctly with the RGB565 inversion fix.
- Camera: `/dev/video0` is working. `fswebcam` is not recommended; use
  GStreamer or OpenCV for camera capture.
