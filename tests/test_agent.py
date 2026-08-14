from src.crew_lead.agent import agent

response = agent.invoke({
    "messages": [
        {
            "role": "user",
            "content": (
                "Flight 6E123 is delayed. "
                "Perform a complete crew disruption assessment "
                "and recommend the next operational actions."
            ),
        }
    ]
})

print(response["messages"][-1].content)