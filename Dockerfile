FROM python:3.10-alpine AS build
RUN apk add build-base python3-dev linux-headers pcre-dev jpeg-dev zlib-dev
RUN pip install --upgrade pip
RUN pip install uwsgi

FROM python:3.10-alpine AS deps
WORKDIR /vxtiktok
COPY requirements.txt requirements.txt
COPY --from=build /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
RUN pip install -r requirements.txt

FROM python:3.10-alpine AS runner
EXPOSE 9000
RUN apk add pcre-dev jpeg-dev zlib-dev
WORKDIR /vxtiktok
CMD ["uwsgi", "vxtiktok.ini"]
COPY --from=build /usr/local/bin/uwsgi /usr/local/bin/uwsgi
COPY --from=deps /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY . .
