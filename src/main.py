from src.agent.agent_runner import agent


def main():
    response = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "In folder Machine Learning, there is a note named Test note. Can you add in the end of the note the following content: 'SIFT is a feature detection algorithm used in computer vision tasks.' ",
                }
            ]
        }
    )

    messages = response["messages"]
    final_message = messages[-1]  # the assistant’s last reply
    print(final_message.content)  # use .content instead of dict access


if __name__ == "__main__":
    main()
