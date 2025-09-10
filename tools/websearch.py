# Load environment variables from .env automatically
from langchain_tavily import TavilySearch
import os
from dotenv import load_dotenv

# Load .env file into environment variables
load_dotenv()

tavily_key = os.getenv("TAVILY_API_KEY")
if not tavily_key:
    raise ValueError("TAVILY_API_KEY is not set in .env file or environment.")

# Example: create Tavily search tool
tavily_tool = TavilySearch(
    max_results=5,
    tavily_api_key=tavily_key
)