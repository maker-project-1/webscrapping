FROM golang

RUN mkdir /app
RUN mkdir /ressource

ADD . /app/
ADD ./raw_ctg_page_extracts.xlsx /ressource/

WORKDIR /app

RUN go get github.com/tealeg/xlsx
RUN go build -o binary ./src/main.go ./src/check.go ./src/manageHttp.go ./src/file.go

ENTRYPOINT [ "/app/binary" ]