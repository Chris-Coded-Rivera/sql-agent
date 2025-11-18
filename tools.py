
from langchain_community.utilities import SQLDatabase
from langchain.tools import tool
from langgraph.runtime import get_runtime
from dataclasses import dataclass

@dataclass
class RuntimeContext:
    db: SQLDatabase

# Defining sql execution tool
@tool("execute_sql", description="Execute SQLite commands and return results")
def execute_sql(query: str) -> str:
    """Execute SQLite command and return results."""
    runtime = get_runtime(RuntimeContext)
    db = runtime.context.db

    try:
        return db.run(query)
    except Exception as e:
        return f"Error: {e}"
