"""
Calendar integration interface for scheduling calls with leads.

Supports multiple calendar providers:
- Google Calendar
- Calendly
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel


class CalendarEvent(BaseModel):
    """Calendar event model."""
    event_id: str
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    attendees: List[str]
    meeting_url: Optional[str]
    location: Optional[str]


class CalendarAvailability(BaseModel):
    """Calendar availability slot."""
    start_time: datetime
    end_time: datetime
    is_available: bool


class CalendarIntegration(ABC):
    """Abstract base class for calendar integrations."""

    @abstractmethod
    async def create_event(
        self,
        title: str,
        description: str,
        start_time: datetime,
        end_time: datetime,
        attendee_email: str,
        attendee_name: Optional[str] = None
    ) -> CalendarEvent:
        """
        Create a calendar event.

        Args:
            title: Event title
            description: Event description
            start_time: Event start time
            end_time: Event end time
            attendee_email: Attendee email address
            attendee_name: Attendee name (optional)

        Returns:
            Created calendar event
        """
        pass

    @abstractmethod
    async def get_event(self, event_id: str) -> Optional[CalendarEvent]:
        """
        Get a calendar event by ID.

        Args:
            event_id: Event ID

        Returns:
            Calendar event or None if not found
        """
        pass

    @abstractmethod
    async def update_event(
        self,
        event_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> CalendarEvent:
        """
        Update a calendar event.

        Args:
            event_id: Event ID
            title: New title (optional)
            description: New description (optional)
            start_time: New start time (optional)
            end_time: New end time (optional)

        Returns:
            Updated calendar event
        """
        pass

    @abstractmethod
    async def cancel_event(self, event_id: str) -> bool:
        """
        Cancel a calendar event.

        Args:
            event_id: Event ID

        Returns:
            True if cancelled successfully
        """
        pass

    @abstractmethod
    async def get_availability(
        self,
        start_date: datetime,
        end_date: datetime,
        duration_minutes: int = 30
    ) -> List[CalendarAvailability]:
        """
        Get available time slots.

        Args:
            start_date: Start date for availability check
            end_date: End date for availability check
            duration_minutes: Duration of the meeting in minutes

        Returns:
            List of available time slots
        """
        pass

    @abstractmethod
    async def send_meeting_invite(
        self,
        event_id: str,
        attendee_email: str,
        attendee_name: Optional[str] = None
    ) -> bool:
        """
        Send meeting invite to attendee.

        Args:
            event_id: Event ID
            attendee_email: Attendee email
            attendee_name: Attendee name (optional)

        Returns:
            True if invite sent successfully
        """
        pass
