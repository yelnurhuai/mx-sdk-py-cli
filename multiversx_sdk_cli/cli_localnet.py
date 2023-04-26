import logging
from pathlib import Path
from typing import Any, List

from multiversx_sdk_cli import cli_shared, ux
from multiversx_sdk_cli.constants import ONE_YEAR_IN_SECONDS
from multiversx_sdk_cli.errors import KnownError
from multiversx_sdk_cli.localnet import (step_build_software, step_clean,
                                         step_config, step_new,
                                         step_prerequisites, step_start)

logger = logging.getLogger("cli.localnet")


def setup_parser(args: List[str], subparsers: Any) -> Any:
    parser = cli_shared.add_group_subparser(
        subparsers,
        "localnet",
        "Set up, start and control localnets"
    )
    subparsers = parser.add_subparsers()

    # Setup
    sub = cli_shared.add_command_subparser(
        subparsers,
        "localnet",
        "setup",
        "Set up a localnet (runs 'prerequisites', 'build' and 'config' in one go)"
    )
    add_argument_configfile(sub)
    sub.set_defaults(func=localnet_setup)

    # New
    sub = cli_shared.add_command_subparser(
        subparsers,
        "localnet",
        "new",
        "Create a new localnet configuration"
    )
    add_argument_configfile(sub)
    sub.set_defaults(func=localnet_new)

    # Prerequisites
    sub = cli_shared.add_command_subparser(
        subparsers,
        "localnet",
        "prerequisites",
        "Download and verify the prerequisites for running a localnet"
    )
    add_argument_configfile(sub)
    sub.set_defaults(func=localnet_prerequisites)

    # Build
    sub = cli_shared.add_command_subparser(
        subparsers,
        "localnet",
        "build",
        "Build necessary software for running a localnet"
    )
    add_argument_configfile(sub)
    sub.add_argument('--software', choices=["node", "seednode", "proxy"], nargs="+", default=["node", "seednode", "proxy"], help="The software to build (default: %(default)s)")
    sub.set_defaults(func=localnet_build)

    # Start
    sub = cli_shared.add_command_subparser(
        subparsers,
        "localnet",
        "start",
        "Start a localnet"
    )
    add_argument_configfile(sub)
    sub.add_argument("--stop-after-seconds", type=int, required=False, default=ONE_YEAR_IN_SECONDS, help="Stop the localnet after a given number of seconds (default: %(default)s)")
    sub.set_defaults(func=localnet_start)

    # Config
    sub = cli_shared.add_command_subparser(
        subparsers,
        "localnet",
        "config",
        "Configure a localnet (required before starting it the first time or after clean)"
    )
    add_argument_configfile(sub)
    sub.set_defaults(func=localnet_config)

    # Clean
    sub = cli_shared.add_command_subparser(
        subparsers,
        "localnet",
        "clean",
        "Erase the currently configured localnet (must be already stopped)"
    )
    add_argument_configfile(sub)
    sub.set_defaults(func=localnet_clean)


def add_argument_configfile(parser: Any):
    help_config_file = "An optional configuration file describing the localnet"
    parser.add_argument("--configfile", type=Path, required=False, default=Path("localnet.toml"), help=help_config_file)


def localnet_new(args: Any):
    logger.info("New localnet (creating configuration file)...")

    step_new.new_config(args.configfile)

    ux.show_message("New localnet configuration file created (or already existing). Make sure to inspect it. In order to fetch localnet prerequisites, run:\n\n$ mxpy localnet prerequisites")


def localnet_clean(args: Any):
    logger.info("Cleaning localnet...")
    guard_configfile(args)

    step_clean.clean(configfile=args.configfile)

    ux.show_message("Localnet cleaned. In order to configure (prepare) the localnet, run:\n\n$ mxpy localnet config")


def localnet_prerequisites(args: Any):
    logger.info("Gathering prerequisites...")
    guard_configfile(args)

    step_prerequisites.fetch_prerequisites(configfile=args.configfile)

    ux.show_message("Prerequisites gathered. In order to build the localnet software, run:\n\n$ mxpy localnet build")


def localnet_build(args: Any):
    logger.info("Building binaries...")
    guard_configfile(args)

    step_build_software.build(configfile=args.configfile, software_components=args.software)

    ux.show_message("Binaries built. In order to configure (prepare) the localnet, run:\n\n$ mxpy localnet config")


def localnet_config(args: Any):
    logger.info("Configuring localnet...")
    guard_configfile(args)

    step_config.configure(configfile=args.configfile)

    ux.show_message("Localnet configured. In order to start it, run:\n\n$ mxpy localnet start")


def localnet_start(args: Any):
    logger.info("Starting localnet...")
    guard_configfile(args)

    step_start.start(configfile=args.configfile, stop_after_seconds=args.stop_after_seconds)


def localnet_setup(args: Any):
    logger.info("Setting up localnet...")

    step_new.new_config(args.configfile)
    step_prerequisites.fetch_prerequisites(configfile=args.configfile)
    step_build_software.build(configfile=args.configfile, software_components=["node", "seednode", "proxy"])
    step_clean.clean(configfile=args.configfile)
    step_config.configure(configfile=args.configfile)

    ux.show_message("Localnet setup complete. In order to start it, run:\n\n$ mxpy localnet start")


def guard_configfile(args: Any):
    configfile = args.configfile.resolve()
    old_configfile_in_workdir = Path("testnet.toml").resolve()

    if not configfile.exists():
        raise KnownError(f"Localnet config file does not exist: {configfile}")

    if old_configfile_in_workdir.exists():
        logger.error(f"""For less ambiguity, the old "testnet.toml" config file should be removed: {old_configfile_in_workdir}""")
        raise KnownError(f"""Found old "testnet.toml" config file in working directory: {old_configfile_in_workdir}""")
