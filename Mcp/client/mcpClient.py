
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client
import sys as sys
from datetime import timedelta
import json

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="python",  # Executable
    args=["mcpdemo.py"],  # Optional command line arguments
    env=None,  # Optional environment variables
)


# Optional: create a sampling callback
async def handle_sampling_message(
    message: types.CreateMessageRequestParams,
) -> types.CreateMessageResult:
    return types.CreateMessageResult(
        role="assistant",
        content=types.TextContent(
            type="text",
            text="Hello, world! from model",
        ),
        model="gpt-3.5-turbo",
        stopReason="endTurn",
    )


async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(
            read, write, sampling_callback=handle_sampling_message
        ) as session:
            # Initialize the connection
            await session.initialize()

            # # List available prompts
            # prompts = await session.list_prompts()

            # # Get a prompt
            # prompt = await session.get_prompt(
            #     "example-prompt", arguments={"arg1": "value"}
            # )

            # List available resources
            # resources = await session.list_resources()

            # List available tools
            tools = await session.list_tools()
            print(tools)

            # Read a resource
            # content, mime_type = await session.read_resource("file://some/path")

            # Call a tool
            # result = await session.call_tool("tool-name", arguments={"arg1": "value"})

class MCPClient:
    def __init__(self, name):
        self.tools = ''
        self.name = name
        pass

    async def connect_to_server(self, endpoint):
        self.endpoint = endpoint
        try:
            async with streamablehttp_client(endpoint, headers={"api_key": "IyMGI1ZDhjMTA2ZTExZjBiYTMyMGQ4Zm"}, timeout=timedelta(seconds=60*5), sse_read_timeout=timedelta(seconds=60*60)) as streams:
                async with ClientSession(
                    streams[0],
                    streams[1],
                ) as self.session:
                    await self.session.initialize()
                    self.tools = await self.session.list_tools()
                    return True
        except Exception as e:
            print(e)
        return False

    async def call_tools(self, name, arguments):
        try:
            async with streamablehttp_client(self.endpoint, headers={"api_key": "IyMGI1ZDhjMTA2ZTExZjBiYTMyMGQ4Zm"}, timeout=timedelta(seconds=60*5), sse_read_timeout=timedelta(seconds=60*60)) as streams:
                async with ClientSession(
                    streams[0],
                    streams[1],
                ) as self.session:
                    await self.session.initialize()
                    result = await self.session.call_tool(name, arguments=arguments)
                    if result.isError == True:
                        src = {
                            "Comment":result.content[0].text
                        }
                        return json.dumps(src)
                    else:
                        return result.content[0].text
        except Exception as e:
            src = {
                "Comment":str(e)
            }
            return json.dumps(src)

async def connect(mcp, endpoint):
    return await mcp.connect_to_server(endpoint)

async def call(mcp, name, arguments):
    return await mcp.call_tools(name, arguments)

def connect_sync(mcp, endpoint):
    from anyio import run
    return run(mcp.connect_to_server, endpoint)

def call_sync(mcp, name, arguments):
    from anyio import run
    return run(mcp.call_tools, name, arguments)

if __name__ == "__main__":
    mcp = MCPClient('name')
    from anyio import run
    run(mcp.connect_to_server)
    connect(mcp, 'http://10.10.90.15:8000/sse')
    print(mcp.tools)

