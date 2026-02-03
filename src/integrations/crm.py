"""
CRM integration interface for syncing lead data.

Supports multiple CRM providers:
- Notion
- HubSpot
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel


class CRMContact(BaseModel):
    """CRM contact model."""
    contact_id: str
    email: Optional[str]
    phone_number: str
    name: Optional[str]
    company: Optional[str]
    properties: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class CRMDeal(BaseModel):
    """CRM deal/opportunity model."""
    deal_id: str
    contact_id: str
    title: str
    amount: Optional[float]
    stage: str
    probability: Optional[float]
    close_date: Optional[datetime]
    properties: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class CRMNote(BaseModel):
    """CRM note/activity model."""
    note_id: str
    contact_id: str
    content: str
    note_type: str  # call, email, meeting, note
    created_at: datetime


class CRMIntegration(ABC):
    """Abstract base class for CRM integrations."""

    @abstractmethod
    async def create_contact(
        self,
        phone_number: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> CRMContact:
        """
        Create a contact in the CRM.

        Args:
            phone_number: Contact phone number
            email: Contact email (optional)
            name: Contact name (optional)
            properties: Additional contact properties

        Returns:
            Created CRM contact
        """
        pass

    @abstractmethod
    async def get_contact(
        self,
        phone_number: Optional[str] = None,
        email: Optional[str] = None,
        contact_id: Optional[str] = None
    ) -> Optional[CRMContact]:
        """
        Get a contact from the CRM.

        Args:
            phone_number: Contact phone number (optional)
            email: Contact email (optional)
            contact_id: Contact ID (optional)

        Returns:
            CRM contact or None if not found
        """
        pass

    @abstractmethod
    async def update_contact(
        self,
        contact_id: str,
        properties: Dict[str, Any]
    ) -> CRMContact:
        """
        Update a contact in the CRM.

        Args:
            contact_id: Contact ID
            properties: Properties to update

        Returns:
            Updated CRM contact
        """
        pass

    @abstractmethod
    async def create_deal(
        self,
        contact_id: str,
        title: str,
        amount: Optional[float] = None,
        stage: str = "new",
        properties: Optional[Dict[str, Any]] = None
    ) -> CRMDeal:
        """
        Create a deal/opportunity in the CRM.

        Args:
            contact_id: Associated contact ID
            title: Deal title
            amount: Deal amount (optional)
            stage: Deal stage
            properties: Additional deal properties

        Returns:
            Created CRM deal
        """
        pass

    @abstractmethod
    async def update_deal(
        self,
        deal_id: str,
        properties: Dict[str, Any]
    ) -> CRMDeal:
        """
        Update a deal in the CRM.

        Args:
            deal_id: Deal ID
            properties: Properties to update

        Returns:
            Updated CRM deal
        """
        pass

    @abstractmethod
    async def add_note(
        self,
        contact_id: str,
        content: str,
        note_type: str = "note"
    ) -> CRMNote:
        """
        Add a note/activity to a contact.

        Args:
            contact_id: Contact ID
            content: Note content
            note_type: Type of note (call, email, meeting, note)

        Returns:
            Created CRM note
        """
        pass

    @abstractmethod
    async def sync_lead_data(
        self,
        lead_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Sync lead data to CRM.

        This is a convenience method that creates/updates contact,
        creates deal if needed, and adds conversation notes.

        Args:
            lead_data: Complete lead data including:
                - phone_number
                - email (optional)
                - name (optional)
                - project_type
                - budget
                - timeline
                - score
                - conversation_summary

        Returns:
            Sync result with contact_id and deal_id
        """
        pass
