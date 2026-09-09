"""
medcen.py - Website Import Handler for Windows Media Centre
Handles web content display and rendering in a fictional Media Centre TV OS
"""

import json
import requests
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class WebImport:
    """Represents a website import configuration"""
    name: str
    url: str
    display_mode: str  # 'fullscreen', 'windowed', 'overlay'
    auto_refresh: int  # seconds, 0 = disabled
    cache_enabled: bool
    last_loaded: Optional[datetime] = None


class MediaCentreWebImporter:
    """Handles website imports for Windows Media Centre"""
    
    def __init__(self, config_path: str = "isexpect.json"):
        self.config = self._load_config(config_path)
        self.imports: Dict[str, WebImport] = {}
        self.cache_dir = Path(self.config.get("cache", {}).get("directory", "./web_cache"))
        self.cache_dir.mkdir(exist_ok=True)
        self.current_import: Optional[WebImport] = None
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found")
            return {}
    
    def add_website_import(self, name: str, url: str, display_mode: str = "fullscreen", 
                          auto_refresh: int = 0, cache_enabled: bool = True) -> Dict:
        """Add a website to import into Media Centre"""
        
        if not self._validate_url(url):
            return {"status": "error", "message": "Invalid URL"}
        
        web_import = WebImport(
            name=name,
            url=url,
            display_mode=display_mode,
            auto_refresh=auto_refresh,
            cache_enabled=cache_enabled
        )
        
        self.imports[name] = web_import
        logger.info(f"Added website import: {name} - {url}")
        
        return {
            "status": "success",
            "import": {
                "name": name,
                "url": url,
                "display_mode": display_mode
            }
        }
    
    def _validate_url(self, url: str) -> bool:
        """Validate URL format"""
        return url.startswith(("http://", "https://"))
    
    def load_website(self, import_name: str) -> Dict:
        """Load and display a website"""
        
        if import_name not in self.imports:
            return {"status": "error", "message": f"Import '{import_name}' not found"}
        
        web_import = self.imports[import_name]
        self.current_import = web_import
        
        try:
            # Try to load from cache first
            if web_import.cache_enabled:
                cached_content = self._get_cached_content(import_name)
                if cached_content:
                    return {
                        "status": "loaded",
                        "import": import_name,
                        "url": web_import.url,
                        "display_mode": web_import.display_mode,
                        "content_source": "cache",
                        "html": cached_content
                    }
            
            # Fetch fresh content
            response = requests.get(web_import.url, timeout=10)
            response.raise_for_status()
            
            html_content = response.text
            
            # Cache if enabled
            if web_import.cache_enabled:
                self._cache_content(import_name, html_content)
            
            web_import.last_loaded = datetime.now()
            
            return {
                "status": "loaded",
                "import": import_name,
                "url": web_import.url,
                "display_mode": web_import.display_mode,
                "content_source": "live",
                "html": html_content,
                "timestamp": web_import.last_loaded.isoformat()
            }
        
        except requests.RequestException as e:
            logger.error(f"Failed to load website {import_name}: {e}")
            return {
                "status": "error",
                "message": f"Failed to load website: {str(e)}"
            }
    
    def _get_cached_content(self, import_name: str) -> Optional[str]:
        """Retrieve cached website content"""
        cache_file = self.cache_dir / f"{import_name}.html"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Failed to read cache for {import_name}: {e}")
        
        return None
    
    def _cache_content(self, import_name: str, html_content: str) -> None:
        """Cache website content locally"""
        cache_file = self.cache_dir / f"{import_name}.html"
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"Cached content for {import_name}")
        except Exception as e:
            logger.warning(f"Failed to cache content for {import_name}: {e}")
    
    def set_display_mode(self, import_name: str, display_mode: str) -> Dict:
        """Change how the website is displayed"""
        
        if import_name not in self.imports:
            return {"status": "error", "message": f"Import '{import_name}' not found"}
        
        valid_modes = ["fullscreen", "windowed", "overlay"]
        
        if display_mode not in valid_modes:
            return {"status": "error", "message": f"Invalid display mode. Valid: {valid_modes}"}
        
        self.imports[import_name].display_mode = display_mode
        
        return {
            "status": "success",
            "import": import_name,
            "display_mode": display_mode
        }
    
    def enable_auto_refresh(self, import_name: str, interval_seconds: int) -> Dict:
        """Enable auto-refresh for a website"""
        
        if import_name not in self.imports:
            return {"status": "error", "message": f"Import '{import_name}' not found"}
        
        self.imports[import_name].auto_refresh = interval_seconds
        
        return {
            "status": "success",
            "import": import_name,
            "auto_refresh": f"{interval_seconds}s"
        }
    
    def list_imports(self) -> Dict:
        """List all website imports"""
        
        imports_list = [
            {
                "name": name,
                "url": imp.url,
                "display_mode": imp.display_mode,
                "auto_refresh": imp.auto_refresh,
                "last_loaded": imp.last_loaded.isoformat() if imp.last_loaded else None
            }
            for name, imp in self.imports.items()
        ]
        
        return {
            "status": "success",
            "total": len(imports_list),
            "imports": imports_list
        }
    
    def remove_import(self, import_name: str) -> Dict:
        """Remove a website import"""
        
        if import_name not in self.imports:
            return {"status": "error", "message": f"Import '{import_name}' not found"}
        
        del self.imports[import_name]
        
        # Clear cache
        cache_file = self.cache_dir / f"{import_name}.html"
        if cache_file.exists():
            cache_file.unlink()
        
        return {
            "status": "success",
            "message": f"Removed import '{import_name}'"
        }


# CLI Usage
if __name__ == "__main__":
    import sys
    
    importer = MediaCentreWebImporter()
    
    # Example: Add YouTube import
    importer.add_website_import("YouTube", "https://youtube.com", "fullscreen", auto_refresh=30)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "load" and len(sys.argv) > 2:
            import_name = sys.argv[2]
            result = importer.load_website(import_name)
            print(json.dumps({k: v for k, v in result.items() if k != 'html'}, indent=2))
        
        elif command == "list":
            result = importer.list_imports()
            print(json.dumps(result, indent=2))
        
        elif command == "add" and len(sys.argv) > 3:
            name = sys.argv[2]
            url = sys.argv[3]
            result = importer.add_website_import(name, url)
            print(json.dumps(result, indent=2))