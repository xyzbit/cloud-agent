package tools

import (
	"strconv"
	"strings"
)

const AddToolName = `AddTool`

const AddToolDescription = `
Use this tool for addition calculations.
	example:
		1+2 =?
	then Action Input is: 1,2
`

const AddToolParam = `{"type":"object","properties":{"numbers":{"type":"array","items":{"type":"integer"}}}}`

const SubToolName = `SubTool`

const SubToolDescription = `
Use this tool for subtraction calculations.
	example:
		1-2 =?
	then Action Input is: 1,2
`

const SubToolParam = `{"type":"object","properties":{"numbers":{"type":"array","items":{"type":"integer"}}}}`

func AddTool(numbers string) int {
	num := strings.Split(numbers, ",")
	inum0, _ := strconv.Atoi(num[0])
	inum1, _ := strconv.Atoi(num[1])
	return inum0 + inum1
}

func SubTool(numbers string) int {
	num := strings.Split(numbers, ",")
	inum0, _ := strconv.Atoi(num[0])
	inum1, _ := strconv.Atoi(num[1])
	return inum0 - inum1
}
