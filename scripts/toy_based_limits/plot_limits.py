#!/usr/bin/env python
import argparse
import json

import numpy
import matplotlib.pyplot as plt

from plotting.utility import plot_limits


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input",
                        type=str,
                        help="Input json file")
    parser.add_argument("-p", "--poi",
                        type=str,
                        help="The POI considered in the fits."
    )
    parser.add_argument("-m", "--mass",
                        type=str,
                        help="Mass of the considered signal."
    )
    return parser.parse_args()


def main(args):
    with open(args.input, "r") as fi:
        limits = json.load(fi)

    plot_limits(limits["hybrid"],
                limits["asymptotic"],
                output_name="limits_{}_{}-update.png".format(args.poi, args.mass),
                proc=args.poi.split("_")[1][0:-1],
                mass=args.mass)
    return


if __name__ == "__main__":
    args = parse_args()
    main(args)
