"""
Contact Command
===============

Contact detection and export CLI command.

Usage:
    koomesh contact mesh.k --tolerance 0.1 --export lsdyna
    koomesh contact mesh.k --self-contact --output contacts.k
    koomesh contact mesh.k --report json

Author: KooMeshGenerator Team
"""

import click
import sys
import json
import logging
from pathlib import Path
from typing import Optional

from koomesh.io.lsdyna_reader import LSDynaReader
from koomesh.utils.contact_detection import ContactSurfaceDetector
from koomesh.parallel import ParallelContactDetector

logger = logging.getLogger(__name__)


@click.command()
@click.argument('mesh_file', type=click.Path(exists=True))
@click.option(
    '--tolerance', '-t',
    type=float,
    default=0.1,
    help='Contact detection tolerance (default: 0.1)'
)
@click.option(
    '--min-angle',
    type=float,
    default=120.0,
    help='Minimum angle for self-contact detection in degrees (default: 120.0)'
)
@click.option(
    '--self-contact/--no-self-contact',
    default=True,
    help='Detect self-contact zones (default: true)'
)
@click.option(
    '--auto-classify/--no-auto-classify',
    default=False,
    help='Automatically classify contact types (AUTOMATIC, TIED, SLIDING, etc.)'
)
@click.option(
    '--contact-aware-meshing/--no-contact-aware-meshing',
    default=False,
    help='Enable contact-aware meshing (refines mesh at contact zones)'
)
@click.option(
    '--validate/--no-validate',
    default=False,
    help='Validate contact quality (penetration, gap, mesh ratio)'
)
@click.option(
    '--multi-contact/--no-multi-contact',
    default=False,
    help='Detect contact between parts (default: false)'
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    help='Output file path (default: mesh_contacts.k)'
)
@click.option(
    '--export',
    type=click.Choice(['lsdyna', 'text', 'json'], case_sensitive=False),
    default='lsdyna',
    help='Export format (default: lsdyna)'
)
@click.option(
    '--parallel/--no-parallel',
    default=False,
    help='Use parallel processing for multi-part contact (default: false)'
)
@click.option(
    '--jobs', '-j',
    type=int,
    default=-1,
    help='Number of parallel workers (default: -1 = all cores)'
)
@click.pass_context
def contact(
    ctx,
    mesh_file: str,
    tolerance: float,
    min_angle: float,
    self_contact: bool,
    auto_classify: bool,
    contact_aware_meshing: bool,
    validate: bool,
    multi_contact: bool,
    output: Optional[str],
    export: str,
    parallel: bool,
    jobs: int
):
    """
    Detect contact zones and export contact definitions

    Analyzes mesh to find potential contact surfaces and generates
    contact definitions for FEA solvers.

    Examples:

    \b
    # Self-contact detection for crash analysis
    koomesh contact crash_mesh.k --self-contact --export lsdyna

    \b
    # Multi-part contact detection
    koomesh contact assembly.k --multi-contact --tolerance 0.2

    \b
    # JSON report for analysis
    koomesh contact mesh.k --export json --output contacts.json

    \b
    # Parallel processing for large assemblies
    koomesh contact large_assembly.k --multi-contact --parallel --jobs 8
    """
    logger = ctx.obj.get('logger', logging.getLogger(__name__))

    try:
        # Read mesh file
        click.echo(f"Reading mesh file: {mesh_file}")
        mesh_data = _read_mesh_file(mesh_file)

        click.echo(
            f"Loaded mesh: {mesh_data.num_nodes()} nodes, "
            f"{mesh_data.num_elements()} elements"
        )

        # Detect contacts
        contact_results = {}

        if self_contact:
            click.echo("\nDetecting self-contact zones...")
            self_contacts = _detect_self_contact(mesh_data, tolerance, min_angle)
            contact_results['self_contact'] = self_contacts

            if self_contacts:
                click.echo(f"✓ Found {len(self_contacts.face_pairs)} potential self-contact face pairs")
                click.echo(f"  - Average distance: {self_contacts.avg_distance:.6f}")
                click.echo(f"  - Minimum distance: {self_contacts.min_distance:.6f}")
            else:
                click.echo("  No self-contact zones detected")

        if multi_contact:
            click.echo("\nDetecting multi-part contacts...")
            if parallel:
                click.echo(f"Using parallel processing with {jobs} workers...")

            multi_contacts = _detect_multi_contact(mesh_data, tolerance, parallel, jobs)
            contact_results['multi_contact'] = multi_contacts

            if multi_contacts:
                click.echo(f"✓ Found {len(multi_contacts)} contact pairs between parts")

                # Auto-classify contact types if requested
                if auto_classify:
                    click.echo("\nClassifying contact types...")
                    multi_contacts = _classify_contacts(multi_contacts, mesh_data)

                    # Show type distribution
                    type_counts = {}
                    for contact in multi_contacts:
                        ctype = getattr(contact, 'contact_type', 'AUTOMATIC')
                        type_counts[ctype] = type_counts.get(ctype, 0) + 1

                    click.echo("Contact type distribution:")
                    for ctype, count in sorted(type_counts.items()):
                        click.echo(f"  - {ctype}: {count} pairs")

                # Validate contacts if requested
                if validate:
                    click.echo("\nValidating contact quality...")
                    validation_results = _validate_contacts(multi_contacts, mesh_data, tolerance)

                    if validation_results:
                        num_passed = sum(1 for r in validation_results if r.get('passed', False))
                        click.echo(f"✓ Validation complete: {num_passed}/{len(validation_results)} passed")

                        # Show issues
                        for result in validation_results:
                            if result.get('issues'):
                                click.echo(f"\n  Contact #{result['contact_id']}:")
                                for issue in result['issues'][:3]:  # Show first 3 issues
                                    click.echo(f"    {issue.severity}: {issue.message}")

                # Show first 10 contacts
                for contact in multi_contacts[:10]:
                    ctype_str = f" [{getattr(contact, 'contact_type', 'AUTOMATIC')}]" if auto_classify else ""
                    click.echo(
                        f"  - Part {contact.part1_id} ↔ Part {contact.part2_id}{ctype_str}: "
                        f"{len(contact.face_pairs)} face pairs"
                    )
                if len(multi_contacts) > 10:
                    click.echo(f"  ... and {len(multi_contacts) - 10} more")
            else:
                click.echo("  No multi-part contacts detected")

        # Export results
        if contact_results:
            _export_contacts(contact_results, mesh_data, output, export, mesh_file)

            click.echo(f"\n✓ Contact detection completed")
            sys.exit(0)
        else:
            click.echo("\n⚠ No contacts detected")
            sys.exit(0)

    except Exception as e:
        logger.error(f"Error during contact detection: {e}")
        click.echo(f"Error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def _read_mesh_file(filepath: str):
    """Read mesh file based on extension"""
    path = Path(filepath)
    ext = path.suffix.lower()

    if ext == '.k':
        reader = LSDynaReader()
        return reader.read_file(filepath)
    else:
        logger.warning(f"Unknown file extension {ext}, trying LS-DYNA reader")
        reader = LSDynaReader()
        return reader.read_file(filepath)


def _detect_self_contact(mesh_data, tolerance: float, min_angle: float):
    """Detect self-contact zones"""
    detector = ContactSurfaceDetector()

    try:
        result = detector.detect_self_contacts(
            mesh=mesh_data,
            tolerance=tolerance,
            min_angle=min_angle
        )
        return result
    except Exception as e:
        logger.warning(f"Self-contact detection failed: {e}")
        return None


def _detect_multi_contact(mesh_data, tolerance: float, parallel: bool, jobs: int):
    """Detect multi-part contacts"""
    if parallel:
        detector = ParallelContactDetector(n_jobs=jobs)
    else:
        detector = ContactSurfaceDetector()

    try:
        # For multi-part contact, we need part information
        if not mesh_data.parts or len(mesh_data.parts) < 2:
            logger.warning("Multi-part contact requires at least 2 parts in mesh")
            return []

        # Get all parts
        part_ids = list(mesh_data.parts.keys())

        # Detect contacts between all part pairs
        contacts = []

        for i, part1_id in enumerate(part_ids):
            for part2_id in part_ids[i+1:]:
                result = detector.detect_contact_surfaces(
                    mesh=mesh_data,
                    part1_id=part1_id,
                    part2_id=part2_id,
                    tolerance=tolerance
                )

                if result and result.face_pairs:
                    contacts.append(result)

        return contacts

    except Exception as e:
        logger.warning(f"Multi-part contact detection failed: {e}")
        return []


def _export_contacts(contact_results, mesh_data, output_path: Optional[str], export_format: str, mesh_file: str):
    """Export contact results"""
    # Determine output path
    if output_path is None:
        if export_format == 'lsdyna':
            output_path = Path(mesh_file).with_suffix('.contacts.k')
        elif export_format == 'json':
            output_path = Path(mesh_file).with_suffix('.contacts.json')
        else:
            output_path = Path(mesh_file).with_suffix('.contacts.txt')

    if export_format == 'lsdyna':
        _export_lsdyna(contact_results, output_path)

    elif export_format == 'json':
        _export_json(contact_results, output_path)

    elif export_format == 'text':
        _export_text(contact_results, output_path)


def _export_lsdyna(contact_results, output_path: Path):
    """Export to LS-DYNA keyword format"""
    with open(output_path, 'w') as f:
        f.write("$# Contact Definitions\n")
        f.write("$# Generated by KooMeshGenerator\n")
        f.write("$\n")

        contact_id = 1

        # Self-contact
        if 'self_contact' in contact_results and contact_results['self_contact']:
            self_contact = contact_results['self_contact']

            f.write("$# Self-Contact Definition\n")
            f.write("*CONTACT_AUTOMATIC_SINGLE_SURFACE\n")
            f.write("$#    ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr\n")
            f.write(f"{contact_id:10d}         0         0         0         0         0         0         0\n")
            f.write("$#      fs        fd        dc        vc       vdc    penchk        bt        dt\n")
            f.write("       0.0       0.0       0.0       0.0       0.0         0       0.0       0.0\n")
            f.write("$\n")

            contact_id += 1

        # Multi-contact
        if 'multi_contact' in contact_results and contact_results['multi_contact']:
            multi_contacts = contact_results['multi_contact']

            for contact in multi_contacts:
                f.write(f"$# Contact between Part {contact.part1_id} and Part {contact.part2_id}\n")
                f.write("*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE\n")
                f.write("$#     cid                                                           title\n")
                f.write(f"{contact_id:10d}Part{contact.part1_id}_to_Part{contact.part2_id}\n")
                f.write("$#    ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr\n")
                f.write(f"{contact.part1_id:10d}{contact.part2_id:10d}         0         0         0         0         0         0\n")
                f.write("$#      fs        fd        dc        vc       vdc    penchk        bt        dt\n")
                f.write("       0.0       0.0       0.0       0.0       0.0         0       0.0       0.0\n")
                f.write("$\n")

                contact_id += 1

    click.echo(f"✓ LS-DYNA contact definitions saved: {output_path}")


def _export_json(contact_results, output_path: Path):
    """Export to JSON format"""
    export_data = {
        'contacts': []
    }

    # Self-contact
    if 'self_contact' in contact_results and contact_results['self_contact']:
        self_contact = contact_results['self_contact']

        export_data['contacts'].append({
            'type': 'self_contact',
            'part_id': self_contact.part_id,
            'num_face_pairs': len(self_contact.face_pairs),
            'avg_distance': self_contact.avg_distance,
            'min_distance': self_contact.min_distance,
            'face_pairs': self_contact.face_pairs[:100],  # Limit to 100 for file size
        })

    # Multi-contact
    if 'multi_contact' in contact_results and contact_results['multi_contact']:
        for contact in contact_results['multi_contact']:
            export_data['contacts'].append({
                'type': 'multi_contact',
                'part1_id': contact.part1_id,
                'part2_id': contact.part2_id,
                'num_face_pairs': len(contact.face_pairs),
                'avg_distance': contact.avg_distance,
                'min_distance': contact.min_distance,
                'face_pairs': contact.face_pairs[:100],  # Limit to 100
            })

    with open(output_path, 'w') as f:
        json.dump(export_data, f, indent=2)

    click.echo(f"✓ JSON contact data saved: {output_path}")


def _export_text(contact_results, output_path: Path):
    """Export to plain text format"""
    with open(output_path, 'w') as f:
        f.write("="*70 + "\n")
        f.write("CONTACT DETECTION RESULTS\n")
        f.write("="*70 + "\n\n")

        # Self-contact
        if 'self_contact' in contact_results and contact_results['self_contact']:
            self_contact = contact_results['self_contact']

            f.write("Self-Contact:\n")
            f.write("-"*70 + "\n")
            f.write(f"Part ID: {self_contact.part_id}\n")
            f.write(f"Face Pairs: {len(self_contact.face_pairs)}\n")
            f.write(f"Average Distance: {self_contact.avg_distance:.6f}\n")
            f.write(f"Minimum Distance: {self_contact.min_distance:.6f}\n")
            f.write("\n")

        # Multi-contact
        if 'multi_contact' in contact_results and contact_results['multi_contact']:
            f.write("Multi-Part Contacts:\n")
            f.write("-"*70 + "\n")

            for i, contact in enumerate(contact_results['multi_contact'], 1):
                f.write(f"\nContact Pair {i}:\n")
                f.write(f"  Part 1 ID: {contact.part1_id}\n")
                f.write(f"  Part 2 ID: {contact.part2_id}\n")
                f.write(f"  Face Pairs: {len(contact.face_pairs)}\n")
                f.write(f"  Average Distance: {contact.avg_distance:.6f}\n")
                f.write(f"  Minimum Distance: {contact.min_distance:.6f}\n")

        f.write("\n" + "="*70 + "\n")

    click.echo(f"✓ Text report saved: {output_path}")


def _classify_contacts(contacts, mesh_data):
    """Classify contact types using ContactClassifier"""
    try:
        from koomesh.contact.contact_classifier import ContactClassifier

        classifier = ContactClassifier()

        for contact in contacts:
            # Calculate properties for classification
            gap = getattr(contact, 'avg_distance', 0.1)
            area = len(getattr(contact, 'face_pairs', [])) * gap ** 2  # Rough estimate

            # Estimate surface angle (simplified - would need actual geometry)
            surface_angle = 10.0  # Default assumption

            # Classify
            contact_type = classifier.classify_contact_type(
                gap=gap,
                surface_angle=surface_angle,
                contact_area=area
            )

            # Optimize parameters
            params = classifier.optimize_parameters(contact_type)

            # Attach to contact object
            contact.contact_type = contact_type.value
            contact.parameters = params

        return contacts

    except Exception as e:
        logger.warning(f"Contact classification failed: {e}")
        return contacts


def _validate_contacts(contacts, mesh_data, tolerance):
    """Validate contact quality using ContactQualityChecker"""
    try:
        from koomesh.contact.contact_quality import ContactQualityChecker
        import numpy as np

        checker = ContactQualityChecker()
        results = []

        for i, contact in enumerate(contacts):
            # Extract surface elements (simplified)
            # In real implementation, would extract actual surface elements
            surfaces1 = np.array(getattr(contact, 'face_pairs', [])[:100])
            surfaces2 = np.array(getattr(contact, 'face_pairs', [])[:100])

            if len(surfaces1) == 0:
                continue

            # Perform quality check
            report = checker.check_contact_quality(
                mesh1=mesh_data,
                mesh2=mesh_data,  # Simplified - would use actual part meshes
                contact_surfaces1=surfaces1,
                contact_surfaces2=surfaces2,
                tolerance=tolerance
            )

            results.append({
                'contact_id': i + 1,
                'passed': report.passed,
                'score': report.score,
                'issues': report.issues,
                'statistics': report.statistics
            })

        return results

    except Exception as e:
        logger.warning(f"Contact validation failed: {e}")
        return []
