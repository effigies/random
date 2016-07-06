#!/bin/bash
#
# Split PDF into sub-books
#
# Usage: subbook.sh PDF [SPLIT [...]]
#
# If splits are specified, books are split AFTER the specified pages
#
# If no splits are specified, an attempt is made to make ~40 page books,
# which are ~10 double-sided pages when printed, with all but the last
# book having the same number of pages, and that a multiple of 4.
# Short books (<57 pages) are not split.
#
# Books should be printed to flip on the short edge.
#
# 2016 Chris Markiewicz

set -e

FNAME=$(basename "$1" .pdf)
BASE=$(dirname "$1")/$FNAME
shift;

set -x

# Split pages
mkdir -p "$BASE"
pdfseparate "$BASE.pdf" "$BASE/page-%03d.pdf"

{ set +x; } 2> /dev/null

# Get bounds
START=1
FINAL=$(ls "$BASE"/page-???.pdf | sort -n | tail -n 1 | \
        sed -e 's/.*page-0*\(..*\).pdf/\1/')

# Don't split short documents (56 pages is within stapler limits)
# unless given explicit split
if [ $FINAL -le 56 -a $# -eq 0 ]; then
    set -x
    rm -r $BASE
    pdfbook --short-edge "$BASE.pdf" &> /dev/null
    exit 0
fi

# If no specification, split at roughly 40 pages
if [ $# -eq 0 ]; then
    # Number of subbooks (minus 1)
    let SUBS=($FINAL-1)/40
    # Interval should be a multiple of 4, aiming for similar sizes
    # across subbooks
    let "INTERVAL = FINAL / ($SUBS+1) / 4 * 4"
    for SUB in `seq 1 $SUBS`; do
        ENDS=(${ENDS[@]} `expr $SUB "*" $INTERVAL`)
    done
    ENDS=(${ENDS[@]} $FINAL)
else
    ENDS=($@ $FINAL)
fi

# Produce subbooks
SUBBOOK=1
for END in ${ENDS[*]}; do
    PADDED=$(printf "{%03d..%03d}" $START $END)
    set -x
    eval pdfunite "$BASE"/page-$PADDED.pdf "$BASE.$SUBBOOK.pdf"
    pdfbook --short-edge "$BASE.$SUBBOOK.pdf" &> /dev/null
    rm "$BASE.$SUBBOOK.pdf"
    { set +x; } 2> /dev/null
    let START=$END+1
    let SUBBOOK=SUBBOOK+1
done

set -x
rm -r "$BASE"
