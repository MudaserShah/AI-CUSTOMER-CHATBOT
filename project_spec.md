# AI Customer Support Agent

## Goal
Build an AI support system that can answer customer questions,
retrieve company information, check order status, create support
tickets, and escalate complex cases to a human.

## Users
- Customers
- Support agents
- Admin

## Main Use Cases

### UC-01: General Question
Customer asks about refund, shipping, warranty, etc.
→ Agent searches knowledge base
→ Gives grounded answer

### UC-02: Order Status
Customer asks about an order
→ Agent gets order information
→ Returns actual status

### UC-03: Support Issue
Customer reports a problem
→ Agent gathers relevant information
→ Creates support ticket
→ Returns ticket number

### UC-04: Complex/Sensitive Case
Customer asks for something requiring human judgment
→ Agent escalates to human
→ Customer is informed

### UC-05: Unknown Question
Agent doesn't have reliable information
→ Agent does NOT invent an answer
→ Escalates or asks for clarification


# Use Case 01: Refund Policy

## Customer
New Customer

## User Message
"What is your refund policy?"

## Intent
GENERAL_QUESTION / REFUND_POLICY

## Agent Needs To
Retrieve the company's refund policy from the knowledge base
and generate an answer based only on the retrieved information.

## Tool / System Needed
RAG / Knowledge Retrieval

## Expected Result
The system retrieves the relevant refund policy:
"Customers can request a refund within 4 days."

## Final Response
"Our refund policy allows customers to request a refund
within 4 days."

## Failure Case

If the knowledge base does not contain a reliable refund policy,
the agent must not invent an answer.

It should say:
"I don't have enough information about the refund policy.
Let me connect you with our support team."

# Use Case 02: Order Status

## Customer
Existing Customer

## User Message
"Where is my order #12345?"

## Intent
SPECIFIC_QUESTION / ORDER_STATUS

## Agent Needs To
Get the order information from the database with the particular order no
and the get the order whether it is shipped, delivered.

## Tool / System Needed
Order Tool  / database

## Expected Result
The system retrieves the order status
"your order is ready to be shipped with this order no #12345"

## Final Response
"your order is ready to be shipped and will deliver with 2 - 3 working days."


# Use Case 03: Change Delivery Address

## Customer
Existing Customer

## User Message
"I want to change the delivery address for my order #56789."

## Intent
ORDER_MODIFICATION / CHANGE_DELIVERY_ADDRESS

## Agent Needs To
1. Retrieve order #56789 from the order system.
2. Check the current order status.
3. If the order has already been shipped, do not modify the address and inform the customer.
4. If the order has not been shipped, verify the customer's identity.
5. Request human approval before making the address change.
6. After human approval, update the delivery address in the order system.
7. Confirm the successful update to the customer.

## Tool / System Needed
Order Management Tool / Database
Human Approval

## Expected Result
The system successfully updates the delivery address for order #56789 after customer verification and human approval.

## Final Response
"Your delivery address for order #56789 has been successfully updated."

## Failure Cases
- If the order is already shipped:
  "Your order #56789 has already been shipped, so the delivery address cannot be changed at this time."

- If customer verification fails:
  "I'm unable to verify your identity, so I can't make changes to the delivery address."

- If human approval is required:
  "Your address change request has been submitted for verification. We'll update you once it's approved."

# Use Case 04: Cancel Order

## Customer
Existing Customer

## User Message
"I want to cancel my order #78901."

## Intent
ORDER_MODIFICATION / CANCEL_ORDER

## Agent Needs To
1. Retrieve order #78901 from the order system.
2. Check the current order status.
3. If the order has already been delivered, inform the customer that it cannot be cancelled.
4. If the order has already been shipped, check the company's cancellation policy.
5. If the order is eligible for cancellation, verify the customer's identity.
6. Request human approval if required by company policy.
7. Cancel the order using the Order Management Tool.
8. Confirm the cancellation to the customer.

## Tool / System Needed
Order Management Tool / Database
Customer Verification
Human Approval (if required)

## Expected Result
The system successfully cancels order #78901 if the order is eligible for cancellation.

## Final Response
"Your order #78901 has been successfully cancelled."

## Failure Cases
- If the order cannot be cancelled:
  "I'm sorry, but order #78901 can no longer be cancelled because it has already been shipped."

- If verification fails:
  "I'm unable to verify your identity, so I can't cancel the order."

- If the cancellation fails:
  "I wasn't able to cancel your order at this time. I'll connect you with our support team."

# Use Case 05: Product Availability

## Customer
New Customer

## User Message
"Do you have the iPhone 15 Pro 256GB in stock?"

## Intent
PRODUCT_INFORMATION / INVENTORY_CHECK

## Agent Needs To
1. Identify the requested product and variant.
2. Search the inventory system for the product.
3. Check the current stock quantity.
4. Return the current availability to the customer.
5. If the product is out of stock, provide the available alternative if one exists.

## Tool / System Needed
Inventory Management Tool / Database

## Expected Result
The system retrieves the current inventory information for the requested product.

Example:
"iPhone 15 Pro 256GB — 7 units available."

## Final Response
"Yes, the iPhone 15 Pro 256GB is currently in stock. We have 7 units available."

## Failure Cases
- If the product is out of stock:
  "The iPhone 15 Pro 256GB is currently out of stock."

- If the product cannot be found:
  "I couldn't find that product in our inventory. Could you please check the product name or model?"

- If the inventory system is unavailable:
  "I'm unable to check the current stock right now. Please try again shortly."

Task	AI/LLM?
Understand customer message	✅
Determine intent	✅
Search knowledge	Partially
Query database	❌ Tool/backend
Check authorization	❌ Normal code
Create ticket	❌ Tool/backend
Apply business rules	❌ Normal code
Generate natural-language answer	✅
Store conversation	❌ Database
Authentication	❌ Normal code


                 Customer
                    ↓
                Frontend
                    ↓
                 FastAPI
                    ↓
              Agent Layer
             /     |      \
            ↓      ↓       ↓
          RAG    Tools   Memory
           ↓       ↓       ↓
      Vector DB  APIs   PostgreSQL
             \     |     /
              \    |    /
                 LLM
                  ↓
              Validator
                  ↓
               Response


Version 1
User
 ↓
FastAPI
 ↓
LLM
 ↓
Answer

Version 2
User
 ↓
FastAPI
 ↓
LLM + RAG
 ↓
Answer

Version 3
User
 ↓
Agent
 ↓
RAG + Order Tool
 ↓
Answer

Version 4
Agent
 ↓
RAG
 ↓
Order Tool
 ↓
Ticket Tool
 ↓
Human Escalation


Version 5
Production System
 ↓
Authentication
 ↓
Validation
 ↓
Evaluation
 ↓
Tracing
 ↓
Security
 ↓
Docker
 ↓
Deployment