#!/usr/bin/env python
#
# Chris Markiewicz 2020
#
# Inspired by http://finance.jasonstrimpel.com/bulk-stock-download/
#
# Stripped down to bare-bones, but with additional features:
#
# 1) Dates are parsed and saved as dates, not strings
# 2) Values rounded to nearest cent
# 3) May output to ODS, XLSX or print to screen
import argparse
import logging
import io
from functools import lru_cache, partial
from pathlib import Path
from datetime import datetime, timedelta
from dateutil.parser import parse as parsedate
import requests
import pandas as pd


YAHOO_API = "https://query1.finance.yahoo.com/v7/finance/download/{symbol}"
SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    }
)


def get_historical_data(symbol, start_date, end_date):
    params = {
        "period1": int(start_date.timestamp()),
        "period2": int(end_date.timestamp()),
        "interval": "1d",
        "events": "history",
        "includeAdjustedClose": "true",
    }
    logging.getLogger("tickers").info(f"Retrieving {symbol}")
    res = SESSION.get(YAHOO_API.format(symbol=symbol), params=params)
    if res.ok:
        return pd.read_csv(io.BytesIO(res.content), index_col="Date", parse_dates=True)
    else:
        logging.getLogger("tickers").debug(f"Request: {res.request}")
        logging.getLogger("tickers").debug(f"Response: {res}")
    raise ValueError(f"Could not retrieve symbol {symbol}")


@lru_cache()  # Cache columns to permit duplicates without a second API call
def get_observations(symbol, field, start_date, end_date):
    orig = get_historical_data(symbol, start_date, end_date)[field]
    return pd.DataFrame({symbol: orig}, index=orig.index)


def get_tickers(symbols, field, start_date, end_date):
    return pd.concat(
        (get_observations(symbol, field, start_date, end_date) for symbol in symbols),
        axis=1,
    )


def main():
    fields = "Open,High,Low,Close,Adj Close,Volume".split(",")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s", "--symbols", required=True, help="Comma-delimited list or file"
    )
    parser.add_argument(
        "-f",
        "--field",
        default="Close",
        metavar="FIELD",
        choices=fields,
        help=f"One of {fields}",
    )
    parser.add_argument("-o", "--output", metavar="PATH")
    parser.add_argument("-n", "--fillna", choices=("forward", "none"))
    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument("start_date", nargs="?", help="First date (default 1 week ago)")
    parser.add_argument("end_date", nargs="?", help="Final date (default today)")
    opts = parser.parse_args()

    logging.basicConfig(level=("WARNING", "INFO", "DEBUG")[opts.verbose])

    end = parsedate(opts.end_date) if opts.end_date else datetime.today()
    start = parsedate(opts.start_date) if opts.start_date else end - timedelta(weeks=1)

    if end < start:
        raise ValueError(f"Start date ({start}) cannot come after end date ({end})")

    sym_path = Path(opts.symbols)
    if sym_path.exists():
        symbols = [sym for sym in sym_path.read_text().splitlines() if sym]
    else:
        symbols = opts.symbols.split(",")

    filterna = pd.DataFrame.dropna
    if opts.fillna:
        kwargs = {}
        if opts.fillna == "forward":
            kwargs["method"] = "ffill"
        elif opts.fillna == "none":
            kwargs["value"] = 0
        filterna = partial(pd.DataFrame.fillna, **kwargs)

    df = get_tickers(symbols, opts.field, start, end)
    df = filterna(df).round(4).sort_index(ascending=False)

    if opts.output:
        df.to_excel(opts.output)
    else:
        print(df)


if __name__ == "__main__":
    main()
