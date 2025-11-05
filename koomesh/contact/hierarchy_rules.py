"""
Hierarchy-Based Contact Rules
==============================

This module implements rules for determining contact types based on
assembly hierarchy relationships.

Rules:
- Same parent (siblings) → Tied contact
- Parent-child → Tied contact
- Different assemblies → Surface contact
- Large level difference → Automatic contact

Usage:
    >>> from koomesh.contact.hierarchy_rules import HierarchyRules
    >>> rules = HierarchyRules()
    >>> contact_type = rules.determine_contact_type(node1, node2)
"""

import logging
from typing import Optional, Dict, List
from koomesh.io.hierarchy_parser import HierarchyNode
from koomesh.contact.contact_data import ContactType, ContactPair


class HierarchyRules:
    """
    Hierarchy-based contact type determination

    This class implements rules to automatically determine appropriate
    contact types based on the hierarchical relationship between parts.

    Rules Configuration:
        sibling_type: Contact type for sibling parts
        parent_child_type: Contact type for parent-child relationship
        different_assembly_type: Contact type for different assemblies
        level_diff_threshold: Level difference for automatic contact
        same_level_type: Contact type for parts at same level

    Example:
        >>> rules = HierarchyRules()
        >>> contact_type = rules.determine_contact_type(node1, node2)
        >>> print(f"Contact type: {contact_type.value}")
    """

    def __init__(self):
        """Initialize hierarchy rules with default settings"""
        self.logger = logging.getLogger(__name__)

        # Default rule configuration
        self.rules = {
            'sibling': ContactType.TIED,
            'parent_child': ContactType.TIED,
            'different_assembly': ContactType.SURFACE_TO_SURFACE,
            'same_level': ContactType.SURFACE_TO_SURFACE,
            'level_diff_2_or_more': ContactType.AUTOMATIC,
        }

        # Thresholds
        self.level_diff_threshold = 2

    def determine_contact_type(self,
                               node1: HierarchyNode,
                               node2: HierarchyNode) -> ContactType:
        """
        Determine contact type based on hierarchy relationship

        Args:
            node1: First hierarchy node
            node2: Second hierarchy node

        Returns:
            Appropriate ContactType for this pair

        Example:
            >>> type = rules.determine_contact_type(part1_node, part2_node)
        """
        # Check relationship type
        relationship = self._determine_relationship(node1, node2)

        self.logger.debug(
            f"Relationship between '{node1.name}' and '{node2.name}': {relationship}"
        )

        # Apply rules based on relationship
        if relationship == 'sibling':
            return self.rules['sibling']

        elif relationship == 'parent_child':
            return self.rules['parent_child']

        elif relationship == 'same_level':
            return self.rules['same_level']

        elif relationship == 'different_assembly':
            return self.rules['different_assembly']

        elif relationship == 'large_level_diff':
            return self.rules['level_diff_2_or_more']

        else:
            # Default to surface-to-surface
            return ContactType.SURFACE_TO_SURFACE

    def _determine_relationship(self,
                               node1: HierarchyNode,
                               node2: HierarchyNode) -> str:
        """
        Determine hierarchical relationship between two nodes

        Returns:
            Relationship type string:
            - 'sibling': Same parent
            - 'parent_child': One is parent of the other
            - 'same_level': Same depth level
            - 'different_assembly': Different root assemblies
            - 'large_level_diff': Large difference in levels
            - 'unknown': Cannot determine
        """
        # Check for parent-child relationship
        if self._is_parent_child(node1, node2):
            return 'parent_child'

        # Check for sibling relationship
        if self._is_sibling(node1, node2):
            return 'sibling'

        # Check level difference
        level_diff = abs(node1.level - node2.level)
        if level_diff >= self.level_diff_threshold:
            return 'large_level_diff'

        # Check if same level
        if node1.level == node2.level:
            # Check if same assembly
            if self._same_assembly(node1, node2):
                return 'same_level'
            else:
                return 'different_assembly'

        # Default
        return 'unknown'

    def _is_sibling(self, node1: HierarchyNode, node2: HierarchyNode) -> bool:
        """Check if nodes are siblings (same parent)"""
        return (node1.parent is not None and
                node2.parent is not None and
                node1.parent == node2.parent)

    def _is_parent_child(self, node1: HierarchyNode, node2: HierarchyNode) -> bool:
        """Check if one node is parent of the other"""
        return node1.parent == node2 or node2.parent == node1

    def _same_assembly(self, node1: HierarchyNode, node2: HierarchyNode) -> bool:
        """Check if nodes belong to same top-level assembly"""
        root1 = self._get_root(node1)
        root2 = self._get_root(node2)
        return root1 == root2

    def _get_root(self, node: HierarchyNode) -> HierarchyNode:
        """Get root node of hierarchy"""
        current = node
        while current.parent is not None:
            current = current.parent
        return current

    def apply_rules_to_contact(self,
                               contact: ContactPair,
                               node1: HierarchyNode,
                               node2: HierarchyNode):
        """
        Apply hierarchy rules to update contact pair

        Modifies contact in place based on hierarchy rules.

        Args:
            contact: Contact pair to update
            node1: First hierarchy node
            node2: Second hierarchy node
        """
        # Determine contact type from hierarchy
        contact_type = self.determine_contact_type(node1, node2)

        # Update contact type
        contact.contact_type = contact_type

        # Set friction based on contact type
        if contact_type == ContactType.TIED:
            contact.friction = 0.0  # No friction for tied contacts
        elif contact_type == ContactType.SURFACE_TO_SURFACE:
            contact.friction = 0.0  # Default no friction, user can override
        elif contact_type == ContactType.AUTOMATIC:
            contact.friction = 0.3  # Default friction for automatic contact

        # Store relationship info in metadata
        relationship = self._determine_relationship(node1, node2)
        contact.metadata['hierarchy_relationship'] = relationship
        contact.metadata['level_diff'] = abs(node1.level - node2.level)

        self.logger.debug(
            f"Applied rules: {node1.name} <-> {node2.name} → {contact_type.value}"
        )

    def configure_rule(self, rule_name: str, contact_type: ContactType):
        """
        Configure a specific rule

        Args:
            rule_name: Rule name ('sibling', 'parent_child', etc.)
            contact_type: ContactType to use for this rule

        Example:
            >>> rules.configure_rule('sibling', ContactType.SURFACE_TO_SURFACE)
        """
        if rule_name in self.rules:
            self.rules[rule_name] = contact_type
            self.logger.info(f"Configured rule '{rule_name}' → {contact_type.value}")
        else:
            self.logger.warning(f"Unknown rule name: {rule_name}")

    def set_level_diff_threshold(self, threshold: int):
        """
        Set threshold for level difference

        Args:
            threshold: Minimum level difference for 'large_level_diff' rule
        """
        self.level_diff_threshold = threshold
        self.logger.info(f"Set level_diff_threshold = {threshold}")

    def get_rules_summary(self) -> Dict[str, str]:
        """
        Get summary of current rules

        Returns:
            Dictionary mapping rule names to contact types
        """
        return {
            name: contact_type.value
            for name, contact_type in self.rules.items()
        }

    def print_rules(self):
        """Print current rules configuration"""
        print("\nHierarchy-Based Contact Rules:")
        print("=" * 60)

        for rule_name, contact_type in self.rules.items():
            print(f"  {rule_name:.<40} {contact_type.value}")

        print(f"\n  Level difference threshold: {self.level_diff_threshold}")
        print("=" * 60)


class ContactRuleEngine:
    """
    Contact rule engine with customizable rules

    This class provides a more advanced rule system with user-defined rules.

    Example:
        >>> engine = ContactRuleEngine()
        >>> engine.add_rule(lambda n1, n2: n1.level == n2.level,
        ...                ContactType.TIED, priority=10)
    """

    def __init__(self):
        """Initialize rule engine"""
        self.rules: List[Dict] = []
        self.default_type = ContactType.SURFACE_TO_SURFACE
        self.logger = logging.getLogger(__name__)

    def add_rule(self,
                condition,
                contact_type: ContactType,
                priority: int = 0,
                name: Optional[str] = None):
        """
        Add a custom rule

        Args:
            condition: Function that takes (node1, node2) and returns bool
            contact_type: ContactType to use if condition is true
            priority: Rule priority (higher = checked first)
            name: Optional rule name

        Example:
            >>> engine.add_rule(
            ...     lambda n1, n2: 'bolt' in n1.name.lower(),
            ...     ContactType.TIED,
            ...     priority=100,
            ...     name='bolt_rule'
            ... )
        """
        rule = {
            'condition': condition,
            'contact_type': contact_type,
            'priority': priority,
            'name': name or f'rule_{len(self.rules)}'
        }

        self.rules.append(rule)

        # Sort rules by priority (descending)
        self.rules.sort(key=lambda r: r['priority'], reverse=True)

        self.logger.info(
            f"Added rule '{rule['name']}' with priority {priority} → {contact_type.value}"
        )

    def evaluate(self,
                node1: HierarchyNode,
                node2: HierarchyNode) -> ContactType:
        """
        Evaluate all rules to determine contact type

        Args:
            node1, node2: Hierarchy nodes

        Returns:
            ContactType based on first matching rule
        """
        # Try each rule in priority order
        for rule in self.rules:
            try:
                if rule['condition'](node1, node2):
                    self.logger.debug(
                        f"Rule '{rule['name']}' matched: "
                        f"{node1.name} <-> {node2.name} → {rule['contact_type'].value}"
                    )
                    return rule['contact_type']
            except Exception as e:
                self.logger.warning(
                    f"Error evaluating rule '{rule['name']}': {e}"
                )

        # No rule matched, use default
        return self.default_type

    def clear_rules(self):
        """Clear all rules"""
        self.rules.clear()
        self.logger.info("Cleared all rules")

    def num_rules(self) -> int:
        """Get number of rules"""
        return len(self.rules)


def create_default_rules() -> HierarchyRules:
    """
    Create default hierarchy rules

    Returns:
        HierarchyRules with standard configuration

    Example:
        >>> rules = create_default_rules()
    """
    rules = HierarchyRules()

    # Configure standard rules
    # Siblings and parent-child → tied (detail parts)
    rules.configure_rule('sibling', ContactType.TIED)
    rules.configure_rule('parent_child', ContactType.TIED)

    # Different assemblies → surface contact
    rules.configure_rule('different_assembly', ContactType.SURFACE_TO_SURFACE)

    # Same level but different assembly → surface contact
    rules.configure_rule('same_level', ContactType.SURFACE_TO_SURFACE)

    # Large level difference → automatic contact
    rules.configure_rule('level_diff_2_or_more', ContactType.AUTOMATIC)

    rules.set_level_diff_threshold(2)

    return rules
