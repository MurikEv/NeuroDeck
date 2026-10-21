import os
import sys
import time


WIDTH = 320
HEIGHT = 480

GPIO_CHIP = "gpiochip3"
RST_LINE = 17
DC_LINE = 18

SPI_BUS = 3
SPI_DEVICE = 0
SPI_PATH = f"/dev/spidev{SPI_BUS}.{SPI_DEVICE}"
SPI_SPEED_HZ = 24_000_000

WRITE_CHUNK_PIXELS = 1024
WRITE_CHUNK_BYTES = WRITE_CHUNK_PIXELS * 2
COLOR_INVERSION_TABLE = bytes.maketrans(
    bytes(range(256)),
    bytes(range(255, -1, -1)),
)

_BUILTIN_FONT = {
    " ": (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    ".": (0x00, 0x00, 0x00, 0x00, 0x00, 0x04, 0x04),
    "-": (0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00),
    ":": (0x00, 0x04, 0x04, 0x00, 0x04, 0x04, 0x00),
    "?": (0x0E, 0x11, 0x01, 0x02, 0x04, 0x00, 0x04),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F),
    "3": (0x1E, 0x01, 0x01, 0x0E, 0x01, 0x01, 0x1E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x10, 0x1E, 0x01, 0x01, 0x1E),
    "6": (0x0E, 0x10, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x01, 0x0E),
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0F, 0x10, 0x10, 0x10, 0x10, 0x10, 0x0F),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0F, 0x10, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x1F),
    "J": (0x01, 0x01, 0x01, 0x01, 0x11, 0x11, 0x0E),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x15, 0x0A),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
}


class _BitmapPixels:
    def __init__(self, rows):
        self._rows = rows

    def __getitem__(self, position):
        column, row = position
        return self._rows[row][column]


class _BitmapMask:
    def __init__(self, rows):
        self._rows = rows

    @property
    def size(self):
        width = len(self._rows[0]) if self._rows else 0
        return width, len(self._rows)

    def load(self):
        return _BitmapPixels(self._rows)

    def crop(self, box):
        left, top, right, bottom = box
        return _BitmapMask(
            [row[left:right] for row in self._rows[top:bottom]]
        )


class ST7796Display:
    """Small, direct SPI status display for the NeuroDeck boot process."""

    def __init__(self):
        self._chip = None
        self._rst = None
        self._dc = None
        self._spi = None

        try:
            self._open_hardware()
            self.init_display()
        except Exception:
            self.close()
            raise

    def _open_hardware(self):
        if not os.path.exists(SPI_PATH):
            raise FileNotFoundError(f"{SPI_PATH} not found")

        try:
            import spidev
        except ImportError as exc:
            raise RuntimeError("Python module 'spidev' is not installed") from exc

        try:
            import gpiod
        except ImportError as exc:
            raise RuntimeError("Python module 'gpiod' is not installed") from exc

        # Keep the libgpiod v1 API used by the proven hardware test.
        self._chip = gpiod.Chip(GPIO_CHIP)
        self._rst = self._chip.get_line(RST_LINE)
        self._dc = self._chip.get_line(DC_LINE)

        self._rst.request(
            consumer="st7796_rst",
            type=gpiod.LINE_REQ_DIR_OUT,
        )
        self._dc.request(
            consumer="st7796_dc",
            type=gpiod.LINE_REQ_DIR_OUT,
        )

        self._spi = spidev.SpiDev()
        self._spi.open(SPI_BUS, SPI_DEVICE)
        self._spi.max_speed_hz = SPI_SPEED_HZ
        self._spi.mode = 0

    def _require_open(self):
        if any(
            handle is None
            for handle in (self._chip, self._rst, self._dc, self._spi)
        ):
            raise RuntimeError("display is not initialized")

    def _write_command(self, command):
        self._dc.set_value(0)
        self._spi.writebytes([command])

    def _write_data(self, data):
        self._dc.set_value(1)
        self._spi.writebytes(list(data))

    def _reset(self):
        self._rst.set_value(1)
        time.sleep(0.05)
        self._rst.set_value(0)
        time.sleep(0.1)
        self._rst.set_value(1)
        time.sleep(0.15)

    def init_display(self):
        """Reset and initialize the controller with the proven ST7796 sequence."""
        self._require_open()
        self._reset()

        self._write_command(0x01)  # Software reset
        time.sleep(0.15)

        self._write_command(0x11)  # Sleep out
        time.sleep(0.15)

        self._write_command(0x20)  # Display inversion off
        time.sleep(0.05)

        self._write_command(0x3A)  # Pixel format
        self._write_data([0x55])  # 16-bit RGB565

        self._write_command(0x36)  # Memory access control
        self._write_data([0x48])

        self._write_command(0x29)  # Display on
        time.sleep(0.1)

    def _set_window(self, x0, y0, x1, y1):
        self._write_command(0x2A)  # Column address set
        self._write_data(
            [
                (x0 >> 8) & 0xFF,
                x0 & 0xFF,
                (x1 >> 8) & 0xFF,
                x1 & 0xFF,
            ]
        )

        self._write_command(0x2B)  # Row address set
        self._write_data(
            [
                (y0 >> 8) & 0xFF,
                y0 & 0xFF,
                (y1 >> 8) & 0xFF,
                y1 & 0xFF,
            ]
        )

        self._write_command(0x2C)  # Memory write

    @staticmethod
    def _validate_color(color):
        if not isinstance(color, int) or not 0 <= color <= 0xFFFF:
            raise ValueError("color must be an RGB565 value from 0x0000 to 0xFFFF")
        return color

    def _write_repeated_pixel(self, pixel_bytes, pixel_count):
        self._dc.set_value(1)
        full_chunk = pixel_bytes * WRITE_CHUNK_PIXELS

        while pixel_count >= WRITE_CHUNK_PIXELS:
            self._spi.writebytes(full_chunk)
            pixel_count -= WRITE_CHUNK_PIXELS

        if pixel_count:
            self._spi.writebytes(pixel_bytes * pixel_count)

    def _write_buffer(self, data):
        self._dc.set_value(1)
        write_buffer = getattr(self._spi, "writebytes2", None)
        if write_buffer is not None:
            write_buffer(data)
            return

        for offset in range(0, len(data), WRITE_CHUNK_BYTES):
            chunk = data[offset:offset + WRITE_CHUNK_BYTES]
            self._spi.writebytes(list(chunk))

    def fill_color(self, color):
        """Fill the full display with one logical RGB565 color."""
        self._require_open()
        color = self._validate_color(color)

        # Required workaround for this particular panel.
        color = color ^ 0xFFFF
        pixel_bytes = [(color >> 8) & 0xFF, color & 0xFF]

        self._set_window(0, 0, WIDTH - 1, HEIGHT - 1)
        self._write_repeated_pixel(pixel_bytes, WIDTH * HEIGHT)

    def blit_rgb565(self, data, width, height, x=0, y=0):
        """Write logical, big-endian RGB565 pixels to a display rectangle."""
        self._require_open()
        width = int(width)
        height = int(height)
        x = int(x)
        y = int(y)

        if width <= 0 or height <= 0:
            raise ValueError("width and height must be positive")
        if x < 0 or y < 0 or x + width > WIDTH or y + height > HEIGHT:
            raise ValueError("RGB565 rectangle is outside the display bounds")

        data = bytes(data)
        expected_size = width * height * 2
        if len(data) != expected_size:
            raise ValueError(
                f"RGB565 data must contain {expected_size} bytes, got {len(data)}"
            )

        # XORing every byte is equivalent to color = color ^ 0xFFFF for each
        # big-endian RGB565 word, while avoiding a slow per-pixel Python loop.
        panel_data = data.translate(COLOR_INVERSION_TABLE)
        self._set_window(x, y, x + width - 1, y + height - 1)
        self._write_buffer(panel_data)

    @staticmethod
    def _load_font(image_font):
        try:
            return image_font.truetype("DejaVuSans.ttf", 24)
        except OSError:
            return image_font.load_default()

    @staticmethod
    def _render_builtin_text(text):
        scale = 3
        glyph_width = 5
        glyph_height = 7
        glyph_advance = 6
        width = ((len(text) * glyph_advance) - 1) * scale
        rows = [[False] * width for _ in range(glyph_height * scale)]

        for character_index, character in enumerate(text.upper()):
            glyph = _BUILTIN_FONT.get(character, _BUILTIN_FONT["?"])
            glyph_x = character_index * glyph_advance * scale

            for row_index, row_bits in enumerate(glyph):
                for column_index in range(glyph_width):
                    bit = 1 << (glyph_width - column_index - 1)
                    if not row_bits & bit:
                        continue

                    pixel_x = glyph_x + (column_index * scale)
                    pixel_y = row_index * scale
                    for offset_y in range(scale):
                        for offset_x in range(scale):
                            rows[pixel_y + offset_y][pixel_x + offset_x] = True

        return _BitmapMask(rows)

    def draw_text(
        self,
        text,
        x=10,
        y=10,
        color=0xFFFF,
        background=None,
    ):
        """Draw basic text at x/y using logical RGB565 colors."""
        self._require_open()

        text = str(text)
        if not text:
            return

        x = int(x)
        y = int(y)
        color = self._validate_color(color)
        if background is not None:
            background = self._validate_color(background)

        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            mask = self._render_builtin_text(text)
        else:
            font = self._load_font(ImageFont)
            probe = Image.new("1", (1, 1), 0)
            probe_draw = ImageDraw.Draw(probe)

            if hasattr(probe_draw, "textbbox"):
                left, top, right, bottom = probe_draw.textbbox(
                    (0, 0),
                    text,
                    font=font,
                )
            else:
                width, height = probe_draw.textsize(text, font=font)
                left, top, right, bottom = 0, 0, width, height

            text_width = max(0, right - left)
            text_height = max(0, bottom - top)
            if text_width == 0 or text_height == 0:
                return

            mask = Image.new("1", (text_width, text_height), 0)
            ImageDraw.Draw(mask).text(
                (-left, -top),
                text,
                fill=1,
                font=font,
            )

        text_width, text_height = mask.size

        source_left = max(0, -x)
        source_top = max(0, -y)
        source_right = min(text_width, WIDTH - x)
        source_bottom = min(text_height, HEIGHT - y)
        if source_left >= source_right or source_top >= source_bottom:
            return

        mask = mask.crop(
            (source_left, source_top, source_right, source_bottom)
        )
        screen_x = x + source_left
        screen_y = y + source_top
        draw_width, draw_height = mask.size
        pixels = mask.load()

        # Apply the panel workaround once to every text pixel sent over SPI.
        color = color ^ 0xFFFF
        foreground_bytes = [(color >> 8) & 0xFF, color & 0xFF]

        if background is None:
            self._draw_transparent_mask(
                pixels,
                draw_width,
                draw_height,
                screen_x,
                screen_y,
                foreground_bytes,
            )
            return

        background = background ^ 0xFFFF
        background_bytes = [
            (background >> 8) & 0xFF,
            background & 0xFF,
        ]
        self._draw_opaque_mask(
            pixels,
            draw_width,
            draw_height,
            screen_x,
            screen_y,
            foreground_bytes,
            background_bytes,
        )

    def _draw_transparent_mask(
        self,
        pixels,
        width,
        height,
        screen_x,
        screen_y,
        foreground_bytes,
    ):
        for row in range(height):
            column = 0
            while column < width:
                while column < width and not pixels[column, row]:
                    column += 1
                run_start = column
                while column < width and pixels[column, row]:
                    column += 1

                if run_start < column:
                    self._set_window(
                        screen_x + run_start,
                        screen_y + row,
                        screen_x + column - 1,
                        screen_y + row,
                    )
                    self._write_repeated_pixel(
                        foreground_bytes,
                        column - run_start,
                    )

    def _draw_opaque_mask(
        self,
        pixels,
        width,
        height,
        screen_x,
        screen_y,
        foreground_bytes,
        background_bytes,
    ):
        self._set_window(
            screen_x,
            screen_y,
            screen_x + width - 1,
            screen_y + height - 1,
        )
        self._dc.set_value(1)

        chunk = []
        for row in range(height):
            for column in range(width):
                if pixels[column, row]:
                    chunk.extend(foreground_bytes)
                else:
                    chunk.extend(background_bytes)

                if len(chunk) == WRITE_CHUNK_PIXELS * 2:
                    self._spi.writebytes(chunk)
                    chunk = []

        if chunk:
            self._spi.writebytes(chunk)

    def close(self):
        """Release SPI and GPIO resources. Safe to call more than once."""
        resources = (
            ("SPI", "_spi", "close"),
            ("DC GPIO", "_dc", "release"),
            ("RST GPIO", "_rst", "release"),
            ("GPIO chip", "_chip", "close"),
        )

        for label, attribute, close_method in resources:
            resource = getattr(self, attribute)
            setattr(self, attribute, None)
            if resource is None:
                continue

            try:
                getattr(resource, close_method)()
            except Exception as exc:
                print(
                    f"ST7796 display cleanup warning ({label}): {exc}",
                    file=sys.stderr,
                )
