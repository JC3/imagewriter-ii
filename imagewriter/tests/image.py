import argparse
import logging
import numpy as np

from PIL import Image

from imagewriter import ImageWriterII, Quality


def main ():

    args = argparse.ArgumentParser()
    args.add_argument("path", help="path to printer serial port")
    args.add_argument("imagefile", help="path to image file to print")
    args.add_argument("--hdpi", type=int, default=72, help="horizontal resolution (dpi)")
    args.add_argument("--vdpi", type=int, default=72, help="vertical resolution (dpi)")
    args.add_argument("-b", "--baud", type=int, default=9600, help="serial baud rate")
    args.add_argument("-v", "--verbose", action="store_true", help="enable debug logging")
    opts = args.parse_args()

    logging.basicConfig(level=logging.DEBUG if opts.verbose else logging.INFO)

    image_pil = Image.open(opts.imagefile)
    image = np.asarray(image_pil)
    width_inch = image.shape[1] / opts.hdpi

    with ImageWriterII(opts.path, baud=opts.baud) as printer:
        page_width = printer.queryInfo().carriage_width - 2.5
        printer.reset()
        printer.setQuality(Quality.HIGH)
        printer.printImage(image, opts.hdpi, opts.vdpi, max(0.0, (page_width - width_inch) / 2.0))


if __name__ == "__main__":

    main()
