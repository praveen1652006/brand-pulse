"""
Monkey patch to fix snscrape compatibility with Python 3.13
"""
import importlib.util
import sys
import os

def patch_snscrape():
    """Patch snscrape to work with Python 3.13"""
    try:
        # Find the snscrape modules directory
        import snscrape
        snscrape_path = os.path.dirname(snscrape.__file__)
        modules_path = os.path.join(snscrape_path, 'modules')
        
        # Patch the modules/__init__.py
        init_file = os.path.join(modules_path, '__init__.py')
        
        if os.path.exists(init_file):
            with open(init_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print("Original content:")
            print(content)
            print("\n" + "="*50 + "\n")
            
            # Create a completely new __init__.py that works with Python 3.13
            new_content = '''import pkgutil
import importlib.util
import sys

__all__ = []

def _import_modules():
	for importer, moduleName, isPackage in pkgutil.iter_modules(__path__):
		if moduleName.startswith('_'):
			continue
		try:
			# Use importlib for Python 3.12+ compatibility
			if hasattr(importer, 'find_spec'):
				spec = importer.find_spec(moduleName)
				if spec is not None:
					module = importlib.util.module_from_spec(spec)
					sys.modules[f'snscrape.modules.{moduleName}'] = module
					spec.loader.exec_module(module)
					globals()[moduleName] = module
					if hasattr(module, '__all__'):
						__all__.extend(module.__all__)
					else:
						__all__.append(moduleName)
			else:
				# Fallback for older Python versions
				module = importer.find_module(moduleName).load_module(moduleName)
				globals()[moduleName] = module
				if hasattr(module, '__all__'):
					__all__.extend(module.__all__)
				else:
					__all__.append(moduleName)
		except Exception as e:
			print(f"Warning: Could not import module {moduleName}: {e}")
			continue

_import_modules()
'''
            
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"Successfully patched {init_file}")
            return True
        
    except Exception as e:
        print(f"Failed to patch snscrape: {e}")
        return False
    
    return False

if __name__ == "__main__":
    patch_snscrape()
