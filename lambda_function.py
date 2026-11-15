import os
from io import BytesIO
from urllib.parse import unquote_plus

import boto3
from PIL import Image

s3 = boto3.client("s3")
DESTINATION_BUCKET = os.environ["DESTINATION_BUCKET"]
THUMBNAIL_SIZE = (200, 200)
def resize_image(bucket, key):
    # Read the original image from S3.
    response = s3.get_object(Bucket=bucket, Key=key)

    with response["Body"] as stream:
        image_data = stream.read()

    # Resize the image while keeping its proportions.
    with Image.open(BytesIO(image_data)) as image:
        image_format = image.format
        image.thumbnail(THUMBNAIL_SIZE)

        output = BytesIO()
        image.save(output, format=image_format)

    # Save the thumbnail in the destination bucket.
    s3.put_object(
        Bucket=DESTINATION_BUCKET,
        Key=key,
        Body=output.getvalue(),
        ContentType=Image.MIME[image_format]
    )

    return {"bucket": DESTINATION_BUCKET, "key": key}
def lambda_handler(event, context):
    try:
        results = []

        if "Records" in event:
            # Handle images uploaded directly to S3.
            for record in event["Records"]:
                bucket = record["s3"]["bucket"]["name"]
                key = unquote_plus(record["s3"]["object"]["key"])
                results.append(resize_image(bucket, key))
        else:
            # Handle an image requested through Step Functions.
            bucket = event["bucket"]
            key = event["key"]
            results.append(resize_image(bucket, key))

        return {"success": True, "images": results}

    except Exception as error:
        print(f"Image processing failed: {error}")

        if "Records" in event:
            raise

        return {"success": False, "error": str(error)}