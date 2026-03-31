"""Dagger CI pipeline for Formbricks.

Run all checks:  dagger call -m ci all --src app
Run individual:  dagger call -m ci lint --src app
"""

import dagger
from dagger import dag, function, object_type


@object_type
class Ci:
    """CI pipeline for Formbricks — lint, typecheck, test, build."""

    def _base(self, src: dagger.Directory) -> dagger.Container:
        """Shared base container: Node 22 + pnpm + installed deps."""
        return (
            dag.container()
            .from_("node:22-alpine")
            # pnpm is bundled via corepack in the package.json packageManager field
            .with_exec(["corepack", "enable"])
            .with_mounted_directory("/app", src)
            .with_workdir("/app")
            # Install deps — cache the pnpm store for speed
            .with_mounted_cache("/root/.local/share/pnpm/store", dag.cache_volume("pnpm-store"))
            .with_exec(["pnpm", "install", "--frozen-lockfile"])
        )

    @function
    async def lint(self, src: dagger.Directory) -> str:
        """Run ESLint across the monorepo."""
        return await (
            self._base(src)
            .with_exec(["pnpm", "lint"])
            .stdout()
        )

    @function
    async def typecheck(self, src: dagger.Directory) -> str:
        """Run TypeScript type checking."""
        return await (
            self._base(src)
            .with_exec(["pnpm", "turbo", "run", "type-check"])
            .stdout()
        )

    @function
    async def test(self, src: dagger.Directory) -> str:
        """Run Vitest unit tests."""
        return await (
            self._base(src)
            .with_exec(["pnpm", "test"])
            .stdout()
        )

    @function
    async def build(self, src: dagger.Directory) -> str:
        """Build the Formbricks app."""
        return await (
            self._base(src)
            .with_exec(["pnpm", "build"])
            .stdout()
        )

    @function
    async def all(self, src: dagger.Directory) -> str:
        """Run the full CI pipeline: lint → typecheck → test → build."""
        base = self._base(src)

        # Run lint, typecheck, and test in parallel (they're independent)
        lint_result = (
            base.with_exec(["pnpm", "lint"]).stdout()
        )
        typecheck_result = (
            base.with_exec(["pnpm", "turbo", "run", "type-check"]).stdout()
        )
        test_result = (
            base.with_exec(["pnpm", "test"]).stdout()
        )

        # Await all
        await lint_result
        await typecheck_result
        await test_result

        # Build last (depends on types being correct)
        build_result = await (
            base.with_exec(["pnpm", "build"]).stdout()
        )

        return "All CI checks passed."
