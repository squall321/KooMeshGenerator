"""
Contact Data Structures
========================

This module provides data structures for representing contact interfaces.

Structures:
- ContactType: Contact type enumeration
- ContactPair: Contact pair between two surfaces
- TiedContact: Tied (bonded) contact
- SurfaceContact: Surface-to-surface contact

Usage:
    >>> from koomesh.contact.contact_data import ContactPair, ContactType
    >>> pair = ContactPair(master_part="Part1", slave_part="Part2")
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Set
import numpy as np


class ContactType(Enum):
    """
    Contact type enumeration

    Contact types supported:
    - TIED: Completely bonded contact (no separation)
    - SURFACE_TO_SURFACE: General surface contact with friction
    - AUTOMATIC: Automatic contact detection
    - TIEBREAK: Breakable tied contact
    - ERODING: Contact that handles element erosion
    - RIGID_BODY: Contact with rigid body
    """
    TIED = "tied"
    SURFACE_TO_SURFACE = "surface_to_surface"
    AUTOMATIC = "automatic"
    TIEBREAK = "tiebreak"
    ERODING = "eroding"
    RIGID_BODY = "rigid_body"


@dataclass
class ContactSurface:
    """
    Contact surface definition

    Attributes:
        part_name: Name of the part
        part_id: Part ID
        element_ids: List of surface element IDs
        face_ids: List of face IDs (for hex/tet elements)
        node_ids: List of surface node IDs (optional)
        metadata: Additional surface data
    """
    part_name: str
    part_id: int
    element_ids: List[int] = field(default_factory=list)
    face_ids: List[int] = field(default_factory=list)
    node_ids: List[int] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

    def num_elements(self) -> int:
        """Get number of surface elements"""
        return len(self.element_ids)

    def num_nodes(self) -> int:
        """Get number of surface nodes"""
        return len(self.node_ids)


@dataclass
class ContactPair:
    """
    Contact pair between two surfaces

    Attributes:
        master_surface: Master surface
        slave_surface: Slave surface
        contact_type: Type of contact
        friction: Friction coefficient
        penalty_factor: Penalty stiffness factor
        gap: Initial gap distance
        metadata: Additional contact data
        id: Contact pair ID
    """
    master_surface: ContactSurface
    slave_surface: ContactSurface
    contact_type: ContactType = ContactType.SURFACE_TO_SURFACE
    friction: float = 0.0
    penalty_factor: float = 1.0
    gap: float = 0.0
    metadata: Dict = field(default_factory=dict)
    id: Optional[int] = None

    def __post_init__(self):
        """Initialize contact pair"""
        if self.id is None:
            # Auto-generate ID (to be set by contact manager)
            pass

    def is_tied(self) -> bool:
        """Check if contact is tied"""
        return self.contact_type == ContactType.TIED

    def is_frictional(self) -> bool:
        """Check if contact has friction"""
        return self.friction > 0

    def get_master_part(self) -> str:
        """Get master part name"""
        return self.master_surface.part_name

    def get_slave_part(self) -> str:
        """Get slave part name"""
        return self.slave_surface.part_name

    def reverse(self):
        """Reverse master and slave"""
        self.master_surface, self.slave_surface = self.slave_surface, self.master_surface

    def __repr__(self) -> str:
        return (f"ContactPair(master='{self.master_surface.part_name}', "
                f"slave='{self.slave_surface.part_name}', "
                f"type={self.contact_type.value})")


@dataclass
class TiedContact(ContactPair):
    """
    Tied (bonded) contact

    Tied contacts constrain slave nodes to master surface.
    No relative motion is allowed.

    Additional Attributes:
        constraint_type: Type of constraint ("node_to_surface", "surface_to_surface")
        tolerance: Distance tolerance for tying nodes
        node_constraints: List of (slave_node, master_weights) for each slave node
    """
    constraint_type: str = "surface_to_surface"
    tolerance: float = 1e-6
    node_constraints: List = field(default_factory=list)

    def __post_init__(self):
        """Initialize tied contact"""
        super().__post_init__()
        self.contact_type = ContactType.TIED

    def add_node_constraint(self, slave_node: int,
                           master_nodes: List[int],
                           weights: List[float]):
        """
        Add node constraint

        Constrains slave_node to master surface through weighted interpolation.

        Args:
            slave_node: Slave node ID
            master_nodes: List of master node IDs
            weights: Interpolation weights
        """
        self.node_constraints.append({
            'slave_node': slave_node,
            'master_nodes': master_nodes,
            'weights': weights
        })

    def num_constraints(self) -> int:
        """Get number of node constraints"""
        return len(self.node_constraints)


@dataclass
class SurfaceContact(ContactPair):
    """
    Surface-to-surface contact

    General surface contact with friction and optional separation.

    Additional Attributes:
        static_friction: Static friction coefficient
        dynamic_friction: Dynamic friction coefficient
        cohesion: Cohesion stress
        allow_separation: Allow surfaces to separate
        depth_of_penetration: Penetration tolerance
    """
    static_friction: float = 0.0
    dynamic_friction: float = 0.0
    cohesion: float = 0.0
    allow_separation: bool = True
    depth_of_penetration: float = 0.0

    def __post_init__(self):
        """Initialize surface contact"""
        super().__post_init__()
        if self.contact_type == ContactType.TIED:
            self.contact_type = ContactType.SURFACE_TO_SURFACE

        # Set dynamic friction from static if not specified
        if self.dynamic_friction == 0.0 and self.static_friction > 0:
            self.dynamic_friction = self.static_friction * 0.8


@dataclass
class AutomaticContact(ContactPair):
    """
    Automatic contact

    LS-DYNA automatic contact with self-contact and adaptive features.

    Additional Attributes:
        self_contact: Enable self-contact
        single_surface: Use single surface formulation
        thickness: Shell thickness for contact
        erosion: Handle element erosion
    """
    self_contact: bool = False
    single_surface: bool = False
    thickness: float = 0.0
    erosion: bool = False

    def __post_init__(self):
        """Initialize automatic contact"""
        super().__post_init__()
        self.contact_type = ContactType.AUTOMATIC


class ContactManager:
    """
    Contact manager for organizing contact pairs

    Manages multiple contact pairs and provides utility functions.

    Attributes:
        contacts: List of contact pairs
        next_id: Next contact ID

    Example:
        >>> manager = ContactManager()
        >>> manager.add_contact(contact_pair)
        >>> tied_contacts = manager.get_contacts_by_type(ContactType.TIED)
    """

    def __init__(self):
        """Initialize contact manager"""
        self.contacts: List[ContactPair] = []
        self.next_id = 1

    def add_contact(self, contact: ContactPair) -> int:
        """
        Add contact pair

        Args:
            contact: Contact pair to add

        Returns:
            Contact ID
        """
        if contact.id is None:
            contact.id = self.next_id
            self.next_id += 1

        self.contacts.append(contact)
        return contact.id

    def get_contact(self, contact_id: int) -> Optional[ContactPair]:
        """Get contact by ID"""
        for contact in self.contacts:
            if contact.id == contact_id:
                return contact
        return None

    def remove_contact(self, contact_id: int) -> bool:
        """Remove contact by ID"""
        for i, contact in enumerate(self.contacts):
            if contact.id == contact_id:
                del self.contacts[i]
                return True
        return False

    def get_contacts_by_type(self, contact_type: ContactType) -> List[ContactPair]:
        """Get all contacts of a specific type"""
        return [c for c in self.contacts if c.contact_type == contact_type]

    def get_contacts_by_parts(self, part1: str, part2: str) -> List[ContactPair]:
        """Get contacts between two parts"""
        contacts = []
        for c in self.contacts:
            if ((c.master_surface.part_name == part1 and c.slave_surface.part_name == part2) or
                (c.master_surface.part_name == part2 and c.slave_surface.part_name == part1)):
                contacts.append(c)
        return contacts

    def get_all_parts(self) -> Set[str]:
        """Get set of all parts involved in contacts"""
        parts = set()
        for contact in self.contacts:
            parts.add(contact.master_surface.part_name)
            parts.add(contact.slave_surface.part_name)
        return parts

    def num_contacts(self) -> int:
        """Get total number of contacts"""
        return len(self.contacts)

    def get_statistics(self) -> Dict:
        """
        Get contact statistics

        Returns:
            Dictionary with contact statistics
        """
        stats = {
            'total': self.num_contacts(),
            'by_type': {}
        }

        for contact_type in ContactType:
            count = len(self.get_contacts_by_type(contact_type))
            if count > 0:
                stats['by_type'][contact_type.value] = count

        stats['num_parts'] = len(self.get_all_parts())

        return stats

    def validate(self) -> bool:
        """
        Validate all contacts

        Returns:
            True if all contacts are valid
        """
        for contact in self.contacts:
            # Check that surfaces have elements
            if contact.master_surface.num_elements() == 0:
                raise ValueError(
                    f"Contact {contact.id}: Master surface has no elements"
                )

            if contact.slave_surface.num_elements() == 0:
                raise ValueError(
                    f"Contact {contact.id}: Slave surface has no elements"
                )

            # Check friction coefficient
            if contact.friction < 0:
                raise ValueError(
                    f"Contact {contact.id}: Friction coefficient cannot be negative"
                )

        return True

    def print_summary(self):
        """Print contact summary"""
        stats = self.get_statistics()

        print(f"\nContact Summary:")
        print(f"{'='*60}")
        print(f"Total Contacts: {stats['total']}")
        print(f"Parts Involved: {stats['num_parts']}")
        print(f"\nBy Type:")

        for contact_type, count in stats['by_type'].items():
            print(f"  {contact_type}: {count}")

        print(f"{'='*60}\n")

    def clear(self):
        """Clear all contacts"""
        self.contacts.clear()
        self.next_id = 1

    def __repr__(self) -> str:
        return f"ContactManager(contacts={len(self.contacts)})"
