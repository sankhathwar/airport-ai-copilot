"""
Gemini tool configuration for the Airport Operations AI Copilot.

This module connects our application-level tool schemas
to the Gemini client configuration.
"""

import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.tool_schemas import TOOL_SCHEMAS


load_dotenv()

MODEL_NAME = "gemini-3.6-flash"


def create_gemini_client():
    """
    Create a Gemini client using the configured API key.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not configured."
        )

    return genai.Client(api_key=api_key)


def create_gemini_tools():
    """
    Convert our application tool schemas into
    Gemini-compatible function declarations.
    """

    function_declarations = []

    for tool in TOOL_SCHEMAS:
        function_declarations.append(
            types.FunctionDeclaration(
                name=tool["name"],
                description=tool["description"],
                parameters=tool["parameters"]
            )
        )

    return [
        types.Tool(
            function_declarations=function_declarations
        )
    ]