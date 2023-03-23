#!/usr/bin/env python

import argparse

import numpy as np
import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("input",
                        help="Path to the input text file"
                        )
    return parser.parse_args()


def remove_duplicate_minima(df):
    """Remove duplicate minima in file.

    The minimum of the likelihood is computed in each job
    and is thus included multiple times in the scan of the
    TChain object.
    """
    return df.drop_duplicates()


def replace_negative_entries(df, method="zero"):
    """Replace negative log-likelihood values.

    These values are in the file as for some scanned parameters
    the likelihood is smaller than in the fit minimum.
    Two methods are provided to remove these entries:
        `zero`: Set the log-likelihood values to zero
        `interpolate`: Use the neighbouring values to interpolate
                        the value for the negative entry
    """
    if method == "zero":
        df.loc[df["deltaNLL"] < 0, "deltaNLL"] = 0.
    elif method == "interpolate":
        # Get index of row
        indices = np.flatnonzero(df["deltaNLL"] < 0)
        for ind in indices:
            df.iloc[ind, df.columns.get_indexer(["deltaNLL"])] = (
                    df.iloc[ind-1, df.columns.get_indexer(["deltaNLL"])]
                    + df.iloc[ind+1, df.columns.get_indexer(["deltaNLL"])]) / 2.
        # TODO: Check if this is not a value at the boundary
    else:
        raise RuntimeError("Given method %s not known." % method)
    return df


def main(args):
    # Read in data from specified input file
    infilename = args.input
    df = pd.read_table(infilename, sep=" ",
                       names=["r_ggH", "r_bbH", "deltaNLL"],
                       index_col=False)
    print(df)
    # Remove duplicate entries in input file
    df = remove_duplicate_minima(df)
    # Replace negative entries
    df = replace_negative_entries(df, method="interpolate")
    # Write cleaned dataframe back to file
    outname = infilename.replace(".out", "_cleaned.txt")
    df.to_csv(outname, sep=" ",
              float_format="%.6f",
              header=False, index=False)
    return


if __name__ == "__main__":
    args = parse_args()
    main(args)
