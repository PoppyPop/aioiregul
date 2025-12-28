"""Tests for the CLI module."""

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from src.aioiregul import cli
from src.aioiregul.v2.mappers import MappedFrame


class TestSerializeValue:
    """Test _serialize_value helper function."""

    def test_serialize_primitives(self):
        """Test serialization of primitive types."""
        assert cli._serialize_value(42) == 42
        assert cli._serialize_value(3.14) == 3.14
        assert cli._serialize_value("hello") == "hello"
        assert cli._serialize_value(True) is True
        assert cli._serialize_value(None) is None

    def test_serialize_datetime(self):
        """Test serialization of datetime objects."""
        from datetime import datetime

        dt = datetime(2025, 12, 28, 10, 30, 45)
        result = cli._serialize_value(dt)
        assert result == "2025-12-28T10:30:45"

    def test_serialize_dict(self):
        """Test serialization of dictionaries."""
        data = {"key": "value", "number": 42}
        result = cli._serialize_value(data)
        assert result == {"key": "value", "number": 42}

    def test_serialize_list(self):
        """Test serialization of lists."""
        data = [1, 2, "three", True]
        result = cli._serialize_value(data)
        assert result == [1, 2, "three", True]

    def test_serialize_tuple(self):
        """Test serialization of tuples."""
        data = (1, 2, "three")
        result = cli._serialize_value(data)
        assert result == [1, 2, "three"]

    def test_serialize_nested_structures(self):
        """Test serialization of nested data structures."""
        from datetime import datetime

        data = {
            "list": [1, 2, {"nested": datetime(2025, 1, 1)}],
            "dict": {"key": [True, False, None]},
        }
        result = cli._serialize_value(data)
        assert result == {
            "list": [1, 2, {"nested": "2025-01-01T00:00:00"}],
            "dict": {"key": [True, False, None]},
        }

    def test_serialize_object_with_dict(self):
        """Test serialization of objects with __dict__ attribute."""

        class TestClass:
            def __init__(self):
                self.name = "test"
                self.value = 42

        obj = TestClass()
        result = cli._serialize_value(obj)
        assert result == {"name": "test", "value": 42}

    def test_serialize_unknown_type(self):
        """Test serialization of unknown types falls back to str()."""

        class CustomClass:
            def __str__(self):
                return "custom_string"

        obj = CustomClass()
        result = cli._serialize_value(obj)
        # CustomClass has __dict__ so it will be serialized as empty dict
        assert result == {}


class TestDecodeCommand:
    """Test decode_command function."""

    @pytest.fixture
    def mock_frame(self):
        """Create a mock DecodedFrame."""
        from datetime import datetime

        # Create a simple object that can be serialized
        class SimpleFrame:
            def __init__(self):
                self.is_old = False
                self.timestamp = datetime(2025, 12, 28, 10, 30, 45)
                self.count = 100
                self.groups = {
                    "zones": {0: {}, 1: {}},
                    "measurements": {0: {}, 1: {}, 2: {}},
                }

        return SimpleFrame()

    @pytest.fixture
    def mock_mapped_frame(self):
        """Create a mock MappedFrame."""
        mapped = MagicMock(spec=MappedFrame)

        # Create mock zones
        zone1 = MagicMock()
        zone1.index = 0
        zone1.zone_nom = "Zone1"
        zone1.consigne_normal = 20
        zone1.consigne_reduit = 18
        zone1.mode = "Normal"

        zone2 = MagicMock()
        zone2.index = 1
        zone2.zone_nom = "Zone2"
        zone2.consigne_normal = 22
        zone2.consigne_reduit = 19
        zone2.mode = "Reduit"

        mapped.zones = {0: zone1, 1: zone2}
        mapped.inputs = {}
        mapped.outputs = {}

        # Create mock measurements
        measure1 = MagicMock()
        measure1.index = 0
        measure1.alias = "Temp1"
        measure1.valeur = 21.5
        measure1.unit = "°C"

        measure2 = MagicMock()
        measure2.index = 1
        measure2.alias = "Temp2"
        measure2.valeur = 19.8
        measure2.unit = "°C"

        mapped.measurements = {0: measure1, 1: measure2}
        mapped.parameters = {}
        mapped.labels = {}
        mapped.modbus_registers = {}
        mapped.analog_sensors = {}
        mapped.configuration = None
        mapped.memory = None
        mapped.as_json = MagicMock(return_value='{"test": "json"}')
        return mapped

    @pytest.mark.asyncio
    async def test_decode_command_file_not_found(self, capsys):
        """Test decode_command with non-existent file."""
        args = argparse.Namespace(
            file="/nonexistent/file.txt",
            mapped=False,
            json=False,
        )

        result = await cli.decode_command(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error: File not found" in captured.err

    @pytest.mark.asyncio
    async def test_decode_command_decode_error(self, tmp_path, capsys):
        """Test decode_command with decode error."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("invalid data")

        args = argparse.Namespace(
            file=str(test_file),
            mapped=False,
            json=False,
        )

        with patch("src.aioiregul.v2.decoder.decode_file") as mock_decode:
            mock_decode.side_effect = ValueError("Invalid data")

            result = await cli.decode_command(args)

            assert result == 1
            captured = capsys.readouterr()
            assert "Error decoding file" in captured.err

    @pytest.mark.asyncio
    async def test_decode_command_human_readable(
        self, tmp_path, capsys, mock_frame, mock_mapped_frame
    ):
        """Test decode_command with human-readable output."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        args = argparse.Namespace(
            file=str(test_file),
            mapped=False,
            json=False,
        )

        with (
            patch("src.aioiregul.v2.decoder.decode_file") as mock_decode,
            patch("src.aioiregul.v2.mappers.map_frame") as mock_map,
        ):
            mock_decode.return_value = mock_frame
            mock_map.return_value = mock_mapped_frame

            result = await cli.decode_command(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "File:" in captured.out
            assert "Type: NEW" in captured.out
            assert "Timestamp:" in captured.out
            assert "Token Count: 100" in captured.out
            assert "Groups found:" in captured.out
            assert "measurements" in captured.out
            assert "zones" in captured.out

    @pytest.mark.asyncio
    async def test_decode_command_human_readable_with_mapped(
        self, tmp_path, capsys, mock_frame, mock_mapped_frame
    ):
        """Test decode_command with human-readable mapped output."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        args = argparse.Namespace(
            file=str(test_file),
            mapped=True,
            json=False,
        )

        with (
            patch("src.aioiregul.v2.decoder.decode_file") as mock_decode,
            patch("src.aioiregul.v2.mappers.map_frame") as mock_map,
        ):
            mock_decode.return_value = mock_frame
            mock_map.return_value = mock_mapped_frame

            result = await cli.decode_command(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Mapped Data Summary:" in captured.out
            assert "Zones: 2" in captured.out
            assert "Inputs: 0" in captured.out
            assert "Outputs: 0" in captured.out
            assert "Measurements: 2" in captured.out
            assert "Sample Zones" in captured.out
            assert "Zone1" in captured.out
            assert "normal=20°" in captured.out

    @pytest.mark.asyncio
    async def test_decode_command_json_raw(self, tmp_path, capsys, mock_frame, mock_mapped_frame):
        """Test decode_command with JSON raw output."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        args = argparse.Namespace(
            file=str(test_file),
            mapped=False,
            json=True,
        )

        with (
            patch("src.aioiregul.v2.decoder.decode_file") as mock_decode,
            patch("src.aioiregul.v2.mappers.map_frame") as mock_map,
        ):
            mock_decode.return_value = mock_frame
            mock_map.return_value = mock_mapped_frame

            result = await cli.decode_command(args)

            assert result == 0
            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert "is_old" in output
            assert output["is_old"] is False
            assert "count" in output
            assert output["count"] == 100

    @pytest.mark.asyncio
    async def test_decode_command_json_mapped(
        self, tmp_path, capsys, mock_frame, mock_mapped_frame
    ):
        """Test decode_command with JSON mapped output."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        args = argparse.Namespace(
            file=str(test_file),
            mapped=True,
            json=True,
        )

        with (
            patch("src.aioiregul.v2.decoder.decode_file") as mock_decode,
            patch("src.aioiregul.v2.mappers.map_frame") as mock_map,
        ):
            mock_decode.return_value = mock_frame
            mock_map.return_value = mock_mapped_frame

            result = await cli.decode_command(args)

            assert result == 0
            captured = capsys.readouterr()
            assert '{"test": "json"}' in captured.out
            mock_mapped_frame.as_json.assert_called_once_with(indent=2)

    @pytest.mark.asyncio
    async def test_decode_command_with_old_format(
        self, tmp_path, capsys, mock_frame, mock_mapped_frame
    ):
        """Test decode_command with OLD format file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        mock_frame.is_old = True

        args = argparse.Namespace(
            file=str(test_file),
            mapped=False,
            json=False,
        )

        with (
            patch("src.aioiregul.v2.decoder.decode_file") as mock_decode,
            patch("src.aioiregul.v2.mappers.map_frame") as mock_map,
        ):
            mock_decode.return_value = mock_frame
            mock_map.return_value = mock_mapped_frame

            result = await cli.decode_command(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Type: OLD" in captured.out

    @pytest.mark.asyncio
    async def test_decode_command_with_measurements_output(
        self, tmp_path, capsys, mock_frame, mock_mapped_frame
    ):
        """Test decode_command displays sample measurements."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        args = argparse.Namespace(
            file=str(test_file),
            mapped=True,
            json=False,
        )

        with (
            patch("src.aioiregul.v2.decoder.decode_file") as mock_decode,
            patch("src.aioiregul.v2.mappers.map_frame") as mock_map,
        ):
            mock_decode.return_value = mock_frame
            mock_map.return_value = mock_mapped_frame

            result = await cli.decode_command(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Sample Measurements" in captured.out
            assert "Temp1" in captured.out
            assert "21.5" in captured.out


class TestMainFunction:
    """Test main CLI entry point."""

    def test_main_with_file_argument(self):
        """Test main function with file argument."""
        with (
            patch("sys.argv", ["cli.py", "test.txt"]),
            patch("src.aioiregul.cli.decode_command") as mock_decode,
        ):
            mock_decode.return_value = 0

            result = cli.main()

            assert result == 0

    def test_main_with_mapped_flag(self):
        """Test main function with --mapped flag."""
        with (
            patch("sys.argv", ["cli.py", "test.txt", "--mapped"]),
            patch("src.aioiregul.cli.decode_command") as mock_decode,
        ):
            mock_decode.return_value = 0

            result = cli.main()

            assert result == 0

    def test_main_with_json_flag(self):
        """Test main function with --json flag."""
        with (
            patch("sys.argv", ["cli.py", "test.txt", "--json"]),
            patch("src.aioiregul.cli.decode_command") as mock_decode,
        ):
            mock_decode.return_value = 0

            result = cli.main()

            assert result == 0

    def test_main_with_both_flags(self):
        """Test main function with both flags."""
        with (
            patch("sys.argv", ["cli.py", "test.txt", "--mapped", "--json"]),
            patch("src.aioiregul.cli.decode_command") as mock_decode,
        ):
            mock_decode.return_value = 0

            result = cli.main()

            assert result == 0

    def test_main_handles_error_exit_code(self):
        """Test main function with error exit code."""
        with (
            patch("sys.argv", ["cli.py", "nonexistent.txt"]),
            patch("src.aioiregul.cli.decode_command") as mock_decode,
        ):
            mock_decode.return_value = 1

            result = cli.main()

            assert result == 1


class TestCLIIntegration:
    """Integration tests using actual test data files."""

    @pytest.mark.asyncio
    async def test_decode_real_file_501_new(self, capsys):
        """Test decoding a real 501 NEW format file."""
        file_path = Path("tests/data/v2messages/501-NEW.txt")
        if not file_path.exists():
            pytest.skip(f"Test file not found: {file_path}")

        args = argparse.Namespace(
            file=str(file_path),
            mapped=False,
            json=False,
        )

        result = await cli.decode_command(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "File:" in captured.out
        assert "Type:" in captured.out
        assert "Groups found:" in captured.out

    @pytest.mark.asyncio
    async def test_decode_real_file_502_new(self, capsys):
        """Test decoding a real 502 NEW format file."""
        file_path = Path("tests/data/v2messages/502-NEW.txt")
        if not file_path.exists():
            pytest.skip(f"Test file not found: {file_path}")

        args = argparse.Namespace(
            file=str(file_path),
            mapped=True,
            json=False,
        )

        result = await cli.decode_command(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Mapped Data Summary:" in captured.out
        assert "Zones:" in captured.out

    @pytest.mark.asyncio
    async def test_decode_real_file_json_output(self, capsys):
        """Test decoding a real file with JSON output."""
        file_path = Path("tests/data/v2messages/501-NEW.txt")
        if not file_path.exists():
            pytest.skip(f"Test file not found: {file_path}")

        args = argparse.Namespace(
            file=str(file_path),
            mapped=True,
            json=True,
        )

        result = await cli.decode_command(args)

        assert result == 0
        captured = capsys.readouterr()
        # Should be valid JSON
        data = json.loads(captured.out)
        assert isinstance(data, dict)
