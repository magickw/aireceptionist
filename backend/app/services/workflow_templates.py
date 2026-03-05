"""
Predefined workflow templates for common multi-step operations.
"""
from app.services.workflow_engine import WorkflowDefinition, WorkflowStep


def get_booking_workflow() -> WorkflowDefinition:
    """Full booking workflow: check availability -> book -> send SMS -> sync calendar."""
    return WorkflowDefinition(
        name="bookingWorkflow",
        description="Check availability, book appointment, send confirmation SMS, and sync calendar",
        steps=[
            WorkflowStep(
                name="checkAvailability",
                tool_name="checkAvailability",
                input_template={
                    "date": "${date}",
                    "time": "${time}",
                },
                output_variable="availability",
            ),
            WorkflowStep(
                name="bookAppointment",
                tool_name="bookAppointment",
                input_template={
                    "date": "${date}",
                    "time": "${time}",
                    "customer_name": "${customer_name}",
                    "customer_phone": "${customer_phone}",
                    "service": "${service}",
                },
                output_variable="booking",
                condition="${availability.available} == false",
                compensation_action="cancelAppointment",
                compensation_input_template={
                    "appointment_id": "${booking.appointment_id}",
                },
            ),
            WorkflowStep(
                name="sendConfirmationSMS",
                tool_name="sendConfirmationSMS",
                input_template={
                    "customer_phone": "${customer_phone}",
                    "message": "Your appointment for ${service} on ${date} at ${time} has been confirmed.",
                },
                required=False,
            ),
        ],
    )


def get_order_workflow() -> WorkflowDefinition:
    """Order workflow: place order -> confirm -> process payment."""
    return WorkflowDefinition(
        name="orderWorkflow",
        description="Place order, confirm it, and process payment",
        steps=[
            WorkflowStep(
                name="placeOrder",
                tool_name="placeOrder",
                input_template={
                    "items": "${items}",
                    "delivery_method": "${delivery_method}",
                },
                output_variable="order",
            ),
            WorkflowStep(
                name="confirmOrder",
                tool_name="confirmOrder",
                input_template={
                    "customer_name": "${customer_name}",
                    "customer_phone": "${customer_phone}",
                },
                output_variable="confirmation",
                compensation_action="cancelOrder",
                compensation_input_template={
                    "order_id": "${order.order_id}",
                },
            ),
            WorkflowStep(
                name="processPayment",
                tool_name="processPayment",
                input_template={
                    "amount": "${order.total_amount}",
                },
                output_variable="payment",
                compensation_action="refundPayment",
                compensation_input_template={
                    "payment_id": "${payment.payment_id}",
                },
                required=False,
            ),
        ],
    )


# Registry of available workflows
WORKFLOW_REGISTRY = {
    "bookingWorkflow": get_booking_workflow,
    "orderWorkflow": get_order_workflow,
}


def get_workflow(name: str) -> WorkflowDefinition:
    """Get a workflow definition by name."""
    factory = WORKFLOW_REGISTRY.get(name)
    if not factory:
        raise ValueError(f"Unknown workflow: {name}. Available: {list(WORKFLOW_REGISTRY.keys())}")
    return factory()
