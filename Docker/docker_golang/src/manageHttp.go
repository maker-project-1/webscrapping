package main

import (
	"fmt"
	"net/http"
	"strings"
)

func httpRequest(w http.ResponseWriter, r *http.Request) {
	if r.Method == "GET" {
		fmt.Printf("GET Method\n")
		url := strings.Split(r.URL.String(), "/")

		file := getFile(url[1])

		fmt.Printf(file)
		fmt.Printf("\n")

		if file != "" {
			fmt.Printf("File Found\n")
			fileFound(w, file)
		} else {
			fmt.Printf("File Not Found\n")
			fileNotFound(w)
		}
	}

}
