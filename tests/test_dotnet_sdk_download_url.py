import pytest

from echo import build_dotnet_sdk_download_url


def test_dotnet_sdk_default_linux_tarball():
    url = build_dotnet_sdk_download_url("8.0.400")
    expected = (
        "https://dotnetcli.blob.core.windows.net/dotnet/Sdk/8.0.400/"
        "dotnet-sdk-8.0.400-linux-x64.tar.gz"
    )
    assert url == expected


def test_dotnet_sdk_preview_version_and_zip_extension():
    url = build_dotnet_sdk_download_url(
        "9.0.0-preview.2.24157.9",
        runtime_id="win-x64",
        archive_format=".zip",
    )
    expected = (
        "https://dotnetcli.blob.core.windows.net/dotnet/Sdk/9.0.0-preview.2.24157.9/"
        "dotnet-sdk-9.0.0-preview.2.24157.9-win-x64.zip"
    )
    assert url == expected


@pytest.mark.parametrize(
    "version",
    ["", "9.0/../../evil", " 8.0.100"],
)
def test_dotnet_sdk_invalid_version(version):
    with pytest.raises(ValueError):
        build_dotnet_sdk_download_url(version)


@pytest.mark.parametrize("runtime_id", ["", "linux/x64", "-arm64"])
def test_dotnet_sdk_invalid_runtime(runtime_id):
    with pytest.raises(ValueError):
        build_dotnet_sdk_download_url("8.0.400", runtime_id=runtime_id)


@pytest.mark.parametrize("archive_format", ["", "..tar.gz", "tar.gz/", ".tar.gz.exe"])
def test_dotnet_sdk_invalid_archive_format(archive_format):
    with pytest.raises(ValueError):
        build_dotnet_sdk_download_url("8.0.400", archive_format=archive_format)
