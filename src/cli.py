from src.agent.agent import app
from src.services.customer_service import CustomerService

def run_chatbot():

        customer_id = input("Customer ID: ")

        service = CustomerService()

        customer = service.get_or_create_customer(
        customer_id
)

        conversations = service.get_conversations(
    customer_id
)

        if conversations:
            print("\nYour conversations:")

            for i, conversation in enumerate(conversations, start=1):
                print(f"{i}. {conversation[2]}")

            print("0. Start a new conversation")

            choice = int(input("\nSelect conversation: "))

            if choice == 0:
                conversation = service.start_conversation(
               customer_id
        )
            else:
                conversation = service.select_conversation(
            customer_id,
            choice
        )

                if conversation is None:
                    print("Invalid conversation selection.")
                    exit()

        else:
            conversation = service.start_conversation(
        customer_id
    )

        thread_id = conversation[2]

        print(f"\nConversation started for {thread_id}")

        while True:
            user_input = input("You: ")

            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break

            result = app.invoke(
            {
                "customer_id": customer_id,
                "messages": [
                    {
                        "role": "user",
                        "content": user_input
                    }
                ]
            },
            config={
                "configurable": {
                    "thread_id": thread_id
                }
            }
        )

            print("Assistant:", result["messages"][-1].content)

if __name__ == "__main__":
    run_chatbot()
