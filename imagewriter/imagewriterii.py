import logging
from enum import Enum
from binascii import hexlify
import dataclasses
import re
import serial
import numpy as np

from typing import Optional, Union

from .errors import NoPrinterDetectedError, UnsupportedPrinterError


_PRINTER_CHARSET = "latin1" # latin1 isn't quite right but probably good enough for now...


@dataclasses.dataclass
class PrinterInfo:
    carriage_width: float
    is_color: bool
    has_sheet_feeder: bool


class Font (Enum):
    EXTENDED = 'n'
    PICA = 'N'
    ELITE = 'E'
    SEMICONDENSED = 'e'
    CONDENSED = 'q'
    ULTRACONDENSED = 'Q'
    PROPORTIONAL_PICA = 'p'
    PROPORTIONAL_ELITE = 'P'


class Quality (Enum):
    DRAFT = 'a1'
    CORRESPONDENCE = 'a0'
    NLQ = 'a2'
    LOW = 'a1'     # Draft
    MEDIUM = 'a0'  # Correspondence
    HIGH = 'a2'    # NLQ


class LineSpacing (Enum):
    LPI6 = 'A'
    LPI8 = 'B'


class ImageWriterII:

    def __init__ (self, path: str, *,
                  logger: Optional[logging.Logger] = None,
                  validate: bool = True,
                  baud: int = 9600):
        self._logger = logger or logging.getLogger("imagewriter-ii")
        self._path = path
        if path == "-":
            self._port = None
            self._logger.info("Debug mode; not opening a printer.")
        else:
            self._port = serial.Serial(
                port=path,
                baudrate=baud,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                dsrdtr=True
            )
            self._logger.info(f"Opened printer on {path} at {baud} baud.")
            if validate:
                info = self.queryInfo()
                if info.is_color:
                    raise UnsupportedPrinterError("Color ribbons are not yet supported by this library.")

    @property
    def path (self) -> str:
        return self._path

    def __enter__ (self) -> "ImageWriterII":
        return self

    def __exit__ (self, extype, exval, exstack) -> None:
        self.close()

    # ========== Basic functions ==========

    def _write (self, data: Union[str,bytes,bytearray]) -> None:
        if self._port is not None:
            if isinstance(data, str):
                data = data.encode(_PRINTER_CHARSET)
            self._port.write(data)

    def _readline (self, timeout: float) -> str:
        if self._port is not None:
            self._port.timeout = timeout
            data = self._port.read_until(b"\x0d")
            self._logger.debug("read:    " + str(hexlify(data, " ")))
            return data.decode(_PRINTER_CHARSET)[:-1]
        else:
            return ""

    def write (self, data: str) -> None:
        self._logger.debug("raw:     " + str(hexlify(data.encode(_PRINTER_CHARSET), " ")))
        self._write(data)

    def print (self, text: str = "") -> None:
        self._logger.debug("text:    " + text)
        self._write(text + "\r\n")

    def command (self, cmd: str) -> None:
        self._logger.debug("command: " + str(hexlify(cmd.encode(_PRINTER_CHARSET), " ")))
        self._write("\x1b" + cmd)

    def close (self) -> None:
        if self._port != None:
            self._port.close()
            self._port = None
            self._logger.info(f"Closed printer on {self._path}")

    # ========== Command convenience functions ===============

    @staticmethod
    def _pad (prefix: str, n: int, length: int) -> str:
        return prefix + str(n).zfill(length)

    @staticmethod
    def _padcheck (prefix: str, n: int, length: int, lo: int, hi: int, what: str) -> str:
        if n < lo or n > hi:
            raise ValueError(what + " must be from " + str(lo) + " to " + str(hi) + ".")
        else:
            return ImageWriterII._pad(prefix, n, length)

    def reset (self) -> None:
        self.command("c")

    def softReset (self, quality: Optional[Quality] = None) -> None:
        if quality is not None:
            self.setQuality(quality);
        self.setFont(Font.ELITE);
        self.setDoubleWidth(False);
        self.setSpacing(0);
        self.setBold(False);
        self.setUnderline(False);
        self.setSuperscript(False); # implies setSubscript(False)
        self.setHalfHeight(False);
        self.setZeroSlash(False);
        self.setLeftMargin(0);
        self.setPageLengthIn(11);
        self.setUnidirectional(False);
        self.setLineSpacing(LineSpacing.LPI6);
        self.setReverseLineFeeding(False);
        self.setPerforationSkip(True);
        self.setPaperOutSensor(True);

    def setQuality (self, quality: Quality) -> None:
        if not isinstance(quality, Quality):
            raise TypeError("quality must be an instance of Quality Enum");
        self.command(quality.value)

    def setFont (self, font: Font) -> None:
        if not isinstance(font, Font):
            raise TypeError("font must be an instance of Font Enum")
        self.command(font.value)

    def setDoubleWidth (self, enable: bool) -> None:
        self.write("\x0e" if enable else "\x0f")

    def setSpacing (self, spacing: int) -> None:
        self.command(self._padcheck("s", spacing, 1, 0, 9, "Character spacing"))

    def insertSpacing (self, spacing: int) -> None:
        self.command(self._padcheck("", spacing, 1, 1, 6, "Space insertion count"))

    def setBold (self, enable: bool) -> None:
        self.command("!" if enable else '"')

    def setUnderline (self, enable: bool) -> None:
        self.command("X" if enable else "Y")

    def setHalfHeight (self, enable: bool) -> None:
        self.command("w" if enable else "W")

    def setSuperscript (self, enable: bool) -> None:
        self.command("x" if enable else "z")

    def setSubscript (self, enable: bool) -> None:
        self.command("y" if enable else "z")

    def setZeroSlash (self, enable: bool) -> None:
        self.command("\x44\x00\x01" if enable else "\x5a\x00\x01")

    def setLeftMargin (self, cols: int) -> None:
        self.command(self._padcheck("L", cols, 3, 0, 999, "Left margin"))

    def setPageLength (self, hpt: int) -> None:
        self.command(self._padcheck("H", hpt, 4, 1, 9999, "Page length"))

    def setPageLengthIn (self, inch: float) -> None:
        self.setPageLength(round(inch * 144.0))

    def setUnidirectional (self, enable: bool) -> None:
        self.command(">" if enable else "<")

    def movePrintHead (self, dots: int) -> None:
        self.command(self._padcheck("F", dots, 4, 0, 9999, "Print head position"))

    def setLineSpacing (self, spacing: Union[LineSpacing,int]) -> None:
        if isinstance(spacing, int):
            self.command(self._padcheck("T", spacing, 2, 1, 99, "Line spacing"))
        elif isinstance(spacing, LineSpacing):
            self.command(spacing.value)
        else:
            raise TypeError("Line spacing must be a LineSpacing Enum or an int.")

    def setReverseLineFeeding (self, enable: bool) -> None:
        self.command("r" if enable else "f")

    def setPerforationSkip (self, enable: bool) -> None:
        self.command("\x44\x00\x04" if enable else "\x5a\x00\x04")

    def setPaperOutSensor (self, enable: bool) -> None:
        self.command("o" if enable else "O")

    def setTOF (self) -> None:
        self.command("v")

    def feedToTOF (self) -> None:
        self.write("\x0c")

    def feedLines (self, count: int) -> None:
        if count == 0:
            return
        elif count < 1 or count > 15:
            raise ValueError("Line count must be from 1 to 15.")
        countstr = [ "1", "2", "3", "4", "5", "6", "7", "8", "9", ":", ";", "<", "=", ">", "?" ]
        self.command("\x1f" + countstr[count-1])

    def queryId (self, timeout: float = 5.0) -> str:
        self.command("?")
        return self._readline(timeout)

    @staticmethod
    def parseId (idstr: str) -> Optional[PrinterInfo]:
        m = re.fullmatch(r"^IW([0-9]+)(C?)(F?)", idstr)
        return PrinterInfo(
            carriage_width=float(m.group(1)),
            is_color=(m.group(2) == "C"),
            has_sheet_feeder=(m.group(3) == "F")
        ) if m else None

    def queryInfo (self, timeout: float = 5.0) -> PrinterInfo:
        if self._port is None: # then fake it
            return PrinterInfo(carriage_width=10.0, is_color=False, has_sheet_feeder=False)
        info = ImageWriterII.parseId(self.queryId(timeout))
        if info is None:
            raise NoPrinterDetectedError(f"Device at {self._path} is not an ImageWriter II.")
        else:
            return info

    # ========== The whole point of these printers ==========

    @staticmethod
    def _padcommand (code: str, n: int, length: int) -> bytes:
        return b"\x1b" + ImageWriterII._pad(code, n, length).encode(_PRINTER_CHARSET)

    @staticmethod
    def _encodeRows (image: np.ndarray, y: int, ystep: int) -> bytearray:
        blankline = True
        line = bytearray(ImageWriterII._padcommand("G", image.shape[1], 4))
        for x in range(0, image.shape[1]):
            bdata = 0
            for yoff in range(8):
                yy = y + yoff * ystep
                black = (image[yy][x][0] < 128) if yy < image.shape[0] else False
                if black:
                    bdata = bdata | (1 << yoff)
            if bdata:
                blankline = False
            line.append(bdata)
        if blankline: # just discard all data if line is blank, improves performance
            line = bytearray()
        line.extend(b"\r\n")
        return line

    @staticmethod
    def _encodeImage72 (image: np.ndarray) -> bytearray:
        data = bytearray(b"\x1bT16")
        for y in range(0, image.shape[0], 8):
            data.extend(ImageWriterII._encodeRows(image, y, 1))
        return data

    @staticmethod
    def _encodeImage144 (image: np.ndarray) -> bytearray:
        data = bytearray()
        for y in range(0, image.shape[0], 16):
            data.extend(b"\x1bT01")
            data.extend(ImageWriterII._encodeRows(image, y, 2))
            data.extend(b"\x1bT15")
            data.extend(ImageWriterII._encodeRows(image, y + 1, 2))
        return data

    def printImage (self, image: np.ndarray, hdpi: int, vdpi: int, xinch: float) -> None:
        # note: on return the following printer settings have been modified:
        # - font
        # - line spacing
        # - double-width mode
        # - unidirectional print mode
        # - left margin

        HDPI_FONT = {
            72: Font.EXTENDED,
            80: Font.PICA,
            96: Font.ELITE,
            107: Font.SEMICONDENSED,
            120: Font.CONDENSED,
            136: Font.ULTRACONDENSED,
            144: Font.PROPORTIONAL_PICA,
            160: Font.PROPORTIONAL_ELITE
        }

        VDPI_ENCODE = {
            72: ImageWriterII._encodeImage72,
            144: ImageWriterII._encodeImage144
        }

        hdpi = round(hdpi) # we are documented as taking ints but let's be nice
        vdpi = round(vdpi) # and accept floats anyways.

        if image.ndim == 2:
            image = image.reshape((image.shape[0], image.shape[1], 1))
        elif image.ndim != 3:
            raise ValueError(f"Unsupported image array shape {image.shape}.")
        if image.shape[0] == 0 or image.shape[1] == 0 or image.shape[2] == 0:
            return
        if image.shape[1] > 9999:
            raise ValueError(f"Image too large.")

        if hdpi not in HDPI_FONT:
            raise ValueError(f"Unsupported horizontal resolution {hdpi}.")
        if vdpi not in VDPI_ENCODE:
            raise ValueError(f"Unsupported vertical resolution {vdpi}.")

        self.setUnidirectional(True) # for best alignment between rows
        self.setDoubleWidth(False)
        self.setFont(Font.ULTRACONDENSED) # 17 columns per inch
        self.setLeftMargin(max(0, min(999, round(17.0 * xinch))))
        self.setFont(HDPI_FONT[hdpi])

        self._write(VDPI_ENCODE[vdpi](image))
