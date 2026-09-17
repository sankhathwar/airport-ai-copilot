"""
Gemini function-calling demonstration.

Flow:

User query
    ↓
Gemini
    ↓
Function call
    ↓
Python executes tool
    ↓
Tool result
    ↓
Gemini
    ↓
Final answer
"""

from google.genai import types

from src.gemini_tools import (
    create_gemini_client,
    create_gemini_tools,
    MODEL_NAME,
)

from src.tools import execute_tool


def run_function_calling_demo(query: str):

    client = create_gemini_client()
    tools = create_gemini_tools()

    # --------------------------------------------------
    # STEP 1: Ask Gemini to understand the query
    # --------------------------------------------------

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=query,
        config={
            "tools": tools
        }
    )

    candidate = response.candidates[0]

    # --------------------------------------------------
    # STEP 2: Find the function call
    # --------------------------------------------------

    function_call = None

    for part in candidate.content.parts:
        if part.function_call:
            function_call = part.function_call
            break

    # Gemini may answer directly without using a tool
    if function_call is None:
        return {
            "status": "no_tool_call",
            "answer": response.text
        }

    # --------------------------------------------------
    # STEP 3: Extract function name + arguments
    # --------------------------------------------------

    tool_name = function_call.name
    arguments = dict(function_call.args)

    print("\nGemini selected tool:")
    print(tool_name)

    print("\nTool arguments:")
    print(arguments)

    # --------------------------------------------------
    # STEP 4: Execute tool locally
    # --------------------------------------------------

    tool_result = execute_tool(
        tool_name,
        arguments
    )

    print("\nTool result:")
    print(tool_result)

        # --------------------------------------------------
    # STEP 5: Send tool result back to Gemini
    # --------------------------------------------------

    tool_response_part = types.Part(
        function_response=types.FunctionResponse(
            name=tool_name,
            response=tool_result
        )
    )

    final_response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(text=query)
                ]
            ),

            # Gemini's previous response containing
            # the function call
            candidate.content,

            # Result returned by our Python tool
            types.Content(
                role="user",
                parts=[
                tool_response_part
            ]
            )
        ],
        config={
            "tools": tools
        }
    )

    # --------------------------------------------------
    # STEP 6: Return final answer
    # --------------------------------------------------

    return {
        "status": "success",
        "tool_name": tool_name,
        "arguments": arguments,
        "tool_result": tool_result,
        "final_answer": final_response.text
    }


if __name__ == "__main__":

    query = "What's happening at SFO?"

    result = run_function_calling_demo(query)

    print("\n==============================")
    print("FINAL ANSWER")
    print("==============================")

    print(result["final_answer"])