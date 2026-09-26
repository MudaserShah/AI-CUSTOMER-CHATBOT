from src.database.repository import CustomerRepository


class CustomerService:

    def __init__(self):
        self.repository = CustomerRepository()

    def get_or_create_customer(self, customer_id):
        return self.repository.get_or_create_customer(
        customer_id=customer_id
    )

    def get_or_create_conversation(self, customer_id):
        return self.repository.get_or_create_conversation(
        customer_id=customer_id
    )

    def start_conversation(self, customer_id):
        return self.repository.create_new_conversation(
        customer_id=customer_id
    )

    def get_conversations(self, customer_id):
        return self.repository.get_conversations(
        customer_id=customer_id
    )

    def select_conversation(self, customer_id, index):
        conversations = self.get_conversations(customer_id)

        if not conversations:
            return None

        if index < 1 or index > len(conversations):
            return None

        return conversations[index - 1]




if __name__ == "__main__":
    service = CustomerService()

    conversations = service.get_conversations(
        "customer-002"
    )

    for i, conversation in enumerate(conversations, start=1):
        print(
            f"{i}. {conversation[2]}"
        )

    selected = service.select_conversation(
        "customer-002",
        2
    )

    print("Selected:", selected)