package main

import (
    "context"
    "flag"
    "log"
    "time"

    client "echo_computer_agent_client"
)

func main() {
    baseURL := flag.String("base-url", "http://127.0.0.1:8000", "Echo Computer Agent base URL")
    flag.Parse()

    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()

    c := client.NewClient(*baseURL, nil)
    functions, err := c.ListFunctions(ctx)
    if err != nil {
        log.Fatal(err)
    }
    if len(functions.Functions) == 0 {
        log.Fatal("no functions returned")
    }

    chat, err := c.Chat(ctx, client.ChatRequest{Message: "launch echo.bank"})
    if err != nil {
        log.Fatal(err)
    }
    if chat.Function == "" {
        log.Fatal("empty function name")
    }

    log.Printf("chat response: %s", chat.Message)
}
