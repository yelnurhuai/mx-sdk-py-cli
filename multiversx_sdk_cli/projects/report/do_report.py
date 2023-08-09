import copy
import logging
from pathlib import Path
from typing import Any, Dict, List

from multiversx_sdk_cli import cli_shared, utils
from multiversx_sdk_cli.projects.core import get_project_paths_recursively
from multiversx_sdk_cli.projects.report.data.report import (
    Report, merge_list_of_reports)
from multiversx_sdk_cli.projects.report.features.features import \
    get_default_report_features
from multiversx_sdk_cli.projects.report.format.format_options import \
    FormatOptions
from multiversx_sdk_cli.projects.report.report_creator import ReportCreator

logger = logging.getLogger("report")


def do_report(args: Any, build_options: Any) -> None:
    compare_report_paths = args.compare
    if compare_report_paths is None:
        _build_report(args, build_options)
    else:
        _compare_reports(args, compare_report_paths)


def _build_report(args: Any, build_options: Dict[str, Any]) -> None:
    base_path = Path(args.path)
    project_paths = get_project_paths_recursively(base_path)
    options = get_default_report_features()

    args_copy = _prepare_args_for_build(args)
    build_args = cli_shared.convert_args_object_to_args_list(args_copy)

    report_creator = ReportCreator(options, skip_build=args.skip_build, skip_twiggy=args.skip_twiggy, build_options=build_options, build_args=build_args)
    report = report_creator.create_report(base_path, project_paths)
    _finalize_report(report, args)


def _prepare_args_for_build(args: Any):
    args_copy = copy.deepcopy(args)

    arguments: Dict[str, Any] = args_copy.__dict__
    arguments.pop("output_format", None)
    arguments.pop("output_file", None)

    return args_copy


def _compare_reports(args: Any, merge_report_paths: List[Path]) -> None:
    reports = [Report.load_from_file(report_path) for report_path in merge_report_paths]
    final_report = merge_list_of_reports(reports)
    _finalize_report(final_report, args)


def _finalize_report(report: Report, args: Any) -> None:
    output = _get_report_output_string(report, args)
    _store_output(output, args)


def _get_report_output_string(report: Report, args: Any) -> str:
    output_format = args.output_format
    if output_format == 'github-markdown':
        return report.to_markdown(FormatOptions(github_markdown=True))
    if output_format == 'text-markdown':
        return report.to_markdown(FormatOptions(github_markdown=False))
    elif output_format == 'json':
        return report.to_json_string()
    raise Exception('Invalid output format')


def _store_output(output: str, args: Any) -> None:
    output_file_path = args.output_file
    if output_file_path is None:
        print(output)
    else:
        utils.write_file(Path(output_file_path), output)
