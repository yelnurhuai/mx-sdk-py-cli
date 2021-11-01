#!/usr/bin/env bash

source "./shared.sh"

testAll() {
    set -x

    ${ERDPY} --verbose deps install rust
    ${ERDPY} --verbose deps install clang
    ${ERDPY} --verbose deps install vmtools --overwrite

    ${ERDPY} --verbose deps check rust
    ${ERDPY} --verbose deps check clang
    ${ERDPY} --verbose deps check vmtools

    set +x
}
