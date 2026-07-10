"""Database seeding entrypoint.

Kept separate from migrations by design: migrations manage schema, this manages data.
Populated in Task 06 (domain models & seed data).
"""

import asyncio


async def seed() -> None:
    raise NotImplementedError("Seed data is implemented in Task 06.")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
