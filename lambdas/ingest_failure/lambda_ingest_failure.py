import os, json, boto3, requests

S3_BUCKET = os.environ["S3_BUCKET"]
SQS_URL   = os.environ["SQS_URL"]
JENKINS_URL = os.environ["JENKINS_URL"]

s3  = boto3.client("s3")
sqs = boto3.client("sqs")

def get_jenkins_creds():
    return os.environ["JENKINS_USER"], os.environ["JENKINS_TOKEN"]

def jget(path, auth):
    url = f"{JENKINS_URL.rstrip('/')}/{path.lstrip('/')}"
    r = requests.get(url, auth=auth, timeout=30)
    r.raise_for_status()
    return r

def handler(event, _ctx):
    qs = (event.get("queryStringParameters") or {})
    job = qs.get("job")
    build = qs.get("build")
    if not job or not build:
        return {"statusCode": 400, "body": "missing job/build"}

    auth = get_jenkins_creds()

    meta    = jget(f"/job/{job}/{build}/api/json", auth).json()
    console = jget(f"/job/{job}/{build}/consoleText", auth).text
    tests   = None
    try:
        tests = jget(f"/job/{job}/{build}/testReport/api/json", auth).json()
    except Exception:
        pass

    prefix = f"{job}/{build}"
    s3.put_object(Bucket=S3_BUCKET, Key=f"{prefix}/meta.json", Body=json.dumps(meta).encode())
    s3.put_object(Bucket=S3_BUCKET, Key=f"{prefix}/console.txt", Body=console.encode())
    if tests:
        s3.put_object(Bucket=S3_BUCKET, Key=f"{prefix}/tests.json", Body=json.dumps(tests).encode())

    sqs.send_message(QueueUrl=SQS_URL, MessageBody=json.dumps({
        "job": job, "build": build, "s3_prefix": prefix
    }))

    return {"statusCode": 200, "body": "ok"}