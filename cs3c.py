#!/usr/bin/env python
"""
S3 bucket information CLI. Not a catchy name, but it works.

Coveo S3 Challenge
"""

import boto3
import click
import json
import re


units = {
    "b": (1, "B"),
    "k": (1024, "Kb"),
    "m": (1048576, "Mb"),
    "g": (1073741824, "Gb"),
    "t": (1099511627776, "Tb")
}

types = {
    "st": "STANDARD",
    "ia": "STANDARD_IA",
    "gl": "GLACIER",
    "rr": "REDUCED_REDUNDANCY"
}

CONTEXT_SETTINGS = dict(token_normalize_func=lambda x: x.lower())


@click.group()
def cli():
    pass


def new_session(access_key, secret_key):
    session = boto3.session.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )
    s3 = session.resource("s3")
    return s3


def bucket_as_print(bucket, unit_size):
    # parse bucket data and make pretty(-ish) for printing
    unit_size = units.get(unit_size.lower()) or units["b"]
    click.secho(bucket["name"], bold=True)
    click.echo("Created {0}".format(bucket["creation_date"].strftime("%c")))
    click.echo("Total: {0} objects".format(bucket["totals"]["count"]))
    click.echo("Total: {0:.2f} {1} total size".format(
        bucket["totals"]["size"] / unit_size[0], unit_size[1]
    ))
    if bucket["totals"]["last_modified"]:
        click.echo("Total: Last modified {0}".format(
            bucket["totals"]["last_modified"].strftime("%c")
        ))
    for x in bucket["storage_types"]:
        t = bucket["storage_types"][x]
        if not t["count"]:
            continue
        click.echo("{0}: {1} objects".format(x, t["count"]))
        click.echo("{0}: {1:.2f} {2} total size".format(
            x, t["size"] / unit_size[0], unit_size[1]
        ))
        if t["last_modified"]:
            click.echo("{0}: Last modified {1}".format(
                x, t["last_modified"].strftime("%c")
            ))


def bucket_as_json(bucket, unit_size):
    # make bucket data serializable
    unit_size = units.get(unit_size.lower()) or units["b"]
    bucket["creation_date"] = bucket["creation_date"].isoformat()
    bucket["totals"]["size"] = bucket["totals"]["size"] / unit_size[0]
    bucket["totals"]["units"] = unit_size[1]
    bucket["totals"]["last_modified"] = \
        bucket["totals"]["last_modified"].isoformat()\
        if bucket["totals"]["last_modified"] else None
    for x in bucket["storage_types"]:
        t = bucket["storage_types"][x]
        t["size"] = t["size"] / unit_size[0]
        t["units"] = unit_size[1]
        t["last_modified"] = t["last_modified"].isoformat()\
            if t["last_modified"] else None
    return bucket


def iterbuckets(
        s3, storage_type, re_filter=None, loc_filter=None,
        prefix_filter=None):
    for x in s3.buckets.all():
        # apply bucket name filter, if given
        if re_filter:
            try:
                re_filter = re.compile(re_filter)
            except re.error:
                raise click.ClickException("Invalid regex")
            if not re.search(re_filter, x.name):
                continue

        # apply region filter, if given
        location = s3.meta.client.get_bucket_location(Bucket=x.name)\
            .get("LocationConstraint")
        if loc_filter and loc_filter != location:
            continue

        # data is gathered by storage type (standard, ia, etc)
        #   then summed into total information at the end of the process
        data = {}
        for y in iterobjects(s3, x.name, prefix_filter):
            if y["StorageClass"] not in data:
                data[y["StorageClass"]] = {
                    "name": y["StorageClass"], "count": 0, "size": 0,
                    "last_modified": None
                }
            sto = data[y["StorageClass"]]
            sto["count"] += 1
            sto["size"] += y["Size"]
            sto["last_modified"] = max(
                y["LastModified"], sto["last_modified"]
            ) if sto["last_modified"] else y["LastModified"]

        # return gathered data and sums
        bucket_data = {
            "name": x.name,
            "creation_date": x.creation_date,
            "location": location,
            "totals": {
                "count": sum(data[y]["count"] for y in data),
                "size": sum(data[y]["size"] for y in data),
                "last_modified": max(
                    (data[y]["last_modified"] for y in data
                     if data[y]["last_modified"]),
                    default=None
                )
            },
            "storage_types": []
        }
        if storage_type:
            bucket_data["storage_types"] = data

        yield bucket_data


def iterobjects(s3, name, prefix_filter):
    # paginate through lots of objects, applying prefix filter
    #   server-side if necessary
    paginator = s3.meta.client.get_paginator('list_objects')
    operation_parameters = {'Bucket': name}
    if prefix_filter:
        operation_parameters.update({'Prefix': prefix_filter})
    page_iterator = paginator.paginate(**operation_parameters)
    for page in page_iterator:
        if not page.get("Contents"):
            continue
        for y in page["Contents"]:
            yield y


@cli.command(name="list", context_settings=CONTEXT_SETTINGS)
@click.option(
    'unit_size', '-s', '--size', default="B", type=click.Choice(units.keys()),
    help='Display results in [B]ytes, [K]b, [M]b, [G]b or [T]b'
)
@click.option(
    'is_json', '-j', '--json', default=False, is_flag=True,
    help='Output as JSON'
)
@click.option(
    'storage_type', '-t', '--type', is_flag=True,
    help='Group by storage type (standard, infrequent access, etc)'
)
@click.option(
    'prefix_filter', '-p', '--prefix',
    help='Filter count/size data based on path prefix'
)
@click.option(
    're_filter', '-f', '--filter',
    help='Filter bucket names (regex compatible)'
)
@click.option(
    'loc_filter', '-l', '--location',
    help='Filter buckets by region (e.g. "us-west-2")'
)
@click.option('--access-key', envvar='AWS_ACCESS_KEY', help='AWS access key')
@click.option('--secret-key', envvar='AWS_SECRET_KEY', help='AWS secret key')
def list_buckets(
        unit_size, is_json, storage_type, prefix_filter, re_filter,
        loc_filter, access_key, secret_key):
    out = []
    s3 = new_session(access_key, secret_key)
    for x in iterbuckets(
            s3, storage_type, re_filter, loc_filter, prefix_filter
            ):
        if is_json:
            out.append(bucket_as_json(x, unit_size))
        else:
            bucket_as_print(x, unit_size)
    if is_json:
        click.echo(json.dumps(out))


if __name__ == "__main__":
    cli()
