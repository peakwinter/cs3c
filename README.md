# cs3c

Grab basic information about S3 buckets and the objects within.


### Install

```
git clone $REPO_URL && cd cs3c
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt && pip install -e .

cs3c list
```


### Use

*Note*: AWS credentials can also be passed as env vars `AWS_ACCESS_KEY` and `AWS_SECRET_KEY`.

```
Usage: cs3c list [OPTIONS]

Options:
  -s, --size [g|m|t|k|b]  Display results in [B]ytes, [K]b, [M]b, [G]b or [T]b
  -j, --json              Output as JSON
  -t, --type              Group by storage type (standard, infrequent access,
                          etc)
  -p, --prefix TEXT       Filter count/size data based on path prefix
  -f, --filter TEXT       Filter bucket names (regex compatible)
  -l, --location TEXT     Filter buckets by region (e.g. "us-west-2")
  --access-key TEXT       AWS access key
  --secret-key TEXT       AWS secret key
  --help                  Show this message and exit.
```


### Test

Some basic test cases are included; run `python setup.py test`.


### Other notes

Uses `click` and `boto3`. Developed and tested with Python 3.x.
