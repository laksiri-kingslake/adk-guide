from google.adk.agents.llm_agent import Agent

async def update_bigquery_api_count(
   tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext, tool_response: Dict)
  
   if tool.name in ["execute_sql"]:
       if tool_response.get("status") == "ERROR":
           failure_count = tool_context.state.get("bigquery_api_failure", 0)
           tool_context.state["bigquery_api_failure"] = failure_count + 1
   return None 

async def run_conversation_async(prompt: str):
   app_name="bigquery_chat_app"
   user_id="my_user_id"
   session_id = "session_001"

   session_service = InMemorySessionService()   
   session = await session_service.create_session(
       app_name=app_name,
       user_id=user_id,
       session_id=session_id
   )
   runner = Runner(
       agent=root_agent,
       app_name=app_name, 
       session_service=session_service
   )
  
   final_response = await call_agent_async(
       prompt=prompt, runner=runner, user_id=user_id, session_id=session_id
   )

async def call_agent_async(prompt: str, runner, user_id, session_id):
  content = types.Content(role='user', parts=[types.Part(text=prompt)])
  response = {"total_token_count": 0} 

  async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
         if event.content and event.content.parts:
             for content_part in event.content.parts:
                 if content_part.function_call:
                     function_call_details = content_part.function_call
                     tool_call_data = {
                         "tool_name": function_call_details.name,
                         "args": function_call_details.args,
                     }
         if event.usage_metadata:
             response["total_token_count"] += event.usage_metadata.total_token_count or 0

         if event.is_final_response():
             final_response_text = event.content.parts[0].text
             response["final_response_text"] = final_response_text
             break

         return response 

root_agent = Agent(
  model="gemini-2.0-flash",
  name="bigquery_agent_eval",
  description=(
    "Agent that answers questions about BigQuery data by executing SQL queries"
  ),
  instruction="""
    You are a data analysis agent with access to several BigQuery tools.
    Use the appropriate tools to retrieve BigQuery metadata and execute SQL queries in order to answer the users question.
    Run these queries in the project-id: <PROJECT ID>.
    ALL questions relate to data stored in the <DATASET> dataset.
  """,
  tools=[bigquery_toolset],

  after_tool_callback=update_bigquery_api_count
)


