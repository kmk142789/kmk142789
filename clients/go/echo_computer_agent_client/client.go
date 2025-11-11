package echo_computer_agent_client

import (
    "bytes"
    "context"
    "encoding/json"
    "fmt"
    "net/http"
    "strings"
)

type ChatRequest struct {
    Message string `json:"message"`
    Inputs map[string]any `json:"inputs,omitempty"`
    Execute *bool `json:"execute,omitempty"`
}

type ChatResponse struct {
    Function string `json:"function"`
    Message string `json:"message"`
    Data map[string]any `json:"data"`
    Metadata map[string]any `json:"metadata"`
}

type FunctionDescription struct {
    Name string `json:"name"`
    Description string `json:"description"`
    Parameters map[string]any `json:"parameters"`
    Metadata map[string]any `json:"metadata"`
}

type FunctionListResponse struct {
    Functions []FunctionDescription `json:"functions"`
}

type Client struct {
    baseURL string
    httpClient *http.Client
    defaultHeaders map[string]string
}

func NewClient(baseURL string, httpClient *http.Client) *Client {
    trimmed := strings.TrimRight(baseURL, "/")
    if httpClient == nil {
        httpClient = http.DefaultClient
    }
    return &Client{
        baseURL: trimmed,
        httpClient: httpClient,
        defaultHeaders: map[string]string{},
    }
}

func (c *Client) SetDefaultHeader(key, value string) {
    c.defaultHeaders[key] = value
}

func (c *Client) ListFunctions(ctx context.Context) (*FunctionListResponse, error) {
    req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.baseURL+"/functions", nil)
    if err != nil {
        return nil, err
    }
    for k, v := range c.defaultHeaders {
        req.Header.Set(k, v)
    }
    resp, err := c.httpClient.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    if resp.StatusCode >= 400 {
        return nil, fmt.Errorf("request failed with status %d", resp.StatusCode)
    }
    var payload FunctionListResponse
    if err := json.NewDecoder(resp.Body).Decode(&payload); err != nil {
        return nil, err
    }
    return &payload, nil
}

func (c *Client) Chat(ctx context.Context, request ChatRequest) (*ChatResponse, error) {
    body, err := json.Marshal(request)
    if err != nil {
        return nil, err
    }
    req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.baseURL+"/chat", bytes.NewReader(body))
    if err != nil {
        return nil, err
    }
    req.Header.Set("Content-Type", "application/json")
    for k, v := range c.defaultHeaders {
        req.Header.Set(k, v)
    }
    resp, err := c.httpClient.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    if resp.StatusCode >= 400 {
        return nil, fmt.Errorf("request failed with status %d", resp.StatusCode)
    }
    var payload ChatResponse
    if err := json.NewDecoder(resp.Body).Decode(&payload); err != nil {
        return nil, err
    }
    return &payload, nil
}
