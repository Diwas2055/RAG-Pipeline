from fastapi import APIRouter, HTTPException
from src.api.schemas import (
    TaskResponse,
    TaskStatusResponse,
    ProcessDataRequest,
    AddNumbersRequest,
    DivideNumbersRequest,
    ChainCalculationRequest,
    ParallelCalculationRequest,
)
from src.api.dependencies import get_task_result
from src.tasks.basic_tasks import (
    process_data_task,
    add_numbers_task,
    divide_numbers_task,
    aggregate_results_task,
)
from src.core.queues import (
    AVAILABLE_QUEUES,
    QUEUE_DESCRIPTIONS,
    TASK_ROUTES,
    get_queue_for_task,
)
from celery import chain, group, chord

router = APIRouter(prefix="/tasks", tags=["Task Management"])


@router.get("/info")
async def get_task_info():
    """Get information about available queues and registered tasks"""
    return {
        "queues": [
            {"name": queue, "description": QUEUE_DESCRIPTIONS.get(queue, "")}
            for queue in AVAILABLE_QUEUES
        ],
        "tasks": [
            {"name": task_name, "queue": queue}
            for task_name, queue in TASK_ROUTES.items()
        ],
    }


@router.post("/process", response_model=TaskResponse)
async def process_data(request: ProcessDataRequest):
    """Start a background task to process data"""
    queue = get_queue_for_task("tasks.process_data")
    task = process_data_task.apply_async(args=[request.data], queue=queue)
    return TaskResponse(task_id=task.id, status="Task started")


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Check the status of a background task"""
    task_result = get_task_result(task_id)
    if task_result.ready():
        return TaskStatusResponse(
            task_id=task_id, status="Completed", result=task_result.get()
        )
    return TaskStatusResponse(task_id=task_id, status="Pending")


@router.post("/calculate/add", response_model=TaskResponse)
async def add_numbers(request: AddNumbersRequest):
    """Add two numbers asynchronously (demo)"""
    queue = get_queue_for_task("tasks.add_numbers")
    task = add_numbers_task.apply_async(args=[request.x, request.y], queue=queue)
    return TaskResponse(task_id=task.id, status="Task submitted")


@router.post("/calculate/divide", response_model=TaskResponse)
async def divide_numbers(request: DivideNumbersRequest):
    """Divide two numbers asynchronously with retry logic (demo)"""
    queue = get_queue_for_task("tasks.divide_numbers")
    task = divide_numbers_task.apply_async(
        args=[request.dividend, request.divisor], queue=queue
    )
    return TaskResponse(task_id=task.id, status="Task submitted")


@router.post("/workflow/chain", response_model=TaskResponse)
async def execute_chain_workflow(request: ChainCalculationRequest):
    """Execute a chain of tasks: add(x, y) then divide by divisor (demo)"""
    queue = get_queue_for_task("tasks.add_numbers")
    task_chain = chain(
        add_numbers_task.s(request.x, request.y).set(queue=queue),
        divide_numbers_task.s(request.divisor).set(queue=queue),
    )
    result = task_chain.apply_async()
    return TaskResponse(task_id=result.id, status="Task chain submitted")


@router.post("/workflow/parallel", response_model=TaskResponse)
async def execute_parallel_workflow(request: ParallelCalculationRequest):
    """Execute parallel tasks and aggregate results: add(x, y) + divide(x, z) (demo)"""
    queue = get_queue_for_task("tasks.add_numbers")
    header = group(
        add_numbers_task.s(request.x, request.y).set(queue=queue),
        divide_numbers_task.s(request.x, request.z).set(queue=queue),
    )
    callback = aggregate_results_task.s().set(queue=queue)
    result = chord(header)(callback)
    return TaskResponse(task_id=result.id, status="Parallel workflow submitted")
