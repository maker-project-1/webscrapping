package main

import (
	"fmt"
	"net/http"
	"os"

	"github.com/tealeg/xlsx"
)

func fileFound(w http.ResponseWriter, excelFileName string) {
	xlFile, err := xlsx.OpenFile(excelFileName)

	if err != nil {
		os.Exit(84)
	}

	table := "<html> <table> </html>"
	w.Write([]byte(fmt.Sprintf(table)))

	for _, sheet := range xlFile.Sheets {

		for _, row := range sheet.Rows {
			line := "<html> <tr> </html>"
			w.Write([]byte(fmt.Sprintf(line)))

			for _, cell := range row.Cells {
				text := cell.String()
				caseExcel := "<html> <td>" + text + "</td> </html>"
				w.Write([]byte(fmt.Sprintf(caseExcel)))

			}
			endLine := "<html> </tr> </html>"
			w.Write([]byte(fmt.Sprintf(endLine)))
		}
	}
	endtable := "<html>" +
		"</table>" +
		"<form action=\"http://localhost:8080\" method=\"get\">" +
		"<input type=\"submit\" value=\"Return\">" +
		"</form>" +
		"</html>"

	w.Write([]byte(fmt.Sprintf(endtable)))
}

func fileNotFound(w http.ResponseWriter) {
	fileNotFoundDisplay := "<html>" +
		"FILE NOT FOUND" +
		"<br>Please launch the Script before checking result" +
		"<script> var timer = setTimeout(function() { window.location='http://localhost:8080' }, 5000); </script>" +
		"</html>"

	w.Write([]byte(fmt.Sprintf(fileNotFoundDisplay)))
}
