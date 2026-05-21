---
title: "Agents with Amazon Ads MCP Server workshop overview"
source_url: "https://advertising.amazon.com/API/docs/en-us/knowledge-hub/hands-on-workshops/amazon-ads-mcp-server/01-overview"
library: "Amazon Ads Advanced Tools Center"
section: "knowledge-hub"
downloaded_at: "2026-05-13"
status: "captured"
---

# Agents with Amazon Ads MCP Server workshop overview

This workshop helps technical teams build agentic AI solutions for Amazon Ads. It covers custom MCP servers, LangGraph agents, Amazon Bedrock AgentCore, and the Amazon Ads MCP Server.

## Objectives

- Understand Model Context Protocol (MCP) and tool/API connection patterns.
- Build and deploy a custom MCP server backed by an Amazon Bedrock Knowledge Base.
- Create a LangGraph agent using Claude on Amazon Bedrock.
- Deploy MCP servers and agents to Amazon Bedrock AgentCore.
- Connect to the official Amazon Ads MCP Server to manage advertising campaigns through natural language.
- Produce artifacts that can be adapted for production agentic workflows.

## Audience

Solutions architects, software engineers, and technical leads working with Amazon Ads API and AI-powered automation.

## Learning tracks

| Track | Modules | What it builds | Additional requirements |
| --- | --- | --- | --- |
| Track A | 1-6 | Custom MCP server, Bedrock Knowledge Base wrapper, LangGraph agent, AgentCore deployment | AWS/Bedrock/Python setup |
| Track B | 7-9 | Amazon Ads MCP Server integration and multi-server Ads campaign agent | Ads API Client ID, Client Secret, Refresh Token |
| Cleanup | 10 | Deletes workshop resources | Applies to both tracks |

## End-state architecture

```text
Amazon Bedrock AgentCore
  - LangGraph Agent (A2A protocol)
  - Knowledge Base MCP Server
  - Amazon Ads MCP Server

AWS services
  - Amazon Bedrock / Claude
  - Bedrock Knowledge Base
  - AWS Secrets Manager
  - CloudWatch Logs

External
  - Amazon Ads API
```

## Data flow

- Client invokes LangGraph Agent through AgentCore.
- LangGraph Agent invokes MCP servers.
- LangGraph Agent calls Claude on Amazon Bedrock.
- Knowledge Base MCP Server calls Bedrock Knowledge Base retrieval/generation.
- Amazon Ads MCP Server calls Amazon Ads API.
- Secrets are read from AWS Secrets Manager.
- Runtime logs stream to CloudWatch.

## Core components

| Component | Role |
| --- | --- |
| Knowledge Base MCP Server | FastMCP server exposing `query_knowledge_base` and `retrieve_and_generate`. |
| Amazon Ads MCP Server | Official Amazon Ads MCP Server, open beta, translates natural language into Ads API calls. |
| LangGraph Agent | Discovers MCP tools, converts them to LangChain tools, and orchestrates calls using Claude on Bedrock. |
| AgentCore | Managed runtime for MCP servers and A2A agents. |

## Prerequisites

Required for all tracks:

- Python 3.13+
- AWS account with Amazon Bedrock access
- AWS CLI configured
- AgentCore CLI
- `uv`
- `pip`

Track B additionally requires:

- Amazon Ads API Client ID
- Amazon Ads API Client Secret
- Amazon Ads API Refresh Token

Safety note: for production environments, use IAM Identity Center or temporary credentials where possible. Do not commit secrets to source control.

## Module list

| Module | Title | Estimated time |
| --- | --- | --- |
| 01 | Workshop overview and prerequisites | 20 min |
| 02 | MCP and AgentCore concepts | 15 min |
| 03 | Build an MCP Server | 30 min |
| 04 | Deploy MCP Server to AgentCore | 20 min |
| 05 | Build a LangGraph Agent | 45 min |
| 06 | Deploy Agent to AgentCore | 20 min |
| 07 | Connect to Amazon Ads MCP Server | 30 min |
| 08 | Build an Ads Campaign Agent | 45 min |
| 09 | Testing and monitoring | 20 min |
| 10 | Cleanup and next steps | 10 min |

Total estimate: ~4 hours.

## What gets built

1. Knowledge Base MCP Server.
2. LangGraph Agent using Claude on Bedrock.
3. Ads Campaign Agent that aggregates the custom Knowledge Base MCP server and Amazon Ads MCP Server.

## Routing use

Use this page when the user asks about building an AI skill/agent around Amazon Ads, connecting local knowledge to Ads API actions, MCP server architecture, or natural-language Ads campaign automation.
