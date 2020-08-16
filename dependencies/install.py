import logging
from typing import List

from erdpy import config, errors
from erdpy.dependencies.modules import (ArwenToolsModule, DependencyModule, NodejsModule,
                                        Rust, StandaloneModule)

logger = logging.getLogger("install")


def install_module(key: str, tag: str = "", overwrite: bool = False):
    module = get_module_by_key(key)
    module.install(tag, overwrite)


def get_module_directory(key: str) -> str:
    module = get_module_by_key(key)
    default_tag = config.get_dependency_tag(key)
    directory = module.get_directory(default_tag)
    return directory


def get_module_by_key(key: str) -> DependencyModule:
    matches = [module for module in get_all_deps() if module.key == key or key in module.aliases]
    if len(matches) != 1:
        raise errors.UnknownDependency(key)

    return matches[0]


def get_all_deps() -> List[DependencyModule]:
    return [
        StandaloneModule(key="llvm", aliases=["clang", "cpp"]),
        ArwenToolsModule(key="arwentools", aliases=[]),
        Rust(key="rust", aliases=[]),
        NodejsModule(key="nodejs", aliases=[])
    ]
