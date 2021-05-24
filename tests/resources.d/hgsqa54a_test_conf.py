from tribun import Key, put

DOWN_REVISION = None
REVISION = "hgsqa54a"


def upgrade():
    put(
        [
            Key("tribun/tests/groum", "hop"),
            Key("tribun/tests", [Key("toto", "tata")]),
        ]
    )


def downgrade():
    pass
