"""Dagger CI pipeline for Formbricks.

Run all checks:  dagger call -m ci all --src .
Run individual:  dagger call -m ci lint --src .
"""

import dagger
from dagger import dag, function, object_type


@object_type
class Ci:
    """CI pipeline for Formbricks — lint, test, build."""

    def _base(self, src: dagger.Directory) -> dagger.Container:
        """Shared base container: Node 22 + pnpm + installed deps."""
        return (
            dag.container()
            .from_("node:22-alpine")
            # pnpm is bundled via corepack in the package.json packageManager field
            .with_exec(["corepack", "enable"])
            .with_mounted_directory("/app", src)
            .with_workdir("/app")
            # Dummy env vars required by @t3-oss/env validation in tests/build
            .with_env_variable("DATABASE_URL", "postgresql://localhost:5432/formbricks")
            .with_env_variable("ENCRYPTION_KEY", "0".rjust(64, "0"))
            .with_env_variable("NEXTAUTH_SECRET", "test-secret")
            .with_env_variable("NEXTAUTH_URL", "http://localhost:3000")
            .with_env_variable("WEBAPP_URL", "http://localhost:3000")
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
            .with_exec(["pnpm", "build", "--filter=@formbricks/web..."])
            .stdout()
        )

    @function
    async def all(self, src: dagger.Directory) -> str:
        """Run the full CI pipeline: lint → test → build."""
        base = self._base(src)

        # Run lint and test in parallel (they're independent)
        lint_result = base.with_exec(["pnpm", "lint"]).stdout()
        test_result = base.with_exec(["pnpm", "test"]).stdout()

        await lint_result
        await test_result

        # Build last
        await base.with_exec(["pnpm", "build", "--filter=@formbricks/web..."]).stdout()

        return "All CI checks passed."
