from server.agents.user_agent import user_agent

def main():
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting the chat.")
            break
        user_agent.print_response(user_input)

if __name__ == "__main__":
    main()