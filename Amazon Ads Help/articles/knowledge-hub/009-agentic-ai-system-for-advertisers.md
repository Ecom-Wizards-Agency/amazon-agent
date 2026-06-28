---
title: "How to architect an agentic AI system for Advertisers"
source_url: "https://advertising.amazon.com/API/docs/en-us/knowledge-hub/blogs/genai/gen-ai-amazon-ads"
library: "Amazon Ads Advanced Tools Center"
section: "knowledge-hub"
downloaded_at: "2026-05-13"
status: "captured"
---

# Agentic AI System for Advertisers

This article describes a multi-agent architecture for advertising workflows such as campaign analysis, audience creation, campaign setup, measurement, reporting, and optimization.

## Core idea

Advertisers can use a hierarchical multi-agent architecture with a central Router Agent. The router receives the user request, identifies the intent, sends the task to the right specialized agent, and synthesizes the response back into one user-facing answer.

## Architecture visuals

![Agent architecture](https://d3a0d0y2hgofx6.cloudfront.net/en-us/_images/knowledge_hub_images/blogs/Agent-Architecture.png)

![Agent block diagram](https://d3a0d0y2hgofx6.cloudfront.net/en-us/_images/knowledge_hub_images/blogs/block-diagram.png)

![Agent interactions](https://d3a0d0y2hgofx6.cloudfront.net/en-us/_images/knowledge_hub_images/blogs/interactions.png)

## Architecture layers

| Layer | Role |
| --- | --- |
| User interface | Single place where users ask questions or request actions. |
| Router Agent | Recognizes intent, chooses the right domain agent, manages context, and synthesizes final responses. |
| Agent capability registry | Structured metadata describing each agent, domain, available tools, and routing rules. |
| Domain agents | Specialized agents for areas such as audiences, measurement, campaign creation, creative, reporting, or optimization. |
| Knowledge bases | Domain-specific RAG stores for documentation, best practices, historical solutions, and internal playbooks. |
| Tool/API layer | MCP tools and APIs used by agents to create, inspect, or modify advertising resources. |
| Operations layer | Deployment, logging, monitoring, security, and scaling through Bedrock AgentCore or containerized services. |
| Human approval | Required handoff for sensitive, irreversible, or externally visible actions. |

## Communication patterns

- A2A protocol supports agent-to-agent task collaboration and task lifecycle tracking.
- MCP provides tool access for retrieval, APIs, and operational actions.
- Agent Cards describe capabilities so the router can discover the right domain agent.
- Short-term memory keeps the current session context and task state.
- Long-term memory is stored in knowledge bases or traditional databases and retrieved as needed.

## Interaction workflow

1. User submits a query.
2. Router Agent analyzes intent and context.
3. Router Agent selects the best domain agent from the capability registry.
4. Domain Agent retrieves knowledge or invokes approved tools.
5. Router Agent receives the output, checks fit, and presents a unified response.
6. If the topic changes, the router transfers the task to another agent while preserving context.

## Why it matters for this local SOP master

This pattern maps directly to the planned Amazon routing skill:

| Skill need | Article pattern |
| --- | --- |
| Search the right local library first | Domain knowledge bases and RAG. |
| Decide which workflow applies | Router Agent and capability registry. |
| Guide Chrome actions step by step | Domain agents plus tool/API layer. |
| Stop before risky actions | Human-in-the-loop governance. |
| Preserve screenshots/tables | Knowledge base artifacts and workflow checkpoints. |

## Stop-before-risky-action rules

Pause for explicit approval before:

- Creating, pausing, changing, or deleting campaigns.
- Changing budgets, bids, targeting, audiences, or creative.
- Sending support messages or creator communications.
- Exporting, uploading, or syncing customer data.
- Connecting APIs, tokens, or secret-bearing services.

## Routing use

Use this page when the user asks about building AI agents for Amazon Ads, routing Amazon workflows, MCP/A2A/AgentCore architecture, or turning the local Amazon docs library into a practical assistant skill.
