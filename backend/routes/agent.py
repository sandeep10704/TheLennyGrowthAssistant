from fastapi import APIRouter, Depends, status
from models.schemas import AgentRouterRequest, AgentRouterResponse
from services.agent_router import AgentRouter, get_agent_router

router = APIRouter(tags=["Agent Router"])


@router.post(
    "/router",
    response_model=AgentRouterResponse,
    status_code=status.HTTP_200_OK,
    summary="Agent Intent Router",
    description=(
        "Classifies user intent and routes to the appropriate generator:\n"
        "- Question -> RAG Answer Generator (`type: 'answer'`)\n"
        "- 'write article' -> Essay Generator (`type: 'essay'`)\n"
        "- 'create page' -> Artifact Generator (`type: 'artifact'`)\n\n"
        "Returns structured output: `{ 'type': 'answer' | 'essay' | 'artifact', 'data': ... }`"
    ),
)
async def route_agent_request(
    request: AgentRouterRequest,
    agent_router: AgentRouter = Depends(get_agent_router),
):
    """
    Execute user prompt through the Agent Router:
    1. Classifies intent: 'answer', 'essay', or 'artifact'
    2. Executes the corresponding specialized generation pipeline
    3. Returns structured payload: `{ 'type': ..., 'data': ... }`
    """
    return await agent_router.route_and_execute(request)
