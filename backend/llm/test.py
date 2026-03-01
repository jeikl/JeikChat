import os
from volcenginesdkarkruntime import Ark
from volcenginesdkarkruntime.types.responses.response_completed_event import ResponseCompletedEvent
from volcenginesdkarkruntime.types.responses.response_reasoning_summary_text_delta_event import ResponseReasoningSummaryTextDeltaEvent
from volcenginesdkarkruntime.types.responses.response_output_item_added_event import ResponseOutputItemAddedEvent
from volcenginesdkarkruntime.types.responses.response_text_delta_event import ResponseTextDeltaEvent
from volcenginesdkarkruntime.types.responses.response_text_done_event import ResponseTextDoneEvent

# Get API Key：https://console.volcengine.com/ark/region:ark+cn-beijing/apikey
api_key = "6246ef67-931a-4f19-9409-89b42fc04a91"

client = Ark(
    base_url='https://ark.cn-beijing.volces.com/api/v3',
    api_key=api_key,
)

# Create a request
response = client.responses.create(
    model="doubao-seed-1-6-251015",
    input="常见的十字花科植物有哪些？",
    stream=True
)

for event in response:
    if isinstance(event, ResponseReasoningSummaryTextDeltaEvent):
        print(event.delta, end="")
    if isinstance(event, ResponseOutputItemAddedEvent):
        print("\noutPutItem " + event.type + " start:")
    if isinstance(event, ResponseTextDeltaEvent):
        print(event.delta,end="")
    if isinstance(event, ResponseTextDoneEvent):
        print("\noutPutTextDone.")
    if isinstance(event, ResponseCompletedEvent):
        print("Response Completed. Usage = " + event.response.usage.model_dump_json())