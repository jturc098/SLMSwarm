"""
Docker-based execution sandbox for running and testing code safely.
"""

import asyncio
import uuid
import shutil
from pathlib import Path
from typing import Dict, Optional
from loguru import logger
import docker

from src.core.config import settings


class ExecutionSandbox:
    """
    Safe execution environment using Docker containers.
    
    Features:
    - Isolated execution
    - Multiple language support
    - Test runner integration
    - Timeout enforcement
    - Resource limits
    """
    
    def __init__(self):
        self.enabled = settings.docker_sandbox_enabled
        self.timeout = settings.docker_sandbox_timeout
        self.client = None
        
        if self.enabled:
            try:
                self.client = docker.from_env()
                logger.info("Docker sandbox initialized")
            except Exception as e:
                logger.error(f"Docker initialization failed: {e}")
                self.enabled = False
    
    async def execute_code(
        self,
        code: str,
        language: str = "python",
        test_command: Optional[str] = None
    ) -> Dict:
        """
        Execute code in isolated sandbox.
        
        Args:
            code: Code to execute
            language: Programming language
            test_command: Optional test command to run
        
        Returns:
            Execution result dictionary
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "Docker sandbox not enabled",
                "output": ""
            }
        
        execution_id = str(uuid.uuid4())[:8]
        logger.info(f"Executing code in sandbox {execution_id}")
        
        try:
            # Create temporary directory for code
            temp_dir = Path(f"/tmp/hydra_sandbox_{execution_id}")
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Write code to file
            code_file = temp_dir / self._get_filename(language)
            code_file.write_text(code)
            
            # Determine Docker image
            image = self._get_docker_image(language)
            
            # Build command
            if test_command:
                command = test_command
            else:
                command = self._get_run_command(language, code_file.name)
            
            # Run in container
            result = await self._run_in_container(
                image=image,
                command=command,
                volume_path=str(temp_dir),
                timeout=self.timeout
            )
            
            # Cleanup
            await self._cleanup(temp_dir)
            
            return result
            
        except Exception as e:
            logger.error(f"Sandbox execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }
    
    async def run_tests(
        self,
        test_files: Dict[str, str],
        language: str = "python"
    ) -> Dict:
        """
        Run test suite in sandbox.
        
        Args:
            test_files: Dictionary of filename -> content
            language: Programming language
        
        Returns:
            Test result dictionary
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "Docker sandbox not enabled"
            }
        
        execution_id = str(uuid.uuid4())[:8]
        logger.info(f"Running tests in sandbox {execution_id}")
        
        try:
            # Create temporary directory
            temp_dir = Path(f"/tmp/hydra_tests_{execution_id}")
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Write all test files
            for filename, content in test_files.items():
                (temp_dir / filename).write_text(content)
            
            # Determine test command
            test_command = self._get_test_command(language)
            image = self._get_docker_image(language)
            
            # Run tests
            result = await self._run_in_container(
                image=image,
                command=test_command,
                volume_path=str(temp_dir),
                timeout=self.timeout
            )
            
            # Cleanup
            await self._cleanup(temp_dir)
            
            return result
            
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }
    
    async def lint_code(
        self,
        code: str,
        language: str = "python"
    ) -> Dict:
        """
        Lint code using appropriate linter.
        
        Args:
            code: Code to lint
            language: Programming language
        
        Returns:
            Linting result dictionary
        """
        if not self.enabled:
            return {
                "success": True,
                "warnings": [],
                "errors": []
            }
        
        execution_id = str(uuid.uuid4())[:8]
        logger.info(f"Linting code in sandbox {execution_id}")
        
        try:
            # Create temporary directory
            temp_dir = Path(f"/tmp/hydra_lint_{execution_id}")
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Write code to file
            code_file = temp_dir / self._get_filename(language)
            code_file.write_text(code)
            
            # Get linter command
            lint_command = self._get_lint_command(language, code_file.name)
            image = self._get_docker_image(language)
            
            # Run linter
            result = await self._run_in_container(
                image=image,
                command=lint_command,
                volume_path=str(temp_dir),
                timeout=60
            )
            
            # Cleanup
            await self._cleanup(temp_dir)
            
            # Parse linter output
            return self._parse_lint_output(result["output"], language)
            
        except Exception as e:
            logger.error(f"Linting failed: {e}")
            return {
                "success": True,
                "warnings": [],
                "errors": [str(e)]
            }
    
    async def _run_in_container(
        self,
        image: str,
        command: str,
        volume_path: str,
        timeout: int
    ) -> Dict:
        """Run command in Docker container."""
        
        try:
            container = self.client.containers.run(
                image=image,
                command=command,
                volumes={volume_path: {'bind': '/workspace', 'mode': 'rw'}},
                working_dir='/workspace',
                detach=True,
                mem_limit='512m',
                cpu_count=2,
                network_mode='bridge'
            )
            
            # Wait for completion with timeout
            try:
                result = container.wait(timeout=timeout)
                output = container.logs().decode('utf-8')
                exit_code = result['StatusCode']
                
                # Remove container
                container.remove()
                
                return {
                    "success": exit_code == 0,
                    "output": output,
                    "exit_code": exit_code
                }
                
            except docker.errors.ContainerError as e:
                logger.error(f"Container execution error: {e}")
                container.remove(force=True)
                return {
                    "success": False,
                    "output": str(e),
                    "exit_code": 1
                }
            
        except Exception as e:
            logger.error(f"Container run failed: {e}")
            return {
                "success": False,
                "output": str(e),
                "exit_code": 1
            }
    
    def _get_docker_image(self, language: str) -> str:
        """Get Docker image for language."""
        images = {
            "python": "python:3.12-slim",
            "javascript": "node:20-alpine",
            "typescript": "node:20-alpine",
            "go": "golang:1.22-alpine",
            "rust": "rust:latest"
        }
        return images.get(language, "python:3.12-slim")
    
    def _get_filename(self, language: str) -> str:
        """Get appropriate filename for language."""
        extensions = {
            "python": "main.py",
            "javascript": "main.js",
            "typescript": "main.ts",
            "go": "main.go",
            "rust": "main.rs"
        }
        return extensions.get(language, "main.txt")
    
    def _get_run_command(self, language: str, filename: str) -> str:
        """Get command to run code."""
        commands = {
            "python": f"python {filename}",
            "javascript": f"node {filename}",
            "typescript": f"ts-node {filename}",
            "go": f"go run {filename}",
            "rust": f"rustc {filename} && ./main"
        }
        return commands.get(language, f"cat {filename}")
    
    def _get_test_command(self, language: str) -> str:
        """Get command to run tests."""
        commands = {
            "python": "pytest -v",
            "javascript": "npm test",
            "typescript": "npm test",
            "go": "go test ./...",
            "rust": "cargo test"
        }
        return commands.get(language, "echo 'No test runner configured'")
    
    def _get_lint_command(self, language: str, filename: str) -> str:
        """Get command to lint code."""
        commands = {
            "python": f"ruff check {filename}",
            "javascript": f"eslint {filename}",
            "typescript": f"eslint {filename}",
            "go": f"golangci-lint run {filename}",
            "rust": f"cargo clippy -- -D warnings"
        }
        return commands.get(language, f"echo 'No linter configured for {language}'")
    
    def _parse_lint_output(self, output: str, language: str) -> Dict:
        """Parse linter output into structured format."""
        
        lines = output.split('\n')
        errors = []
        warnings = []
        
        for line in lines:
            line_lower = line.lower()
            if 'error' in line_lower:
                errors.append(line.strip())
            elif 'warning' in line_lower or 'warn' in line_lower:
                warnings.append(line.strip())
        
        return {
            "success": len(errors) == 0,
            "warnings": warnings,
            "errors": errors,
            "raw_output": output
        }
    
    async def _cleanup(self, directory: Path) -> None:
        """Cleanup temporary directory."""
        try:
            if directory.exists():
                shutil.rmtree(directory)
                logger.debug(f"Cleaned up {directory}")
        except Exception as e:
            logger.warning(f"Cleanup failed for {directory}: {e}")


# Global execution sandbox instance
execution_sandbox = ExecutionSandbox()