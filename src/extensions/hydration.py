"""
Spec hydration system for filesystem-based state management.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger

from src.core.models import ProjectPlan, ProjectSpec, Task, TaskStatus


class SpecHydration:
    """
    Implements the Hydration Pattern for spec-driven development.
    
    The filesystem acts as the source of truth:
    - spec.md: Project requirements (immutable)
    - plan.md: Technical architecture
    - tasks.md: Task DAG with dependencies
    """
    
    def __init__(self, spec_dir: Path = Path("./specs")):
        self.spec_dir = spec_dir
        self.spec_dir.mkdir(parents=True, exist_ok=True)
        
        self.spec_file = self.spec_dir / "spec.md"
        self.plan_file = self.spec_dir / "plan.md"
        self.tasks_file = self.spec_dir / "tasks.md"
    
    async def hydrate_context(self) -> Dict[str, any]:
        """
        Load all specification files to hydrate agent context.
        
        Returns:
            Dictionary with spec, plan, and tasks
        """
        logger.info("Hydrating context from specification files")
        
        context = {
            "spec": await self.load_spec() if self.spec_file.exists() else None,
            "plan": await self.load_plan() if self.plan_file.exists() else None,
            "tasks": await self.load_tasks() if self.tasks_file.exists() else [],
        }
        
        logger.info(f"Hydrated {len(context['tasks'])} tasks from filesystem")
        return context
    
    async def load_spec(self) -> Optional[ProjectSpec]:
        """Load project specification from spec.md."""
        
        if not self.spec_file.exists():
            return None
        
        content = self.spec_file.read_text()
        
        # Parse markdown sections
        sections = self._parse_markdown_sections(content)
        
        return ProjectSpec(
            title=sections.get("title", "Untitled Project"),
            description=sections.get("description", ""),
            requirements=self._parse_list_section(sections.get("requirements", "")),
            constraints=self._parse_list_section(sections.get("constraints", "")),
            acceptance_criteria=self._parse_list_section(sections.get("acceptance criteria", "")),
            metadata={}
        )
    
    async def load_plan(self) -> Optional[ProjectPlan]:
        """Load project plan from plan.md."""
        
        if not self.plan_file.exists():
            return None
        
        content = self.plan_file.read_text()
        sections = self._parse_markdown_sections(content)
        
        # Parse structured sections
        tech_stack = self._parse_tech_stack(sections.get("tech stack", ""))
        file_structure = self._parse_file_structure(sections.get("file structure", ""))
        
        return ProjectPlan(
            architecture=sections.get("architecture", ""),
            tech_stack=tech_stack,
            file_structure=file_structure,
            api_schema=None,  # Would parse if present
            database_schema=None,  # Would parse if present
            tasks=[],  # Tasks loaded separately
            metadata={}
        )
    
    async def load_tasks(self) -> List[Task]:
        """Load tasks from tasks.md."""
        
        if not self.tasks_file.exists():
            return []
        
        content = self.tasks_file.read_text()
        return self._parse_tasks_markdown(content)
    
    async def save_spec(self, spec: ProjectSpec) -> None:
        """Save specification to spec.md."""
        
        content = f"""# {spec.title}

## Description
{spec.description}

## Requirements
{self._format_list(spec.requirements)}

## Constraints
{self._format_list(spec.constraints)}

## Acceptance Criteria
{self._format_list(spec.acceptance_criteria)}
"""
        self.spec_file.write_text(content)
        logger.info(f"Saved specification to {self.spec_file}")
    
    async def save_plan(self, plan: ProjectPlan) -> None:
        """Save plan to plan.md."""
        
        content = f"""# Technical Plan

## Architecture
{plan.architecture}

## Tech Stack
{self._format_tech_stack(plan.tech_stack)}

## File Structure
```
{self._format_file_structure(plan.file_structure)}
```
"""
        
        if plan.api_schema:
            content += f"\n## API Schema\n```json\n{json.dumps(plan.api_schema, indent=2)}\n```\n"
        
        if plan.database_schema:
            content += f"\n## Database Schema\n```json\n{json.dumps(plan.database_schema, indent=2)}\n```\n"
        
        self.plan_file.write_text(content)
        logger.info(f"Saved plan to {self.plan_file}")
    
    async def save_tasks(self, tasks: List[Task]) -> None:
        """Save tasks to tasks.md."""
        
        content = "# Task List\n\n"
        
        for task in tasks:
            checkbox = "x" if task.status == TaskStatus.COMPLETED else " "
            content += f"- [{checkbox}] **{task.title}** (`{task.id}`)\n"
            content += f"  - Status: {task.status.value}\n"
            content += f"  - Priority: {task.priority.value}\n"
            
            if task.dependencies:
                content += f"  - Depends on: {', '.join(task.dependencies)}\n"
            
            if task.description:
                content += f"  - Description: {task.description}\n"
            
            content += "\n"
        
        self.tasks_file.write_text(content)
        logger.info(f"Saved {len(tasks)} tasks to {self.tasks_file}")
    
    async def update_task_status(self, task_id: str, status: TaskStatus) -> None:
        """Update status of a single task."""
        
        tasks = await self.load_tasks()
        
        for task in tasks:
            if task.id == task_id:
                task.status = status
                break
        
        await self.save_tasks(tasks)
        logger.info(f"Updated task {task_id} to status {status.value}")
    
    def _parse_markdown_sections(self, content: str) -> Dict[str, str]:
        """Parse markdown into sections by headers."""
        
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.split("\n"):
            if line.startswith("##"):
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = line.lstrip("#").strip().lower()
                current_content = []
            elif line.startswith("#"):
                sections["title"] = line.lstrip("#").strip()
            else:
                current_content.append(line)
        
        if current_section:
            sections[current_section] = "\n".join(current_content).strip()
        
        return sections
    
    def _parse_list_section(self, content: str) -> List[str]:
        """Parse markdown list into string list."""
        
        items = []
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("-") or line.startswith("*"):
                items.append(line.lstrip("-*").strip())
        return items
    
    def _parse_tech_stack(self, content: str) -> Dict[str, str]:
        """Parse tech stack section."""
        
        stack = {}
        for line in content.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                stack[key.strip().lstrip("-*")] = value.strip()
        return stack
    
    def _parse_file_structure(self, content: str) -> Dict[str, any]:
        """Parse file structure from code block."""
        # Simplified - would implement tree parsing
        return {"raw": content}
    
    def _parse_tasks_markdown(self, content: str) -> List[Task]:
        """Parse tasks from markdown checklist."""
        
        tasks = []
        current_task = None
        
        for line in content.split("\n"):
            line = line.strip()
            
            # Task checkbox line
            if line.startswith("- ["):
                if current_task:
                    tasks.append(current_task)
                
                # Extract checkbox state
                is_completed = "x" in line[3:5].lower()
                
                # Extract title and ID
                rest = line[5:].strip()
                if "`" in rest:
                    title_part, id_part = rest.split("`", 1)
                    title = title_part.strip().lstrip("**").rstrip("**").strip()
                    task_id = id_part.strip("`").strip()
                else:
                    title = rest.strip().lstrip("**").rstrip("**").strip()
                    task_id = f"task_{len(tasks) + 1}"
                
                current_task = Task(
                    id=task_id,
                    title=title,
                    description="",
                    status=TaskStatus.COMPLETED if is_completed else TaskStatus.PENDING
                )
            
            # Task metadata lines
            elif current_task and line.startswith("- "):
                if "Status:" in line:
                    status_str = line.split("Status:")[1].strip()
                    try:
                        current_task.status = TaskStatus(status_str)
                    except ValueError:
                        pass
                
                elif "Priority:" in line:
                    priority_str = line.split("Priority:")[1].strip()
                    from src.core.models import TaskPriority
                    try:
                        current_task.priority = TaskPriority(priority_str)
                    except ValueError:
                        pass
                
                elif "Depends on:" in line:
                    deps = line.split("Depends on:")[1].strip()
                    current_task.dependencies = [d.strip() for d in deps.split(",")]
                
                elif "Description:" in line:
                    current_task.description = line.split("Description:")[1].strip()
        
        if current_task:
            tasks.append(current_task)
        
        return tasks
    
    def _format_list(self, items: List[str]) -> str:
        """Format list as markdown."""
        return "\n".join(f"- {item}" for item in items)
    
    def _format_tech_stack(self, stack: Dict[str, str]) -> str:
        """Format tech stack as markdown."""
        return "\n".join(f"- **{key}**: {value}" for key, value in stack.items())
    
    def _format_file_structure(self, structure: Dict[str, any]) -> str:
        """Format file structure."""
        # Simplified
        return structure.get("raw", "")