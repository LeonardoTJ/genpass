"""Allow ``python -m genpass``."""

from genpass.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
