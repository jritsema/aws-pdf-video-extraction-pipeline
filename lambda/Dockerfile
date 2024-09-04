FROM public.ecr.aws/lambda/python:3.9

RUN yum update -y && yum clean all

COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY *.py ./

CMD ["lambda_function.lambda_handler"]
