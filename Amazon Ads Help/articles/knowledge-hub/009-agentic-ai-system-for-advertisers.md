---
title: "How to architect an agentic AI system for Advertisers"
source_url: "https://advertising.amazon.com/API/docs/en-us/knowledge-hub/blogs/genai/gen-ai-amazon-ads"
library: "Amazon Ads Advanced Tools Center"
section: "knowledge-hub"
downloaded_at: "2026-10-07"
status: "captured"
---

# How to architect an agentic AI system for Advertisers

by Chintan Sanghavi Lead Solutions Architect @ Amazon Ads: December 27th 2025

## Introduction

Advertisers execute several key activities to create and optimize successful campaigns. For example, analysis of past campaign performance, brand guidelines, creative effectiveness, audience creation, targeting, media selection and finally campaign setup in Amazon Ads console.

Once the campaigns are created, advertisers need to obtain performance measurement data to optimize campaigns based on data insights.

To create an agentic AI system, the advertiser has to consider many aspects such as how to create a modular system, how many agents should they create, how to provide accurate answers, how to validate the response and actions taken by an agent etc. These can be complex and time-consuming tasks.

The objective of this blog is to provide an approach to build an agentic AI system. The final solution depends on the requirements of the advertiser, existing applications etc.

## Solution Overview

To implement an agentic AI system, as shown above in the diagram, advertisers can implement a hierarchical multi-agent architecture with a central orchestrator. This system uses a main Router Agent to direct user queries to specialized agents based on their expertise. This approach delivers a unified user experience while maximizing domain-specific knowledge and tools. The system will run on Amazon Bedrock and Amazon Bedrock AgentCore to meet security, scalability, and performance requirements.

This architecture offers several advantages: - Independent agent development and deployment allows advertisers to select agents that fit their enterprise needs - Incremental development enables advertisers to start with basic capabilities and expand over time - Faster production deployment through the built-in security and scalability features of Amazon Bedrock AgentCore - Agent monetization opportunities through the Agentic Marketplace, where other advertisers can purchase and use your agents.

The architecture will be composed of the following key layers and components:

- **User Interface (UI) Layer**: A unified interface where users submit their queries. The user interacts only with the main system, not the individual sub-agents directly.
- **Orchestration/Routing Layer**: This is the core of the system, managed by the Router Agent (or orchestrator). Router Agent (Main Agent): This LLM-based agent is responsible for: - Intent Recognition: Analyzing the initial user query to determine the required domain of expertise. - Agent Routing: Dynamically selecting and routing the query to the most appropriate specialized agent. This decision is made based on defined agent capabilities and descriptions. - Context Management: Maintaining the conversational context throughout the interaction, ensuring smooth "warm transfers" of information between agents if a query requires multiple domains. - Response Synthesis: Receiving outputs from the specialized agent(s) and synthesizing them into a coherent, single response for the user, maintaining a unified brand voice. - Agent Capability Registry: A structured metadata system (e.g., a simple database or configuration file) that lists the function, domain, and available tools of each specialized agent. The Router Agent references this registry for routing decisions. Agents will communicate using a combination of the **Agent2Agent (A2A)**protocol for collaboration and the**Model Context Protocol (MCP)** for tool use.
- **Domain Agents Layer**: These are the individual, specialized support agents, each acting as an independent microservice. The examples of Specialized Agents are 1/ Audience Agent 2/ Measurement Agent. Each agent is tightly scoped to a specific task or knowledge domain to reduce hallucinations and increase accuracy.
- **Communication**: Agents will communicate with each other using Agent2Agent (A2A) protocol for collaboration and use Model Context Protocol (MCP) for tool use.
- **Discover Capabilities**: Agents publish "Agent Cards" (structured metadata) that the Router Agent uses to dynamically discover which agent handles which domain.
- **Manage Tasks**: A2A defines a clear lifecycle for tasks (submitted, working, completed, etc.), allowing the Router Agent to monitor progress on long-running requests and manage stateful interactions across different agents.
- **Private Knowledge Bases (Vector DBs)**: The specialized agent may have access to its own dedicated, domain-specific knowledge base (vector database) via Retrieval-Augmented Generation (RAG). This ensures they provide accurate, relevant information for their area.
- **Tool Integration**: Agents will use specific tools or APIs to perform actions, such as creating audiences or creation of campaigns.
- **Infrastructure and Operations Layer**: Use of containerization (e.g., Docker containers) to deploy agents as microservices, allowing them to scale dynamically based on demand. This will help us to deploy agents on Amazon Bedrock AgentCore and if needed outside of AgentCore to Amazon EKS or Amazon ECS.
- **Security, Monitoring and Observability:** Robust logging and monitoring tools to track router performance, identify failure points, and ensure compliance and security. It should have enterprise-grade security features like JWT and OAuth 2.0 for authentication, ensuring only authorized agents participate in the workflow.
- **Human-in-the-Loop (HITL) Governance**: A mechanism for seamless handoff to a human for complex or sensitive cases that the AI system cannot complete or requires Human approval.
- **Memory Management and Storage**: Memory is handled at different levels to maintain context and provide long-term knowledge access. - **Short-term Memory (Context Window)**: The immediate conversation history (messages, task IDs, status) is maintained within the active session and passed between the Router Agent and the relevant Domain Agents using the A2A and MCP protocols. - **Long-term Memory (Knowledge Bases)**: Long-term, factual knowledge is stored in dedicated Vector Databases and traditional databases. This data is static or updated periodically (e.g., product documentation, historical solutions, best practices). Agents access this memory only via RAG (Retrieval-Augmented Generation) calls using their MCP interfaces, ensuring the core LLM does not "memorize" everything and can access up-to-date, verifiable information. The memory database can be hosted on AgentCore Memory or vector database such as Amazon OpenSearch for scalability.

## Interaction Workflow

1. A user submits a query via the UI.
2. The Router Agent analyzes the intent and context.
3. The Router Agent selects the appropriate Domain Agent based on its analysis and the capability registry.
4. The selected Domain Agent uses RAG or invokes tool to retrieve information and generates a response.
5. The Router Agent receives the response and presents it to the user.
6. If the next query from the user changes topics, the Router Agent seamlessly routes to a different Domain Agent, maintaining continuity.

## Summary

Agentic AI and generative AI are an evolving space, and can drastically change the way advertisers are working today. They have the potential to increase productivity significantly and increase return on investment (ROI) on advertising spend.

Generative AI technologies like Amazon Bedrock AgentCore, Strands, the choice of LLM model etc are critical components of building Agentic AI systems.

The goal of the above architecture is to accelerate the development and creation of agentic AI applications.

Amazon Ads and technology partners of Amazon Ads have created pre-built MCP servers and agents to help advertisers to build Agentic AI systems.

### About the authors

**Chintan Sanghavi**
Chintan is a lead solutions architect at Amazon Ads, driving innovation with Generative AI, AWS, and Amazon Ads solutions. He has extensive experience building complex multi-technology solutions.
