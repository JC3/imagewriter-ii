import logging
from enum import Enum
from binascii import hexlify
import serial

from typing import Optional, Union


_PRINTER_CHARSET = "latin1" # latin1 isn't quite right but probably good enough for now...


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

    def __init__ (self, path: str, logger: Optional[logging.Logger] = None):
        self._logger = logger or logging.getLogger("imagewriter-ii")
        self._path = path
        if path == "-":
            self._port = None
            self._logger.info("Debug mode; not opening a printer.")
        else:
            self._port = serial.Serial(
                port=path,
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                dsrdtr=True
            )
            self._logger.info("Opened printer on " + path)

    @property
    def path (self) -> str:
        return self._path

    def __enter__ (self) -> "ImageWriterII":
        return self

    def __exit__ (self, extype, exval, exstack) -> None:
        self.close()

    # ========== Basic functions ==========

    def _write (self, data: str) -> None:
        if self._port is not None:
            self._port.write(data.encode(_PRINTER_CHARSET))

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
        if type(spacing) == int:
            self.command(self._padcheck("T", spacing, 2, 1, 99, "Line spacing"))
        elif type(spacing) == LineSpacing:
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
        self.write("\x0c") # TODO: not sure if this is correct, check printer docs

    def feedLines (self, count: int) -> None:
        if count == 0:
            return
        elif count < 1 or count > 15:
            raise ValueError("Line count must be from 1 to 15.")
        countstr = [ "1", "2", "3", "4", "5", "6", "7", "8", "9", ":", ";", "<", "=", ">", "?" ]
        self.command("\x1f" + countstr[count-1])
