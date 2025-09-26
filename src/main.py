from src.agent.agent_runner import agent


def main():
    response = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "In SIFT note which is located in Machine Learning folder add new content: 'SIFT is a feature detection algorithm.' and add tag 'ml'.",
                }
            ]
        }
    )

    messages = response["messages"]
    final_message = messages[-1]  # the assistant’s last reply
    print(final_message.content)  # use .content instead of dict access


if __name__ == "__main__":
    main()
