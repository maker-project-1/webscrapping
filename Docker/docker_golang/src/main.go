package main

import (
	"fmt"
	"log"
	"net/http"

	_ "github.com/tealeg/xlsx"
)

const (
	// PathExcel = "/ressource/" => where the excel files are stock"
	PathExcel = "/ressource/"

	// Extension = ".xlsx => format of the files"
	Extension = ".xlsx"
)

func main() {
	// '/' is the url that we are going to work on
	http.HandleFunc("/", httpRequest)

	fmt.Printf("Ready\n")

	// Define the port where we are going to work on
	if err := http.ListenAndServe(":80", nil); err != nil {
		log.Fatal(err)
	}
}
