import logging
import os
import shutil
from os import path
from pathlib import Path
from typing import Dict, List, Optional

from multiversx_sdk_cli import (config, dependencies, downloader, errors,
                                myprocess, utils, workstation)
from multiversx_sdk_cli.dependencies.resolution import (
    DependencyResolution, get_dependency_resolution)
from multiversx_sdk_cli.ux import show_warning

logger = logging.getLogger("modules")


class DependencyModule:
    def __init__(self, key: str, aliases: List[str] = []):
        self.key = key
        self.aliases = aliases

    def get_directory(self, tag: str) -> Path:
        raise NotImplementedError()

    def install(self, overwrite: bool) -> None:
        # We install the default tag
        tag = config.get_dependency_tag(self.key)

        if tag == 'latest':
            tag = self.get_latest_release()

        logger.info(f"install: key={self.key}, tag={tag}, overwrite={overwrite}")

        if self._should_skip(tag, overwrite):
            logger.info("Already exists. Skip install.")
            return

        self.uninstall(tag)
        self._do_install(tag)

        self._post_install(tag)

    def _do_install(self, tag: str) -> None:
        raise NotImplementedError()

    def _post_install(self, tag: str):
        pass

    def _should_skip(self, tag: str, overwrite: bool) -> bool:
        if overwrite:
            return False
        return self.is_installed(tag)

    def uninstall(self, tag: str) -> None:
        raise NotImplementedError()

    def is_installed(self, tag: str) -> bool:
        raise NotImplementedError()

    def get_env(self) -> Dict[str, str]:
        raise NotImplementedError()

    def get_latest_release(self) -> str:
        raise NotImplementedError()

    def get_resolution(self) -> DependencyResolution:
        return get_dependency_resolution(self.key)


class StandaloneModule(DependencyModule):
    def __init__(self,
                 key: str,
                 aliases: List[str] = [],
                 repo_name: Optional[str] = None,
                 organisation: Optional[str] = None):
        super().__init__(key, aliases)
        self.archive_type = "tar.gz"
        self.repo_name = repo_name
        self.organisation = organisation

    def _do_install(self, tag: str):
        self._download(tag)
        self._extract(tag)

    def uninstall(self, tag: str):
        if os.path.isdir(self.get_directory(tag)):
            shutil.rmtree(self.get_directory(tag))

    def is_installed(self, tag: str) -> bool:
        return path.isdir(self.get_directory(tag))

    def _download(self, tag: str):
        url = self._get_download_url(tag)
        archive_path = self._get_archive_path(tag)
        downloader.download(url, str(archive_path))

    def _extract(self, tag: str):
        archive_path = self._get_archive_path(tag)
        destination_folder = self.get_directory(tag)

        if self.archive_type == "tar.gz":
            utils.untar(archive_path, destination_folder)
        elif self.archive_type == "zip":
            utils.unzip(archive_path, destination_folder)
        else:
            raise errors.UnknownArchiveType(self.archive_type)

    def get_directory(self, tag: str) -> Path:
        return config.get_dependency_directory(self.key, tag)

    def get_source_directory(self, tag: str) -> Path:
        # Due to how the GitHub creates archives for repository releases, the
        # path will contain the tag in two variants: with the 'v' prefix (e.g.
        # "v1.1.0"), but also without (e.g. "1.1.0"), hence the need to remove
        # the initial 'v'.
        tag_no_v = tag
        if tag_no_v.startswith("v"):
            tag_no_v = tag_no_v[1:]
        assert isinstance(self.repo_name, str)

        source_folder_option_1 = self.get_directory(tag) / f'{self.repo_name}-{tag_no_v}'
        source_folder_option_2 = self.get_directory(tag) / f'{self.repo_name}-{tag}'
        return source_folder_option_1 if source_folder_option_1.exists() else source_folder_option_2

    def get_parent_directory(self) -> Path:
        return config.get_dependency_parent_directory(self.key)

    def _get_download_url(self, tag: str) -> str:
        platform = workstation.get_platform()

        url = config.get_dependency_url(self.key, tag, platform)
        if not url:
            raise errors.PlatformNotSupported(self.key, platform)

        url = url.replace("{TAG}", tag)
        return url

    def get_latest_release(self) -> str:
        if self.repo_name is None or self.organisation is None:
            raise ValueError(f'{self.key}: repo_name or organisation not specified')

        org_repo = f'{self.organisation}/{self.repo_name}'
        tag = utils.query_latest_release_tag(org_repo)
        return tag

    def _get_archive_path(self, tag: str) -> Path:
        tools_folder = Path(workstation.get_tools_folder())
        archive = tools_folder / f"{self.key}.{tag}.{self.archive_type}"
        return archive


class VMToolsModule(StandaloneModule):
    def __init__(self, key: str, aliases: List[str] = []):
        super().__init__(key, aliases)
        self.repo_name = 'mx-chain-vm-go'
        self.organisation = 'multiversx'

    def _post_install(self, tag: str):
        dependencies.install_module('golang')

        self.build_binary(tag, 'test')
        self.make_binary_symlink_in_parent_folder(tag, 'test', 'run-scenarios')
        self.copy_libwasmer_in_parent_directory(tag)

    def build_binary(self, tag: str, binary_name: str):
        source_folder = self.binary_source_folder(tag, binary_name)
        golang = dependencies.get_module_by_key("golang")
        golang_env = golang.get_env()
        myprocess.run_process(['go', 'build'], cwd=source_folder, env=golang_env)

    def binary_source_folder(self, tag: str, binary_name: str):
        directory = self.get_source_directory(tag)
        return directory / 'cmd' / binary_name

    def make_binary_symlink_in_parent_folder(self, tag: str, binary_name: str, symlink_name: str):
        source_folder = self.binary_source_folder(tag, binary_name)
        binary = source_folder / binary_name

        parent = self.get_parent_directory()
        symlink = parent / symlink_name

        symlink.unlink(missing_ok=True)
        symlink.symlink_to(binary)

    def copy_libwasmer_in_parent_directory(self, tag: str):
        libwasmer_directory = self.get_source_directory(tag) / 'wasmer'
        cmd_test_directory = self.get_source_directory(tag) / 'cmd' / 'test'
        parent_directory = self.get_parent_directory()
        for f in libwasmer_directory.iterdir():
            if f.suffix in ['.dylib', '.so', '.dll']:
                # Copy the dynamic library near the "run-scenarios" symlink
                shutil.copy(f, parent_directory)
                # Though, also copy the dynamic library near the target executable (seems to be necessary on MacOS)
                shutil.copy(f, cmd_test_directory)

    def get_env(self) -> Dict[str, str]:
        return dict()

    def get_source_directory(self, tag: str) -> Path:
        directory = self.get_directory(tag)
        first_subdirectory = next(directory.iterdir())
        return first_subdirectory


class GolangModule(StandaloneModule):
    def _post_install(self, tag: str):
        parent_directory = self.get_parent_directory()
        utils.ensure_folder(path.join(parent_directory, "GOPATH"))
        utils.ensure_folder(path.join(parent_directory, "GOCACHE"))

    def is_installed(self, tag: str) -> bool:
        resolution = self.get_resolution()

        if resolution == DependencyResolution.Host:
            which_go = shutil.which("go")
            logger.info(f"which go: {which_go}")

            return which_go is not None
        if resolution == DependencyResolution.SDK:
            return super().is_installed(tag)

        raise errors.BadDependencyResolution(self.key, resolution)

    def get_env(self) -> Dict[str, str]:
        resolution = self.get_resolution()
        directory = self.get_directory(config.get_dependency_tag(self.key))
        parent_directory = self.get_parent_directory()

        if resolution == DependencyResolution.Host:
            return {
                "PATH": os.environ.get("PATH", ""),
                "GOPATH": os.environ.get("GOPATH", ""),
                "GOCACHE": os.environ.get("GOCACHE", ""),
                "GOROOT": os.environ.get("GOROOT", "")
            }
        if resolution == DependencyResolution.SDK:
            current_path = os.environ.get("PATH", "")
            current_path_parts = current_path.split(":")
            current_path_parts_without_go = [part for part in current_path_parts if "/go/bin" not in part]
            current_path_without_go = ":".join(current_path_parts_without_go)

            return {
                # At this moment, cc (build-essential) is needed to compile go dependencies (e.g. Node, VM)
                "PATH": f"{(directory / 'go' / 'bin')}:{current_path_without_go}",
                "GOPATH": str(self.get_gopath()),
                "GOCACHE": str(parent_directory / "GOCACHE"),
                "GOROOT": str(directory / "go")
            }

        raise errors.BadDependencyResolution(self.key, resolution)

    def get_gopath(self) -> Path:
        return self.get_parent_directory() / "GOPATH"

    def get_latest_release(self) -> str:
        raise errors.UnsupportedConfigurationValue("Golang tag must always be explicit, not latest")


class Rust(DependencyModule):
    def is_installed(self, tag: str) -> bool:
        which_rustc = shutil.which("rustc")
        which_cargo = shutil.which("cargo")
        which_sc_meta = shutil.which("sc-meta")
        which_wasm_opt = shutil.which("wasm-opt")
        which_twiggy = shutil.which("twiggy")
        logger.info(f"which rustc: {which_rustc}")
        logger.info(f"which cargo: {which_cargo}")
        logger.info(f"which sc-meta: {which_sc_meta}")
        logger.info(f"which wasm-opt: {which_wasm_opt}")
        logger.info(f"which twiggy: {which_twiggy}")

        dependencies = [which_rustc, which_cargo, which_sc_meta, which_wasm_opt, which_twiggy]
        return all(dependency is not None for dependency in dependencies)

    def install(self, overwrite: bool) -> None:
        self._check_install_env(apply_correction=overwrite)

        module = dependencies.get_module_by_key("rust")
        tag: str = config.get_dependency_tag(module.key)

        if not overwrite:
            show_warning(f"We recommend using rust {tag}. If you'd like to overwrite your current version please run `mxpy deps install rust --overwrite`.")
        logger.info(f"install: key={self.key}, tag={tag}, overwrite={overwrite}")

        if overwrite:
            logger.info("Overwriting the current rust version...")
        elif self.is_installed(""):
            return

        self._install_rust(tag)
        self._install_sc_meta()
        self._install_wasm_opt()
        self._install_twiggy()

    def _check_install_env(self, apply_correction: bool = True):
        """
        See https://rust-lang.github.io/rustup/installation/index.html#choosing-where-to-install.
        """

        current_cargo_home = os.environ.get("CARGO_HOME", None)
        current_rustup_home = os.environ.get("RUSTUP_HOME", None)
        if current_cargo_home:
            show_warning(f"""CARGO_HOME variable is set to: {current_cargo_home}.
This may cause problems with the installation.""")

            if apply_correction:
                show_warning(f"CARGO_HOME will be temporarily unset.")
                os.environ["CARGO_HOME"] = ""

        if current_rustup_home:
            show_warning(f"""RUSTUP_HOME variable is set to: {current_rustup_home}.
This may cause problems with the installation of rust.""")

            if apply_correction:
                show_warning(f"RUSTUP_HOME will be temporarily unset.")
                os.environ["RUSTUP_HOME"] = ""

    def _install_rust(self, tag: str) -> None:
        installer_url = self._get_installer_url()
        installer_path = self._get_installer_path()

        downloader.download(installer_url, str(installer_path))
        utils.mark_executable(str(installer_path))

        if tag:
            toolchain = tag
        else:
            toolchain = "nightly"

        args = [str(installer_path), "--verbose", "--default-toolchain", toolchain, "--profile",
                "minimal", "--target", "wasm32-unknown-unknown", "-y"]

        logger.info("Installing rust.")
        myprocess.run_process(args)

    def _install_sc_meta(self):
        logger.info("Installing multiversx-sc-meta.")
        tag = config.get_dependency_tag("sc-meta")
        args = ["cargo", "install", "multiversx-sc-meta"]

        if tag != "latest":
            args.extend(["--version", tag])

        myprocess.run_process(args)

    def _install_wasm_opt(self):
        logger.info("Installing wasm-opt. This may take a while.")
        tag = config.get_dependency_tag("wasm-opt")
        args = ["cargo", "install", "wasm-opt", "--version", tag]
        myprocess.run_process(args)

    def _install_twiggy(self):
        logger.info("Installing twiggy.")
        tag = config.get_dependency_tag("twiggy")
        args = ["cargo", "install", "twiggy"]

        if tag != "latest":
            args.extend(["--version", tag])

        myprocess.run_process(args)

    def _get_installer_url(self) -> str:
        if workstation.is_windows():
            return "https://win.rustup.rs"
        return "https://sh.rustup.rs"

    def _get_installer_path(self) -> Path:
        tools_folder = workstation.get_tools_folder()

        if workstation.is_windows():
            return tools_folder / "rustup-init.exe"
        return tools_folder / "rustup.sh"

    def uninstall(self, tag: str):
        directory = self.get_directory("")
        if os.path.isdir(directory):
            shutil.rmtree(directory)

    def get_directory(self, tag: str) -> Path:
        tools_folder = workstation.get_tools_folder()
        return tools_folder / "vendor-rust"

    def get_env(self) -> Dict[str, str]:
        return dict(os.environ)

    def get_latest_release(self) -> str:
        raise errors.UnsupportedConfigurationValue("Rust tag must either be explicit, empty or 'nightly'")


class TestWalletsModule(StandaloneModule):
    def __init__(self, key: str):
        super().__init__(key, [])
        self.organisation = "multiversx"
        self.repo_name = "mx-sdk-testwallets"

    def _post_install(self, tag: str):
        # We'll create a "latest" symlink
        target = self.get_source_directory(tag)
        link = path.join(self.get_parent_directory(), "latest")
        utils.symlink(str(target), link)
