import argparse
import logging

from imagewriter import ImageWriterII


def main ():

    args = argparse.ArgumentParser()
    args.add_argument("path", help="path to printer serial port")
    args.add_argument("-v", "--verbose", action="store_true", help="enable debug logging")
    opts = args.parse_args()

    logging.basicConfig(level=logging.DEBUG if opts.verbose else logging.INFO)

    with ImageWriterII(opts.path) as printer:
        print(printer.queryId())
        print(printer.queryInfo())


if __name__ == "__main__":

    main()
    
