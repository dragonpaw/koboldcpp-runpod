# koboldcpp-runpod

A rebuild of [KoboldCpp](https://github.com/LostRuins/koboldcpp)'s Linux CUDA
single-file binary (`koboldcpp-linux-x64`) with **native SASS for sm_86 and
sm_89**, built for RunPod A40 (Ampere) and L40S (Ada) pods.

## Why

Upstream's CUDA 12 release build (`ARCHES_CU12`) embeds PTX only, up to
`compute_80`. On an sm_86 or sm_89 GPU the driver JIT-compiles every kernel
on first start; on a fresh pod that measured about 80 seconds before the
model could load. This build ships cubins for sm_86 and sm_89 (plus
`compute_89` PTX for forward compatibility), so there is nothing to JIT on
those GPUs.

Nothing else changes. The workflow mirrors upstream's
`.github/workflows/kcpp-build-release-linux.yaml` and only rewrites the
Makefile's `LLAMA_ARCHES_CU12` gencode list:

```
-gencode arch=compute_86,code=sm_86
-gencode arch=compute_89,code=sm_89
-gencode arch=compute_89,code=compute_89
-DKCPP_LIMIT_CUDA_MAX_ARCH=890
```

The job fails unless `cuobjdump --list-elf koboldcpp_cublas.so` shows both
`sm_86` and `sm_89`.

GPUs older than sm_86 are **not** supported by this binary (no PTX for them).
Use upstream's build for those.

## Current build

| Release | Upstream source |
| --- | --- |
| [`v1.123.1-sm86-sm89`](https://github.com/dragonpaw/koboldcpp-runpod/releases/tag/v1.123.1-sm86-sm89) | [`LostRuins/koboldcpp@9be8c136`](https://github.com/LostRuins/koboldcpp/tree/9be8c136ae7e17eb50d9b7a6f3dff5038fcc3186) (tag `v1.123.1`) |

Each release's notes link the exact upstream commit it was built from.

## Using it

The official KoboldCpp RunPod/Docker image downloads the binary named by
`KCPP_BIN_OVERRIDE` in place of its default, so point that at a pinned
release asset (never `latest`):

```
KCPP_BIN_OVERRIDE=https://github.com/dragonpaw/koboldcpp-runpod/releases/download/v1.123.1-sm86-sm89/koboldcpp-linux-x64
```

## Bumping to a new upstream version

1. Actions → *Build koboldcpp-linux-x64 (sm_86 + sm_89)* → Run workflow,
   with `upstream_tag` set to the new upstream tag (e.g. `v1.124.0`), or
   `gh workflow run build.yml -R dragonpaw/koboldcpp-runpod -f upstream_tag=v1.124.0`.
2. The job publishes release `<tag>-sm86-sm89` with the asset.
3. Update the table above and whatever pins the download URL.

If upstream reshapes the `LLAMA_ARCHES_CU12` Makefile block or the dist
output name, the patch step or rename step fails loudly; adjust the workflow
to match.

## License

KoboldCpp is licensed under the GNU Affero General Public License v3.0; this
repository and its release binaries are distributed under the same license
(see [LICENSE](LICENSE), copied from upstream). The complete corresponding
source for each binary is the upstream commit linked in its release notes,
plus the Makefile change described above and in
[`.github/workflows/build.yml`](.github/workflows/build.yml). Portions of the
bundled ggml / llama.cpp / stable-diffusion.cpp code are MIT-licensed upstream
(see `MIT_LICENSE_GGML_SDCPP_LLAMACPP_ONLY.md` in the upstream repository).
