import os
import time
from datetime import datetime
from config import load_config
from content_generator import generate_focus_content
from rules_analyzer import RulesAnalyzer
from rules_generator import RulesGenerator
from rules_watcher import ProjectWatcherManager
import logging
from auto_updater import AutoUpdater

def get_default_config():
    """Get default configuration with parent directory as project path."""
    return {
        'project_path': os.path.abspath(os.path.join(os.path.dirname(__file__), '..')),
        'update_interval': 60,
        'max_depth': 3,
        'ignored_directories': [
            '__pycache__',
            'node_modules',
            'venv',
            '.git',
            '.idea',
            '.vscode',
            'dist',
            'build',
            'CursorFocus'
        ],
        'ignored_files': [
            '.DS_Store',
            '*.pyc',
            '*.pyo'
        ],
        'binary_extensions': [
            '.png',
            '.jpg',
            '.jpeg',
            '.gif',
            '.ico',
            '.pdf',
            '.exe',
            '.bin'
        ],
        'file_length_standards': {
            '.js': 300,
            '.jsx': 250,
            '.ts': 300,
            '.tsx': 250,
            '.py': 400,
            '.css': 400,
            '.scss': 400,
            '.less': 400,
            '.sass': 400,
            '.html': 300,
            '.vue': 250,
            '.svelte': 250,
            '.json': 100,
            '.yaml': 100,
            '.yml': 100,
            '.toml': 100,
            '.md': 500,
            '.rst': 500,
            '.php': 400,
            '.phtml': 300,
            '.ctp': 300,
            'default': 300
        },
        'file_length_thresholds': {
            'warning': 1.0,
            'critical': 1.5,
            'severe': 2.0
        },
        'project_types': {
            'chrome_extension': {
                'indicators': ['manifest.json'],
                'required_files': [],
                'description': 'Chrome Extension'
            },
            'node_js': {
                'indicators': ['package.json'],
                'required_files': [],
                'description': 'Node.js Project'
            },
            'python': {
                'indicators': ['setup.py', 'pyproject.toml'],
                'required_files': [],
                'description': 'Python Project'
            },
            'react': {
                'indicators': [],
                'required_files': ['src/App.js', 'src/index.js'],
                'description': 'React Application'
            },
            'php': {
                'indicators': ['composer.json', 'index.php'],
                'required_files': [],
                'description': 'PHP Project'
            },
            'laravel': {
                'indicators': ['artisan'],
                'required_files': [],
                'description': 'Laravel Project'
            },
            'wordpress': {
                'indicators': ['wp-config.php'],
                'required_files': [],
                'description': 'WordPress Project'
            }
        }
    }

def setup_cursor_focus(project_path):
    """Set up CursorFocus for a project by generating necessary files."""
    try:
        # Generate .cursorrules file
        print(f"Analyzing project: {project_path}")
        analyzer = RulesAnalyzer(project_path)
        project_info = analyzer.analyze_project_for_rules()
        
        rules_generator = RulesGenerator(project_path)
        rules_file = rules_generator.generate_rules_file(project_info)
        print(f"✅ Generated {rules_file}")

        # Generate initial Focus.md with default config
        focus_file = os.path.join(project_path, 'Focus.md')
        default_config = get_default_config()
        content = generate_focus_content(project_path, default_config)
        with open(focus_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Generated {focus_file}")

        print("\n🎉 CursorFocus setup complete!")
        print("Generated files:")
        print(f"- {rules_file}")
        print(f"- {focus_file}")
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        raise

def monitor_project(project_config, global_config):
    """Monitor a single project."""
    project_path = project_config['project_path']
    print(f"\n🔍 Monitoring project: {project_config['name']} at {project_path}")
    
    # Merge project config with global config
    config = {**global_config, **project_config}
    
    focus_file = os.path.join(project_path, 'Focus.md')
    last_content = None
    last_update = 0

    # Start rules watcher for this project
    watcher = ProjectWatcherManager()
    watcher.add_project(project_path, project_config['name'])

    while True:
        current_time = time.time()
        
        if current_time - last_update < config.get('update_interval', 60):
            time.sleep(1)
            continue
            
        content = generate_focus_content(project_path, config)
        
        if content != last_content:
            try:
                with open(focus_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                last_content = content
                print(f"✅ {project_config['name']} Focus.md updated at {datetime.now().strftime('%I:%M:%S %p')}")
            except Exception as e:
                print(f"❌ Error writing Focus.md for {project_config['name']}: {e}")
        
        last_update = current_time

def main():
    """Main function to monitor multiple projects."""
    # Setup logging
    logging.basicConfig(
        level=logging.WARNING,
        format='%(levelname)s: %(message)s'
    )

    # Check updates before running the program
    print("\n🔄 Checking for updates...")
    updater = AutoUpdater()
    update_info = updater.check_for_updates()
    
    if update_info:
        print(f"\n📦 New updates available")
        print(f"Commit: {update_info['message']}")
        print(f"Author: {update_info['author']}")
        print(f"Date: {update_info['date']}")
        
        if input("\nDo you want to update? (y/n): ").lower() == 'y':
            print("\n⏳ Downloading and installing update...")
            if updater.update(update_info):
                print("✅ Update successful! Please restart the application.")
                return
            else:
                print("❌ Update failed. Continuing with current version.")
    else:
        print("✅ You are using the latest version.")

    config = load_config()
    if not config:
        print("No config.json found, using default configuration")
        config = get_default_config()

    if 'projects' not in config:
        # Handle single project config for backward compatibility
        config['projects'] = [{
            'name': 'Default Project',
            'project_path': config['project_path'],
            'update_interval': config.get('update_interval', 60),
            'max_depth': config.get('max_depth', 3)
        }]

    # Create threads for each project
    from threading import Thread
    threads = []
    
    try:
        for project in config['projects']:
            # Setup project if needed
            rules_file = os.path.join(project['project_path'], '.cursorrules')
            if not os.path.exists(rules_file):
                setup_cursor_focus(project['project_path'])

            # Start monitoring thread
            thread = Thread(
                target=monitor_project,
                args=(project, config),
                daemon=True
            )
            thread.start()
            threads.append(thread)

        print("\n📝 Press Ctrl+C to stop all monitors")
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n👋 Stopping all CursorFocus monitors")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == '__main__':
    main() 