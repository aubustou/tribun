from tribun import Key, put

DOWN_REVISION = None
REVISION = "hgsqa54a"


def upgrade():
    put(
        [
            ConfigurationKey("tribun/tests/groum", "hop"),
            ConfigurationKey("tribun/tests", [ConfigurationKey("toto", "tata")]),
        ]
    )


def downgrade():
    pass
