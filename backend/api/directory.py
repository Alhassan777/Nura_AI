"""
Directory Browser API Endpoints

Simple proof of concept API endpoints for directory operations
to support the frontend DirectoryBrowser component.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
import stat
import mimetypes

router = APIRouter(prefix="/directory", tags=["directory"])

# Base directory for browsing (for security, limit to a specific folder)
BASE_DIR = Path("./demo_filesystem")
BASE_DIR.mkdir(exist_ok=True)


# Create some demo files and folders if they don't exist
def initialize_demo_filesystem():
    """Initialize demo filesystem with sample files and folders"""
    demo_files = {
        "README.md": "# Demo Directory\n\nThis is a demo directory for the Nura frontend component.\n",
        "docs/getting-started.md": "# Getting Started\n\nWelcome to the Nura project!\n",
        "docs/api-reference.md": "# API Reference\n\nAPI documentation here.\n",
        "src/components/Button.tsx": "import React from 'react';\n\nexport const Button = () => {\n  return <button>Click me</button>;\n};\n",
        "src/utils/helpers.ts": "export const formatDate = (date: Date) => {\n  return date.toLocaleDateString();\n};\n",
        "config.json": json.dumps({"name": "nura-demo", "version": "1.0.0"}, indent=2),
        "scripts/setup.sh": "#!/bin/bash\necho 'Setting up project...'\nnpm install\n",
    }

    for file_path, content in demo_files.items():
        full_path = BASE_DIR / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        if not full_path.exists():
            full_path.write_text(content)


# Initialize on startup
initialize_demo_filesystem()


class DirectoryItem(BaseModel):
    name: str
    type: str  # 'file' or 'directory'
    size: Optional[int] = None
    path: str
    modified: Optional[str] = None
    permissions: Optional[str] = None


class DirectoryListing(BaseModel):
    items: List[DirectoryItem]
    current_path: str
    parent_path: Optional[str] = None


class CreateItemRequest(BaseModel):
    path: str
    name: str
    type: str  # 'file' or 'directory'
    content: Optional[str] = None


class UpdateFileContentRequest(BaseModel):
    path: str
    content: str


def safe_path(path: str) -> Path:
    """Ensure path is safe and within BASE_DIR"""
    # Remove leading slash and resolve path
    clean_path = path.lstrip("/")
    full_path = (BASE_DIR / clean_path).resolve()

    # Ensure the path is within BASE_DIR
    if not str(full_path).startswith(str(BASE_DIR.resolve())):
        raise HTTPException(
            status_code=403, detail="Access denied: Path outside allowed directory"
        )

    return full_path


def get_file_info(file_path: Path) -> DirectoryItem:
    """Get file/directory information"""
    try:
        stat_info = file_path.stat()
        relative_path = str(file_path.relative_to(BASE_DIR))

        # Determine type
        item_type = "directory" if file_path.is_dir() else "file"

        # Get size for files
        size = stat_info.st_size if item_type == "file" else None

        # Get modification time
        modified = datetime.fromtimestamp(stat_info.st_mtime).isoformat()

        # Get permissions (simplified)
        permissions = oct(stat_info.st_mode)[-3:]

        return DirectoryItem(
            name=file_path.name,
            type=item_type,
            size=size,
            path=f"/{relative_path}" if relative_path != "." else "/",
            modified=modified,
            permissions=permissions,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error reading file info: {str(e)}"
        )


@router.get("/list", response_model=DirectoryListing)
async def list_directory(path: str = Query("/", description="Directory path to list")):
    """List contents of a directory"""
    try:
        dir_path = safe_path(path)

        if not dir_path.exists():
            raise HTTPException(status_code=404, detail="Directory not found")

        if not dir_path.is_dir():
            raise HTTPException(status_code=400, detail="Path is not a directory")

        items = []

        # List all items in the directory
        for item_path in sorted(dir_path.iterdir()):
            try:
                items.append(get_file_info(item_path))
            except:
                # Skip items that can't be read
                continue

        # Sort: directories first, then files
        items.sort(key=lambda x: (x.type != "directory", x.name.lower()))

        # Determine parent path
        parent_path = None
        if str(dir_path) != str(BASE_DIR):
            parent = dir_path.parent
            parent_relative = str(parent.relative_to(BASE_DIR))
            parent_path = f"/{parent_relative}" if parent_relative != "." else "/"

        current_relative = str(dir_path.relative_to(BASE_DIR))
        current_path = f"/{current_relative}" if current_relative != "." else "/"

        return DirectoryListing(
            items=items, current_path=current_path, parent_path=parent_path
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error listing directory: {str(e)}"
        )


@router.post("/create")
async def create_item(request: CreateItemRequest):
    """Create a new file or directory"""
    try:
        parent_path = safe_path(request.path)

        if not parent_path.exists() or not parent_path.is_dir():
            raise HTTPException(
                status_code=400, detail="Parent directory does not exist"
            )

        new_item_path = parent_path / request.name

        if new_item_path.exists():
            raise HTTPException(status_code=409, detail="Item already exists")

        if request.type == "directory":
            new_item_path.mkdir(parents=True)
        elif request.type == "file":
            new_item_path.write_text(request.content or "")
        else:
            raise HTTPException(status_code=400, detail="Invalid item type")

        return {
            "message": f"{request.type.capitalize()} created successfully",
            "path": str(new_item_path.relative_to(BASE_DIR)),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating item: {str(e)}")


@router.delete("/delete")
async def delete_item(path: str = Query(..., description="Path to item to delete")):
    """Delete a file or directory"""
    try:
        item_path = safe_path(path)

        if not item_path.exists():
            raise HTTPException(status_code=404, detail="Item not found")

        if item_path == BASE_DIR:
            raise HTTPException(status_code=403, detail="Cannot delete root directory")

        if item_path.is_dir():
            # Remove directory and all contents
            import shutil

            shutil.rmtree(item_path)
        else:
            # Remove file
            item_path.unlink()

        return {"message": "Item deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting item: {str(e)}")


@router.get("/file-content")
async def get_file_content(path: str = Query(..., description="Path to file")):
    """Get file content"""
    try:
        file_path = safe_path(path)

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Handle binary files
            content = "[Binary file - cannot display content]"

        return {"content": content, "path": path}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


@router.put("/file-content")
async def update_file_content(request: UpdateFileContentRequest):
    """Update file content"""
    try:
        file_path = safe_path(request.path)

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")

        file_path.write_text(request.content, encoding="utf-8")

        return {"message": "File updated successfully", "path": request.path}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating file: {str(e)}")


# Health check for directory service
@router.get("/health")
async def directory_health():
    """Health check for directory service"""
    return {
        "status": "healthy",
        "service": "directory-browser",
        "base_directory": str(BASE_DIR),
        "base_directory_exists": BASE_DIR.exists(),
    }
