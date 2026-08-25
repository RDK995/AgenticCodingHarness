import sys

from receipt.report import render


def main(argv):
    if len(argv) != 2:
        print("usage: python3 -m receipt <file>", file=sys.stderr)
        return 2
    with open(argv[1]) as handle:
        print(render(handle.read().splitlines()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
