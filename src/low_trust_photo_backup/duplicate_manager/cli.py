"""optional - for command-line usage"""

from low_trust_photo_backup.duplicate_manager.core import DuplicateFinder


def main():
    """Command-line interface for duplicate finder."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: uv run duplicate_manager <directory> [min_size_bytes]")
        print("Example: uv run duplicate_manager /path/to/folder 1024")
        sys.exit(1)
    
    directory = sys.argv[1]
    min_size = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    
    try:
        finder = DuplicateFinder(directory, min_size)
        print(f"Scanning: {directory}")
        print(f"Minimum file size: {min_size} bytes\n")
        
        result = finder.find()
        
        if result.total_groups == 0:
            print("No duplicates found.")
        else:
            print(f"{'='*70}")
            print(f"DUPLICATE FILES FOUND")
            print(f"{'='*70}")
            print(f"Total duplicate groups: {result.total_groups}")
            print(f"Total duplicate files: {result.total_files}")
            print(f"Potential space savings: {result.wasted_mb:.2f} MB ({result.wasted_gb:.2f} GB)")
            print(f"{'='*70}\n")
            
            for idx, (file_hash, files) in enumerate(result.duplicates.items(), 1):
                file_size = files[0].stat().st_size
                size_mb = file_size / (1024 * 1024)
                
                print(f"Group {idx}: {len(files)} duplicates ({size_mb:.2f} MB each)")
                print(f"  Hash: {file_hash}")
                
                for file_path in files:
                    print(f"  - {file_path}")
                print()
    
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
