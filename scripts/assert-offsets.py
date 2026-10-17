#!/usr/bin/env python3
"""Verify an exact per-run Kafka offset increase and emit new-record ranges."""
import argparse
from pathlib import Path


def offsets(path, topic):
    result = {}
    for line in Path(path).read_text().splitlines():
        fields = line.split(':')
        if (len(fields) != 3 or fields[0] != topic
                or not fields[1].isdigit() or not fields[2].isdigit()):
            raise ValueError(f'Invalid offset row: {line!r}')
        partition, offset = map(int, fields[1:])
        if partition in result:
            raise ValueError(f'Duplicate partition: {partition}')
        result[partition] = offset
    if not result:
        raise ValueError('No partition offsets returned')
    return result


def new_ranges(before, after, expected):
    if expected < 1:
        raise ValueError('Expected record count must be positive')
    if before.keys() != after.keys():
        raise ValueError('Partition set changed during the scenario')
    if any(after[p] < before[p] for p in before):
        raise ValueError('Offsets moved backwards during the scenario')
    delta = sum(after[p] - before[p] for p in before)
    if delta != expected:
        raise ValueError(f'Produced {delta} new records, expected exactly {expected}')
    return [(p, before[p], after[p] - before[p]) for p in sorted(before)
            if after[p] > before[p]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--topic', required=True)
    parser.add_argument('--expected', type=int, required=True)
    parser.add_argument('before')
    parser.add_argument('after')
    args = parser.parse_args()
    try:
        ranges = new_ranges(offsets(args.before, args.topic),
                            offsets(args.after, args.topic), args.expected)
    except ValueError as error:
        parser.exit(1, f'ASSERT FAILED: {error}\n')
    for partition, start, count in ranges:
        print(partition, start, count)


if __name__ == '__main__':
    main()
