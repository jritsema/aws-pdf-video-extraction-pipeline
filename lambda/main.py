import lambda_function


def main():

    event = {
        'Records': [
            {
                'eventVersion': '2.1',
                'eventSource': 'aws:s3',
                'awsRegion': 'us-east-1',
                'eventTime': '2023-08-17T18:27:03.595Z',
                'eventName': 'ObjectCreated:Put',
                'requestParameters': {'sourceIPAddress': '192.168.1.1'},
                'responseElements': {
                    'x-amz-request-id': 'Q6S3HYEX86WM7QD4',
                    'x-amz-id-2': 'NXTUJQfEeqQ0ivVVRNLodeaE1OEECT8wfe8BJrQAGDm+17h9cIY+a1tyGJRdWiqFeC3IVXriFAUAuGdluP+BE2pxjdnKxrt8'
                },
                's3': {
                    's3SchemaVersion': '1.0',
                    'configurationId': 'tf-s3-lambda-20230817175708354200000002',
                    'bucket': {
                        'name': 'test-bucket',
                        'arn': 'arn:aws:s3:::test-bucket'
                    },
                    'object': {
                        'key': 'test.pdf',
                        'size': 169,
                        'eTag': '7a24d9c24ce4b6378f2f46eef4ce3e97',
                        'sequencer': '0064DE667785C8536C'
                    }
                }
            }
        ]
    }

    res = lambda_function.lambda_handler(event, context=None)
    print(res)


if __name__ == "__main__":
    main()
