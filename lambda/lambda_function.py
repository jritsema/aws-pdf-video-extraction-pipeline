import os
from datetime import datetime
import boto3
import fitz
import urllib
import urllib.parse
import json

s3 = boto3.client("s3")
kendra = boto3.client("kendra")
textract = boto3.client("textract")
transcribe = boto3.client("transcribe")


def lambda_handler(event, context):
    """lambda entrypoint"""

    print("lambda_handler")
    print(event)
    print()

    for record in event["Records"]:

        # which file has been created?
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
        print(f"created: s3://{bucket}/{key}")

        # get file name
        file = key.split("/")[-1]

        # when PDFs are created:
        if key.endswith(".pdf"):
            # extract images from pdf and write to s3
            process_pdf(file, bucket, key)

        # when videos are created:
        elif key.endswith(".mp4"):
            # get video transciption
            process_video(file, bucket, key)

        # process transcription output
        elif key.endswith("transcribe.out"):
            # write transcription to s3
            process_transcription(file, bucket, key)

    print("done")


def process_pdf(file, bucket, key):
    """process pdf files"""

    path = f"/tmp/{file}"
    print(f"\ndownloading {key} from s3...")
    s3.download_file(bucket, key, path)

    # extract images from pdf
    images = f"/tmp/images"
    if not os.path.exists(images):
        os.makedirs(images)
    print("\nextracting images from pdf...")
    extract_images_from_pdf(path, images)

    # run images through textract and upload to s3
    process_images(images, bucket, key)


def process_video(file, bucket, key):

    # get file extension of file
    ext = key.split(".")[-1]
    media_file = f"s3://{bucket}/{key}"
    print()
    print("processing video ", media_file)

    # job name can't have spaces
    # add timestamp for unique job names
    dt = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    job = f"{dt}-{key}"
    job = job.replace(" ", "_")

    # transcribe doesn't seem to like spaces in output_key
    key = key.replace(" ", "*!*")
    output_key = f"{key}/transcribe.out"
    print(f"output_key = {output_key}")

    # run video through transcribe to get audio transcriptions
    print(f"submitting job {job}")
    response = transcribe.start_transcription_job(
        TranscriptionJobName=job,
        LanguageCode='en-US',
        # MediaSampleRateHertz=123,
        MediaFormat=ext,
        Media={
            'MediaFileUri': media_file,
            # 'RedactedMediaFileUri': 'string'
        },
        OutputBucketName=bucket,
        OutputKey=output_key,
        # Settings={
        #     'VocabularyName': 'string',
        #     'ShowSpeakerLabels': True|False,
        #     'MaxSpeakerLabels': 123,
        #     'ChannelIdentification': True|False,
        #     'ShowAlternatives': True|False,
        #     'MaxAlternatives': 123,
        #     'VocabularyFilterName': 'string',
        #     'VocabularyFilterMethod': 'remove'|'mask'|'tag'
        # },
    )


def process_transcription(file, bucket, key):
    """process transcription output"""

    # get key output from s3 and convert to json
    response = s3.get_object(Bucket=bucket, Key=key)
    json_object = response['Body'].read().decode('utf-8')
    parsed_json = json.loads(json_object)
    print(parsed_json)
    if parsed_json["status"] != "COMPLETED":
        raise Exception("transcription job not completed")
    transcript = parsed_json["results"]["transcripts"][0]["transcript"]

    # write transcript back to s3
    # remove special characters
    s3_path = key.replace("*!*", " ")
    s3_path = s3_path.replace("transcribe.out", "transcribe.txt")
    print(f"writing transcript to {s3_path}...")
    s3.put_object(Body=transcript, Bucket=bucket, Key=s3_path)

    # delete intermedia artifacts
    print(f"deleting {key} and everything under it from s3...")
    parts = key.split("/")
    key = "/".join(parts[:-1])
    delete_s3_objects(bucket, key)
    print("done")


def delete_s3_objects(bucket_name, prefix):
    """
    Delete all objects under the specified prefix in the S3 bucket.
    """
    # List objects in the specified prefix
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

    # Check if objects were found
    if 'Contents' in response:
        objects = [{'Key': obj['Key']} for obj in response['Contents']]

        # Delete objects
        s3.delete_objects(Bucket=bucket_name, Delete={'Objects': objects})

        print(f"Deleted {len(objects)} objects under prefix '{prefix}'.")
    else:
        print(f"No objects found under prefix '{prefix}'.")


def extract_images_from_pdf(pdf_path, output_folder):
    pdf_document = fitz.open(pdf_path)
    print(f"\nfound {pdf_document.page_count} pages")

    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        images = page.get_images(full=True)

        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]

            image_path = f"{output_folder}/page{page_num + 1}_img{img_index + 1}.png"

            with open(image_path, "wb") as image_file:
                print(f"writing {image_path}")
                image_file.write(image_bytes)

    pdf_document.close()


# s3://{bucket}/doc.pdf/{image}/textract.txt
def process_images(local_directory, bucket_name, prefix):
    for root, dirs, files in os.walk(local_directory):
        for file in files:
            print()
            local_path = os.path.join(root, file)
            s3_path = os.path.join(prefix, file)
            print(f"uploading {local_path} to {s3_path}...\n")
            try:
                s3.upload_file(local_path, bucket_name, s3_path)
                print(f"Successfully uploaded {local_path} to {s3_path}")
            except Exception as e:
                print(f"Error uploading {local_path} to {s3_path}: {e}")

            # run image through textract (ocr)
            with open(local_path, "rb") as image_file:
                image_data = image_file.read()

            print("running image through textract")
            response = textract.analyze_document(
                Document={"Bytes": image_data},
                FeatureTypes=["FORMS", "TABLES"]
            )

            # write local text file with extracted lines
            textract_file_name = f"{local_directory}/textract.txt"
            with open(textract_file_name, "w") as textract_file:
                for block in response["Blocks"]:
                    if block["BlockType"] == "LINE":
                        textract_file.write(f"{block['Text']}\n")

            # upload textract file to s3
            # /doc.pdf/image.png/textract.txt
            s3_path = os.path.join(s3_path, "textract.txt")
            print(f"uploading {textract_file_name} to {s3_path}...\n")
            s3.upload_file(textract_file_name, bucket_name, s3_path)
