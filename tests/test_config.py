import textwrap

from tuff import entry


def test_log(capsys, tmp_path):
    config = entry.Config(None)

    config.log(tmp_path, "foo")
    config.log(tmp_path, "foo")
    config.log(tmp_path, "bar")
    config.log(tmp_path)
    config.log(tmp_path, "foo")

    captured = capsys.readouterr()

    # Test the captured output, both std and err
    assert (
        captured.out.strip()
        == textwrap.dedent(
            f"""
        ; {str(tmp_path)[1:]}
        foo

        ; {str(tmp_path)[1:]}
        foo
          ... this message will not repeat again ...

        ; {str(tmp_path)[1:]}
        bar
        """
        ).strip()
    )
    assert captured.err == ""
