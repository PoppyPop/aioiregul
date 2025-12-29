"""Tests for the IRegul v2 async socket client."""

import asyncio
import contextlib
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from src.aioiregul.v2.client import IRegulClient
from src.aioiregul.v2.mappers import MappedFrame


class TestIRegulClientInit:
    """Test IRegulClient initialization."""

    def test_init_with_explicit_args(self):
        """Test initialization with explicit arguments."""
        client = IRegulClient(
            host="test.local",
            port=8080,
            device_id="dev123",
            password="key456",
            timeout=30.0,
        )

        assert client.host == "test.local"
        assert client.port == 8080
        assert client.device_id == "dev123"
        assert client.password == "key456"
        assert client.timeout == 30.0

    def test_init_with_env_defaults(self, monkeypatch):
        """Test initialization with environment variable defaults."""
        monkeypatch.setenv("IREGUL_HOST", "env.host")
        monkeypatch.setenv("IREGUL_PORT", "9000")
        monkeypatch.setenv("IREGUL_DEVICE_ID", "env_dev")
        monkeypatch.setenv("IREGUL_PASSWORD_V2", "env_key")

        client = IRegulClient()

        assert client.host == "env.host"
        assert client.port == 9000
        assert client.device_id == "env_dev"
        assert client.password == "env_key"

    def test_init_default_host_and_port(self, monkeypatch):
        """Test default host and port values."""
        monkeypatch.setenv("IREGUL_DEVICE_ID", "dev")
        monkeypatch.setenv("IREGUL_PASSWORD_V2", "key")
        monkeypatch.delenv("IREGUL_HOST", raising=False)
        monkeypatch.delenv("IREGUL_PORT", raising=False)

        client = IRegulClient()

        assert client.host == "i-regul.fr"
        assert client.port == 443

    def test_init_missing_required_env_device_id(self, monkeypatch):
        """Test initialization fails with missing IREGUL_DEVICE_ID."""
        monkeypatch.setenv("IREGUL_PASSWORD_V2", "key")
        monkeypatch.delenv("IREGUL_DEVICE_ID", raising=False)

        with pytest.raises(
            ValueError, match="Missing required environment variable: IREGUL_DEVICE_ID"
        ):
            IRegulClient()

    def test_init_missing_required_env_device_key(self, monkeypatch):
        """Test initialization fails with missing IREGUL_DEVICE_KEY."""
        monkeypatch.setenv("IREGUL_DEVICE_ID", "dev")
        monkeypatch.delenv("IREGUL_PASSWORD_V2", raising=False)

        with pytest.raises(
            ValueError, match="Missing required environment variable: IREGUL_PASSWORD_V2"
        ):
            IRegulClient()

    def test_init_partial_env_override(self, monkeypatch):
        """Test partial override of environment variables."""
        monkeypatch.setenv("IREGUL_HOST", "env.host")
        monkeypatch.setenv("IREGUL_PORT", "9000")
        monkeypatch.setenv("IREGUL_DEVICE_ID", "env_dev")
        monkeypatch.setenv("IREGUL_PASSWORD_V2", "env_key")

        client = IRegulClient(host="override.host", port=8888)

        assert client.host == "override.host"
        assert client.port == 8888
        assert client.device_id == "env_dev"
        assert client.password == "env_key"


class TestDefrostCommand:
    """Test the defrost() method."""

    @pytest.mark.asyncio
    async def test_defrost_success(self):
        """Test successful defrost command."""
        client = IRegulClient(
            host="test.local",
            port=443,
            device_id="dev123",
            password="key456",
        )

        # Mock the socket connection
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_writer.close = Mock()
        mock_writer.write = Mock()

        # Simulate defrost success response
        mock_reader.readuntil.return_value = b"defrost_ok}"

        with patch("asyncio.open_connection", return_value=(mock_reader, mock_writer)) as mock_conn:
            result = await client.defrost()

            assert result is True
            mock_conn.assert_called_once_with("test.local", 443, limit=100000)
            mock_writer.write.assert_called_once()
            mock_writer.close.assert_called_once()
            mock_writer.wait_closed.assert_called_once()

            # Verify the message format
            call_args = mock_writer.write.call_args[0][0]
            assert b"cdraminfo" in call_args
            assert b"dev123" in call_args
            assert b"key456" in call_args
            assert b"{203#}" in call_args

    @pytest.mark.asyncio
    async def test_defrost_failure_no_ok(self):
        """Test defrost failure when response doesn't contain defrost_ok."""
        client = IRegulClient(
            host="test.local",
            port=443,
            device_id="dev123",
            password="key456",
        )

        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_writer.close = Mock()
        mock_writer.write = Mock()
        mock_reader.readuntil.return_value = b"error}"

        with patch("asyncio.open_connection", return_value=(mock_reader, mock_writer)):
            result = await client.defrost()

            assert result is False

    @pytest.mark.asyncio
    async def test_defrost_connection_timeout(self):
        """Test defrost with connection timeout."""
        client = IRegulClient(
            host="test.local",
            port=443,
            device_id="dev123",
            password="key456",
            timeout=1.0,
        )

        with (
            patch("asyncio.open_connection", side_effect=TimeoutError("Connection timeout")),
            pytest.raises(TimeoutError, match="Connection timeout to test.local:443"),
        ):
            await client.defrost()

    @pytest.mark.asyncio
    async def test_defrost_connection_refused(self):
        """Test defrost with connection refused."""
        client = IRegulClient(
            host="test.local",
            port=443,
            device_id="dev123",
            password="key456",
        )

        with (
            patch(
                "asyncio.open_connection", side_effect=ConnectionRefusedError("Connection refused")
            ),
            pytest.raises(ConnectionError, match="Failed to connect to test.local:443"),
        ):
            await client.defrost()

    @pytest.mark.asyncio
    async def test_defrost_oserror(self):
        """Test defrost with OSError."""
        client = IRegulClient(
            host="test.local",
            port=443,
            device_id="dev123",
            password="key456",
        )

        with (
            patch("asyncio.open_connection", side_effect=OSError("Network error")),
            pytest.raises(ConnectionError, match="Failed to connect to test.local:443"),
        ):
            await client.defrost()

    @pytest.mark.asyncio
    async def test_defrost_cleanup_on_success(self):
        """Test that writer is properly closed even on success."""
        client = IRegulClient(
            host="test.local",
            port=443,
            device_id="dev123",
            password="key456",
        )

        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_writer.close = Mock()
        mock_writer.write = Mock()
        mock_reader.readuntil.return_value = b"defrost_ok}"

        with patch("asyncio.open_connection", return_value=(mock_reader, mock_writer)):
            await client.defrost()

            mock_writer.close.assert_called_once()
            mock_writer.wait_closed.assert_called_once()

    @pytest.mark.asyncio
    async def test_defrost_cleanup_on_error(self):
        """Test that writer is properly closed even on error."""
        client = IRegulClient(
            host="test.local",
            port=443,
            device_id="dev123",
            password="key456",
        )

        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_writer.close = Mock()
        mock_writer.write = Mock()
        mock_reader.readuntil.side_effect = TimeoutError("Read timeout")

        with patch("asyncio.open_connection", return_value=(mock_reader, mock_writer)):
            with pytest.raises(TimeoutError):
                await client.defrost()

            mock_writer.close.assert_called_once()
            mock_writer.wait_closed.assert_called_once()


class TestGetDataCommand:
    """Test the get_data() method."""

    @pytest.mark.asyncio
    async def test_get_data_success(self):
        """Test successful get_data command."""
        client = IRegulClient(
            host="test.local",
            port=443,
            device_id="dev123",
            password="key456",
        )

        # Mock the socket connection
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_writer.close = Mock()
        mock_writer.write = Mock()

        # Create a minimal mock response that will be decoded
        mock_response = (
            b"NEW15/01/2025 23:38:51{10#mem@0&etat[10]&alarme_flag[False]&journal[initialisation]}"
        )
        mock_reader.readuntil.return_value = mock_response

        with (
            patch("asyncio.open_connection", return_value=(mock_reader, mock_writer)),
            patch("src.aioiregul.v2.client.decode_text") as mock_decode,
        ):
            mock_frame = MagicMock()
            mock_frame.timestamp = datetime(2025, 1, 15, 23, 38, 51)
            mock_frame.is_old = False
            mock_frame.count = 10
            mock_frame.groups = {}
            mock_decode.return_value = mock_frame

            with patch("src.aioiregul.v2.client.map_frame") as mock_map:
                mock_mapped = MagicMock(spec=MappedFrame)
                mock_map.return_value = mock_mapped

                result = await client.get_data()

                assert result == mock_mapped
                mock_writer.write.assert_called_once()
                mock_writer.close.assert_called_once()
                mock_writer.wait_closed.assert_called_once()

                # Verify the message format
                call_args = mock_writer.write.call_args[0][0]
                assert b"cdraminfo" in call_args
                assert b"dev123" in call_args
                assert b"key456" in call_args
                assert b"{502#}" in call_args

    @pytest.mark.asyncio
    async def test_get_data_with_config_skeleton_uses_501_and_merges(self):
        """When provided a skeleton, client should issue 501 and merge values."""
        # Provide a skeleton with keys only (no values)
        skeleton = {
            "mem": {0: {"etat": "", "alarme_flag": ""}},
        }

        client = IRegulClient(
            host="test.local",
            port=443,
            device_id="dev123",
            password="key456",
            config_skeleton=skeleton,
        )

        # Mock the socket connection
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_writer.close = Mock()
        mock_writer.write = Mock()

        # Simulate a NEW frame arriving
        mock_reader.readuntil.return_value = b"NEW15/01/2025 23:38:51{10#mem@0&etat[10]}"

        # Prepare decoded frame with values-only (as from 501)
        decoded_mock = MagicMock()
        decoded_mock.timestamp = datetime(2025, 1, 15, 23, 38, 51)
        decoded_mock.is_old = False
        decoded_mock.count = 10
        decoded_mock.groups = {"mem": {0: {"etat": 10}}}

        with (
            patch("asyncio.open_connection", return_value=(mock_reader, mock_writer)),
            patch("src.aioiregul.v2.client.decode_text") as mock_decode,
            patch("src.aioiregul.v2.client.map_frame") as mock_map,
        ):
            mock_decode.return_value = decoded_mock

            mapped_result = MagicMock(spec=MappedFrame)
            mock_map.return_value = mapped_result

            result = await client.get_data()

            # Ensure we returned the mapped frame
            assert result == mapped_result

            # Verify 501 was used (because skeleton is provided)
            call_args = mock_writer.write.call_args[0][0]
            assert b"{501#}" in call_args

            # Verify merge behavior: keys from skeleton retained, values from 501 overlaid
            # Inspect the merged frame passed to map_frame
            merged_frame_arg = mock_map.call_args[0][0]
            assert merged_frame_arg.groups["mem"][0]["etat"] == 10
            assert merged_frame_arg.groups["mem"][0]["alarme_flag"] == ""

    @pytest.mark.asyncio
    async def test_get_data_populates_skeleton_then_uses_501_on_next_call(self):
        """Without skeleton, first call (502) should populate it; next call should use 501."""
        client = IRegulClient(
            host="test.local",
            port=443,
            device_id="dev123",
            password="key456",
        )

        # First call: no skeleton, expect 502 and skeleton population
        mock_reader1 = AsyncMock()
        mock_writer1 = AsyncMock()
        mock_writer1.close = Mock()
        mock_writer1.write = Mock()
        mock_reader1.readuntil.return_value = (
            b"NEW15/01/2025 23:38:51{10#mem@0&etat[10]&alarme_flag[False]}"
        )

        decoded_502 = MagicMock()
        decoded_502.timestamp = datetime(2025, 1, 15, 23, 38, 51)
        decoded_502.is_old = False
        decoded_502.count = 10
        decoded_502.groups = {
            "mem": {0: {"etat": 10, "alarme_flag": False}},
            "Z": {0: {"zone_nom": "Living Room", "consigne_normal": 20.0}},
        }

        with (
            patch("asyncio.open_connection", return_value=(mock_reader1, mock_writer1)),
            patch("src.aioiregul.v2.client.decode_text") as mock_decode1,
            patch("src.aioiregul.v2.client.map_frame") as mock_map1,
        ):
            mock_decode1.return_value = decoded_502
            mock_map1.return_value = MagicMock(spec=MappedFrame)

            await client.get_data()

            # Verify 502 used and skeleton now populated with actual values from 502
            # mem group should be excluded, Z group should be cached (without dynamic fields)
            call_args1 = mock_writer1.write.call_args[0][0]
            assert b"{502#}" in call_args1
            assert client.config_skeleton == {
                "Z": {0: {"zone_nom": "Living Room", "consigne_normal": 20.0}}
            }

        # Second call: skeleton exists, expect 501 and merged frame
        mock_reader2 = AsyncMock()
        mock_writer2 = AsyncMock()
        mock_writer2.close = Mock()
        mock_writer2.write = Mock()
        mock_reader2.readuntil.return_value = (
            b"NEW15/01/2025 23:39:51{10#Z@0&consigne_normal[21.0]}"
        )

        decoded_501 = MagicMock()
        decoded_501.timestamp = datetime(2025, 1, 15, 23, 39, 51)
        decoded_501.is_old = False
        decoded_501.count = 10
        decoded_501.groups = {"Z": {0: {"consigne_normal": 21.0}}}

        with (
            patch("asyncio.open_connection", return_value=(mock_reader2, mock_writer2)),
            patch("src.aioiregul.v2.client.decode_text") as mock_decode2,
            patch("src.aioiregul.v2.client.map_frame") as mock_map2,
        ):
            mock_decode2.return_value = decoded_501
            mapped_result = MagicMock(spec=MappedFrame)
            mock_map2.return_value = mapped_result

            result = await client.get_data()

            # 501 should be used
            call_args2 = mock_writer2.write.call_args[0][0]
            assert b"{501#}" in call_args2

            # Verify merged frame passed to map_frame contains both fields
            # consigne_normal updated from 501, zone_nom preserved from cached skeleton
            merged_frame_arg = mock_map2.call_args[0][0]
            assert merged_frame_arg.groups["Z"][0]["consigne_normal"] == 21.0
            assert merged_frame_arg.groups["Z"][0]["zone_nom"] == "Living Room"
            assert result is mapped_result

    @pytest.mark.asyncio
    async def test_get_data_connection_timeout(self):
        """Test get_data with connection timeout."""
        client = IRegulClient(
            host="test.local",
            port=443,
            device_id="dev123",
            password="key456",
            timeout=1.0,
        )

        with (
            patch("asyncio.open_connection", side_effect=TimeoutError("Connection timeout")),
            pytest.raises(TimeoutError, match="Connection timeout to test.local:443"),
        ):
            await client.get_data()

    @pytest.mark.asyncio
    async def test_get_data_connection_refused(self):
        """Test get_data with connection refused."""
        client = IRegulClient(
            host="test.local",
            port=443,
            device_id="dev123",
            password="key456",
        )

        with (
            patch(
                "asyncio.open_connection", side_effect=ConnectionRefusedError("Connection refused")
            ),
            pytest.raises(ConnectionError, match="Failed to connect to test.local:443"),
        ):
            await client.get_data()

    @pytest.mark.asyncio
    async def test_get_data_cleanup_on_success(self):
        """Test that writer is properly closed on success."""
        client = IRegulClient(
            host="test.local",
            port=443,
            device_id="dev123",
            password="key456",
        )

        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_writer.close = Mock()
        mock_writer.write = Mock()
        mock_reader.readuntil.return_value = b"NEW15/01/2025 23:38:51{10#}"

        with (
            patch("asyncio.open_connection", return_value=(mock_reader, mock_writer)),
            patch("src.aioiregul.v2.client.decode_text"),
            patch("src.aioiregul.v2.client.map_frame"),
        ):
            try:
                await client.get_data()
            except Exception:
                contextlib.suppress(Exception)

            mock_writer.close.assert_called_once()
            mock_writer.wait_closed.assert_called_once()


class TestReadNewResponse:
    """Test the _read_new_response() helper method."""

    @pytest.mark.asyncio
    async def test_read_new_response_immediate_new(self):
        """Test reading NEW response when first frame is NEW."""
        client = IRegulClient(
            host="test.local",
            port=443,
            device_id="dev123",
            password="key456",
        )

        mock_reader = AsyncMock()
        mock_reader.readuntil.return_value = b"NEW15/01/2025 23:38:51{10#mem@0&etat[10]}"

        result = await client._read_new_response(mock_reader, timeout=5.0)

        assert result == "NEW15/01/2025 23:38:51{10#mem@0&etat[10]}"
        mock_reader.readuntil.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_new_response_skip_old(self):
        """Test reading NEW response after skipping OLD frames."""
        client = IRegulClient(
            host="test.local",
            port=443,
            device_id="dev123",
            password="key456",
        )

        mock_reader = AsyncMock()
        # First call returns OLD, second returns NEW
        mock_reader.readuntil.side_effect = [
            b"OLD15/01/2025 23:34:47{10#}",
            b"NEW15/01/2025 23:38:51{10#}",
        ]

        result = await client._read_new_response(mock_reader, timeout=5.0)

        assert result == "NEW15/01/2025 23:38:51{10#}"
        assert mock_reader.readuntil.call_count == 2

    @pytest.mark.asyncio
    async def test_read_new_response_timeout(self):
        """Test timeout waiting for NEW response."""
        client = IRegulClient(
            host="test.local",
            port=443,
            device_id="dev123",
            password="key456",
        )

        mock_reader = AsyncMock()

        # Simulate a response that will timeout before returning
        async def slow_read(*args, **kwargs):
            await asyncio.sleep(2.0)

        mock_reader.readuntil.side_effect = slow_read

        with pytest.raises(TimeoutError):
            await client._read_new_response(mock_reader, timeout=0.1)

    @pytest.mark.asyncio
    async def test_read_new_response_incomplete_read(self):
        """Test handling of incomplete read from device."""
        client = IRegulClient(
            host="test.local",
            port=443,
            device_id="dev123",
            password="key456",
        )

        mock_reader = AsyncMock()
        mock_reader.readuntil.side_effect = asyncio.IncompleteReadError(b"partial", 10)

        with pytest.raises(ValueError, match="Incomplete response from device"):
            await client._read_new_response(mock_reader, timeout=5.0)

    @pytest.mark.asyncio
    async def test_read_new_response_limit_overrun(self):
        """Test handling of response that exceeds buffer limit."""
        client = IRegulClient(
            host="test.local",
            port=443,
            device_id="dev123",
            password="key456",
        )

        mock_reader = AsyncMock()
        mock_reader.readuntil.side_effect = asyncio.LimitOverrunError("too much data", 1000)

        with pytest.raises(ValueError, match="Response too large or invalid format"):
            await client._read_new_response(mock_reader, timeout=5.0)

    @pytest.mark.asyncio
    async def test_read_new_response_empty_response(self):
        """Test handling of empty response."""
        client = IRegulClient(
            host="test.local",
            port=443,
            device_id="dev123",
            password="key456",
        )

        mock_reader = AsyncMock()
        mock_reader.readuntil.return_value = b""

        with pytest.raises(ValueError, match="Empty response from device"):
            await client._read_new_response(mock_reader, timeout=5.0)


class TestIRegulClientIntegration:
    """Integration tests for IRegulClient."""

    @pytest.mark.asyncio
    async def test_multiple_commands_sequence(self):
        """Test sequence of commands in realistic scenario."""
        client = IRegulClient(
            host="test.local",
            port=443,
            device_id="dev123",
            password="key456",
        )

        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_writer.close = Mock()
        mock_writer.write = Mock()

        # First call for defrost
        mock_reader.readuntil.return_value = b"defrost_ok}"

        with patch("asyncio.open_connection", return_value=(mock_reader, mock_writer)):
            result = await client.defrost()
            assert result is True

            # Reset mock for second call
            mock_writer.reset_mock()
            mock_reader.reset_mock()
            mock_reader.readuntil.return_value = b"NEW15/01/2025 23:38:51{10#}"

            # Second call for get_data
            with patch("src.aioiregul.v2.client.decode_text") as mock_decode:
                mock_frame = MagicMock()
                mock_frame.timestamp = datetime(2025, 1, 15, 23, 38, 51)
                mock_decode.return_value = mock_frame

                with patch("src.aioiregul.v2.client.map_frame") as mock_map:
                    mock_mapped = MagicMock(spec=MappedFrame)
                    mock_map.return_value = mock_mapped

                    result = await client.get_data()
                    assert result == mock_mapped


class TestGetConfigSkeleton:
    """Tests for get_config_skeleton() behavior."""

    @pytest.mark.asyncio
    async def test_get_config_skeleton_issues_502_and_returns_empty_values(self):
        """Client should send 502 and return empty-valued skeleton matching decoded groups."""
        client = IRegulClient(
            host="test.local",
            port=443,
            device_id="dev123",
            password="key456",
        )

        # Mock the socket connection
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_writer.close = Mock()
        mock_writer.write = Mock()

        # Simulate a NEW 502 response frame arriving
        mock_reader.readuntil.return_value = (
            b"NEW15/01/2025 23:38:51{10#mem@0&etat[10]&alarme_flag[False];sondes@1&temp[21.5]}"
        )

        # Prepare decoded frame with full groups (as from 502)
        decoded_mock = MagicMock()
        decoded_mock.timestamp = datetime(2025, 1, 15, 23, 38, 51)
        decoded_mock.is_old = False
        decoded_mock.count = 10
        decoded_mock.groups = {
            "mem": {0: {"etat": 10, "alarme_flag": False}},
            "Z": {
                1: {
                    "zone_nom": "Zone1",
                    "consigne_normal": 21.5,
                    "consigne_reduit": 18.0,
                    "consigne_horsgel": 10.0,
                    "mode_select": 1,
                    "mode": 2,
                }
            },
        }

        # mem group is excluded, Z group should have only non-dynamic fields
        # mode and mode_select are dynamic fields and should not be cached
        expected_skeleton = {
            "Z": {
                1: {
                    "zone_nom": "Zone1",
                    "consigne_normal": 21.5,
                    "consigne_reduit": 18.0,
                    "consigne_horsgel": 10.0,
                }
            },
        }

        with (
            patch("asyncio.open_connection", return_value=(mock_reader, mock_writer)),
            patch("src.aioiregul.v2.client.decode_text") as mock_decode,
            patch("src.aioiregul.v2.client.map_frame") as mock_map,
        ):
            mock_decode.return_value = decoded_mock
            mock_map.return_value = MagicMock(spec=MappedFrame)

            await client.get_data()
            skeleton = client.config_skeleton

            # Ensure writer interaction and command formatting
            mock_writer.write.assert_called_once()
            call_args = mock_writer.write.call_args[0][0]
            assert b"{502#}" in call_args

            # Validate skeleton excludes mem, P, J groups and dynamic fields
            assert skeleton == expected_skeleton

            # Cleanup checks
            mock_writer.close.assert_called_once()
            mock_writer.wait_closed.assert_called_once()

    @pytest.mark.asyncio
    async def test_full_workflow_502_then_501(self):
        """Test complete workflow: first 502 call builds skeleton, second 501 call uses and updates it."""
        # Load real data from test files
        data_dir = Path(__file__).parent / "data" / "v2messages"
        response_502 = (data_dir / "502-NEW-20251227-161838.txt").read_text()
        response_501 = (data_dir / "501-NEW-20251227-161419.txt").read_text()

        client = IRegulClient(
            host="test.local",
            port=443,
            device_id="dev123",
            password="key456",
        )

        # Initially, client has no skeleton
        assert client.config_skeleton is None

        # --- FIRST CALL: 502 (full configuration) ---
        mock_reader_1 = AsyncMock()
        mock_writer_1 = AsyncMock()
        mock_writer_1.close = Mock()
        mock_writer_1.write = Mock()
        mock_reader_1.readuntil.return_value = response_502.encode("utf-8")

        with patch("asyncio.open_connection", return_value=(mock_reader_1, mock_writer_1)):
            result_1 = await client.get_data()

            # Verify 502 command was sent
            call_args_1 = mock_writer_1.write.call_args[0][0]
            assert b"{502#}" in call_args_1

            # Verify result is a MappedFrame
            assert isinstance(result_1, MappedFrame)

            # After first call, skeleton should be built (excluding mem, P, J and dynamic fields)
            assert client.config_skeleton is not None
            skeleton_after_502 = client.config_skeleton

            # Serialize skeleton to JSON using client method
            skeleton_json = client.save_skeleton()

            # Verify JSON serialization worked
            assert isinstance(skeleton_json, str)
            assert len(skeleton_json) > 0

            # Check that skeleton contains expected groups (but not mem, P, J)
            assert "mem" not in skeleton_after_502
            assert "P" not in skeleton_after_502
            assert "J" not in skeleton_after_502

            # Check that Z group exists with zone data (static fields only, no dynamic)
            for _, zone_data in skeleton_after_502["Z"].items():
                # These static fields should be present
                assert isinstance(zone_data, dict)
                # Dynamic fields should not be cached
                assert "valeur" not in zone_data
                assert "resultat" not in zone_data
                assert "etat" not in zone_data

            # Check that A group exists with sensor metadata (but not dynamic fields)
            for _, sensor_data in skeleton_after_502["A"].items():
                # Dynamic fields should not be cached
                assert "valeur" not in sensor_data
                assert "etat" not in sensor_data
                # But static metadata should be present
                assert "type" in sensor_data or "flag" in sensor_data

        # --- SECOND CALL: 501 (values-only) ---
        # Deserialize skeleton from JSON and restore it using client method
        client.load_skeleton_from(skeleton_json)

        # Verify deserialized skeleton matches original
        assert client.config_skeleton == skeleton_after_502

        # Now client has a skeleton, should use 501 command
        mock_reader_2 = AsyncMock()
        mock_writer_2 = AsyncMock()
        mock_writer_2.close = Mock()
        mock_writer_2.write = Mock()
        mock_reader_2.readuntil.return_value = response_501.encode("utf-8")

        with patch("asyncio.open_connection", return_value=(mock_reader_2, mock_writer_2)):
            result_2 = await client.get_data()

            # Verify 501 command was sent (because skeleton exists)
            call_args_2 = mock_writer_2.write.call_args[0][0]
            assert b"{501#}" in call_args_2

            # Verify result is a MappedFrame
            assert isinstance(result_2, MappedFrame)

            # Skeleton should still exist after the 501 call
            # Since mode/mode_select are not cached, skeleton should be identical
            assert client.config_skeleton is not None
            assert client.config_skeleton == skeleton_after_502

            # Result should contain merged data from both skeleton and 501 response
            # The mapped frame should have both cached static fields and dynamic values
            assert result_2 is not None
            assert len(result_2.inputs) > 0  # Verify we have input data from merged response

            assert result_2.measurements.get(4).valeur == 2.11656  # Example access to measurement 4
