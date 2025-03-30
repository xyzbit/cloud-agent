package main

import (
	"fmt"
	"log"
	"regexp"
	"strconv"
	"strings"

	"github.com/xyzbit/cloud-agent/message"
	"github.com/xyzbit/cloud-agent/tools"
)

const Template = `Answer the following questions as best you can. You have access to the following tools:


%s


Use the following format:


Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [%s]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question


Begin!


Question: %s
`

func main() {
	query := "1+2+3+4-5-6=? Use the AddTool and SubTool to calculate the result. Just give me a number result"

	addtool := tools.AddToolName + ":" + tools.AddToolDescription + "\nparam: \n" + tools.AddToolParam
	subtool := tools.SubToolName + ":" + tools.SubToolDescription + "\nparam: \n" + tools.SubToolParam
	toolsL := make([]string, 0)
	toolsL = append(toolsL, addtool, subtool)

	tool_names := make([]string, 0)
	tool_names = append(tool_names, tools.AddToolName, tools.SubToolName)

	prompt := fmt.Sprintf(Template, strings.Join(toolsL, "\n\n"), strings.Join(tool_names, ","), query)

	//注入用户prompt
	message.MessageStore.AddForUser(prompt)
	log.Println("prompt: ", message.MessageStore.ToMessage())
	i := 1
	for i < 5 {
		first_response := message.NormalChat(message.MessageStore.ToMessage())
		regexPattern := regexp.MustCompile(`Final Answer:\s*(.*)`)
		finalAnswer := regexPattern.FindStringSubmatch(first_response.Content)
		if len(finalAnswer) > 1 {
			fmt.Println("========最终 GPT 回复========")
			fmt.Println(first_response.Content)
			break
		}
		fmt.Printf("========第%d轮回答========\n", i)
		fmt.Println(first_response)

		message.MessageStore.AddForAssistant(first_response)

		regexAction := regexp.MustCompile(`Action:\s*(.*?)[.\n]`)
		regexActionInput := regexp.MustCompile(`Action Input:\s*(.*?)[.\n]`)

		action := regexAction.FindStringSubmatch(first_response.Content)
		actionInput := regexActionInput.FindStringSubmatch(first_response.Content)

		log.Println("action: ", action)
		log.Println("actionInput: ", actionInput)
		if len(action) > 1 && len(actionInput) > 1 {
			i++
			result := 0
			//需要调用工具
			if action[1] == "AddTool" {
				fmt.Println("calls AddTool")
				result = tools.AddTool(actionInput[1])
			} else if action[1] == "SubTool" {
				fmt.Println("calls SubTool")
				result = tools.SubTool(actionInput[1])
			}
			fmt.Println("========函数返回结果========")
			fmt.Println(result)

			Observation := "Observation: " + strconv.Itoa(result)
			prompt = first_response.Content + Observation
			fmt.Printf("========第%d轮的prompt========\n", i)
			fmt.Println(prompt)
			message.MessageStore.AddForUser(prompt)
		}
	}
}
