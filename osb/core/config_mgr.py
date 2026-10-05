"""Remote configuration manager for rclone.

Complies with NASA JPL Power of 10 rules.
Provides CRUD operations, presets, and connection validation for object storage remotes.
"""

import json
from typing import Any, Dict, List, Optional

from osb.core.constants import MAX_REMOTE_COUNT, PROVIDER_S3
from osb.core.logger import log_action, log_error
from osb.core.models import OperationResult, RemoteConfig
from osb.core.rclone_cli import RcloneCli


class ConfigManager:
    """Manages creation, modification, deletion, and testing of rclone remotes."""

    def __init__(self, cli: Optional[RcloneCli] = None) -> None:
        """Initialize configuration manager with CLI reference."""
        self._cli = cli or RcloneCli()
        assert self._cli is not None, "CLI executor must not be None"
        assert isinstance(self._cli, RcloneCli), "CLI must be an instance of RcloneCli"

    def list_remotes(self) -> OperationResult:
        """Fetch all configured remotes parsed into RemoteConfig objects."""
        res = self._cli.execute_command(["config", "dump"], timeout_sec=10)
        if not res.success:
            return res

        try:
            dump_data = json.loads(res.data or "{}")
            assert isinstance(dump_data, dict), "Config dump must return a JSON dictionary"
            remotes: List[RemoteConfig] = []
            keys = list(dump_data.keys())
            bound_count = min(len(keys), MAX_REMOTE_COUNT)

            # NASA Rule 2: Statically bounded loop
            for i in range(bound_count):
                name = keys[i]
                cfg_dict = dump_data[name]
                remote_obj = self._dict_to_remote(name, cfg_dict)
                remotes.append(remote_obj)

            return OperationResult(success=True, message="Remotes loaded", data=remotes)
        except json.JSONDecodeError as err:
            return OperationResult(success=False, message=f"Config JSON error: {str(err)}")

    def _dict_to_remote(self, name: str, cfg: Dict[str, Any]) -> RemoteConfig:
        """Helper to convert dictionary to RemoteConfig dataclass."""
        assert isinstance(name, str) and len(name) > 0, "Remote name must be valid"
        assert isinstance(cfg, dict), "Configuration must be a dictionary"

        rtype = str(cfg.get("type", "s3"))
        provider = str(cfg.get("provider", ""))
        endpoint = str(cfg.get("endpoint", ""))
        region = str(cfg.get("region", ""))
        access_key = str(cfg.get("access_key_id", ""))
        secret_key = str(cfg.get("secret_access_key", ""))
        path_style = str(cfg.get("force_path_style", "true")).lower() == "true"
        env_auth = str(cfg.get("env_auth", "false")).lower() == "true"

        return RemoteConfig(
            name=name,
            type=rtype,
            provider=provider,
            endpoint=endpoint,
            region=region,
            access_key_id=access_key,
            secret_access_key=secret_key,
            force_path_style=path_style,
            env_auth=env_auth,
        )

    def save_remote(self, config: RemoteConfig) -> OperationResult:
        """Create or update a remote using rclone config create with non-interactive flag."""
        assert isinstance(config, RemoteConfig), "Must provide valid RemoteConfig"
        assert len(config.name) > 0, "Remote name cannot be empty"

        args = ["config", "create", config.name, config.type, "--non-interactive"]
        if config.provider:
            args.extend(["provider", config.provider])
        if config.endpoint:
            args.extend(["endpoint", config.endpoint])
        if config.region:
            args.extend(["region", config.region])
        if config.access_key_id:
            args.extend(["access_key_id", config.access_key_id])
        if config.secret_access_key:
            args.extend(["secret_access_key", config.secret_access_key])

        args.extend(["force_path_style", "true" if config.force_path_style else "false"])
        args.extend(["env_auth", "true" if config.env_auth else "false"])

        res = self._cli.execute_command(args, timeout_sec=15)
        assert isinstance(res, OperationResult), "Must return OperationResult"
        if res.success:
            log_action("ConfigManager", f"Remote '{config.name}' saved successfully")
        else:
            log_error("ConfigManager", f"Failed to save remote '{config.name}': {res.message[:120]}")
        return res

    def delete_remote(self, name: str) -> OperationResult:
        """Remove a remote from rclone configuration."""
        assert isinstance(name, str) and len(name) > 0, "Remote name cannot be empty"
        res = self._cli.execute_command(["config", "delete", name], timeout_sec=10)
        assert isinstance(res, OperationResult), "Must return OperationResult"
        if res.success:
            log_action("ConfigManager", f"Remote '{name}' deleted successfully")
        else:
            log_error("ConfigManager", f"Failed to delete remote '{name}': {res.message[:120]}")
        return res

    def test_remote(self, name: str) -> OperationResult:
        """Validate credentials and reachability for given remote."""
        assert isinstance(name, str) and len(name) > 0, "Remote name cannot be empty"
        log_action("ConfigManager", f"Testing connectivity for remote '{name}'")
        res = self._cli.test_connection(name)
        assert isinstance(res, OperationResult), "Must return OperationResult"
        return res

    @staticmethod
    def _get_base_s3_presets() -> List[Dict[str, str]]:
        """Return base S3 and MinIO provider presets."""
        return [
            {
                "id": "minio",
                "label": "MinIO Server (S3-Compatible)",
                "type": PROVIDER_S3,
                "provider": "Minio",
                "endpoint": "http://127.0.0.1:9000",
                "region": "us-east-1",
                "path_style": "true",
            },
            {
                "id": "aws-s3",
                "label": "Amazon Web Services (AWS S3)",
                "type": PROVIDER_S3,
                "provider": "AWS",
                "endpoint": "",
                "region": "us-east-1",
                "path_style": "false",
            },
            {
                "id": "wasabi",
                "label": "Wasabi Hot Cloud Storage",
                "type": PROVIDER_S3,
                "provider": "Wasabi",
                "endpoint": "https://s3.wasabisys.com",
                "region": "us-east-1",
                "path_style": "true",
            },
        ]

    @staticmethod
    def _get_extended_s3_presets() -> List[Dict[str, str]]:
        """Return extended S3-compatible provider presets."""
        return [
            {
                "id": "cloudflare-r2",
                "label": "Cloudflare R2 Storage",
                "type": PROVIDER_S3,
                "provider": "Cloudflare",
                "endpoint": "https://<account_id>.r2.cloudflarestorage.com",
                "region": "auto",
                "path_style": "false",
            },
            {
                "id": "b2-s3",
                "label": "Backblaze B2 (S3-Compatible API)",
                "type": PROVIDER_S3,
                "provider": "Other",
                "endpoint": "https://s3.us-west-004.backblazeb2.com",
                "region": "us-west-004",
                "path_style": "true",
            },
            {
                "id": "ceph",
                "label": "Ceph Object Gateway (RADOS)",
                "type": PROVIDER_S3,
                "provider": "Ceph",
                "endpoint": "http://ceph-rgw:8000",
                "region": "default",
                "path_style": "true",
            },
            {
                "id": "generic-s3",
                "label": "Generic S3-Compatible Storage",
                "type": PROVIDER_S3,
                "provider": "Other",
                "endpoint": "https://s3.example.com",
                "region": "us-east-1",
                "path_style": "true",
            },
        ]

    @classmethod
    def get_provider_presets(cls) -> List[Dict[str, str]]:
        """Return standardized configuration presets for common object storage platforms."""
        presets = cls._get_base_s3_presets() + cls._get_extended_s3_presets()
        assert len(presets) > 0, "Presets list must not be empty"
        assert len(presets) <= 30, "Presets bounded within sanity limit"
        return presets

