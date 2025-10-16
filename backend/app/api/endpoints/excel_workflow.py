"""
Excel workflow API endpoints for Monte Carlo simulation integration.

Provides complete workflow:
1. Upload Excel → Parse → Simulate → Save
2. Download Excel with Monte Carlo results
3. Download blank or sample templates
"""

import io
from datetime import date, datetime
from typing import Dict
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_auth
from app.database.connection import get_db
from app.schemas.excel_workflow import ExcelSimulationResponse
from app.services.excel_generation_service import ExcelGenerationService
from app.services.excel_parser_service import ExcelParseError, ExcelParserService
from app.services.scheduler.distributions import TriangularDistribution
from app.services.simulation_persistence_service import SimulationPersistenceService
from app.services.simulation_service import SimulationError, SimulationService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/excel", tags=["excel_workflow"])

# File upload limits
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_CONTENT_TYPES = [
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "application/vnd.ms-excel",  # .xls
]


@router.post(
    "/projects/{project_id}/simulate",
    response_model=ExcelSimulationResponse,
    summary="Upload Excel and run Monte Carlo simulation",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Simulation completed successfully"},
        400: {"description": "Bad Request - Invalid Excel format or parsing error"},
        401: {"description": "Unauthorized - Authentication required"},
        413: {"description": "Payload Too Large - File exceeds 10MB"},
        415: {"description": "Unsupported Media Type - Not an Excel file"},
        422: {"description": "Validation Error - Data validation failed"},
        500: {"description": "Internal Server Error - Simulation execution failed"},
    },
)
async def upload_excel_and_simulate(
    project_id: UUID,
    file: UploadFile = File(..., description="Excel file (.xlsx) with task data"),
    iterations: int = Query(
        10000, ge=100, le=100000, description="Monte Carlo iterations"
    ),
    project_start_date: date = Query(
        ..., description="Project start date (YYYY-MM-DD)"
    ),
    user_info: Dict = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> ExcelSimulationResponse:
    """
    Upload Excel file with tasks, parse, run simulation, return results.

    Workflow:
    1. Validate uploaded file (size, type)
    2. Parse Excel with ExcelParserService
    3. Run simulation with SimulationService
    4. Save results to database
    5. Return simulation results with download link

    Args:
        project_id: UUID of the project
        file: Uploaded Excel file
        iterations: Number of Monte Carlo iterations (100-100000)
        project_start_date: Project start date
        user_info: Authenticated user info from JWT
        db: Database session

    Returns:
        ExcelSimulationResponse with simulation results and download URL

    Raises:
        HTTPException: Various status codes for different error conditions
    """
    user_id = UUID(user_info.get("sub"))

    logger.info(
        "Excel upload and simulation requested",
        project_id=str(project_id),
        user_id=str(user_id),
        filename=file.filename,
        iterations=iterations,
    )

    # Step 1: Validate file size
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        logger.warning(
            "File too large",
            size_bytes=len(file_content),
            max_size=MAX_FILE_SIZE,
            filename=file.filename,
        )
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({len(file_content)} bytes) exceeds maximum allowed size ({MAX_FILE_SIZE} bytes)",
        )

    # Step 2: Validate file type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        logger.warning(
            "Invalid file type",
            content_type=file.content_type,
            filename=file.filename,
        )
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. Expected Excel file (.xlsx or .xls)",
        )

    try:
        # Step 3: Parse Excel file
        parser_service = ExcelParserService()
        parsed_data = parser_service.parse_excel_file(file_content, file.filename)

        logger.info(
            "Excel parsed successfully",
            task_count=len(parsed_data.tasks),
            filename=file.filename,
        )

        # Step 4: Validate task structure
        validation_errors = parser_service.validate_task_structure(parsed_data.tasks)
        if validation_errors:
            logger.warning(
                "Excel validation errors",
                errors=validation_errors,
                filename=file.filename,
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"validation_errors": validation_errors},
            )

        # Step 5: Convert tasks to simulation input
        task_distribution_inputs = parser_service.convert_to_distribution_input(
            parsed_data.tasks
        )

        # Step 6: Create duration sampler using triangular distribution
        # Build a map of task_id -> distribution parameters
        task_params = {
            task.task_id: (task.optimistic, task.most_likely, task.pessimistic)
            for task in parsed_data.tasks
        }

        def duration_sampler(task_id: str) -> float:
            """Sample duration from triangular distribution."""
            params = task_params.get(task_id)
            if params is None:
                raise ValueError(f"Unknown task: {task_id}")

            optimistic, most_likely, pessimistic = params
            dist = TriangularDistribution(optimistic, most_likely, pessimistic)
            return dist.sample()

        # Step 7: Run Monte Carlo simulation
        simulation_service = SimulationService()

        try:
            simulation_result = simulation_service.run_simulation(
                tasks=task_distribution_inputs,
                project_start=project_start_date,
                duration_sampler=duration_sampler,
                iterations=iterations,
                percentiles=[10, 50, 90, 95, 99],
            )

            logger.info(
                "Simulation completed",
                mean_duration=simulation_result.mean_duration,
                iterations=simulation_result.iterations_run,
                task_count=simulation_result.task_count,
            )

        except SimulationError as e:
            logger.error("Simulation failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Simulation failed: {str(e)}",
            )

        # Step 8: Save simulation results to database
        persistence_service = SimulationPersistenceService()

        simulation_id = await persistence_service.save_simulation_result(
            db=db,
            project_id=project_id,
            user_id=user_id,
            iterations=simulation_result.iterations_run,
            task_count=simulation_result.task_count,
            project_start_date=project_start_date,
            mean_duration=simulation_result.mean_duration,
            median_duration=simulation_result.median_duration,
            std_deviation=simulation_result.std_deviation,
            confidence_intervals=simulation_result.confidence_intervals,
        )

        logger.info(
            "Simulation result saved",
            simulation_id=simulation_id,
            project_id=str(project_id),
        )

        # Step 9: Build response
        download_url = f"/api/v1/simulations/{simulation_id}/excel"

        return ExcelSimulationResponse(
            simulation_id=simulation_id,
            project_id=str(project_id),
            project_duration_days=simulation_result.project_duration_days,
            confidence_intervals=simulation_result.confidence_intervals,
            mean_duration=simulation_result.mean_duration,
            median_duration=simulation_result.median_duration,
            iterations_run=simulation_result.iterations_run,
            task_count=simulation_result.task_count,
            download_url=download_url,
            created_at=simulation_result.simulation_date,
        )

    except ExcelParseError as e:
        logger.error("Excel parsing failed", error=str(e), filename=file.filename)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Excel parsing failed: {str(e)}",
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            "Unexpected error during Excel workflow",
            error=str(e),
            filename=file.filename,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process Excel file and run simulation",
        )


@router.get(
    "/simulations/{simulation_id}/excel",
    response_class=StreamingResponse,
    summary="Download Excel file with Monte Carlo results",
    responses={
        200: {
            "description": "Excel file with simulation results",
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}
            },
        },
        401: {"description": "Unauthorized - Authentication required"},
        404: {"description": "Not Found - Simulation ID does not exist"},
        500: {"description": "Internal Server Error - Excel generation failed"},
    },
)
async def download_simulation_excel(
    simulation_id: int,
    user_info: Dict = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Generate and download Excel file with Monte Carlo results.

    Creates enhanced Excel file with:
    - Original task list (if available)
    - Monte Carlo results sheet
    - PERT formulas
    - Professional formatting

    Args:
        simulation_id: Simulation result ID
        user_info: Authenticated user info from JWT
        db: Database session

    Returns:
        StreamingResponse with Excel file

    Raises:
        HTTPException: 404 if simulation not found, 500 if generation fails
    """
    user_id = UUID(user_info.get("sub"))

    logger.info(
        "Excel download requested",
        simulation_id=simulation_id,
        user_id=str(user_id),
    )

    try:
        # Step 1: Retrieve simulation result from database
        persistence_service = SimulationPersistenceService()
        simulation_result = await persistence_service.get_simulation_result(
            db=db, simulation_id=simulation_id
        )

        if simulation_result is None:
            logger.warning(
                "Simulation not found",
                simulation_id=simulation_id,
                user_id=str(user_id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Simulation {simulation_id} not found",
            )

        # Step 2: Generate Excel with results
        generation_service = ExcelGenerationService()

        # Create base workbook with task list
        workbook = generation_service.create_template_workbook(
            project_name=f"Project {simulation_result.project_id}",
            include_sample_data=False,
        )

        # Convert SimulationResult DB model to service model
        from app.services.simulation_service import (
            SimulationResult as ServiceSimulationResult,
        )

        service_result = ServiceSimulationResult(
            project_duration_days=simulation_result.mean_duration,
            confidence_intervals=simulation_result.confidence_intervals,
            mean_duration=simulation_result.mean_duration,
            median_duration=simulation_result.median_duration,
            std_deviation=simulation_result.std_deviation,
            iterations_run=simulation_result.iterations,
            simulation_date=simulation_result.created_at,
            task_count=simulation_result.task_count,
        )

        # Add Monte Carlo results sheet
        generation_service.add_monte_carlo_results_sheet(
            workbook=workbook,
            simulation_result=service_result,
            tasks=[],  # Task data not stored in DB yet
            critical_path=[],  # Critical path analysis not implemented yet
        )

        # Apply professional formatting
        generation_service.apply_formatting(workbook)

        # Convert to bytes
        excel_bytes = generation_service.save_workbook_to_bytes(workbook)

        logger.info(
            "Excel generated successfully",
            simulation_id=simulation_id,
            size_bytes=len(excel_bytes),
        )

        # Step 3: Return as streaming response
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"monte_carlo_results_{simulation_id}_{timestamp}.xlsx"

        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-cache, no-store, must-revalidate",
            },
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            "Failed to generate Excel with results",
            simulation_id=simulation_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate Excel file with simulation results",
        )


@router.get(
    "/template",
    response_class=StreamingResponse,
    summary="Download blank Excel template",
    responses={
        200: {
            "description": "Excel template file",
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}
            },
        },
        401: {"description": "Unauthorized - Authentication required"},
        500: {"description": "Internal Server Error - Template generation failed"},
    },
)
async def download_excel_template(
    include_sample_data: bool = Query(False, description="Include sample task data"),
    user_info: Dict = Depends(require_auth),
) -> StreamingResponse:
    """
    Download Excel template for task entry.

    Provides blank or sample-filled template for users to:
    - Enter task information
    - Specify PERT estimates (optimistic, most likely, pessimistic)
    - Define task dependencies
    - Upload for Monte Carlo simulation

    Args:
        include_sample_data: Whether to include sample tasks
        user_info: Authenticated user info from JWT

    Returns:
        StreamingResponse with Excel template

    Raises:
        HTTPException: 500 if template generation fails
    """
    user_id = UUID(user_info.get("sub"))

    logger.info(
        "Template download requested",
        user_id=str(user_id),
        include_sample_data=include_sample_data,
    )

    try:
        # Generate template
        generation_service = ExcelGenerationService()

        workbook = generation_service.create_template_workbook(
            project_name="My Project",
            include_sample_data=include_sample_data,
        )

        # Apply formatting
        generation_service.apply_formatting(workbook)

        # Convert to bytes
        excel_bytes = generation_service.save_workbook_to_bytes(workbook)

        logger.info(
            "Template generated successfully",
            user_id=str(user_id),
            size_bytes=len(excel_bytes),
            has_sample_data=include_sample_data,
        )

        # Return as streaming response
        template_type = "sample" if include_sample_data else "blank"
        filename = f"monte_carlo_template_{template_type}.xlsx"

        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-cache, no-store, must-revalidate",
            },
        )

    except Exception as e:
        logger.error(
            "Failed to generate template",
            user_id=str(user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate Excel template",
        )
