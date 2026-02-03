from celery import Task
from datetime import datetime
from src.workers.celery_app import celery_app
from src.db.connection import get_db_session
from src.services.follow_up_scheduler import FollowUpScheduler
from src.repositories.lead_repository import LeadRepository
from src.integrations.whatsapp_client import get_whatsapp_client
from src.utils.logger import get_logger

logger = get_logger(__name__)


@celery_app.task(name="src.workers.follow_up_worker.check_scheduled_follow_ups")
def check_scheduled_follow_ups():
    """
    Periodic task to check and send scheduled follow-ups.
    Runs every minute via Celery Beat.
    """
    import asyncio
    asyncio.run(_check_and_send_follow_ups())


async def _check_and_send_follow_ups():
    """Check for due follow-ups and send them."""
    try:
        async with get_db_session() as session:
            scheduler = FollowUpScheduler(session)
            lead_repo = LeadRepository(session)
            whatsapp_client = get_whatsapp_client()

            # Get due follow-ups
            due_follow_ups = await scheduler.get_due_follow_ups()

            logger.info(f"Found {len(due_follow_ups)} due follow-ups")

            for follow_up in due_follow_ups:
                try:
                    # Get lead
                    lead = await lead_repo.get_by_id(follow_up.lead_id)
                    if not lead:
                        logger.warning(
                            "Lead not found for follow-up",
                            follow_up_id=str(follow_up.id)
                        )
                        continue

                    # Send follow-up message
                    await whatsapp_client.send_message(
                        lead.phone_number,
                        follow_up.message_content
                    )

                    # Mark as sent
                    await scheduler.mark_follow_up_sent(follow_up.id)

                    logger.info(
                        "Follow-up sent",
                        follow_up_id=str(follow_up.id),
                        lead_id=str(lead.id),
                        attempt=follow_up.attempt_number
                    )

                    # If not at max attempts and lead doesn't respond,
                    # next follow-up will be scheduled by the scheduler
                    # when this follow-up expires without response

                except Exception as e:
                    logger.error(
                        "Failed to send follow-up",
                        follow_up_id=str(follow_up.id),
                        error=str(e)
                    )

    except Exception as e:
        logger.error("Follow-up check failed", error=str(e))


@celery_app.task(name="src.workers.follow_up_worker.schedule_follow_up_task")
def schedule_follow_up_task(lead_id: str, scenario: str, attempt: int = 1):
    """
    Task to schedule a follow-up for a lead.

    Args:
        lead_id: Lead ID (string UUID)
        scenario: Follow-up scenario
        attempt: Attempt number
    """
    import asyncio
    from uuid import UUID
    from src.models.enums import FollowUpScenario

    asyncio.run(_schedule_follow_up(
        UUID(lead_id),
        FollowUpScenario(scenario),
        attempt
    ))


async def _schedule_follow_up(lead_id, scenario, attempt):
    """Schedule a follow-up."""
    try:
        async with get_db_session() as session:
            scheduler = FollowUpScheduler(session)
            await scheduler.schedule_follow_up(lead_id, scenario, attempt)

            logger.info(
                "Follow-up scheduled via task",
                lead_id=str(lead_id),
                scenario=scenario.value,
                attempt=attempt
            )

    except Exception as e:
        logger.error("Failed to schedule follow-up", error=str(e))
