import argparse
import logging

from imagewriter import Font, Quality, LineSpacing, ImageWriterII


def _print_test (p: ImageWriterII) -> None:

    p.print();
    p.setFont(Font.ELITE);
    p.setQuality(Quality.HIGH);
    p.print('This is a test.');
    p.print('This is the second line of the test.');
    p.setFont(Font.PROPORTIONAL_ELITE);
    p.print('Now we\'re testing with proportional fonts.');
    p.print('Here is another line of text with the proportional font.');
    p.setDoubleWidth(True);
    p.print('Double width proportional... does it work?');
    p.setDoubleWidth(False);
    p.print('About to perform a software reset...');
    p.setDoubleWidth(True);
    p.print('Will also test if reset restores normal width!');
    p.reset();
    p.print('This is the font after the software reset.');
    p.print();
    p.print('That should have skipped a blank line.');

    p.print();
    for font in Font:
        p.setFont(font);
        p.print('---- ' + str(font) + ' ----');
        p.print('THE QUICK BROWN FOX JUMPS OVER A LAZY DOG )!@#$%^&*( ~_+{}|:"<>?');
        p.print('the quick brown fox jumps over a lazy dog 0123456789 `-=[]\\;\',./');

    p.print();

    p.setFont(Font.PROPORTIONAL_PICA);
    for x in range(0, 10):
        p.setSpacing(x);
        p.print('Character spacing is ' + str(x) + '.')
    for x in range(1, 7):
        p.write('|');
        p.insertSpacing(x);
    p.print('|');

    p.reset();
    p.write('Typefaces: ');
    p.setBold(True); p.write('bold ');
    p.setBold(False); p.setUnderline(True); p.write('underline');
    p.setUnderline(False); p.setSuperscript(True); p.write(' superscript');
    p.setSubscript(True); p.write(' subscript');
    p.setSubscript(False); p.setHalfHeight(True); p.write(' half-height');
    p.setHalfHeight(False);
    p.print();

    p.print('Default look of zeroes: 00000');
    p.setZeroSlash(True);
    p.print('Zero slash on:          00000');
    p.setZeroSlash(False);
    p.print('Zero slash off:         00000');

    p.setDoubleWidth(True);
    p.setHalfHeight(True);
    p.print('Testing if double-width, half-height works.');
    p.setDoubleWidth(False);
    p.setHalfHeight(False);

    p.print();
    p.setUnidirectional(True);
    p.print('This text should print unidirectionally:');
    for x in range(4, -1, -1):
        p.setLeftMargin(x);
        p.print('Left margin is ' + str(x))
    p.setUnidirectional(False);
    p.print();

    for x in [ LineSpacing.LPI6, LineSpacing.LPI8, 1, 50, 99 ]:
        p.setLineSpacing(x);
        for y in range(3):
            p.print('Line ' + str(y) + ', Line Spacing ' + str(x))

    p.setQuality(Quality.HIGH);
    p.setFont(Font.PROPORTIONAL_PICA);
    p.setDoubleWidth(True);
    p.setSpacing(5);
    p.setBold(True);
    p.setUnderline(True);
    p.setHalfHeight(True);
    p.setZeroSlash(True);
    p.setLeftMargin(10);
    p.setUnidirectional(True);
    p.setLineSpacing(LineSpacing.LPI8);

    p.print();
    p.print();
    p.print();
    p.print();
    p.setReverseLineFeeding(True);

    p.print('This is a test of the softReset function.');
    p.print('It is also going to test reverse feeding.');
    p.print('This should be the topmost line.');
    p.softReset(Quality.DRAFT);

    p.print();
    p.print();
    p.print();
    p.print();
    p.print('Everything should be reset and this should be the bottom line.');


def main ():

    args = argparse.ArgumentParser()
    args.add_argument("path", help="path to printer serial port")
    args.add_argument("-b", "--baud", type=int, default=9600, help="serial baud rate")
    args.add_argument("-v", "--verbose", action="store_true", help="enable debug logging")
    opts = args.parse_args()

    logging.basicConfig(level=logging.DEBUG if opts.verbose else logging.INFO)

    with ImageWriterII(opts.path, baud=opts.baud) as printer:
        printer.reset()
        _print_test(printer)


if __name__ == "__main__":

    main()
